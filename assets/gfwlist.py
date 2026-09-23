#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import subprocess
import sys

source = [
    'curl -sfL https://github.com/Loukky/gfwlist-by-loukky/raw/master/gfwlist.txt | base64 -d | '
    'sed \'/^$\\|@@/d\' | sed \'s#!.\\+##;s#|##g;s#@##g;s#http:\\/\\/##;s#https:\\/\\/##;\' | '
    'sed \'/^[0-9]\\+\\.[0-9]\\+\\.[0-9]\\+\\.[0-9]\\+$/d\' | grep \'^[0-9a-zA-Z\\.-]\\+$\' | '
    'grep "\\." | sed \'s#^\\.\\+##\'',
    'curl -sfL https://github.com/gfwlist/gfwlist/raw/master/gfwlist.txt | base64 -d | '
    'sed \'/^$\\|@@/d\' | sed \'s#!.\\+##;s#|##g;s#@##g;s#http:\\/\\/##;s#https:\\/\\/##;\' | '
    'sed \'/^[0-9]\\+\\.[0-9]\\+\\.[0-9]\\+\\.[0-9]\\+$/d\' | grep \'^[0-9a-zA-Z\\.-]\\+$\' | '
    'grep "\\." | sed \'s#^\\.\\+##\'',
    'curl -sfL https://github.com/hq450/fancyss/raw/master/rules/gfwlist.conf | '
    'sed \'s/ipset=\\/\\.//g;s/\\/gfwlist//g;/^server/d\'',
    'curl -sfL https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/gfw.txt',
]

domains = set()
failed = 0
for script in source:  # traverse fetch commands
    proc = subprocess.run(script, shell=True, capture_output=True, text=True)
    if proc.returncode != 0:  # source fetch failed (curl -f or pipeline error)
        failed += 1
        print('[warn] source failed: %s' % script[:80], file=sys.stderr)
        continue
    raw = proc.stdout.split('\n')
    domains.update(filter(None, raw))
if not domains:  # all sources failed -> refuse to write empty asset
    sys.exit('ERROR: all %d sources failed, refuse to write empty gfwlist.txt' % len(source))
if failed:
    print('[warn] %d/%d sources failed' % (failed, len(source)), file=sys.stderr)
regex = r'^(?=^.{3,255}$)[a-zA-Z0-9][a-zA-Z0-9\-]{0,62}(\.[a-zA-Z0-9][a-zA-Z0-9\-]{0,62})+$'
domains = {x for x in domains if re.search(regex, str(x)) is not None and re.match(r'^\d{1,3}(\.\d{1,3}){3}$', str(x)) is None}  # filter invalid domains / bare IPv4
with open('gfwlist.txt', 'w') as fileObj:
    fileObj.write('\n'.join(sorted(domains)) + '\n')
