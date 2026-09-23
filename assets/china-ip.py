#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
from netaddr import IPSet
from netaddr import IPAddress
from netaddr import IPNetwork
from netaddr.core import AddrFormatError

operators = ['china', 'cmcc', 'chinanet', 'unicom', 'tietong', 'cernet', 'cstnet', 'drpeng', 'googlecn']
operators += ['%s6' % x for x in operators]  # add `...6` suffix
source = [
    'curl -sfL https://github.com/misakaio/chnroutes2/raw/master/chnroutes.txt | sed \'/^#/d\'',
    'curl -sfL https://github.com/metowolf/iplist/raw/master/data/special/china.txt',
    'curl -sfL https://github.com/17mon/china_ip_list/raw/master/china_ip_list.txt',
] + ['curl -sfL https://gaoyifan.github.io/china-operator-ip/%s.txt' % x for x in operators]

ipAddrs = set()
failed = 0
for script in source:  # traverse fetch commands
    proc = subprocess.run(script, shell=True, capture_output=True, text=True)
    if proc.returncode != 0:  # source fetch failed (curl -f or pipeline error)
        failed += 1
        print('[warn] source failed: %s' % script[:80], file=sys.stderr)
        continue
    raw = proc.stdout.split('\n')
    ipAddrs.update(filter(None, raw))
if not ipAddrs:  # all sources failed -> refuse to write empty asset
    sys.exit('ERROR: all %d sources failed, refuse to write empty china-ip.txt' % len(source))
if failed:
    print('[warn] %d/%d sources failed' % (failed, len(source)), file=sys.stderr)

ipv4 = IPSet()
ipv6 = IPSet()
for ipAddr in ipAddrs:  # load all IP data
    try:
        ip = IPNetwork(ipAddr) if '/' in ipAddr else IPAddress(ipAddr)
        ipv4.add(ip) if ip.version == 4 else ipv6.add(ip)
    except AddrFormatError as e:
        print('[warn] invalid IP entry %r: %s' % (ipAddr, e), file=sys.stderr)

with open('china-ip.txt', 'w') as fileObj:  # save to file
    fileObj.write('\n'.join([str(ip) for ip in ipv4.iter_cidrs()]) + '\n')  # format into CIDR
    fileObj.write('\n'.join([str(ip) for ip in ipv6.iter_cidrs()]) + '\n')
