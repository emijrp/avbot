#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import wikipedia

f = open('output.xml', 'r')
acum = u''
for l in f:
    acum += unicode(l, 'utf-8')
    if re.search(ur"</revert>", l):
        revert = acum.split('<revert ')[1].split('</revert>')[0]
        oldtext = revert.split('<oldtext xml:space="preserve">')[1].split('</oldtext')[0]
        newtext = revert.split('<newtext xml:space="preserve">')[1].split('</newtext')[0]
        acum = u''
        wikipedia.showDiff(oldtext, newtext)

f.close()
