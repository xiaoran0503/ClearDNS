#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import subprocess
import sys

source = [
    'curl -sfL https://github.com/felixonmars/dnsmasq-china-list/raw/master/accelerated-domains.china.conf'
    ' | sed \'/^#/d\' | sed \'s/server=\\///g;s/\\/114.114.114.114//g\'',
    'curl -sfL https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/direct-list.txt'
    ' | grep -v \':\'',
    'curl -sfL https://github.com/hq450/fancyss/raw/master/rules/WhiteList_new.txt'
    ' | sed \'s/Server=\\///g;s/\\///g\'',
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
    sys.exit('ERROR: all %d sources failed, refuse to write empty chinalist.txt' % len(source))
if failed:
    print('[warn] %d/%d sources failed' % (failed, len(source)), file=sys.stderr)
regex = r'^(?=^.{3,255}$)[a-zA-Z0-9][a-zA-Z0-9\-]{0,62}(\\.[a-zA-Z0-9][a-zA-Z0-9\-]{0,62})+$'
domains = {x for x in domains if re.search(regex, str(x)) is not None}  # filter invalid domains
with open('chinalist.txt', 'w') as fileObj:
    fileObj.write('\n'.join(sorted(domains)) + '\n')
