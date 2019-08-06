#-*-coding:utf-8-*-

"""

config support
"""

import json
import platform
import os

cfgpath = {
    'Windows':'%AppData%/mmm/',
    'Linux':'/etc/mmm/',
    'Mac OS':'./',
    'Java':'./',
    '':'./'
}[platform.system()]

os.makedirs(cfgpath, exist_ok=True)
cfgpath += 'mmm.json'

def cfginit(path=cfgpath, default={}):
    try:
        with open(path, 'r') as f:
            cfg = json.load(f)
    except FileNotFoundError:
        cfg = default
        with open(path, 'x') as f:
            json.dump(cfg, f)
    return cfg

cfg = cfginit(default={
    'dirs':[],
    'curdir':None,
    'manual_version':False
})

def savecfg(config=None, path=cfgpath):
    global cfg
    if config == None:
        config = cfg
    try:
        with open(cfgpath, 'w') as f:
            json.dump(config, f)
    except IOError as e:
        print(e)

def newdir(path):
    if not len(path):
        path = './'
    path.replace('\\','/')
    if not path.endswith('/'):
        path == '/'
    if not path.endswith('.minecraft/'):
        path += '.minecraft/'
    if not path in cfg['dirs']:
        cfg['dirs'].append(path)
    cfg['curdir'] = path
    os.makedirs(path, exist_ok=True)
    return path