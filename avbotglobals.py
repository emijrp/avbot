# -*- coding: utf-8 -*-

# AVBOT - Anti-Vandalism BOT for MediaWiki projects
# Copyright (C) 2008-2010 Emilio José Rodríguez Posada
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

## @package avbotglobals
# Module for shared variables\n
# Módulo para variables compartidas

""" External modules """
""" Python modules """
import re
import random
import sys
import wikipedia
import time
import os

""" AVBOT modules """
import avbotcomb

""" Default bot preferences """
global preferences
preferences = {
	'botNick':       u'Bot',             #Bot name
	'ownerNick':     u'Owner',             #Owner nick
	'language':      u'es',                #Default language is Spanish
	'family':        u'wikipedia',         #Default project family is Wikipedia
	'site':          0,                    #Empty var
	'network':       u'irc.wikimedia.org', #IRC network where is the IRC channel with recent changes
	'channel':       0,                    #RSS channel for recent changes in Wikipedia
	'nickname':      0,                    #Bot nick in channel, with random numbers to avoid nick collisions
	'port':          6667,                 #Port number
	'logsDirectory': 'botlogs',            #Directory reverts logs, not ending in /
	'newbie':        25,                   #Who is a newbie user? How many edits?
	'statsDelay':    60,                   #How man seconds between showing stats in screen
	'colors':        {
		'steward': 'lightblue',
		'sysop': 'lightblue',
		'bureaucrat': 'lightblue',
		'checkuser': 'lightblue',
		'bot':   'lightpurple',
		'reg':   'lightgreen',
		'anon':  'lightyellow',
	},
	'context':       ur'[ \@\º\ª\·\#\~\$\<\>\/\(\)\'\-\_\:\;\,\.\r\n\?\!\¡\¿\"\=\[\]\|\{\}\+\&]',
	'msg':           {},
	'testmode':      False,
	'nosave':        False,
	'force':         False,
	'trial':         False,
	'editsFilename': 'edits.txt',
	'historyLength': 10, # history length to recover
}

""" Header message """
header  = u"\nAVBOT Copyright (C) 2008-2010 Emilio José Rodríguez Posada\n"
header += u"This program comes with ABSOLUTELY NO WARRANTY.\n"
header += u"This is free software, and you are welcome to redistribute it\n"
header += u"under certain conditions. See license.\n\n"
header += u"############################################################################\n"
header += u"# Name:    AVBOT (Anti-Vandalism BOT)                                      #\n"
header += u"# Version: 1.2                                                             #\n"
header += u"# Tasks:   To revert vandalism, blanking and test edits                    #\n"
header += u"#          To report vandalism waves attacks to admins                     #\n"
header += u"#          To improve new articles (magic interwikis)                      #\n"
header += u"#          To mark for deletion rubbish articles                           #\n"
header += u"############################################################################\n\n"
header += u"Available parameters (* obligatory): -lang, -family, -newbie, -botnick*, -statsdelay, -network, -channel, -ownernick*, -nosave, -force\n"
header += u"Example: python avbot.py -botnick:MyBot -ownernick:MyUser\n"
wikipedia.output(header)

avbotcomb.getParameters()

#if avbotcomb.checkForUpdates(): #no llega al directorio actual (cron lo ejecuta con la absoluta)
#	wikipedia.output(u"***New code available*** Please, update your copy of AVBOT from http://avbot.googlecode.com/svn/trunk/")
#	#sys.exit()

preferences['site']     = wikipedia.Site(preferences['language'], preferences['family'])
if not preferences['nosave']:
	testEdit                = wikipedia.Page(preferences['site'], 'User:%s/Sandbox' % preferences['botNick'])
	testEdit.put(u'Test edit', u'BOT - Arrancando robot', botflag=False, maxTries=1) #same text always, avoid avbotcron edit panic
	testEdit                = wikipedia.Page(wikipedia.Site(u'en', u'wikipedia'), 'User:%s/Sandbox' % preferences['botNick'])
	testEdit.put(u'Test edit', u'BOT - Arrancando robot', botflag=False, maxTries=1) #same text always, avoid avbotcron edit panic

if not preferences['channel']:
	preferences['channel']  = '#%s.%s' % (preferences['language'], preferences['family'])
if not preferences['nickname']:
	preferences['nickname'] = '%s%s' % (preferences['botNick'], str(random.randint(1000, 9999)))

preferences['editsFilename']='%s-%s-edits.txt' % (preferences['language'], preferences['family'])

preferences['goodandevil']=u'Lista del bien y del mal.css'
preferences['exclusions']=u'Exclusiones.css'
preferences['messages']=u'Mensajes.css'
if preferences['site'].lang=='en':
	preferences['goodandevil']=u'Good and evil list.css'
	preferences['exclusions']=u'Exclusions.css'
	preferences['messages']=u'Messages.css'
elif preferences['site'].lang=='pt':
	preferences['goodandevil']=u'Expressões.css'
	preferences['exclusions']=u'Exclusões.css'
	preferences['messages']=u'Mensagens.css'
	
global namespaces
namespaces={}
namespaces[2] = avbotcomb.namespaceTranslator(2)
namespaces[3] = avbotcomb.namespaceTranslator(3)

global statsDic
statsDic={}
statsDic[2]  = {'v':0,'bl':0,'t':0,'s':0,'good':0,'bad':0,'total':0,'d':0}
statsDic[12] = {'v':0,'bl':0,'t':0,'s':0,'good':0,'bad':0,'total':0,'d':0}
statsDic[24] = {'v':0,'bl':0,'t':0,'s':0,'good':0,'bad':0,'total':0,'d':0}

global statsTimersDic
statsTimersDic={'speed':0, 2: time.time(), 12: time.time(), 24: time.time(), 'tvel': time.time()}

global existFile
existFile = '%s-%s-%s-exist.txt' % (preferences['language'], preferences['family'], preferences['botNick'])
global pidFile
pidFile = '%s-%s-%s-mypid.txt' % (preferences['language'], preferences['family'], preferences['botNick'])

global userData
userData={}

global vandalControl
vandalControl={}

global vandalRegexps
vandalRegexps={}

global excludedPages
excludedPages={}

global parserRegexps
parserRegexps={
	'cleandiff-diff-context': re.compile(ur'diff-context'),
	'cleandiff-diff-addedline': re.compile(ur'diff-addedline'),
	'cleandiff-diff-addedline-div': re.compile(ur'<td class="diff-addedline"><div>'),
	'cleandiff-diff-deletedline': re.compile(ur'diff-deletedline'),
	'cleandiff-diffchange': re.compile(ur'(<span class="diffchange">|<span class="diffchange diffchange-inline">|<ins class="diffchange diffchange-inline">)(?P<text>[^<]*?)</(ins|span)>'),
	'watch-1': re.compile(ur'\/'),
	'goodandevil': re.compile(ur'%s:%s/%s' % (namespaces[2], preferences['ownerNick'], preferences['goodandevil'])),
	'exclusions': re.compile(ur'%s:%s/%s' % (namespaces[2], preferences['ownerNick'], preferences['exclusions'])),
	'messages': re.compile(ur'%s:%s/%s' % (namespaces[2], preferences['ownerNick'], preferences['messages'])),
	'anti-birthday-es': re.compile(ur'(?m)^\d{1,2} de (enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)$'),
	'loaduseredits-editcount': re.compile(ur'editcount'),
	'loaduseredits-editcount-d': re.compile(ur' editcount="(\d+)"'),
	'isrubbish-tl-red': re.compile(ur'(?i)\{\{|redirect'),
	'isrubbish-link': re.compile(ur'\[\['),
	'blanqueos':      re.compile(ur'(?i)(redirect|redirección|desamb|\{\{ *(copyvio|destruir|plagio|robotdestruir|wikificar))'), #fix add more cases for en: and pt: mainly
	'block':          re.compile(ur'(?i)\[\[Especial:Log/block\]\] +block +\* +(?P<blocker>.*?) +\* +bloqueó a +\"Usuario\:(?P<blocked>.*?)\" +.*?durante un plazo de \"(?P<block>.*?)\"'),
	#[[Especial:Log/delete]] delete  * Snakeyes * borró "Discusión:Gastronomía en Estados Unidos": borrado rápido usando [[w:es:User:Axxgreazz/Monobook-Suite|monobook-suite]] el contenido era: «{{delete|Vandalismo}} {{fuenteprimaria|6|mayo}} Copia y pega el siguiente código en la página de discusión del creador del artículo: == Ediciones con investigac
	#'borrado': re.compile(ur'(?i)\[\[...(?P<pageTitle>.*?)..\]\].*?delete.*?\*.....(?P<usuario>.*?)...\*'),
	'borrado':        re.compile(ur'(?i)\[\[Especial:Log/delete\]\] +delete +\* +(?P<usuario>.*?) +\* +borró +«(?P<pageTitle>.*?)»\:'),
	'categories':     re.compile(ur'(?i)\[\[ *(Category|Categoría) *\: *[^\]\n\r]+? *\]\]'),
	'conflictivos':   re.compile(ur'(?i)\{\{ *(autotrad|maltrad|mal traducido|wikci|al? (wikcionario|wikicitas|wikinoticias|wikiquote|wikisource)) *\}\}'),
	'destruir':       re.compile(ur'(?i)\{\{ *destruir'),
	#diffstylebegin y end va relacionado
	'diffstylebegin': re.compile(ur'(<span class="diffchange">|<span class="diffchange diffchange-inline">|<ins class="diffchange diffchange-inline">)'),
	'diffstyleend':   re.compile(ur'(<span class="diffchange">|<span class="diffchange diffchange-inline">|<ins class="diffchange diffchange-inline">)(?P<text>[^<]*?)</(ins|span)>'),
	'interwikis':     re.compile(ur'(?i)\[\[ *[a-z]{2} *\: *[^\]\|\n\r]+? *\]\]'),
	'ip':             re.compile(ur'(?im)^([1-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-6])\.([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-6])\.([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-6])\.([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-6])$'),
	'firmas1':        re.compile(ur'<td class="diff-addedline"><div>([^<]*?)</div>'),
	#sin title
	#'edit': re.compile(ur'(?i)\[\[(?P<pageTitle>.*?)\]\] +(?P<nm>.*?) +http\://%s\.wikipedia\.org/w/index\.php\?title\=.*?diff\=(?P<diff>\d+)\&oldid\=(?P<oldid>\d+) +\* +(?P<author>.*?) +\* +\(.*?\) +(?P<resume>.*)' % preferences['language']),
	'edit':           re.compile(ur'(?i)\[\[(?P<pageTitle>.*?)\]\] +(?P<nm>.*?) +http\://%s\.wikipedia\.org/w/index\.php\?diff\=(?P<diff>\d+)\&oldid\=(?P<oldid>\d+)(\&rcid=\d+)? +\* +(?P<author>.*?) +\* +\(.*?\) +(?P<resume>.*)' % preferences['language']),
	#'newpage': re.compile(ur'(?i)\[\[(?P<pageTitle>.*?)\]\] +(?P<nm>.*?) +http\://%s\.wikipedia\.org/w/index\.php\?title\=.*?\&rcid\=\d+ +\* (?P<author>.*?) +\*' % preferences['language']),
	'newpage':        re.compile(ur'(?i)\[\[(?P<pageTitle>.*?)\]\] +(?P<nm>.*?) +http\://%s\.wikipedia\.org/w/index\.php\?oldid\=(?P<oldid>\d+)(\&rcid=\d+)? +\* +(?P<author>.*?) +\* +\(.*?\) +(?P<resume>.*)' % preferences['language']),
	'nuevousuario':   re.compile(ur'(?i)\[\[Especial:Log/newusers\]\] +create +\* +(?P<usuario>.*?) +\* +Usuario nuevo'),
	'protegida':      re.compile(ur'(?i)\[\[Especial:Log/protect\]\] +protect +\* +(?P<protecter>.*?) +\* +protegió +\[\[(?P<pageTitle>.*?)\]\] +\[edit\=(?P<edit>sysop|autoconfirmed)\][^\[]*?\[move\=(?P<move>sysop|autoconfirmed)\]'),
	#protegidacreacion [[Especial:Log/protect]] protect  * Snakeyes *  protegió [[Tucupido cincuentero]] [create=sysop]  (indefinido): Artículo ensayista reincidente
	'desprotegida':   re.compile(ur'(?i)\[\[.*?Especial\:Log/protect.*?\]\].*?unprotect'),
	'spam':           re.compile(ur'(?im)<td class="diff-addedline"><div>[^<]*?(http://[a-z0-9\.\-\=\?\_\/]+)[^<]*?</div></td>'),
	#[[Especial:Log/move]] move_redir  * Manuel González Olaechea y Franco * [[Anexo:Presidente del Perú]] ha sido trasladado a [[Anexo:Presidentes del Perú]] sobre una redirección.
	#[[Especial:Log/move]] move  * Dhidalgo *  [[Macizo Etíope]] ha sido trasladado a [[Macizo etíope]]
	'traslado':       re.compile(ur'(?i)\[\[Especial:Log/move\]\] +move +\* +(?P<usuario>.*?) +\* +\[\[(?P<origen>.*?)\]\] +ha sido trasladado a +\[\[(?P<destino>.*?)\]\]'),
	}

#Check logs directory
if not os.path.exists(preferences['logsDirectory']):
	wikipedia.output(u"Creating logs directory...")
	os.system("mkdir %s" % (preferences['logsDirectory']))
	if not os.path.exists(preferences['logsDirectory']):
		wikipedia.output(u"Error creating directory")
