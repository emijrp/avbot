#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib
import os
import re
import sys

def unescape(s):
    if '&' not in s:
        return s
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&apos;", "'")
    s = s.replace("&quot;", '"')
    s = s.replace("&amp;", "&") # Must be last
    return s

def saverev(rid, rtext):
    f = open('dataset/%s.txt' % (rid), 'w')
    f.write(rtext.encode('utf-8'))
    f.close()

def getreverts(revisions):
    cpagerevs = len(revisions)
    cpagerev = 0
    revertids = []
    if cpagerevs >= 3:
        while cpagerev <= cpagerevs-3:
            if revisions[cpagerev][1]['rev_sha1'] != revisions[cpagerev+1][1]['rev_sha1'] and \
               revisions[cpagerev][1]['rev_sha1'] == revisions[cpagerev+2][1]['rev_sha1'] and \
               revisions[cpagerev][1]['rev_username'] and revisions[cpagerev+1][1]['rev_ip'] and revisions[cpagerev+2][1]['rev_username'] and \
               revisions[cpagerev][1]['rev_username'] != revisions[cpagerev+2][1]['rev_username']:
                revertids.append([revisions[cpagerev+1][1]['rev_id'], revisions[cpagerev][1]['rev_id'], 'REVERTED', revisions[cpagerev+1][1]['rev_text'], revisions[cpagerev][1]['rev_text']])
            cpagerev += 1
    return revertids

def getregulars(revisions):
    cpagerevs = len(revisions)
    cpagerev = 0
    regularids = []
    if cpagerevs >= 3:
        while cpagerev <= cpagerevs-3:
            if revisions[cpagerev][1]['rev_sha1'] != revisions[cpagerev+1][1]['rev_sha1'] and \
               revisions[cpagerev][1]['rev_sha1'] != revisions[cpagerev+2][1]['rev_sha1'] and \
               revisions[cpagerev][1]['rev_username'] and revisions[cpagerev+1][1]['rev_username'] and revisions[cpagerev+2][1]['rev_username'] and \
               revisions[cpagerev][1]['rev_username'] != revisions[cpagerev+1][1]['rev_username'] and \
               revisions[cpagerev][1]['rev_username'] != revisions[cpagerev+2][1]['rev_username']:
                regularids.append([revisions[cpagerev+1][1]['rev_id'], revisions[cpagerev][1]['rev_id'], 'REGULAR', revisions[cpagerev+1][1]['rev_text'], revisions[cpagerev][1]['rev_text']])
            cpagerev += 1
    return regularids

def main():
    filename = sys.argv[1]
    maxreverts = int(sys.argv[2])
    maxregulars = maxreverts*14
    
    if not os.path.exists('dataset'):
        os.makedirs('dataset')
    
    if filename.endswith('.bz2'):
        import bz2
        source = bz2.BZ2File(filename)
    elif filename.endswith('.gz'):
        import gzip
        source = gzip.open(filename)
    elif filename.endswith('.7z'):
        import subprocess
        source = subprocess.Popen('7za e -bd -so %s 2>/dev/null'
                                  % filename,
                                  shell=True,
                                  stdout=subprocess.PIPE,
                                  bufsize=65535).stdout
    else:
        source = open(filename)

    r_page = re.compile(ur'(?im)<page>')
    r_page_end = re.compile(ur'(?im)</page>')
    r_title = re.compile(ur'(?im)<title>')
    r_ns = re.compile(ur'(?im)<ns>')
    r_id = re.compile(ur'(?im)<id>')
    r_rev = re.compile(ur'(?im)<revision>')
    r_rev_end = re.compile(ur'(?im)</revision>')
    r_parentid = re.compile(ur'(?im)<parentid>')
    r_timestamp = re.compile(ur'(?im)<timestamp>')
    r_contributor = re.compile(ur'(?im)<contributor>')
    r_contributor_end = re.compile(ur'(?im)</contributor>')
    r_username = re.compile(ur'(?im)<username>')
    r_ip = re.compile(ur'(?im)<ip>')
    r_minor = re.compile(ur'(?im)<minor />')
    r_comment = re.compile(ur'(?im)<comment>')
    r_text = re.compile(ur'(?im)<text xml:space="preserve">')
    r_text_empty = re.compile(ur'(?im)<text xml:space="preserve" />')
    r_text_end = re.compile(ur'(?im)</text>')
    r_sha1 = re.compile(ur'(?im)<sha1>')
    r_model = re.compile(ur'(?im)<model>')
    r_format = re.compile(ur'(?im)<format>')

    c_pages=0
    c_revs=0
    pagelock = False
    revlock = False
    userlock = False
    textlock = False

    page_title = ''
    page_ns = ''
    page_id = ''
    rev_id = ''
    rev_parentid = ''
    rev_timestamp = ''
    rev_username = ''
    rev_ip = ''
    rev_userid = ''
    rev_minor = ''
    rev_comment = ''
    rev_text = ''
    rev_sha1 = ''
    rev_model = ''
    rev_format = ''

    revisions = {}
    saved = []
    index = []
    for l in source:
        l = unicode(l, 'utf-8')
        #print l
        
        if textlock:
            rev_text += l.split('</text>')[0]
            if re.search(r_text_end, l):
                textlock = False
                rev_text = unescape(rev_text)
                continue
        
        #open tags
        if re.search(r_page, l):
            c_pages += 1
            pagelock = True
            revlock = False
            userlock = False
            continue
        if re.search(r_rev, l):
            c_revs += 1
            revlock = True
            pagelock = False
            userlock = False
            continue
        if re.search(r_contributor, l):
            userlock = True
            pagelock = False
            revlock = False
            continue
        
        #close tags
        if re.search(r_page_end, l):
            if maxreverts == 0 and maxregulars == 0:
                break
            
            if page_ns == '0':
                print page_title
                revisions[page_title]['revisions'].sort()
                reverts = getreverts(revisions[page_title]['revisions'])
                regulars = getregulars(revisions[page_title]['revisions'])
                
                #update limits
                if len(reverts) > maxreverts:
                    reverts = reverts[:maxreverts]
                    maxreverts = 0
                else:
                    maxreverts -= len(reverts)
                if len(regulars) > maxregulars:
                    regulars = regulars[:maxregulars]
                    maxregulars = 0
                else:
                    maxregulars -= len(regulars)
                
                #save
                for ll in [reverts, regulars]:
                    for rid, oid, cat, rtext, otext in ll:
                        index.append('%s;%s;%s' % (rid, oid, cat))
                        if not rid in saved:
                            saverev(rid, rtext)
                            saved.append(rid)
                        if not oid in saved:
                            saverev(oid, otext)
                            saved.append(oid)
                
            page_title = ''
            page_ns = ''
            page_id = ''
            continue
        
        if re.search(r_rev_end, l):
            #print page_id, page_ns, page_title, rev_id, rev_parentid, rev_timestamp, rev_username, rev_ip, rev_userid, rev_minor
            if not revisions.has_key(page_title):
                revisions[page_title] = {'page_title': page_title, 'page_ns': page_ns, 'revisions': []}
            revisions[page_title]['revisions'].append([rev_timestamp, {'rev_id': rev_id, 'rev_sha1': rev_sha1, 'rev_username': rev_username, 'rev_ip': rev_ip, 'rev_text': rev_text}])
            
            rev_id = ''
            rev_parentid = ''
            rev_timestamp = ''
            rev_username = ''
            rev_ip = ''
            rev_userid = ''
            rev_minor = ''
            rev_comment = ''
            rev_text = ''
            rev_sha1 = ''
            rev_model = ''
            rev_format = ''
            continue
        
        if re.search(r_contributor_end, l):
            pass
        
        #reading values
        if pagelock:
            if re.search(r_title, l):
                page_title = l.split('<title>')[1].split('</title>')[0]
            elif re.search(r_ns, l):
                page_ns = l.split('<ns>')[1].split('</ns>')[0]
            elif re.search(r_id, l):
                page_id = l.split('<id>')[1].split('</id>')[0]
        
        if revlock:
            if re.search(r_id, l):
                rev_id = l.split('<id>')[1].split('</id>')[0]
        
        if userlock:
            if re.search(r_id, l):
                rev_userid = l.split('<id>')[1].split('</id>')[0]
        
        if re.search(r_parentid, l):
            rev_parentid = l.split('<parentid>')[1].split('</parentid>')[0]
        elif re.search(r_timestamp, l):
            rev_timestamp = l.split('<timestamp>')[1].split('</timestamp>')[0]
        elif re.search(r_username, l):
            rev_username = l.split('<username>')[1].split('</username>')[0]
        elif re.search(r_ip, l):
            rev_ip = l.split('<ip>')[1].split('</ip>')[0]
        elif re.search(r_minor, l):
            rev_minor = True
        elif re.search(r_comment, l):
            rev_comment = l.split('<comment>')[1].split('</comment>')[0]
        elif re.search(r_text_empty, l):
            rev_text = u''
        elif re.search(r_text, l):
            if re.search(r_text_end, l):
                rev_text = l.split('<text xml:space="preserve">')[1].split('</text>')[0]
                rev_text = unescape(rev_text)
            else:
                textlock = True
                rev_text = l.split('<text xml:space="preserve">')[1]
        elif re.search(r_sha1, l):
            rev_sha1 = l.split('<sha1>')[1].split('</sha1>')[0]
        elif re.search(r_model, l):
            rev_model = l.split('<model>')[1].split('</model>')[0]
        elif re.search(r_format, l):
            rev_format = l.split('<format>')[1].split('</format>')[0]

    index.sort()
    g = open('dataset/index.txt', 'w')
    index = u'revid;oldid;class\n%s' % (u'\n'.join(index))
    g.write(index.encode('utf-8'))
    g.close()

if __name__ == '__main__':
    main()

