#!/usr/bin/env python3
"""End-to-end check: a throwaway Jellyfin with one finished series, Next Up asked the way Android TV asks.

Usage: e2e_test.py <jellyfin image> <plugin out dir>
Needs docker and ffmpeg. Runs the server twice: without the plugin, then with it.
"""
import json, os, shutil, subprocess, sys, tempfile, time, urllib.request

IMAGE, PLUGIN_OUT = sys.argv[1], sys.argv[2]
BASE = "http://127.0.0.1:18096"
AUTH = 'MediaBrowser Client="e2e", Device="e2e", DeviceId="e2e", Version="1"'
work = tempfile.mkdtemp(prefix="jf-e2e-")
season = os.path.join(work, "tv", "Test Show", "Season 01")
os.makedirs(season)
os.makedirs(os.path.join(work, "config"))
os.makedirs(os.path.join(work, "cache"))
token = ""


def call(method, path, body=None):
    headers = {"Content-Type": "application/json", "Authorization": AUTH + (f', Token="{token}"' if token else "")}
    data = json.dumps(body).encode() if body is not None else None
    with urllib.request.urlopen(urllib.request.Request(BASE + path, data, headers, method=method), timeout=30) as r:
        raw = r.read()
        return json.loads(raw) if raw else None


def start():
    subprocess.run(["docker", "rm", "-f", "jf-e2e"], capture_output=True)
    subprocess.run(["docker", "run", "-d", "--name", "jf-e2e", "-u", f"{os.getuid()}:{os.getgid()}",
                    "-p", "127.0.0.1:18096:8096", "-v", f"{work}/config:/config", "-v", f"{work}/cache:/cache",
                    "-v", f"{work}/tv:/data/tv:ro", IMAGE], check=True, capture_output=True)
    for _ in range(90):
        try:
            if call("GET", "/System/Info/Public")["StartupWizardCompleted"] is not None:
                return
        except Exception:
            time.sleep(2)
    sys.exit("server did not start")


def next_up(uid, extra=""):
    # Same parameters as the Android TV home row (HomeFragmentHelper.loadNextUp).
    items = call("GET", f"/Shows/NextUp?userId={uid}&limit=50&enableResumable=false{extra}")["Items"]
    return [f"S{i['ParentIndexNumber']:02}E{i['IndexNumber']:02}" for i in items]


try:
    for e in (1, 2, 3):
        subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=black:s=64x64:d=2",
                        "-c:v", "libx264", os.path.join(season, f"Test Show - S01E{e:02}.mkv")], check=True)

    start()
    call("POST", "/Startup/Configuration", {"UICulture": "en-US", "MetadataCountryCode": "AU", "PreferredMetadataLanguage": "en"})
    call("GET", "/Startup/User")
    call("POST", "/Startup/User", {"Name": "e2e", "Password": "e2e"})
    call("POST", "/Startup/RemoteAccess", {"EnableRemoteAccess": True})
    call("POST", "/Startup/Complete")
    login = call("POST", "/Users/AuthenticateByName", {"Username": "e2e", "Pw": "e2e"})
    token, uid = login["AccessToken"], login["User"]["Id"]
    call("POST", "/Library/VirtualFolders?name=TV&collectionType=tvshows&refreshLibrary=true",
         {"LibraryOptions": {"PathInfos": [{"Path": "/data/tv"}]}})

    for _ in range(90):
        eps = call("GET", f"/Items?userId={uid}&recursive=true&includeItemTypes=Episode")["Items"]
        if len(eps) == 3 and all("IndexNumber" in e and "ParentIndexNumber" in e for e in eps):
            break
        time.sleep(2)
    else:
        sys.exit(f"library scan did not find 3 numbered episodes: {eps}")
    ids = {e["IndexNumber"]: e["Id"] for e in eps}

    # Watched the whole series a month ago, then rewatched E01 today.
    for n in (1, 2, 3):
        call("POST", f"/UserPlayedItems/{ids[n]}?userId={uid}&datePlayed=2026-09-0{n}T12:00:00Z")
    call("POST", f"/UserPlayedItems/{ids[1]}?userId={uid}&datePlayed=2026-10-29T12:00:00Z")

    without = next_up(uid)
    shutil.copytree(PLUGIN_OUT, os.path.join(work, "config", "plugins", "Rewatch Next Up_1.0.0.0"))
    shutil.copy(os.path.join(os.path.dirname(__file__), "meta.json"), os.path.join(work, "config", "plugins", "Rewatch Next Up_1.0.0.0"))
    subprocess.run(["docker", "restart", "jf-e2e"], check=True, capture_output=True)
    token = ""
    start_wait = time.time()
    while time.time() - start_wait < 180:
        try:
            token = call("POST", "/Users/AuthenticateByName", {"Username": "e2e", "Pw": "e2e"})["AccessToken"]
            break
        except Exception:
            time.sleep(2)
    plugins = [p["Name"] + " " + p["Status"] for p in call("GET", "/Plugins")]
    with_plugin = next_up(uid)
    explicit_off = next_up(uid, "&enableRewatching=false")

    print("plugins:", plugins)
    print("without plugin:", without)
    print("with plugin:", with_plugin)
    print("with plugin, client sends enableRewatching=false:", explicit_off)
    assert "Rewatch Next Up Active" in plugins
    assert without == [], without
    assert with_plugin == ["S01E02"], with_plugin
    assert explicit_off == [], explicit_off
    print("PASS")
finally:
    subprocess.run(["docker", "rm", "-f", "jf-e2e"], capture_output=True)
    shutil.rmtree(work, ignore_errors=True)
