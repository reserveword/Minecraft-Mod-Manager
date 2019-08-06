#-*-coding:utf-8-*-

"""

Parse Args
"""

import re

STATE_ACCEPT = 0
STATE_REQUIRE = 1

split_re = re.compile(r'(\'(?:\\\'|[^\'])*\'|\"(?:\\\"|[^\"])*\"|(?:[^\'\" ]|\\\'|\\\")+)|( +)')

def split(cmd):
    """
    Split a str into parts. 
    Parts are divided by spaces(` `). 
    Quoted(`'`or`"`) strings and escaped(`\`) characters 
    are decoded and will keep together.

    ### example:
     - input: `' cmd -c   --command="with space and escaped\\\\n" quote\\\\\\\'Q\\\\\\\''`
     - output: `['cmd','-c','--command=with space and escaped\\n','quote\\\'Q\\\'']`
         
    """
    tmp = re.findall(split_re, cmd.strip())
    cmd = ['']
    for c,_ in tmp:
        if len(c):
            if c[0] in '"\'':
                c = c[1:-1]
            cmd[-1] += c
        else:
            cmd.append(c)
    if not len(cmd):
        cmd = ['']
    return cmd
    

def parse(cmd):
    """
    Parse command into args.
    Accept complete string or iterable of string,
    uses arg.split to split if needed.

    It follows the rules below orderly:
     - first string is command itself.
     - if a string contains `=`, it's a par.
     - if a string starts with `--`, it's an opt.
     - if a string starts with `-`, it's a bunch of flg-s
     - otherwise, it's an arg.
     - par is parsed like `-{key}={value}` or `--{key}={value}`,
       see examples below for details.
    
    Special cases: 
     - If a par does not start with `-` or `--`, 
       it's considered as an arg. 
     - String `'-'` is a flg `-`.
     - String `'--'` is an opt `--`
    
    Returns:

    a dict, with five entries below:
     - `cmd`, a `str` representing the command.
     - `flg`, a `set` including all flg-s.
     - `opt`, a `set` including all opt-s.
     - `par`, a `dict` including all par-s.
     - `arg`, a `list` of all arg-s in the same order as input.

    ### examples:
     - `'-aux'` is a bunch of flg-s `{a,u,x}`
     - `'-c'` is a flg `c`
     - `'-'` is a flg `-`
     - `'--verbose'` is an opt `verbose`
     - `'--'` is an opt ` `(empty string)
     - `'all-the-mods'` is an arg `all-the-mods`
     - `'-infile=Program Files` is a par `{'infile':'Program Files'}`
     - `'--password=123456'` is a par `{'password':'123456'}`
     - `'myfield=myvalue'` *is an arg* `myfield=myvalue`
    """
    if isinstance(cmd, str):
        cmd = split(cmd)
    flg = set()
    opt = set()
    par = {}
    arg = []
    flg2 = False
    state = STATE_ACCEPT
    for c in cmd[1:]:
        delim = c.find('=')
        if not len(c):
            continue
        elif c[0] != '-':
            arg.append(c)
        elif delim != -1:
            par[c[:delim].strip('-')] = c[delim+1:]
        elif len(c) > 1 and c[1] == '-':
            opt.add(c[2:])
        elif len(c) == 1:
            flg2 = True
        else:
            flg.update(c)
    if not flg2:
        flg.discard('-')
    return {'cmd':cmd[0],'flg':flg, 'opt':opt, 'par':par, 'arg':arg}