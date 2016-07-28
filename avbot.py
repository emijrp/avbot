# -*- coding: utf-8 -*-

# AVBOT - Anti-vandalism bot for MediaWiki wikis
# Copyright (C) 2008-2016 emijrp <emijrp@gmail.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#TODO
#sameoldid, evitar que cargue siempr y aproveche el oldtext anterior
#evitar guerras de edicion por clones de avbot, sol: pagina que liste los clones? lin 135 avbotanalysis
#subpaginas centralizadas y sin centralizar en el avbotload
#que no conflicteen las subpáginas de estadisticas
#que se baje el codigo de rediris y lo compruebe con los fucheros locales
#hacer independiente de verdad lo de 'v', 'bl', 'c', etc
#detectar SO para evitar los errores cuando intenta hacer rm
#fix http://pt.wikipedia.org/w/index.php?title=Livro_Estrelas_cadentes&diff=19353599&oldid=19348430

## @package avbot
# Main module\n
# Módulo principal

""" External modules """
""" Python modules """
import os
import random
import re
import sys
import _thread
import time

""" pywikipediabot modules """
import pywikibot

""" AVBOT modules """
"""
import avbotglobals  #Shared info
import avbotload     #Data and regexp loader
import avbotsave     #Saving info in files
import avbotmsg      #Send messages to vandals
import avbotanalysis #Edit analysis to find vandalisms, blanking, and similar malicious edits
import avbotcomb     #Trivia functions
"""

class AVBOT():
    """ Clase AVBOT """
    """ AVBOT class """
    
    def __init__(self):
        """ Inicialización del bot """
        """ Bot initialization """
        
        self.repo = 'https://github.com/emijrp/avbot' # Repository with AVBOT source code
        self.version = self.getVersion() # AVBOT version
        self.path = '/%s' % ('/'.join(os.path.abspath( __file__ ).split('/')[:-1]), )
        
        self.wikiBotName = 'Bot', # Bot username in wiki
        self.wikiManagerName = 'Manager' # Bot manager username in wiki
        self.wikiLanguage = 'en' # Default wiki language is English
        self.wikiFamily = 'wikipedia' # Default wiki family is Wikipedia
        self.site = pywikibot.Site(self.wikiLanguage, self.wikiFamily)
        
        self.rcFeed = 'irc' # Feed mode for recent changes (irc or API)
        self.ircNetwork = 'irc.wikimedia.org' # IRC network where is the recent changes IRC channel
        self.ircPort = 6667 # IRC network port number
        self.ircChannel = '#%s.%s' % (self.wikiLanguage, self.wikiFamily) # Recent changes IRC channel
        self.ircBotName = '%s%s' % (self.wikiBotName, str(random.randint(1000, 9999))) # Bot username in IRC network
        
        self.logsDirectory = 'botlogs' # Directory reverts logs, not ending in /
        self.newbieThreshold = 25 # Threshold edits for newbie users
        self.statsDelay = 60 # Delay in seconds between printing stats
        self.colors = {
            'steward': 'lightblue', 
            'sysop': 'lightblue', 
            'bureaucrat': 'lightblue', 
            'checkuser': 'lightblue', 
            'bot': 'lightpurple', 
            'reg': 'lightgreen',
            'anon': 'lightyellow', 
        }
        self.context = r'[ \@\º\ª\·\#\~\$\<\>\/\(\)\'\-\_\:\;\,\.\r\n\?\!\¡\¿\"\=\[\]\|\{\}\+\&]'
        self.msg = {}
        self.testmode = False
        self.dryrun = False # Don't save any edit in wiki
        self.force = False
        self.trial = False
        self.users = {}
        self.usersFile = '%s.%s.users.txt' % (self.wikiFamily, self.wikiLanguage)
        self.historyLen = 10 # Numer of edits to retrieve by history
        self.filters = []
        self.filtersLocations = [ # Files with regexps and scores to detect vandalism
            {'type': 'file', 'location': 'filters/%s.%s.filters.txt' % (self.wikiFamily, self.wikiLanguage)}, 
            {'type': 'page', 'location': 'User:%s/filters.css' % (self.wikiBotName)}, 
        ]
        self.exclusions = []
        self.exclusionsLocations = [ # Files and pages that lists excluded pages (usual false positives)
            {'type': 'file', 'location': 'exclusions/%s.%s.exclusions.txt' % (self.wikiFamily, self.wikiLanguage)}, 
            {'type': 'page', 'location': 'User:%s/exclusions.css' % (self.wikiBotName)}, 
        ]
        self.messagesLocations = [ # Files with messages to leave in talk pages
            {'type': 'file', 'location': 'messages/%s.%s.messages.txt' % (self.wikiFamily, self.wikiLanguage)}, 
            {'type': 'page', 'location': 'User:%s/messages.css' % (self.wikiBotName)}, 
        ]
        self.namespaces = []
        self.isAliveFile = '%s.%s.alive.txt' % (self.wikiFamily, self.wikiLanguage) # File to check if AVBOT is working
        self.isAliveSeconds = 60 # Touches isAliveFile every X seconds
        self.pidFile = '%s.%s.pid.txt' % (self.wikiFamily, self.wikiLanguage) # File with process ID
        
    def start(self):
        # Welcome message
        header  = "AVBOT Copyright (C) 2008-2016 emijrp <emijrp@gmail.com>\n"
        header += "This program comes with ABSOLUTELY NO WARRANTY.\n"
        header += "This is free software, and you are welcome to redistribute it\n"
        header += "under certain conditions. See license.\n\n"
        header += "############################################################################\n"
        header += "# Name:     AVBOT (Anti-vandalism bot for MediaWiki wikis)                 #\n"
        header += "# Version:  %s                                                            #\n" % (self.version)
        header += "# Features: Revert vandalism, blanking and test edits                      #\n"
        header += "#           Report vandalism attack waves to admins                        #\n"
        header += "#           Mark rubbish articles for deletion                             #\n"
        header += "############################################################################\n\n"
        header += "Available parameters (* obligatory): --wikilang, --wikifamily, --newbieedits, --wikibotname*, --statsdelay, --ircnetwork, --ircchannel, --wikimanagername*, --nosave, --force\n"
        header += "Example: python avbot.py --wikibotname:MyBot --wikimanagername:MyUser\n"
        header +=  u"Loading data for %s:%s project\n" % (avbotglobals.preferences['family'], avbotglobals.preferences['language'])
        header += u"Newbie users are those who have done %s edits or less" % (avbotglobals.preferences['newbie'])
        print(header)
        
        """ Avoid running two or more instances of AVBOT """
        #self.isAlive()
    
        """ Data loaders """
        self.loadUsers()
        self.loadExclusions()
        
        """Messages"""
        """avbotload.loadMessages()
        wikipedia.output(u"Loaded %d messages..." % (len(avbotglobals.preferences['msg'].items())))"""
        
        """Regular expresions for vandalism edits """
        """error=avbotload.loadRegexpList()
        wikipedia.output(u"Loaded and compiled %d regular expresions for vandalism edits...\n%s" % (len(avbotglobals.vandalRegexps.items()), error))"""
        
        if self.rcFeed == 'irc':
            self.rcIRC()
        elif self.rcFeed == 'api':
            self.rcAPI()
    
    def getVersion(self):
        with open('%s/VERSION' % (self.path)) as g:
            self.version = g.read().strip()

    def checkForUpdates(self):
        f = urllib.urlopen('%s/VERSION' % (self.repo))
        remoteversion = f.read().strip()
        
        if remoteversion != preferences['version']:
            return True
        return False    

    def loadUsers(self):
        """ Load info about users (editcount) """
        """ Carga información sobre usuarios (número de ediciones) """
        
        print("Loading info for users")
        self.loadUsersByGroup('steward')
        self.loadUsersByGroup('sysop')
        self.loadUsersByGroup('bureaucrat')
        self.loadUsersByGroup('checkuser')
        self.loadUsersByGroup('bot')
        
        if os.path.isfile('%s/%s' % (self.path, self.usersFile)):
            with open('%s/%s' % (self.path, self.usersFile), 'r') as f:
                for row in f.read().splitlines():
                    username, editcount = row.split(';')
                    if not username in self.users:
                        self.users[username] = {'groups': ['*']}
                    self.users[username]['editcount'] = int(editcount)
        
        print("Loaded info for %d users from %s" % (len(self.users.keys()), self.usersFile))
    
    def loadUsersByGroup(self, group):
        """ Captura lista de usuarios de un grupo """
        """ Fetch user list by group """
    
        aufrom = "!"
        while aufrom:
            query = pywikibot.query.GetData({'action': 'query', 'list': 'allusers', 'augroup': group, 'aulimit': '500', 'aufrom': aufrom}, site = self.site, useAPI = True)
            for row in query['query']['allusers']:
                username = allusers['name']
                if username in self.usernames:
                    self.users[username]['groups'].append(group)
                else:
                    self.users[username] = {'groups': [group]}
            if 'query-continue' in query:
                aufrom = query['query-continue']
            else:
                aufrom = ""
        print("Loaded %d users from %s group" % (len(query['query']['allusers']), group))
    
    def loadExclusions(self):
        """ Carga lista de páginas excluidas """
        """ Load excluded pages list """
        
        for exclusionLocation in self.exclusionsLocations:
            if exclusionLocation['type'] == 'file':
                location = '%s/%s' % (self.path, exclusionLocation['location'])
                if os.path.isfile(location):
                    with open(location, 'r') as f:
                        for row in f.read().strip().splitlines():
                            row = row.strip()
                            if row and not row.startswith('#'): # Remove comments
                                row = row.split('#')[0].strip() # Remove inline comments
                                self.exclusions.append(re.compile(r"(?m)^%s$" % (row)))
                else:
                    print("Not found: %s" % (exclusionLocation['location']))
            elif exclusionLocation['type'] == 'page':
                exclusionsPage = pywikibot.Page(self.site, exclusionLocation['location'])
                if exclusionsPage.exists() and not exclusionsPage.isRedirectPage():
                    for row in exclusionsPage.text.strip().splitlines():
                        row = row.strip()
                        if row and not row.startswith('#'):
                            row = row.split('#')[0].strip()
                            self.exclusions.append(re.compile(r"(?m)^%s$" % (row)))
                else:
                    print("Not found or it is a redirect: %s" % (exclusionLocation['location']))

    def isAlive(self):
        isAliveFile = '%s/%s' % (self.path, self.isAliveFile)
        pidFile = '%s/%s' % (self.path, self.pidFile)
        if os.path.isfile(isAliveFile):
            os.system("rm %s" % (isAliveFile))
            print("It seems AVBOT is running in another process")
            print("Deleting isAlive file %s" % (self.isAliveFile))
            print("Exiting... Please, re-run this script in %d minutes or more" % ((self.isAliveSeconds*5)/60))
            sys.exit()
        else:
            if os.path.isfile(pidFile):
                try:
                    with open(pidFile, 'r') as f:
                        oldpid = f.read().strip()
                    os.system("kill -9 %s" % (oldpid))
                except:
                    pywikibot.output("Error while killing previous AVBOT process. Probably it isn't running anymore")
        
            # Saving current process ID
            with open(pidFile, 'w') as f:
                f.write(str(os.getpid()))
    
        # Starting isAlive checking
        #_thread.start_new_thread(self.isAliveBackground, ())
    
    def isAliveBackground(self):
        isAliveFile = '%s/%s' % (self.path, self.isAliveFile)
        while True:
            if not os.path.isfile(self.isAliveFile):
                with open(self.isAliveFile, 'w') as f:
                    f.write("AVBOT is running")
            time.sleep(self.isAliveSeconds)
    
    def rcIRC(self):
        # Partially from Bryan ircbot http://toolserver.org/~bryan/TsLogBot/TsLogBot.py (MIT License)
        print("Joining to recent changes IRC channel...\n")
        while True:
            try:
                conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                conn.connect((self.ircNetwork, self.ircPort))
                
                conn.sendall('USER %s * * %s\r\n' % (self.ircBotName, self.ircBotName))
                conn.sendall('NICK %s\r\n' % (self.ircBotName))
                conn.sendall('JOIN %s\r\n' % (self.ircChannel))
        
                ircbuffer = ''
                while True:
                    if '\n' in ircbuffer:
                        line = ircbuffer[:ircbuffer.index('\n')]
                        ircbuffer = ircbuffer[len(line) + 1:]
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
                            message = re.sub(r'\x03\d{0,2}', r'', message) #No colors
                            message = re.sub(r'\x02\d{0,2}', r'', message) #No bold
                            if target == self.ircChannel:
                                if message.startswith('\x01ACTION'):
                                    pass #log('* %s %s' % (nick, message[8:]))
                                else:
                                    #todo esta regexp solo vale para ediciones, las páginas nuevas tienen rcid= y no diff: http://en.wikipedia.org/w/index.php?oldid=385928375&rcid=397223378
                                    print(message)
                                    m = re.findall(r'(?im)^\[\[(?P<title>.+?)\]\]\s+(?P<flag>[NMB]*?)\s+(?P<url>https://.+?diff=(?P<diff>\d+?)\&oldid=(?P<oldid>\d+?))\s+\*\s+(?P<user>.+?)\s+\*\s+\((?P<change>[\-\+]\d+?)\)\s+(?P<comment>.*?)$', message)
                                    for i in m:
                                        #flag, change, url
                                        edit_props = {'page': pywikibot.Page(self.site, i.group('title')), 'title': i.group('title'), 'timestamp': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'), 'user': i.group('user'), 'comment': i.group('comment'), 'diff': i.group('diff'), 'oldid': i.group('oldid'), 'change': int(i.group('change'))}
                                        #_thread.start_new_thread(fetchedEdit, (edit_props,))
                                        print(edit_props.items())
                                    pass #log('<%s>\t%s' % (nick, message))
                    else:
                        data = conn.recv(1024)
                        if not data: raise socket.error
                        ircbuffer += data
            except socket.error:
                print >>sys.stderr, 'Socket error!'
            
    def on_welcome(self, c, e):
        """ Se une al canal de IRC de Cambios recientes """
        """ Joins to IRC channel with Recent changes """
        
        c.join(self.channel)
    
    def on_privmsg(self, c, e):
        line = (e.arguments()[0])
        line = avbotcomb.encodeLine(line)
        nick = nm_to_n(e.source())
        
        f = open('privados.txt', 'a')
        timestamp = time.strftime('%X %x')
        line = timestamp+' '+nick+' > '+line+'\n'
        f.write(line.encode('utf-8'))
        f.close()
    
    def on_pubmsg(self, c, e):
        """ Captura cada línea del canal de IRC """
        """ Fetch and parse each line in the IRC channel """
        
        
        """
        editData = {}
        
        line = (e.arguments()[0])
        line = avbotcomb.encodeLine(line)
        line = avbotcomb.cleanLine(line)
        nick = nm_to_n(e.source())
        
        editData['line'] = line
        if re.search(avbotglobals.parserRegexps['edit'], line):
            match = avbotglobals.parserRegexps['edit'].finditer(line)
            for m in match:
                editData['pageTitle'] = m.group('pageTitle')
                editData['diff'] = int(m.group('diff'))
                editData['oldid'] = int(m.group('oldid'))
                editData['author'] = m.group('author')
                editData['userClass'] = avbotcomb.getUserClass(editData)
                    
                nm=m.group('nm')
                editData['new'] = editData['minor']=False
                if re.search('N', nm):
                    editData['new'] = True
                if re.search('M', nm):
                    editData['minor'] = True
                editData['resume'] = m.group('resume')
                
                avbotanalysis.updateStats('total')
                avbotglobals.statsTimersDic['speed'] += 1
                
                #Reload vandalism regular expresions if needed
                #if re.search(ur'%s\:%s\/Lista del bien y del mal\.css' %(avbotglobals.namespaces[2], avbotglobals.preferences['ownerNick']), editData['pageTitle']):
                #   avbotload.reloadRegexpList(editData['author'], editData['diff'])
                if re.search(avbotglobals.parserRegexps['goodandevil'], editData['pageTitle']):
                    avbotload.reloadRegexpList(editData['author'], editData['diff'])
                
                #Reload exclusion list #fix hacer independiente localization
                if re.search(avbotglobals.parserRegexps['exclusions'], editData['pageTitle']):
                    avbotload.loadExclusions()
                
                #Reload messages list
                if re.search(avbotglobals.parserRegexps['messages'], editData['pageTitle']):
                    avbotload.loadMessages()
                
                _thread.start_new_thread(avbotanalysis.editAnalysis, (editData,))
                
                # Avoid to check our edits, aunque ya se chequea en editAnalysis
                if editData['author'] == avbotglobals.preferences['botNick']: 
                    return #Exit
        
                #Check resume for reverts
                if avbotglobals.preferences['language']=='es' and re.search(ur'(?i)(Revertidos los cambios de.*%s.*a la última edición de|Deshecha la edición \d+ de.*%s)' % (avbotglobals.preferences['botNick'], avbotglobals.preferences['botNick']), editData['resume']) and editData['pageTitle']!=u'Usuario:AVBOT/Errores/Automático':
                    if not avbotglobals.preferences['nosave']:
                        wiii=wikipedia.Page(avbotglobals.preferences['site'], u'User:AVBOT/Errores/Automático')
                        wiii.put(u'%s\n# [[%s]], {{subst:CURRENTDAY}} de {{subst:CURRENTMONTHNAME}} de {{subst:CURRENTYEAR}}, http://%s.wikipedia.org/w/index.php?diff=%s&oldid=%s, {{u|%s}}' % (wiii.get(), editData['pageTitle'], avbotglobals.preferences['language'], editData['diff'], editData['oldid'], editData['author']), u'BOT - Informe automático. [[User:%s|%s]] ha revertido a [[User:%s|%s]] en [[%s]]' % (editData['author'], editData['author'], avbotglobals.preferences['botNick'], avbotglobals.preferences['botNick'], editData['pageTitle']), botflag=False, maxTries=3)
        elif re.search(avbotglobals.parserRegexps['newpage'], line):
            match=avbotglobals.parserRegexps['newpage'].finditer(line)
            for m in match:
                editData['pageTitle'] = m.group('pageTitle')
                
                editData['diff'] = editData['oldid']=0
                editData['author'] = m.group('author')
                editData['userClass'] = avbotcomb.getUserClass(editData)
                
                nm = m.group('nm')
                editData['new'] = True
                editData['minor'] = False
                if re.search('M', nm):
                    editData['minor'] = True
                editData['resume']=u''
                
                avbotanalysis.updateStats('total')
                avbotglobals.statsTimersDic['speed'] += 1
                
                #time.sleep(5) #sino esperamos un poco, es posible que exists() devuelva false, hace que se quede indefinidamente intentando guardar la pagina, despues de q la destruyan #fix arreglado con el .exists() antes de .put?
                #insertado time.sleep(5) justo antes de llamar a newArticleAnalysis(editData) en editAnalysis()
                _thread.start_new_thread(avbotanalysis.editAnalysis, (editData,))
        elif re.search(avbotglobals.parserRegexps['block'], line):
            match = avbotglobals.parserRegexps['block'].finditer(line)
            for m in match:
                blocker = m.group('blocker')
                blocked = m.group('blocked')
                block=m.group('block')
                wikipedia.output(u'\03{lightblue}Log: [[User:%s]] (%d) has been blocked by [[User:%s]] (%d) for %s\03{default}' % (blocked, len(blocked), blocker, len(blocker), block))
                _thread.start_new_thread(avbotcomb.blockedUser, (blocker, blocked, block))
        elif re.search(avbotglobals.parserRegexps['nuevousuario'], line):
            match = avbotglobals.parserRegexps['nuevousuario'].finditer(line)
            for m in match:
                usuario = m.group('usuario')
                wikipedia.output(u'\03{lightblue}Log: [[User:%s]] (%d) has signed up.\03{default}' % (usuario, len(usuario)))
        elif re.search(avbotglobals.parserRegexps['borrado'], line):
            match = avbotglobals.parserRegexps['borrado'].finditer(line)
            for m in match:
                pageTitle = m.group('pageTitle')
                usuario = m.group('usuario')
                wikipedia.output(u'\03{lightblue}Log: [[%s]] has been deleted by [[User:%s]]\03{default}' % (pageTitle, usuario))
        elif re.search(avbotglobals.parserRegexps['traslado'], line):
            match = avbotglobals.parserRegexps['traslado'].finditer(line)
            for m in match:
                usuario = m.group('usuario')
                origen = m.group('origen')
                destino = m.group('destino')
                wikipedia.output(u'\03{lightblue}Log: [[%s]] has been moved to [[%s]] by [[User:%s]]\03{default}' % (origen, destino, usuario))
        elif re.search(avbotglobals.parserRegexps['protegida'], line):
            match = avbotglobals.parserRegexps['protegida'].finditer(line)
            for m in match:
                pageTitle = m.group('pageTitle')
                protecter = m.group('protecter')
                edit = m.group('edit')
                move = m.group('move')
                wikipedia.output(u'\03{lightblue}Log: [[%s]] (%d) has been protected by [[User:%s]] (%d), edit=%s (%d), move=%s (%d)\03{default}' % (pageTitle, len(pageTitle), protecter, len(protecter), edit, len(edit), move, len(move)))
                #http://es.wikipedia.org/w/index.php?oldid=23222363#Candados
                #if re.search(ur'autoconfirmed', edit) and re.search(ur'autoconfirmed', move):
                #   _thread.start_new_thread(avbotcomb.semiprotect, (pageTitle, protecter))
        else:
            #wikipedia.output(u'No gestionada ---> %s' % line)
            f = open('lineasnogestionadas.txt', 'a')
            line = u'%s\n' % line
            try:
                f.write(line)
            except:
                try:
                    f.write(line.encode('utf-8'))
                except:
                    pass
            f.close()
        
        #Calculating and showing statistics
        if time.time()-avbotglobals.statsTimersDic['tvel']>=avbotglobals.preferences['statsDelay']: #Showing information in console every X seconds
            intervalo = int(time.time()-avbotglobals.statsTimersDic['tvel'])
            wikipedia.output(u'\03{lightgreen}%s working for %s: language of %s project\03{default}' % (avbotglobals.preferences['botNick'], avbotglobals.preferences['language'], avbotglobals.preferences['family']))
            wikipedia.output(u'\03{lightgreen}Average speed: %d edits/minute\03{default}' % int(avbotglobals.statsTimersDic['speed']/(intervalo/60.0)))
            wikipedia.output(u'\03{lightgreen}Last 2 hours: Vandalism[%d], Blanking[%d], Test[%d], S[%d], Good[%d], Bad[%d], Total[%d], Delete[%d]\03{default}' % (avbotglobals.statsDic[2]['v'], avbotglobals.statsDic[2]['bl'], avbotglobals.statsDic[2]['t'], avbotglobals.statsDic[2]['s'], avbotglobals.statsDic[2]['good'], avbotglobals.statsDic[2]['bad'], avbotglobals.statsDic[2]['total'], avbotglobals.statsDic[2]['d']))
            legend = u''
            for k,v in avbotglobals.preferences['colors'].items():
                legend += u'\03{%s}%s\03{default}, ' % (v, k)
            wikipedia.output(u'Colors meaning: \03{lightred}N\03{default}ew, \03{lightred}m\03{default}inor, %s...' % legend)
            avbotglobals.statsTimersDic['tvel'] = time.time()
            avbotglobals.statsTimersDic['speed'] = 0
        
        #Recalculating statistics
        for period in [2, 12, 24]: #Every 2, 12 and 24 hours
            avbotglobals.statsDic[period]['bad']=avbotglobals.statsDic[period]['v']+avbotglobals.statsDic[period]['bl']+avbotglobals.statsDic[period]['t']+avbotglobals.statsDic[period]['s']
            avbotglobals.statsDic[period]['good']=avbotglobals.statsDic[period]['total']-avbotglobals.statsDic[period]['bad']
            
            if time.time()-avbotglobals.statsTimersDic[period]>=3600*period:
                avbotsave.saveStats(avbotglobals.statsDic, period, avbotglobals.preferences['site'])     #Saving statistics in Wikipedia pages for historical reasons
                avbotglobals.statsTimersDic[period] = time.time()                                        #Saving start time
                avbotglobals.statsDic[period]       = {'v':0,'bl':0,'t':0,'s':0,'good':0,'bad':0,'total':0,'d':0} #Blanking statistics for a new period
        """
        
def main():
    """ Crea un objeto AVBOT y lo lanza """
    """ Creates AVBOT object and launch it """
    
    # Starting AVBOT
    avbot = AVBOT()
    avbot.start()

if __name__ == '__main__':
    main()
