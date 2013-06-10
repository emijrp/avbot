#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

import query
import wikipedia

site = wikipedia.Site('en', 'wikipedia')

def getprevrevid(pageid='', revid=''):
    #http://en.wikipedia.org/w/api.php?action=query& prop=revisions&pageids=3977443&rvstartid=558979915&rvlimit=1
    params = {
        'action': 'query',
        'prop': 'revisions',
        'pageids': pageid,
        'rvstartid': revid,
        'rvlimit': 1,
    }
    data = query.GetData(params, site = site)
    if not 'error' in data.keys():
        return data['query']['pages'][str(pageid)]['revisions'][0]['parentid']
    return ''

def getdiff(fromrev='', torev=''):
    params = {
        'action': 'compare',
        'fromrev': fromrev,
        'torev': torev,
    }
    data = query.GetData(params, site = site)
    if not 'error' in data.keys():
        return data['compare']['*'].strip()
    return ''

def getrevtext(pageid='', revid=''):
    #http://en.wikipedia.org/w/api.php?action=query& prop=revisions&pageids=3977443&rvstartid=558979915&rvlimit=1&rvprop=content
    params = {
        'action': 'query',
        'prop': 'revisions',
        'pageids': pageid,
        'rvstartid': revid,
        'rvlimit': 1,
        'rvprop': 'content',
    }
    data = query.GetData(params, site = site)
    if not 'error' in data.keys():
        return data['query']['pages'][str(pageid)]['revisions'][0]['*']
    return ''

def quote(t=''):
    return re.sub('<', '&lt;', re.sub('>', '&gt;', t))
    
def main():
    output = []
    ns = 0
    params = {
        'action': 'query',
        'list': 'recentchanges',
        'rcstart': '20130608235959',
        'rcdir': 'older',
        'rcnamespace': ns,
        'rcshow': '!bot',
        'rclimit': 5,
        'rctype': 'edit',
        'rcprop': 'ids|title|timestamp|user|comment',
    }
    data = query.GetData(params, site = site)
    if not 'error' in data.keys():
        for rev in data['query']['recentchanges']:
            #[(u'comment', u'Reverting possible vandalism by [[Special:Contributions/Zenwhite44|Zenwhite44]] to version by Addbot. False positive? [[User:ClueBot NG/FalsePositives|Report it]]. Thanks, [[User:ClueBot NG|ClueBot NG]]. (1665331) (Bot)'), (u'rcid', 583484766), (u'pageid', 3977443), (u'title', u'Darenth'), (u'timestamp', u'2013-06-08T23:59:24Z'), (u'revid', 558979925), (u'old_revid', 558979915), (u'user', u'ClueBot NG'), (u'ns', 0), (u'type', u'edit')]
            vandal_revid = rev['old_revid']
            prevvandal_revid = getprevrevid(rev['pageid'], vandal_revid) #la anterior puede ser del vandalo tb, de momento no me importa
            
            vandal_text = getrevtext(rev['pageid'], vandal_revid)
            prevvandal_text = getrevtext(rev['pageid'], prevvandal_revid)
            diff = getdiff(prevvandal_revid, vandal_revid)
            
            output.append(u"""    <revert pageid="%s" ns="%s" old_revid="%s" revid="%s">
        <oldtext xml:space="preserve">%s</oldtext>
        <newtext xml:space="preserve">%s</newtext>
        <diff xml:space="preserve">%s</diff>
    </revert>""" % (rev['pageid'], ns, prevvandal_revid, vandal_revid, quote(prevvandal_text), quote(vandal_text), quote(diff)))
    
    output = u'<dataset>\n%s\n</dataset>' % ('\n'.join(output))
    f = open('output.xml', 'w')
    f.write(output.encode('utf-8'))
    f.close()

if __name__ == '__main__':
    main()
