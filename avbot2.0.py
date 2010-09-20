# -*- coding: utf-8 -*-

#todo
#ircbot https://fisheye.toolserver.org/browse/~raw,r=720/Bryan/TsLogBot/TsLogBot.py
#capacidad para leer CR de irc o de api

import datetime
import os
import random
import re
import time
import thread
import threading
import urllib
import socket
import sys

import wikipedia

class Diegus(threading.Thread):
    def __init__(self, edit_props, fun):
        threading.Thread.__init__(self)
        self.edit_props = edit_props
        self.fun = fun
        self.page = edit_props['page']
        self.oldid = edit_props['oldid']
        self.diff = edit_props['diff']
        self.revcount = 10
        self.oldText = ''
        self.newText = ''
        self.pageHistory = []
        self.HTMLdiff = ''
        
    def run(self):
        #print self.page.title(), self.fun
        if self.fun == 'getOldVersionOldid':
            self.oldText = self.page.getOldVersion(self.oldid, get_redirect=True) #cogemos redirect si se tercia, y ya filtramos luego
            #print 'oldText', self.value, len(self.oldText)
        elif self.fun == 'getOldVersionDiff':
            self.newText = self.page.getOldVersion(self.diff, get_redirect=True) #cogemos redirect si se tercia, y ya filtramos luego
            #print 'newText', self.value, len(self.newText)
        elif self.fun == 'getVersionHistory':
            self.pageHistory = self.page.getVersionHistory(revCount=self.revcount)
        elif self.fun == 'getUrl':
            self.HTMLDiff = preferences['site'].getUrl('/w/index.php?diff=%s&oldid=%s&diffonly=1' % (self.diff, self.oldid))
    
    def getOldText(self):
        return self.oldText
    
    def getNewText(self):
        return self.newText
        
    def getPageHistory(self):
        return self.pageHistory
    
    def getHTMLDiff(self):
        return self.HTMLDiff

usergroups = [] #list of groups
whitelistgroups = ['sysop', 'bot', ] #list of trusted users
users = {} #dic with users sorted by group
useredits = {} #dic with user edits number
colours = {
    'sysop': 'lightblue',
    'bot': 'lightpurple',
    'anon': 'lightyellow',
    '': 'lightgreen',
    }
"""
colourcodes = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 'a', 'b', 'c', 'd', 'e', 'f']
colournames = ['black', 'blue', 'green', 'aqua', 'red', 'purple', 'yellow', 'white', 'grey', 'light blue', 'light green', 'light aqua', 'light red', 'light purple', 'light yellow', 'bright white']
"""

preferences = {
    'language': 'en',
    'family': 'wikipedia',
    'rcAPI': False,
    'rcIRC': True,
    'server': 'irc.wikimedia.org',
    'channel': '#en.wikipedia',
    'ircNick': 'AVBOT%d' % (random.randint(10000,99999)),
    'userEditsFile': 'useredits.txt',
}

preferences['site'] = wikipedia.Site(preferences['language'], preferences['family'])

def loadUsersFromUserGroup(usergroup):
    global users
    
    users[usergroup] = []
    aufrom = '!'
    while aufrom:
        url = 'http://%s.%s.org/w/api.php?action=query&list=allusers&augroup=%s&aulimit=500&aufrom=%s' % (preferences['language'], preferences['family'], usergroup, aufrom.encode('utf-8'))
        f = urllib.urlopen(url)
        raw = unicode(f.read(), 'utf-8')
        f.close()
        m = re.compile(ur'<span style="color:blue;">&lt;u name=&quot;(?P<user>.+?)&quot; /&gt;</span>').finditer(raw)
    
        for i in m:
            user = i.group('user')
            users[usergroup].append(user)
        
        m = re.findall(ur'<span style="color:blue;">&lt;allusers aufrom=&quot;(?P<aufrom>.+?)&quot; /&gt;</span>', raw)
        if m:
            aufrom = m[0]
        else:
            aufrom = ''

def getUserEdits(user):
    edits = 0
    
    if not isIP(user):
        if useredits.has_key(user):
            edits = useredits[user]
        
        if getUserGroup(user) in whitelistgroups: #todo, puede tener varios grupos
            if useredits.has_key(user) and not random.randint(0, 10): #avoid update whitelisted users too much
                return edits
        
        url = 'http://en.wikipedia.org/w/api.php?action=query&list=users&ususers=%s&usprop=editcount' % (urllib.quote(user.encode('utf-8')))
        f = urllib.urlopen(url)
        raw = unicode(f.read(), 'utf-8')
        f.close()
        
        m = re.findall(ur'<span style="color:blue;">&lt;user name=&quot;.+?&quot; editcount=&quot;(\d+?)&quot; /&gt;</span>', raw)
        if m:
            edits = int(m[0])
            useredits[user] = edits
    
    #saving file
    if not random.randint(0, 100):
        saveUserEdits()
    
    return edits

def getUserGroup(user):
    #todo, devolver una lista de grupos mejor?
    for usergroup in usergroups:
        if user in users[usergroup]:
            return usergroup
    
    if isIP(user):
        return 'anon'
    
    return ''

def saveUserEdits():
    f = open(preferences['userEditsFile'], 'w')
    
    for user, edits in useredits.items():
        line = u'%s\t%d\n' % (user, edits)
        f.write(line.encode('utf-8'))
    
    f.close()

def loadUserEdits():
    global useredits
    
    if not os.path.exists(preferences['userEditsFile']):
        #creating empty file
        saveUserEdits()
    
    f = open(preferences['userEditsFile'], 'r')
    for line in f:
        line = unicode(line, 'utf-8')
        line = line[:-1]
        if line:
            user, edits = line.split('\t')
            useredits[user] = int(edits)
    
    f.close()

def loadUserGroups():
    global usergroups
    
    usergroups = ['sysop', 'bot'] #catch from api, no by default
    usergroups = usergroups + whitelistgroups
    
    #avoid dupes
    usergroups2 = usergroups
    usergroups = []
    for usergroup in usergroups2:
        if usergroups.count(usergroup) == 0:
            usergroups.append(usergroup)

def loadUsers():
    if not usergroups:
        loadUserGroups()
    
    for usergroup in usergroups:
        loadUsersFromUserGroup(usergroup=usergroup)
    
    #previously blocked users and ips too?

def loadData():
    #users
    loadUserGroups()
    print 'Loaded %d usergroups' % (len(usergroups))
    print 'Loaded %d white groups: %s' % (len(whitelistgroups), ', '.join(whitelistgroups))
    
    loadUsers()
    for whitegroup in whitelistgroups:
        print 'Loaded %d users in the white group %s' % (len(users[whitegroup]), whitegroup)
    
    loadUserEdits()
    print 'Loaded edit number for %d users' % (len(useredits.keys()))
    
    #other interesting data...

def editIsBlanking(edit_props):
    lenNew = len(edit_props['newText'])
    lenOld = len(edit_props['oldText'])
    
    if lenNew < lenOld and \
       not re.search(ur"(?i)# *REDIRECT", edit_props['newText']):
       #Avoid articles converted into #REDIRECT [[...]] and other legitimate blankings
        percent = (lenOld-lenNew)/(lenOld/100.0)
        if (lenOld>=500 and lenOld<1000 and percent>=90) or \
           (lenOld>=1000 and lenOld<2500 and percent>=85) or \
           (lenOld>=2500 and lenOld<5000 and percent>=75) or \
           (lenOld>=5000 and lenOld<10000 and percent>=72.5) or \
           (lenOld>=10000 and lenOld<20000 and percent>=70) or \
           (lenOld>=20000 and percent>=65):
            return True
    
    return False

def editIsTest(edit_props):
    
    
    return False

def editIsVandalism(edit_props):
    regexps = [
    ur'(?i)\bf+u+c+k+\b',
    ur'(?i)\b(h+a+){2,}\b',
    ur'(?i)\bg+a+y+\b',
    ur'(?i)\bf+a+g+s*\b',
    ur'(?i)\ba+s+s+\b',
    ur'(?i)\bb+i+t+c+h+(e+s+)?\b',
    ]
    
    for regexp in regexps:
        if re.search(regexp, edit_props['newText']) and \
           not re.search(regexp, edit_props['oldText']):
            return True
    
    return False

def editIsVanish(edit_props):
    return False

def userwarning():
    #enviar mensajes según el orden que ya tengan los de la discusión
    pass

def reverted():
    return False

def revert(edit_props, motive=""):
    #print "Detected edit to revert: %s" % motive
    
    #revertind code
    
    #end code
    
    if reverted(): #a lo mejor lo ha revertido otro bot u otra persona
        userwarning() 
    else:
        print "Somebody was faster than us reverting. Reverting not needed"

def editWar(edit_props):
    #comprueba si esa edición ya existe previamente en el historial, por lo que el usuario está insistiendo en que permanezca
    #primero con la longitud, y si hay semejanzas, entonces se compara con el texto completo
    return False

def analize(edit_props):
    if editWar(edit_props):
        #http://es.wikipedia.org/w/api.php?action=query&prop=revisions&titles=Francia&rvprop=size&rvend=2010-07-25T14:54:54Z
        print "Saltamos para evitar la guerra"
        return
    elif dangerous(edit_props):
        #preparing data
        #get last edits in history
        t1=time.time()
        #simplificar las llamas a los hilos? pasar todos los parámetros o solo los necesarios?
        threadHistory = Diegus(edit_props, 'getVersionHistory')
        threadOldid = Diegus(edit_props, 'getOldVersionOldid')
        threadDiff = Diegus(edit_props, 'getOldVersionDiff')
        threadHTMLDiff = Diegus(edit_props, 'getUrl')
        threadHistory.start()
        threadOldid.start()
        threadDiff.start()
        threadHTMLDiff.start()
        threadHistory.join()
        edit_props['pageHistory'] = threadHistory.getPageHistory()
        #print edit_props['pageHistory']
        threadOldid.join()
        edit_props['oldText'] = threadOldid.getOldText()
        threadDiff.join()
        edit_props['newText'] = threadDiff.getNewText()
        #hacer mi propio differ, tengo el oldText y el newText, pedir esto retarda la reversión unos segundos #fix #costoso?
        threadHTMLDiff.join()
        edit_props['HTMLDiff'] = threadHTMLDiff.getHTMLDiff()
        edit_props['HTMLDiff'] = edit_props['HTMLDiff'].split('<!-- content -->')[1]
        edit_props['HTMLDiff'] = edit_props['HTMLDiff'].split('<!-- /content -->')[0] #No change
        #cleandata = cleandiff(editData['pageTitle'], editData['HTMLDiff']) #To clean diff text and to extract inserted lines and words
        line = u'%s %s %s %s %s %s' % (edit_props['title'], time.time()-t1, edit_props['pageHistory'][0][0], len(edit_props['oldText']), len(edit_props['newText']), len(edit_props['HTMLDiff']))
        #wikipedia.output(u'\03{lightred}%s\03{default}' % line)
        
        if editIsBlanking(edit_props):
            #revert(edit_props, motive="blanking")
            wikipedia.output(u'\03{lightred}-> *Blanking* detected in [[%s]] (%s)\03{default}' % (edit_props['title'], edit_props['change']))
        elif editIsTest(edit_props):
            wikipedia.output(u'\03{lightred}-> *Test* detected in [[%s]] (%s)\03{default}' % (edit_props['title'], edit_props['change']))
        elif editIsVandalism(edit_props):
            revert(edit_props, motive="vandalism")
            wikipedia.output(u'\03{lightred}-> *Vandalism* detected in [[%s]] (%s)\03{default}' % (edit_props['title'], edit_props['change']))
        elif editIsVanish(edit_props):
            wikipedia.output(u'\03{lightred}-> *Vanish* detected in [[%s]] (%s)\03{default}' % (edit_props['title'], edit_props['change']))
        else:
            pass

def isIP(user):
    if re.findall(ur"(?im)^\d+\.\d+\.\d+\.\d+$", user): #improve
        return True
    return False

def dangerous(edit_props):
    useredits = getUserEdits(edit_props['user'])
    
    #namespace filter
    if edit_props['page'].namespace() != 0:
        return False
    
    #anon filter
    if isIP(edit_props['user']):
        return True
    
    #group filter
    for whitelistgroup in whitelistgroups:
        if edit_props['user'] in users[whitelistgroup]:
            return False
        
    #edit number filter
    if useredits <= 25:
       return True
    
    return False

def fetchedEdit(edit_props):
    timestamp = edit_props['timestamp'].split('T')[1].split('Z')[0]
    change = edit_props['change']
    if change >= 0:
        change = '+%d' % (change)
    
    line = u'%s [[%s]] {\03{%s}%s\03{default}, %d ed.} (%s)' % (timestamp, edit_props['title'], colours[getUserGroup(edit_props['user'])], edit_props['user'], getUserEdits(edit_props['user']), change)
    if not editWar(edit_props) and dangerous(edit_props):
        wikipedia.output(u'== Analyzing ==> %s' % line)
        thread.start_new_thread(analize, (edit_props,))
    else:
        wikipedia.output(line)

def rcAPI():
    site = wikipedia.Site("en", "wikipedia")
    
    rctimestamp = ""
    rcs = site.recentchanges(number=1)
    for rc in rcs:
        rctimestamp = rc[1]
    
    rcdir = "newer"
    rchistory = []
    while True:
        rcs = site.recentchanges(number=100, rcstart=rctimestamp, rcdir=rcdir) #no devuelve los oldid, mejor hacerme mi propia wikipedia.query
        
        for rc in rcs:
            rcsimple = [rc[0].title(), rc[1], rc[2], rc[3]]
            if rcsimple not in rchistory:
                rchistory = rchistory[-1000:]
                rchistory.append(rcsimple)
                edit_props = {'page': rc[0], 'title': rc[0].title(), 'timestamp': rc[1], 'user': rc[2], 'comment': rc[3], }
                thread.start_new_thread(fetchedEdit, (edit_props,))
            rctimestamp = rc[1]
        time.sleep(3)

def rcIRC():
    #partially from Bryan ircbot published with MIT License http://toolserver.org/~bryan/TsLogBot/TsLogBot.py
    
    while True:
        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.connect((preferences['server'], 6667))
            
            conn.sendall('USER %s * * %s\r\n' % (preferences['ircNick'], preferences['ircNick']))
            conn.sendall('NICK %s\r\n' % (preferences['ircNick']))
            conn.sendall('JOIN %s\r\n' % (preferences['channel']))
    
            buffer = ''
            while True:
                if '\n' in buffer:
                    line = buffer[:buffer.index('\n')]
                    buffer = buffer[len(line) + 1:]
                    line = line.strip()
                    #print >>sys.stderr, line
                    
                    data = line.split(' ', 3)
                    if data[0] == 'PING':
                        conn.sendall('PONG %s\r\n' % data[1])
                    elif data[1] == 'PRIVMSG':
                        nick = data[0][1:data[0].index('!')]
                        target = data[2]
                        message = data[3][1:]
                        message = unicode(message, 'utf-8')
                        message = re.sub(ur'\x03\d{0,2}', ur'', message) #No colors
                        message = re.sub(ur'\x02\d{0,2}', ur'', message) #No bold
                        if target == preferences['channel']:
                            if message.startswith('\x01ACTION'):
                                pass #log('* %s %s' % (nick, message[8:]))
                            else:
                                #todo esta regexp solo vale para ediciones, las páginas nuevas tienen rcid= y no diff: http://en.wikipedia.org/w/index.php?oldid=385928375&rcid=397223378
                                m = re.compile(ur'(?im)^\[\[(?P<title>.+?)\]\]\s+(?P<flag>[NMB]*?)\s+(?P<url>http://.+?diff=(?P<diff>\d+?)\&oldid=(?P<oldid>\d+?))\s+\*\s+(?P<user>.+?)\s+\*\s+\((?P<change>[\-\+]\d+?)\)\s+(?P<comment>.*?)$').finditer(message)
                                for i in m:
                                    #flag, change, url
                                    edit_props = {'page': wikipedia.Page(preferences['site'], i.group('title')), 'title': i.group('title'), 'timestamp': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'), 'user': i.group('user'), 'comment': i.group('comment'), 'diff': i.group('diff'), 'oldid': i.group('oldid'), 'change': int(i.group('change'))}
                                    thread.start_new_thread(fetchedEdit, (edit_props,))
                                pass #log('<%s>\t%s' % (nick, message))
                else:
                    data = conn.recv(1024)
                    if not data: raise socket.error
                    buffer += data
        except socket.error, e:
            print >>sys.stderr, 'Socket error!', e

def run():
    #irc or api
    #por cada usuairo que llegue nuevo list=users (us) para saber cuando se registró
    #evitar que coja ediciones repetidas
    
    if preferences["rcAPI"]:
        rcAPI()
    elif preferences["rcIRC"]:
        rcIRC()
    else:
        print 'You have to choice a feed mode: IRC or API'

def welcome():
    print "#"*80
    print "# Welcome to AVBOT "
    print "#"*80

def bye():
    print "Bye, bye..."

def main():
    welcome()
    loadData()
    run()
    bye()

if __name__ == '__main__':
    main()
