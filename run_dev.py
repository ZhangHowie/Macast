"""Dev launcher — uses a separate config dir to avoid conflicts with the installed Macast.app."""
import os
import sys
import pathlib

# Must be set before any macast import so SETTING_DIR picks it up at module load time.
dev_config = str(pathlib.Path.home() / 'Library' / 'Application Support' / 'xfangfang' / 'Macast-dev')
os.environ.setdefault('MACAST_SETTING_DIR', dev_config)

import gettext
import random
from macast import Setting
from macast.utils import SettingProperty
from macast.macast import gui


def get_base_path(path="."):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), path)


if __name__ == '__main__':
    pathlib.Path(dev_config).mkdir(parents=True, exist_ok=True)
    # Clear stale log so errors from this run are easy to spot
    try:
        os.remove(os.path.join(dev_config, 'macast.log'))
    except FileNotFoundError:
        pass

    candidates = [
        get_base_path('bin/MacOS/mpv'),
        '/Applications/Macast.app/Contents/Resources/bin/MacOS/mpv',
    ]
    Setting.mpv_default_path = next((p for p in candidates if os.path.exists(p)), 'mpv')

    Setting.load()
    Setting.set(SettingProperty.DLNA_FriendlyName, 'Test')
    gui()
