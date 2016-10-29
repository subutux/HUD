#!/usr/bin/env python3
from setuptools import setup
import re

"""
Try to load the locals of pygame.
If that works, dont require pygame. This
is a simple (but effective) fix for Raspbian
who has the pygame package installed by default.
"""

install_requires= [

    "homeassistant==0.31.1",
    "icon-font-to-png==0.3.6",
    "Jinja2==2.8",
    "MarkupSafe==0.23",
    "Pillow==3.4.2",
    "pytz==2016.7",
    "PyYAML==3.12",
    "requests==2.11.1",
    "six==1.10.0",
    "sseclient==0.0.12",
    "tinycss==0.4",
    "typing==3.5.2.2",
    "voluptuous==0.9.2",
    "pgu==0.18"
]

try:
    import pygame.locals
except ImportError as e:
    install_requires.append("pygame==1.9.2b8")
    pass

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
    packages = ["hud"],
    description = "Home Assistant UI Display",
    long_description = long_descr,
    author = "Stijn Van Campenhout",
    author_email = "subutux@gmail.com",
    licence = "MIT",
    package_data = {'hud': [
        'pgu.theme/style.ini',
        'pgu.theme/*.png',
        'pgu.theme/*.ttf',
        'pgu.theme/mdi/materialdesignicons.css',
        'pgu.theme/mdi/materialdesignicons-webfont.ttf'
        ]
    },
    entry_points = {
        "console_scripts": ['hud = hud.hud:main']
    },
    data_files = [
        ('/etc/default',['scripts/hud.opts']),
        ('/etc/systemd/system',['scripts/hud.service']),
        ('/usr/local/sbin',['scripts/hud.init'])
    ],
    install_requires = install_requires,
    dependency_links = [        
        "https://github.com/parogers/pgu/archive/67558479fe9050ba567a39fc9faa32ce74eba786.tar.gz#egg=pgu-0.18",
        "https://bitbucket.org/pygame/pygame/get/010a750596cf.tar.gz#egg=pygame-1.9.2b8"
    ],
    url = "https://github.com/subutux/HUD",
    download_url = "https://github.com/subutux/HUD/tarball/{}".format(version),
    keywords = ["pygame","rpi","ui","touchscreen","homeassistant"]
)
