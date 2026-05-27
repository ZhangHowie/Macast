# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is Macast

Macast is a cross-platform menu bar / system tray application that acts as a **DLNA Media Renderer**. It advertises itself on the local network via SSDP/UPnP, allowing DLNA clients (e.g. a phone running a video app) to push media to be played on the computer using mpv.

## Running / Debugging

**macOS:**
```shell
pip install -r requirements/darwin.txt
python Macast.py
```

**Windows / Linux:**
```shell
pip install -r requirements/common.txt
python Macast.py
# Linux fallback if tray icon doesn't appear:
export PYSTRAY_BACKEND=gtk && python3 Macast.py
```

mpv must be installed separately (system package on Linux, bundled binary on macOS/Windows — see `docs/Development.md`).

## Building / Packaging

See `docs/Development.md` for platform-specific packaging commands (py2app on macOS, pyinstaller on Windows/Linux).

## Internationalization

```shell
# Extract strings
xgettext macast/macast.py -o i18n/macast.pot

# Update existing translations
msgmerge -NU --no-location i18n/zh_CN/LC_MESSAGES/macast.po i18n/macast.pot

# Compile to binary
msgfmt -o i18n/zh_CN/LC_MESSAGES/macast.mo i18n/zh_CN/LC_MESSAGES/macast.po
```

Translation files live in `i18n/<locale>/LC_MESSAGES/`.

## Architecture

The app has four interlocking layers wired together by the **CherryPy event bus** (`cherrypy.engine.publish` / `cherrypy.engine.subscribe`). Components never import each other directly; they communicate exclusively through named bus events.

### 1. Entry point — `Macast.py`
Bootstraps locale, sets the mpv binary path, then calls `macast.macast.gui()`.

### 2. GUI / App — `macast/macast.py` + `macast/gui.py`
`Macast` (subclass of `App`) owns the system tray / menu bar. It constructs a `Service`, wires bus subscriptions for service lifecycle events (`start`, `stop`, `renderer_av_uri`, `ssdp_update_ip`, …), and starts the cast service. `App` is a thin cross-platform shim: **rumps** on macOS, **pystray** everywhere else.

### 3. Service / CherryPy plugins — `macast/server.py` + `macast/plugin.py`
`Service` hosts a CherryPy HTTP server (with `AutoPortServer` for automatic port fallback) and three CherryPy `SimplePlugin`s:
- `RendererPlugin` — wraps the active `Renderer`, subscribes all `set_media_*` methods to the bus.
- `ProtocolPlugin` — wraps the active `Protocol`, subscribes all `set_state_*` methods to the bus.
- `SSDPPlugin` — runs the SSDP/UPnP discovery server and periodically re-announces the device.

### 4. Protocol — `macast/protocol.py`
`DLNAProtocol` implements UPnP AVTransport / RenderingControl / ConnectionManager. It parses incoming SOAP actions, dispatches them to the renderer via `cherrypy.engine.publish('set_media_*')`, and maintains the UPnP state table used by DLNA clients to track playback state. XML service descriptions live in `macast/xml/`.

### 5. Renderer — `macast/renderer.py` + `macast_renderer/mpv.py`
`Renderer` is the abstract base class. `MPVRenderer` (in `macast_renderer/`) drives mpv over a Unix socket (or named pipe on Windows) using JSON IPC. It observes mpv properties (`volume`, `pause`, `time_pos`, …) and calls `set_state_*` on the protocol to keep the DLNA state table in sync.

### Plugin system — `macast/macast.py` (`MacastPlugin` / `MacastPluginManager`)
Third-party renderers and protocols are `.py` files dropped into the user config directory (`appdirs.user_config_dir('Macast', 'xfangfang')`). Each plugin file contains XML metadata comments (`<macast.renderer>ClassName</macast.renderer>` etc.) that `MacastPlugin.load_from_file` parses with regex, then dynamically imports the class. The default renderer is `MPVRenderer` and the default protocol is `DLNAProtocol`.

### Settings — `macast/utils.py`
`Setting` is a class-level (not instance-level) key-value store backed by `macast_setting.json` in the user config dir. `SettingProperty` is the enum of known keys. `SETTING_DIR` is the user config root; custom plugin directories (`renderer/`, `protocol/`) are created there at startup.

## Writing a Custom Renderer

Subclass `macast.renderer.Renderer` and implement the `set_media_*` methods. Add plugin metadata comments at the top of the file:

```python
# <macast.renderer>MyRenderer</macast.renderer>
# <macast.title>My Player</macast.title>
# <macast.platform>darwin,win32,linux</macast.platform>
```

Drop the file into `<config_dir>/renderer/`. See `macast_renderer/mpv.py` for the full reference implementation and the project wiki for the Custom-Renderer tutorial.
