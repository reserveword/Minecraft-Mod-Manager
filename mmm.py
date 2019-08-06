#-*-coding:utf-8-*-

"""

Minecraft Mod Manager
~~~~~~~~~~~~~~~~~~~~~

WIP
"""

from curse import *
from config import cfg, savecfg, newdir, cfginit
from arg import parse

#find curdir
if cfg['curdir']:
    curdir = cfg['curdir']
#add if no curdir
else:
    curdir = newdir(input('add a directory>'))
    savecfg()

if not curdir:
    print('no current dir!')
    exit()

curdircfg = curdir+'mmm.json'
dircfg = cfginit(curdircfg, {
    'versions':{
        ' (common version) ':{
            'dir':'mods/',
            'content':[],
            'state':'Done',
            'pending':[],
            'versions':[]
        }
    },
    'curver':' (common version) '
})
curdirmod = curdir+dircfg['curver']
manual_version = dircfg.get('manual_version',cfg['manual_version'])


def printtable(table, line_format):
    maxlen = [max(i) for i in zip(*[[len(i) for i in j] for j in table])]
    for line, index in zip(table, range(len(table))):
        print(line_format.format(*line,index=index, maxlen=maxlen))

def choicefromdict(dic, table_head, line_format, choice_prompt):
    li = [table_head]
    kli = [None]
    for k,v in dic.items():
        li.append(v)
        kli.append(k)
    printtable(li,line_format)
    choice = input(choice_prompt)
    if choice.isdecimal():
        choice = int(choice)
        if choice < len(li) and choice > 0:
            return kli[choice]
        else:
            return None
    else:
        return None

def downloaditem(itempid, packflg):
    INDEX = INDEX_PACK if packflg else INDEX_MOD
    res = mod_file_page(itempid,url_filelist=url_filelist[INDEX])
    if manual_version:
        itemfid = choicefromdict(res,('state', 'filename', 'size', 'updateTime', 'gameVersion'),'{index}. {0:^{maxlen[0]}}|{1:<{maxlen[1]}}|{2:^{maxlen[2]}}|{3:<{maxlen[3]}}|{4:^{maxlen[4]}}|','input an index to choose version:')
        if itemfid == None:
            return 'no file selected'
    else:
        ver = dircfg['versions'][dircfg['curver']]['versions']
        for k,v in res.items():
            if v[-1] in ver:
                itemfid = k
                break
        else:
            return 'no version avalible for ' + ver
    print('Downloading', res[itemfid][1])
    mod_file(itempid, itemfid, savePath=(curdir if packflg else curdirmod), url_file=url_file[INDEX])


def help_(cmd, **_):
    if cmd[0] != 'help':
        print('Unknown command. Type `help` to see help.')
    return '''command list:
    help    - show this message
    search  - search and install mod or modpack
    cd      - change or add game directory
    set     - change config

    use `<command> --help` to see details 
    press Ctrl-C to exit
    '''

def search(cmd, flg, opt, par, arg):
    if 'h' in flg or 'help' in opt:
        return '''usage: search [-chip] [--options] [<keyword>|-key=<keyword>|-keyword=<keyword>
-c -i --pid    use keyword as project id
-p --pack      search modpacks instead of mods
-h --help      show this message
-key=keyword 
-keyword=keyword provide keyword'''
    if len(arg) == 1:
        key = arg[0]
    elif len(arg) > 1:
        return 'exactly one keyword is required.'
    elif par.__contains__('key'):
        key = par['key']
    elif par.__contains__('keyword'):
        key = par['keyword']
    else:
        return 'exactly one keyword is required.'
    packflg = 'p' in flg or 'pack' in opt
    INDEX = INDEX_PACK if packflg else INDEX_MOD
    if not ('c' in flg or 'i' in flg or 'pid' in opt):
        res = mod_search(key,url_search[INDEX])
        itempid = choicefromdict(res,('','modName'),'{index}. {0:<{maxlen[0]}}','input an index to choose mod:')
        if itempid == None:
            return 'no mod selected'
    else:
        itempid = key
    downloaditem(itempid, packflg)
    res = mod_dep_list(itempid, url_dep[INDEX])
    for k,v in res.items():
        downloaditem(itempid, False)

def cd(cmd, flg, opt, par, arg):
    if 'h' in flg or 'help' in opt or len(arg) != 1:
        return '''usage: cd <path_to_'.minecraft'>'''
    tmp = newdir(arg[0])
    savecfg()
    return tmp

def ls(cmd, flg, opt, par, arg):
    if 'h' in flg or 'help' in opt:
        return '''usage: ls [-l|--local]'''
    if 'l' in flg or 'local' in opt:
        return '\n'.join(curdircfg['versions'].keys())
    else:
        return '\n'.join(cfg['dirs'])

def changecfg(cmd, flg, opt, par, arg):
    if 'h' in flg or 'help' in opt:
        return '''usage: set [-a|--add] [-l|--local] [<key> <value>|-<key>=<value>]
keys: 
version - current active game version
manual - whether to decide mod version manually'''
    addflg = 'a' in flg or 'add' in opt
    locflg = 'l' in flg or 'local' in opt
    for k,v in par.items():
        if k in ('v','ver','version'):
            key = 'v'
            val = v
            break
        elif k in ('m','man','manual','manual_version'):
            key = 'm'
            val = v
            break
    else:
        if len(arg) == 2:
            if k in ('v','ver','version'):
                key = 'v'
                val = v
            elif k in ('m','man','manual','manual_version'):
                key = 'm'
                val = v
            else:
                return 'key not specified'
        else:
            return 'exactly one pair of key-value required'
    if k == 'v':
        if addflg or v.strip() == '' or v in dircfg['versions'].keys():
            dircfg['curver'] = v
            savecfg(dircfg, curdircfg)
        else:
            return 'version not exist. use [-a|--add] to add one, or choose from below:\n'+'\n'.join(dircfg.keys)+'\n\nYou may use \' \'(a space) for common version'
    elif k == 'm':
        if v.lower() in ('true','t','y','yes','on'):
            v = True
        elif v.lower in ('false','f','n','no','off'):
            v = False
        else:
            return 'usage: set manual [-l|--local] (on|off)'
        if locflg:
            dircfg['manual_version'] = v
        else:
            cfg['manual_version'] = v
        manual_version = dircfg.get('manual_version',cfg['manual_version'])
    else:
        'Something Bad Happened'

commands = {
    'help':help_,
    'search':search,
    'cd': cd,
    'ls': ls,
    'set': changecfg
}
try:
    while True:
        cmd = parse(input('mmm@'+curdir+'>'))
        func = commands.get(cmd['cmd'],help_)
        print(func(**cmd))
except EOFError|KeyboardInterrupt:
    print('ended')
    pass
