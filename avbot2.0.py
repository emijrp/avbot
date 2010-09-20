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
import urllib
import socket
import sys

import wikipedia

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
    return False

def editIsTest(edit_props):
    return False

def editIsVandalism(edit_props):
    return False

def editIsVanish(edit_props):
    return False

def userwarning():
    #enviar mensajes según el orden que ya tengan los de la discusión
    pass

def reverted():
    return False

def revert(edit_props, motive=""):
    print "Detected edit to revert: %s" % motive
    
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
        print "Saltamos para evitar guerra"
        return
    elif dangerous(edit_props):
        if editIsBlanking(edit_props):
            revert(edit_props, motive="blanking")
        elif editIsTest(edit_props):
            pass
        elif editIsVandalism(edit_props):
            pass
        elif editIsVanish(edit_props):
            pass
        else:
            pass

def isIP(user):
    if re.findall(ur"(?im)^\d+\.\d+\.\d+\.\d+$", user): #improve
        return True
    return False

def dangerous(edit_props):
    useredits = getUserEdits(edit_props['user'])
    
    #anon filter
    if isIP(edit_props['user']):
        return True
    
    #group filter
    for whitelistgroup in whitelistgroups:
        if edit_props['user'] in users[whitelistgroup]:
            return False
        
    #edit number filter
    if useredits < 25:
       return True
    
    return False

def fetchedEdit(edit_props):
    timestamp = edit_props['timestamp'].split('T')[1].split('Z')[0]
    
    line = u'%s [[%s]] {\03{%s}%s\03{default}, %d ed.}' % (timestamp, edit_props['title'], colours[getUserGroup(edit_props['user'])], edit_props['user'], getUserEdits(edit_props['user']))
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
                                m = re.compile(ur'(?im)^\[\[(?P<title>.+?)\]\]\s+(?P<flag>[NMB]*?)\s+(?P<url>http://.+?diff=(?P<diff>\d+?)\&oldid=(?P<oldid>\d+?))\s+\*\s+(?P<user>.+?)\s+\*\s+\((?P<change>[\-\+]\d+?)\)\s+(?P<comment>.*?)$').finditer(message)
                                for i in m:
                                    #flag, change, url
                                    edit_props = {'page': wikipedia.Page(preferences['site'], i.group('title')), 'title': i.group('title'), 'timestamp': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'), 'user': i.group('user'), 'comment': i.group('comment'), 'diff': i.group('diff'), 'oldid': i.group('oldid')}
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
