# -*- coding: utf-8 -*-

# AVBOT - Antivandal bot for MediaWiki projects
# Copyright (C) 2008 Emilio José Rodríguez Posada
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
# Module for shared variables

import re
import random
import sys
import wikipedia

import avbotcomb

""" Default bot preferences """
global preferences
preferences = {
	'botNick':    u'AVBOT',             #Bot name
	'language':   u'es',                #Default language is Spanish
	'family':     u'wikipedia',         #Default project family is Wikipedia
	'site':       0,
	'network':    u'irc.wikimedia.org', #IRC network where is the IRC channel with recent changes
	'channel':    0,                    #RSS channel for recent changes in Wikipedia
	'nickname':   0,                    #Bot nick in channel, with random numbers to avoid nick collisions
	'port':       6667,                 #Port number
	'newbie':     25,                   #Who is a newbie user? How many edits?
	'statsDelay': 60,
	'colors':     {
		'admin': 'lightblue',
		'bot':   'lightpurple',
		'reg':   'lightgreen',
		'anon':  'lightyellow',
	},
	'context':    ur'[ \@\º\ª\·\#\~\$\<\>\/\(\)\'\-\_\:\;\,\.\r\n\?\!\¡\¿\"\=\[\]\|\{\}\+\&]',
}
avbotcomb.getParameters()
preferences['site']     = wikipedia.Site(preferences['language'], preferences['family'])
preferences['channel']  = '#%s.%s' % (preferences['language'], preferences['family'])
preferences['nickname'] = '%s%s' % (preferences['botNick'], str(random.randint(1000, 9999)))

global statsDic
statsDic={}
statsDic[2]  = {'V':0,'BL':0,'P':0,'S':0,'B':0,'M':0,'T':0,'D':0}
statsDic[12] = {'V':0,'BL':0,'P':0,'S':0,'B':0,'M':0,'T':0,'D':0}
statsDic[24] = {'V':0,'BL':0,'P':0,'S':0,'B':0,'M':0,'T':0,'D':0}

global vandalControl
vandalControl={}

global vandalRegexps
vandalRegexps={}

global excludedPages
excludedPages={}

global parserRegexps
parserRegexps={
	'blanqueos':      re.compile(ur'(?i)redirect|desamb|\{\{ *(copyvio|destruir|plagio|robotdestruir|wikificar)'),
	'block':          re.compile(ur'(?i)\[\[Especial:Log/block\]\] +block +\* +(?P<blocker>.*?) +\* +bloqueó a +\"Usuario\:(?P<blocked>.*?)\" +.*?durante un plazo de \"(?P<block>.*?)\"'),
	#[[Especial:Log/delete]] delete  * Snakeyes * borró "Discusión:Gastronomía en Estados Unidos": borrado rápido usando [[w:es:User:Axxgreazz/Monobook-Suite|monobook-suite]] el contenido era: «{{delete|Vandalismo}} {{fuenteprimaria|6|mayo}} Copia y pega el siguiente código en la página de discusión del creador del artículo: == Ediciones con investigac
	#'borrado': re.compile(ur'(?i)\[\[...(?P<pageTitle>.*?)..\]\].*?delete.*?\*.....(?P<usuario>.*?)...\*'),
	'borrado':        re.compile(ur'(?i)\[\[Especial:Log/delete\]\] +delete +\* +(?P<usuario>.*?) +\* +borró +«(?P<pageTitle>.*?)»\:'),
	'conflictivos':   re.compile(ur'(?i)\{\{ *(autotrad|maltrad|mal traducido|wikci|al? (wikcionario|wikicitas|wikinoticias|wikiquote|wikisource)) *\}\}'),
	'destruir':       re.compile(ur'(?i)\{\{ *destruir'),
	#diffstylebegin y end va relacionado
	'diffstylebegin': re.compile(ur'(<span class="diffchange">|<span class="diffchange diffchange-inline">|<ins class="diffchange diffchange-inline">)'),
	'diffstyleend':   re.compile(ur'(<span class="diffchange">|<span class="diffchange diffchange-inline">|<ins class="diffchange diffchange-inline">)([^<]*?)</(ins|span)>'),
	'ip':             re.compile(ur'(?im)^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'),
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
