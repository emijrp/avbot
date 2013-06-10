#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import hashlib
import re
import sys

index = {}
texts = {}
rules = {}

def log(l):
    f = open('log.html', 'a')
    f.write(l.encode('utf-8'))
    f.close()

def loadindex():
    global index
    f = open('dataset/index.txt', 'r')
    raw = unicode(f.read(), 'utf-8')
    f.close()
    for l in raw.splitlines()[1:]:
        k, v, t = l.split(';')
        index[k] = {'oldid': v, 'class': t}

def loadtext(revid):
    f = open('dataset/%s.txt' % (revid), 'r')
    raw = f.read()
    f.close()
    return raw

def loadtexts():
    global texts
    global index
    for revid, v in index.items():
        if not texts.has_key(revid):
            texts[revid] = loadtext(revid)
        if not texts.has_key(v['oldid']):
            texts[v['oldid']] = loadtext(v['oldid'])

def loadrules():
    global rules
    
    rulesfiles = glob.glob('rules/rules*.txt')
    for rulesfile in rulesfiles:
        rules[rulesfile] = {}
        f = open(rulesfile, 'r')
        raw = f.read().splitlines()
        f.close()
        for l in raw:
            l = l.strip()
            if not l or l.startswith('#') or not ';;;' in l:
                continue
            rule, points = l.split(';;;')
            rules[rulesfile][rule] = {'compiled': re.compile(rule), 'points': points}

def analize(revid, oldid, rules):
    global texts
    
    revidtext = texts[revid]
    oldidtext = texts[oldid]
    points = 0
    for rule_r, rule_p in rules.items():
        points = (len(re.findall(rule_r, revidtext)) * rule_p) - (len(re.findall(rule_r, oldidtext)) * rule_p)
    
    return points >= 0 and 'REGULAR' or 'REVERTED'

def main():
    global index
    global texts
    global rules
    
    loadindex()
    loadtexts()
    loadrules()
    
    for rulesfile, rules2 in rules.items():
        reverts = 0
        solreverted = 0
        solregular = 0
        falsepositives = 0
        for revid, v in index.items():
            if v['class'] == 'REVERTED':
                reverts += 1
            sol = analize(revid, v['oldid'], rules2)
            index[revid]['solution'] = sol
            #print revid, sol
            
            if sol == 'REVERTED':
                solreverted += 1
                if v['class'] != sol:
                    falsepositives += 1
            elif sol == 'REGULAR':
                solregular += 1
                if v['class'] != sol:
                    log('<li>ESCAPED: <a href="http://zu.wikipedia.org/w/index.php?oldid=%s&diff=prev" target="_blank">%s</a><br/>' % (revid, revid))
        
        print '%d reverted (%.1f%% false positives) of %d vandalisms (%.1f%%)' % (solreverted, falsepositives/(solreverted/100.0), reverts, solreverted/(reverts/100.0))
    
if __name__ == '__main__':
    main()

