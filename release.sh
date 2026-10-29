#!/usr/bin/env bash
# Build one version, add it to manifest.json and publish it as a GitHub release.
# Usage: ./release.sh <version, e.g. 1.0.0.0> <target ABI, e.g. 12.2.0.0> "<changelog>"
set -euo pipefail
cd "$(dirname "$0")"
V=$1 ABI=$2 NOTES=$3
REPO=lanjak/jellyfin-plugin-rewatch-nextup
ZIP=rewatch-nextup_$V.zip

python3 - "$V" "$ABI" <<'EOF'
import json, sys
m = json.load(open("meta.json"))
m["version"], m["targetAbi"] = sys.argv[1], sys.argv[2]
json.dump(m, open("meta.json", "w"), indent=2)
EOF

rm -rf out "$ZIP"
docker run --rm -v "$PWD":/src -w /src -u "$(id -u):$(id -g)" -e HOME=/tmp -e DOTNET_CLI_TELEMETRY_OPTOUT=1 \
  mcr.microsoft.com/dotnet/sdk:10.0 dotnet publish -c Release -o /src/out -p:AssemblyVersion="$V" -p:FileVersion="$V"
zip -j -q "$ZIP" out/Jellyfin.Plugin.RewatchNextUp.dll meta.json

python3 - "$V" "$ABI" "$NOTES" "$(md5sum "$ZIP" | cut -d' ' -f1)" "https://github.com/$REPO/releases/download/v$V/$ZIP" <<'EOF'
import datetime, json, sys
v, abi, notes, checksum, url = sys.argv[1:]
meta = json.load(open("meta.json"))
manifest = json.load(open("manifest.json"))
if not manifest:
    manifest = [{k: meta[k] for k in ("guid", "name", "description", "overview", "owner", "category")} | {"versions": []}]
versions = [x for x in manifest[0]["versions"] if x["version"] != v]
stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
manifest[0]["versions"] = [{"version": v, "changelog": notes, "targetAbi": abi, "sourceUrl": url, "checksum": checksum, "timestamp": stamp}] + versions
json.dump(manifest, open("manifest.json", "w"), indent=2)
EOF

gh release create "v$V" "$ZIP" --repo "$REPO" --title "v$V" --notes "$NOTES"
git add manifest.json meta.json
git commit -q -m "Release v$V"
git push -q
