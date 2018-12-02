#!/usr/bin/env python3
from setuptools import setup
import re

"""
Try to load the locals of pygame.
If that works, dont require pygame. This
is a simple (but effective) fix for Raspbian
who has the pygame package installed by default.
"""

install_requires = [

    "homeassistant>0.77",
    "icon-font-to-png==0.3.6",
    "Pillow==3.4.2",
    "requests>=2.20.0",
    "tinycss==0.4",
    "pgu@https://github.com/parogers/pgu/archive/67558479fe9050ba567a39fc9faa32ce74eba786.tar.gz",  # nopep8
    "pygame>=1.9.2b8",
    "moosegesture>=1.0.2",
    "websocket-client>=0.54.0",
    "imagesize >= 1.1.0"
]

version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('hud/hud.py').read(),
    re.M
).group(1)


with open("README.md", "rb") as f:
    long_descr = f.read().decode("utf-8")


setup(
    name="hud",
    version=version,
    packages=["hud"],
    description="Home Assistant UI Display",
    long_description=long_descr,
    author="Stijn Van Campenhout",
    author_email="subutux@gmail.com",
    licence="MIT",
    package_data={'hud': [
        'pgu.theme/style.ini',
        'pgu.theme/*.png',
        'pgu.theme/*.ttf',
        'pgu.theme/mdi/materialdesignicons.css',
        'pgu.theme/mdi/materialdesignicons-webfont.ttf'
    ]
    },
    entry_points={
        "console_scripts": ['hud = hud.hud:main']
    },
    data_files=[
        ('/etc/default', ['scripts/hud.opts']),
        ('/etc/systemd/system', ['scripts/hud.service']),
        ('/usr/local/sbin', ['scripts/hud.init'])
    ],
    install_requires=install_requires,
    url="https://github.com/subutux/HUD",
    download_url="https://github.com/subutux/HUD/tarball/{}".format(version),
    keywords=["pygame", "rpi", "ui", "touchscreen", "homeassistant"]
)
