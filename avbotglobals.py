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

## @package avbotglobals
# Module for shared variables\n
# Módulo para variables compartidas

""" External modules """
""" Python modules """
import re
import random
import sys
import time
import os


avbotcomb.getParameters()



if not preferences['dryrun']:
    testEdit = pywikibot.Page(preferences['site'], 'User:%s/AVBOT' % (preferences['botNick']))
    testEdit.text = 'Starting AVBOT'
    testEdit.save('BOT - Starting AVBOT', botflag=False, maxTries=3) # Same text always, avoid avbotcron edit panic

namespaces[2] = avbotcomb.namespaceTranslator(2)
namespaces[3] = avbotcomb.namespaceTranslator(3)

global statsDic
statsDic={}
statsDic[2]  = {'v':0,'bl':0,'t':0,'s':0,'good':0,'bad':0,'total':0,'d':0}
statsDic[12] = {'v':0,'bl':0,'t':0,'s':0,'good':0,'bad':0,'total':0,'d':0}
statsDic[24] = {'v':0,'bl':0,'t':0,'s':0,'good':0,'bad':0,'total':0,'d':0}

global statsTimersDic
statsTimersDic={'speed':0, 2: time.time(), 12: time.time(), 24: time.time(), 'tvel': time.time()}



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
    'cleandiff-diff-context': re.compile(r'diff-context'),
    'cleandiff-diff-addedline': re.compile(r'diff-addedline'),
    'cleandiff-diff-addedline-div': re.compile(r'<td class="diff-addedline"><div>'),
    'cleandiff-diff-deletedline': re.compile(r'diff-deletedline'),
    'cleandiff-diffchange': re.compile(r'(<span class="diffchange">|<span class="diffchange diffchange-inline">|<ins class="diffchange diffchange-inline">)(?P<text>[^<]*?)</(ins|span)>'),
    'watch-1': re.compile(r'\/'),
    'goodandevil': re.compile(r'%s:%s/%s' % (namespaces[2], preferences['ownerNick'], preferences['goodandevil'])),
    'exclusions': re.compile(r'%s:%s/%s' % (namespaces[2], preferences['ownerNick'], preferences['exclusions'])),
    'messages': re.compile(r'%s:%s/%s' % (namespaces[2], preferences['ownerNick'], preferences['messages'])),
    'anti-birthday-es': re.compile(r'(?m)^\d{1,2} de (enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)$'),

    'isrubbish-tl-red': re.compile(r'(?i)\{\{|redirect'),
    'isrubbish-link': re.compile(r'\[\['),
    'blanqueos':      re.compile(r'(?i)(redirect|redirección|desamb|\{\{ *(db\-|copyvio|destruir|plagio|robotdestruir|wikificar))'), #fix add more cases for en: and pt: mainly db-copyvio
    'block':          re.compile(r'(?i)\[\[Especial:Log/block\]\] +block +\* +(?P<blocker>.*?) +\* +bloqueó a +\"Usuario\:(?P<blocked>.*?)\" +.*?durante un plazo de \"(?P<block>.*?)\"'),
    #[[Especial:Log/delete]] delete  * Snakeyes * borró "Discusión:Gastronomía en Estados Unidos": borrado rápido usando [[w:es:User:Axxgreazz/Monobook-Suite|monobook-suite]] el contenido era: «{{delete|Vandalismo}} {{fuenteprimaria|6|mayo}} Copia y pega el siguiente código en la página de discusión del creador del artículo: == Ediciones con investigac
    #'borrado': re.compile(r'(?i)\[\[...(?P<pageTitle>.*?)..\]\].*?delete.*?\*.....(?P<usuario>.*?)...\*'),
    'borrado':        re.compile(r'(?i)\[\[Especial:Log/delete\]\] +delete +\* +(?P<usuario>.*?) +\* +borró +«(?P<pageTitle>.*?)»\:'),
    'categories':     re.compile(r'(?i)\[\[ *(Category|Categoría) *\: *[^\]\n\r]+? *\]\]'),
    'footerallowed':     re.compile(r"(?i)(\[\[|\=\=|\:\/\/|\{\{|\'\'|\:|\, |\.(com|org|edu|gov|net|info|tv))"), #http://en.wikipedia.org/w/index.php?title=Sukhoi_Superjet_100&diff=353978236&oldid=353978214
    'conflictivos':   re.compile(r'(?i)( Cfd | AfD |(\{\{ *(AfDM|ad|advert|spam|cleanup|copy ?to|db\-|isrev|inuse|Underconstruction|copyvio|copypaste|autotrad|maltrad|mal traducido|anuncio|promocional|publicidad|sin ?relevancia|SRA|irrelevante|wikci|al? (wikcionario|wikicitas|wikinoticias|wikiquote|wikisource))))'), #promocional etc suelen ser blanqueados o mejorados por IPs para que quiten el cartel, evitamos revertir http://en.wikipedia.org/wiki/Wikipedia:Template_messages/Maintenance #fix pasar a una subpágina /Skip
    'destruir':       re.compile(r'(?i)( Cfd | AfD |(\{\{ *(destruir|db\-|spam|ad)))'),
    #diffstylebegin y end va relacionado
    'diffstylebegin': re.compile(r'(<span class="diffchange">|<span class="diffchange diffchange-inline">|<ins class="diffchange diffchange-inline">)'),
    'diffstyleend':   re.compile(r'(<span class="diffchange">|<span class="diffchange diffchange-inline">|<ins class="diffchange diffchange-inline">)(?P<text>[^<]*?)</(ins|span)>'),
    'interwikis':     re.compile(r'(?i)\[\[ *[a-z]{2} *\: *[^\]\|\n\r]+? *\]\]'),
    'ip':             re.compile(r'(?im)^([1-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-6])\.([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-6])\.([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-6])\.([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-6])$'),
    'firmas1':        re.compile(r'<td class="diff-addedline"><div>([^<]*?)</div>'),
    #sin title
    #'edit': re.compile(r'(?i)\[\[(?P<pageTitle>.*?)\]\] +(?P<nm>.*?) +http\://%s\.wikipedia\.org/w/index\.php\?title\=.*?diff\=(?P<diff>\d+)\&oldid\=(?P<oldid>\d+) +\* +(?P<author>.*?) +\* +\(.*?\) +(?P<resume>.*)' % preferences['language']),
    'edit':           re.compile(r'(?i)\[\[(?P<pageTitle>.*?)\]\] +(?P<nm>.*?) +http\://%s\.wikipedia\.org/w/index\.php\?diff\=(?P<diff>\d+)\&oldid\=(?P<oldid>\d+)(\&rcid=\d+)? +\* +(?P<author>.*?) +\* +\(.*?\) +(?P<resume>.*)' % preferences['language']),
    #'newpage': re.compile(r'(?i)\[\[(?P<pageTitle>.*?)\]\] +(?P<nm>.*?) +http\://%s\.wikipedia\.org/w/index\.php\?title\=.*?\&rcid\=\d+ +\* (?P<author>.*?) +\*' % preferences['language']),
    'newpage':        re.compile(r'(?i)\[\[(?P<pageTitle>.*?)\]\] +(?P<nm>.*?) +http\://%s\.wikipedia\.org/w/index\.php\?oldid\=(?P<oldid>\d+)(\&rcid=\d+)? +\* +(?P<author>.*?) +\* +\(.*?\) +(?P<resume>.*)' % preferences['language']),
    'nuevousuario':   re.compile(r'(?i)\[\[Especial:Log/newusers\]\] +create +\* +(?P<usuario>.*?) +\* +Usuario nuevo'),
    'protegida':      re.compile(r'(?i)\[\[Especial:Log/protect\]\] +protect +\* +(?P<protecter>.*?) +\* +protegió +\[\[(?P<pageTitle>.*?)\]\] +\[edit\=(?P<edit>sysop|autoconfirmed)\][^\[]*?\[move\=(?P<move>sysop|autoconfirmed)\]'),
    #protegidacreacion [[Especial:Log/protect]] protect  * Snakeyes *  protegió [[Tucupido cincuentero]] [create=sysop]  (indefinido): Artículo ensayista reincidente
    'desprotegida':   re.compile(r'(?i)\[\[.*?Especial\:Log/protect.*?\]\].*?unprotect'),
    'spam':           re.compile(r'(?im)<td class="diff-addedline"><div>[^<]*?(http://[a-z0-9\.\-\=\?\_\/]+)[^<]*?</div></td>'),
    #[[Especial:Log/move]] move_redir  * Manuel González Olaechea y Franco * [[Anexo:Presidente del Perú]] ha sido trasladado a [[Anexo:Presidentes del Perú]] sobre una redirección.
    #[[Especial:Log/move]] move  * Dhidalgo *  [[Macizo Etíope]] ha sido trasladado a [[Macizo etíope]]
    'traslado':       re.compile(r'(?i)\[\[Especial:Log/move\]\] +move +\* +(?P<usuario>.*?) +\* +\[\[(?P<origen>.*?)\]\] +ha sido trasladado a +\[\[(?P<destino>.*?)\]\]'),
    }

#Check logs directory
if not os.path.exists(preferences['logsDirectory']):
    wikipedia.output(u"Creating logs directory...")
    os.system("mkdir %s" % (preferences['logsDirectory']))
    if not os.path.exists(preferences['logsDirectory']):
        wikipedia.output(u"Error creating directory")
