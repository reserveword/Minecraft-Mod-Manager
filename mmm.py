#-*-coding:utf-8-*-

"""

Minecraft Mod Manager
~~~~~~~~~~~~~~~~~~~~~

WIP
"""

import html5lib
import requests
import sys
import time
from concurrent.futures import ThreadPoolExecutor

w3 = '{http://www.w3.org/1999/xhtml}'
url_base = 'https://www.curseforge.com/minecraft'

url_mods = url_base + '/mc-mods'
url_searchmod = url_mods + '/search?search={key}'
url_mod = url_mods + '/{modpid}'
url_modfilelist = url_mod + '/files/all?page={page}'
url_modfile = url_mod + '/download/{modfid}/file'
url_moddep = url_mod + '/relations/dependencies?page={page}'

url_packs = url_base + '/modpacks'
url_searchpack = url_packs + '/search?search={key}'
url_pack = url_packs + '/{packpid}'
url_packfilelist = url_pack + '/files/all?page={page}'
url_packfile = url_pack + '/download/{packfid}/file'
url_packdep = url_pack + '/relations/dependencies?page={page}'

tp = ThreadPoolExecutor(7)

def urllastpiece(url):
    """runcates a url and return the last part of it

    examples:

        'http://some.website/some/path' => 'path'
        'some.website/path/' => 'path'
        'some.website/' => 'some.website'
        'http://' => ''(empty string)"""
    offset = url[:-1].rfind('/')    #in case it ends with '/'
    return url[offset+1:].strip('/')

def cliprogressbar(total, length=100):
    """a CLI progress bar
    
    usage:

        bar = cliprogressbar(1024)
        for i in range(1024):
            yourthings()
            bar()
        bar(end=True)"""
    lastupd = 0
    done = 0
    def inner(end=False):   #call this when progress inc by 1
        nonlocal lastupd, done
        done += 1
        part = int(length*done/total)
        percent = int(100*done/total)
        now = time.time()
        if now > lastupd+1 or end:
            if end:
                done = total
            lastupd = now
            sys.stdout.write('\r['+'>'*part+'-'*(length-part)+']'+str(percent)+'%')
            sys.stdout.flush()
            if end:
                print()
    return inner

def mod_search(key, page=1):
    """search in curseforge minecraft/mc-mods with keyword=key

    Note: parameter `page` is not used currently
    
    Return Value:

        dict:projectId => name"""
    modlist = {}
    response = requests.get(url_searchmod.format(key=key, page=page)).text
    for a in html5lib.parse(response).findall(f'.//{w3}a'):
        title = a.find(f'./{w3}h3')
        if title != None:
            modlist[urllastpiece(a.attrib['href'])] = title.text
    return modlist

def mod_file_page(modpid, page=1):
    """given mod projectId from `mod_search`, search avalible files.
    
    Return Value:

        dict:fileId => (state, filename, size, updateTime, gameVersion)"""
    filelist = {}
    response = requests.get(url_modfilelist.format(modpid=modpid, page=page)).text
    for tr in html5lib.parse(response).findall(f'.//{w3}tr'):
        row = tr.findall(f'./{w3}td')[:5]
        if not row:
            continue
        row[0] = row[0].find(f'./*/{w3}span').text.strip()
        tmp = row[1].find(f'./{w3}a')
        modfid = urllastpiece(tmp.attrib['href'])
        row[1] = tmp.text.strip()
        row[2] = row[2].text.strip()
        row[3] = row[3].find(f'./{w3}abbr').attrib['data-epoch']
        row[4] = row[4].find(f'./{w3}div/{w3}div').text.strip()
        filelist[modfid] = row
    return filelist

def mod_file(modpid, modfid, savePath='', progressbar=True, overwrite=None):
    """download file with given mod projectId and fileId
    
    Note: Unless `progressbar` is disabled and `overwrite` is set, this method interacts with standard I/O

        overwrite: bool or function () => bool"""
    response = requests.get(url_modfile.format(modpid=modpid,modfid=modfid), stream=True)
    blocklength = 8192
    if progressbar:
        pbar = cliprogressbar(int(response.headers['Content-Length'].strip())/blocklength)
    filename = savePath + urllastpiece(response.request.url)
    try:
        with open(filename,'xb') as fd:
            for chunk in response.iter_content(blocklength):
                fd.write(chunk)
                if progressbar:
                    pbar()
    except FileExistsError as e:
        ow = None
        if overwrite is bool:
            ow = overwrite
        elif overwrite is function:
            ow = overwrite()
        if ow == None:      #it actually supports overwrite() returns None and use stdio for decision
            ow = input(f'File {filename} already exists. Overwrite?[y/N]').lower() in ('y', 'yes')
        if ow:
            with open(filename,'wb') as fd:
                for chunk in response.iter_content(blocklength):
                    fd.write(chunk)
                    if progressbar:
                        pbar()
        else:
            response.close()
            return
    if progressbar:
        pbar(end=True)

def mod_dep_list(modpid):
    modlist = {}
    lastlist = None
    for i in range(500):
        sublist = mod_dep_page(modpid, i+1)
        if sublist == lastlist:
            return modlist
        else:
            modlist.update(sublist)
    return modlist

def mod_dep_page(modpid, page):
    modlist = {}
    response = requests.get(url_moddep.format(modpid=modpid, page=page)).text
    for a in html5lib.parse(response).findall(f'.//{w3}a'):
        title = a.find(f'./{w3}h3')
        if title != None:
            modlist[urllastpiece(a.attrib['href'])] = title.text
    return modlist

def pack_search(key, page=1):
    packlist = {}
    response = requests.get(url_searchpack.format(key=key, page=page)).text
    for a in html5lib.parse(response).findall(f'.//{w3}a'):
        title = a.find(f'./{w3}h3')
        if title != None:
            packlist[urllastpiece(a.attrib['href'])] = title.text
    return packlist

def pack_file_page(packpid, page=1):
    filelist = {}
    response = requests.get(url_packfilelist.format(packpid=packpid, page=page)).text
    for tr in html5lib.parse(response).findall(f'.//{w3}tr'):
        row = tr.findall(f'./{w3}td')[:5]
        if not row:
            continue
        row[0] = row[0].find(f'./*/{w3}span').text.strip()
        tmp = row[1].find(f'./{w3}a')
        packfid = urllastpiece(tmp.attrib['href'])
        row[1] = tmp.text.strip()
        row[2] = row[2].text.strip()
        row[3] = row[3].find(f'./{w3}abbr').attrib['data-epoch']
        row[4] = row[4].find(f'./{w3}div/{w3}div').text.strip()
        filelist[packfid] = row
    return filelist

def pack_file(packpid, packfid, savePath='', progressbar=True, overwrite=None):
    response = requests.get(url_packfile.format(packpid=packpid,packfid=packfid), stream=True)
    blocklength = 8192
    if progressbar:
        pbar = cliprogressbar(int(response.headers['Content-Length'].strip())/blocklength)
    filename = savePath + urllastpiece(response.request.url)
    try:
        with open(filename,'xb') as fd:
            for chunk in response.iter_content(blocklength):
                fd.write(chunk)
                if progressbar:
                    pbar()
    except FileExistsError as e:
        ow = None
        if overwrite is bool:
            ow = overwrite
        elif overwrite is function:
            ow = overwrite()
        if ow == None:      #it actually supports overwrite() returns None and use stdio for decision
            ow = input(f'File {filename} already exists. Overwrite?[y/N]').lower() in ('y', 'yes')
        if ow:
            with open(filename,'wb') as fd:
                for chunk in response.iter_content(blocklength):
                    fd.write(chunk)
                    if progressbar:
                        pbar()
        else:
            response.close()
            return
    if progressbar:
        pbar(end=True)

def pack_dep_list(packpid):
    packlist = {}
    pagenum = 1
    response = requests.get(url_packdep.format(packpid=packpid, page=1)).text
    for a in html5lib.parse(response).findall(f'.//{w3}a'):
        title = a.find(f'./{w3}h3')
        if title != None:
            packlist[urllastpiece(a.attrib['href'])] = title.text
        if a.attrib.__contains__('class') and a.attrib['class'].find('pagination-item') != -1:
            newpage = a.find(f'{w3}span')
            if (newpage != None) and isinstance(newpage.text,str):
                newpage = newpage.text
                if newpage.isdecimal():
                    pagenum = max(int(newpage),pagenum)
    for sublist in tp.map(pack_dep_page,(packpid,)*(pagenum-1),range(2,pagenum+1)):
        packlist.update(sublist)
    return packlist

def pack_dep_page(packpid, page):
    packlist = {}
    response = requests.get(url_packdep.format(packpid=packpid, page=page)).text
    for a in html5lib.parse(response).findall(f'.//{w3}a'):
        title = a.find(f'./{w3}h3')
        if title != None:
            packlist[urllastpiece(a.attrib['href'])] = title.text
    return packlist
