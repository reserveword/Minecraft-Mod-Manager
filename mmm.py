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

def searchmod(key, page=1):
    """search in curseforge minecraft/mc-mods with keyword=key

    Note: parameter `page` is not used currently
    
    Return Value:

        dict:projectId => name"""
    modlist = {}
    response = requests.get(f'https://www.curseforge.com/minecraft/mc-mods/search?search={key}').text
    for a in html5lib.parse(response).findall('.//{http://www.w3.org/1999/xhtml}a'):
        title = a.find('./{http://www.w3.org/1999/xhtml}h3')
        if title != None:
            modlist[urllastpiece(a.attrib['href'])] = title.text
    return modlist

def searchfile(modpid, page=1):
    """given mod projectId from `searchmod`, search avalible files.
    
    Return Value:

        dict:fileId => (state, filename, size, updateTime, gameVersion)"""
    filelist = {}
    response = requests.get(f'https://www.curseforge.com/minecraft/mc-mods/{modpid}/files/all?page={page}').text
    for tr in html5lib.parse(response).findall('.//{http://www.w3.org/1999/xhtml}tr'):
        row = tr.findall('./{http://www.w3.org/1999/xhtml}td')[:5]
        if not row:
            continue
        row[0] = row[0].find('./*/{http://www.w3.org/1999/xhtml}span').text.strip()
        tmp = row[1].find('./{http://www.w3.org/1999/xhtml}a')
        modfid = urllastpiece(tmp.attrib['href'])
        row[1] = tmp.text.strip()
        row[2] = row[2].text.strip()
        row[3] = row[3].find('./{http://www.w3.org/1999/xhtml}abbr').attrib['data-epoch']
        row[4] = row[4].find('./{http://www.w3.org/1999/xhtml}div/{http://www.w3.org/1999/xhtml}div').text.strip()
        filelist[modfid] = row
    return filelist

def getfile(modpid, modfid, savePath='', progressbar=True, overwrite=None):
    """download file with given mod projectId and fileId
    
    Note: Unless `progressbar` is disabled and `overwrite` is set, this method interacts with standard I/O

        overwrite: bool or function () => bool"""
    response = requests.get(f'https://www.curseforge.com/minecraft/mc-mods/{modpid}/download/{modfid}/file', stream=True)
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

