# Rewatch Next Up for Jellyfin

This plugin shows the next episode of a series that you rewatch in Next Up, on all clients.

## The problem

Jellyfin builds Next Up from the furthest episode that you watched. When you watch all of a series, Next Up does not show that series again. If you rewatch the series, Next Up does not show the next episode.

Jellyfin has a fix for this: the `enableRewatching` option of the `/Shows/NextUp` API. With this option, Next Up uses the episode that you played last and shows the next episode after it. But the server default is `false`, and only some clients send the option. The web client has the setting "Enable rewatching in Next Up". The Android TV client and other clients do not send the option.

## What the plugin does

The plugin sets `enableRewatching=true` on each Next Up request that does not set the option. If a client sends the option, the plugin uses the value from the client. Thus the web client setting continues to operate.

The plugin does not change the Next Up logic of Jellyfin. It only turns on the rewatching mode that Jellyfin already has.

## Install

1. In Jellyfin, go to **Dashboard > Plugins > Repositories**.
2. Add this repository URL:

   ```
   https://raw.githubusercontent.com/lanjak/jellyfin-plugin-rewatch-nextup/main/manifest.json
   ```

3. Go to **Catalog**, find **Rewatch Next Up** and install it.
4. Restart Jellyfin.

To install manually, download the zip file from [Releases](https://github.com/lanjak/jellyfin-plugin-rewatch-nextup/releases). Extract it to `<config>/plugins/Rewatch Next Up_<version>/` and restart Jellyfin.

To stop the plugin, go to **Dashboard > Plugins**, disable the plugin and restart Jellyfin.

## Known behavior

When you rewatch an earlier episode of a series that you did not finish, Next Up can show two episodes of that series. One is the next new episode. The other is the next episode after the episode that you rewatched. This is the standard rewatching mode of Jellyfin.

## Compatibility

| Plugin | Jellyfin |
| ------ | -------- |
| 1.0.0.0 | 12.2 |

## Build

The build uses the .NET 10 SDK:

```
dotnet publish -c Release -o out
```

## Test

`e2e_test.py` starts a temporary Jellyfin container with a test series of three episodes. It marks all episodes as watched, then marks episode 1 as watched again. It then gets Next Up with the same request as the Android TV client, first without the plugin and then with the plugin. You must have Docker and ffmpeg.

```
python3 e2e_test.py jellyfin/jellyfin:latest out
```

## Release

`release.sh` builds the plugin, adds the version to `manifest.json` and makes a GitHub release:

```
./release.sh 1.0.0.0 12.2.0.0 "First release"
```

## License

GPL-3.0. See [LICENSE](LICENSE).
