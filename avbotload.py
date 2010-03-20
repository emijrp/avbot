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

## @package avbotload
# Module for data loads: user edits list, admins list, bots list, regexp list and excluded pages list\n
# Módulo para carga de datos: lista de usuarios por número de ediciones, administradores, bots, lista de expresiones regulares y de páginas excluidas

import re
import urllib
import wikipedia
import catlib
import sys

""" AVBOT modules """
import avbotglobals
import avbotcomb

def changedRegexpsList(dic1, dic2):
	""" ¿Los dos diccionarios de expresiones regulares son distintos? """
	""" Check if both dictionaries are not equal """
	if len(dic1.items())!=len(dic2.items()):
		return True
	else:
		changed=False
		for k, v in dic1.items():
			if not dic2.has_key(k):
				return True
	return False

def loadEdits():
	""" Carga fichero con número de ediciones """
	""" Load user edits file """
	newbie=avbotglobals.preferences['newbie']
	ediciones={}
	filename=avbotglobals.preferences['editsFilename']
	try:
		f=open(filename, "r")
	except:
		f=open(filename, "w")
		f.write('')
		f.close()
		f=open(filename, "r")
	l=ur""
	l=f.readline()
	while l:
		l=unicode(l, "utf-8")
		if len(l)>=4: #dos ; y un caracter de nick y un numero de ediciones
			#print l
			tmp=l.split(";")
			usuario=tmp[0]
			numero=tmp[1]
			if numero=='None':
				numero=0
			if numero<1: #nos curamos en salud, por el bug de usuarios con acentos ej: Zósimo, Botellín (aunque a boteellin no deberia ni revisarlo por ser bot)
				numero=newbie+1
			ediciones[usuario]=numero
		l=f.readline()
	f.close()
	
	wikipedia.output(u"Loaded info for %d users from \"%s\"" % (len(ediciones.items()), filename))
	
	avbotglobals.userData['edits']=ediciones

def loadUsers(type):
	""" Captura lista de usuarios de Wikipedia según el tipo deseado """
	""" Fetch user list by class """
	users=[]
	data=avbotglobals.preferences['site'].getUrl("/w/index.php?title=Special:Listusers&limit=5000&group=%s" % type)
	data=data.split('<!-- start content -->')
	data=data[1].split('<!-- end content -->')[0]
	namespace=avbotcomb.namespaceTranslator(2)
	m=re.compile(ur" title=\"%s:(.*?)\">" % namespace).finditer(data)
	for i in m:
		users.append(i.group(1))
	wikipedia.output(u"Loaded info for %d %ss from [[Special:Listusers]]" % (len(users), type))
	avbotglobals.userData[type]=users

def loadSysops():
	""" Carga lista de administradores """
	""" Load sysops list """
	loadUsers('sysop')

def loadBots():
	""" Carga lista de bots """
	""" Load bots list """
	loadUsers('bot')

def loadMessages():
	""" Carga preferencias sobre mensajes """
	""" Load messages preferences """
	#p=wikipedia.Page(avbotglobals.preferences['site'], u'User:%s/Mensajes.css' % avbotglobals.preferences['ownerNick'])
	tras=u'Mensajes.css'
	if avbotglobals.preferences['site'].lang=='en':
		tras=u'Messages.css'
	elif avbotglobals.preferences['site'].lang=='pt':
		tras=u'Mensagens.css'
	if avbotglobals.preferences['site'].lang=='es':
		p=wikipedia.Page(avbotglobals.preferences['site'], u'%s:Emijrp/%s' % (avbotglobals.namespaces[2], tras)) #Fijo a Emijrp para los clones de es:
	else:
		p=wikipedia.Page(avbotglobals.preferences['site'], u'%s:%s/%s' % (avbotglobals.namespaces[2], avbotglobals.preferences['ownerNick'], tras)) 
	raw=''
	if p.exists():
		if not p.isRedirectPage() and not p.isDisambig():
			raw=p.get()
	else:
		ownerNick=avbotglobals.preferences['ownerNick']
		wikipedia.output(u'A preferences page is needed in [[%s]]' % p.title())
		wikipedia.output(u'<pre>\n\n#Introduce a message per line.\n\nV;;100;;Vandalismo;;User:%s/AvisoVandalismo.css;;\nBL;;50;;Blanqueo;;User:%s/AvisoBlanqueo.css;;\nP;;10;;Prueba;;User:%s/AvisoPrueba.css;;\n#dummie\nC;;-100;;Contrapeso;;User:%s/AvisoContrapeso.css;;\n\n</pre>' % (ownerNick, ownerNick, ownerNick, ownerNick))
		wikipedia.output('A preferences page is needed. Please, look last bot edits.')
		if not avbotglobals.preferences['force']:
			sys.exit()
	
	avbotglobals.preferences['msg']={} #empty
	for l in raw.splitlines():
		l=l.strip()
		if len(l)>=3: #evitamos lineas demasiado pequenas
			if l[0]=='#' or l[0]=='<':
				continue
			trozos=l.split(';;')
			type=trozos[0].lower()
			priority=int(trozos[1])
			meaning=trozos[2]
			template=trozos[3]
			avbotglobals.preferences['msg'][type]={'priority': priority, 'meaning': meaning, 'template': template,}

def loadRegexpList():
	""" Carga lista de expresiones regulares """
	""" Load regular expression list """
	#p=wikipedia.Page(avbotglobals.preferences['site'], u'User:%s/Lista del bien y del mal.css' % avbotglobals.preferences['ownerNick'])
	goodandevil=u'Lista del bien y del mal.css'
	if avbotglobals.preferences['site'].lang=='en':
		goodandevil=u'Good and evil list.css'
	elif avbotglobals.preferences['site'].lang=='pt':
		goodandevil=u'Expressões.css'
	p=wikipedia.Page(avbotglobals.preferences['site'], u'%s:%s/%s' % (avbotglobals.namespaces[2], avbotglobals.preferences['ownerNick'], goodandevil))
	raw=''
	if p.exists():
		if not p.isRedirectPage() and not p.isDisambig():
			raw=p.get()
	else:
		wikipedia.output(u'A preferences page is needed in [[%s]]' % p.title())
		wikipedia.output(u'#Introduce one regexp per line. Format: REGEXP;;POINTS;;CLASS;;')
		if not avbotglobals.preferences['force']:
			sys.exit()
		
	c=0
	error=u''
	avbotglobals.vandalRegexps={}
	dontsort=[]
	dosort=[]
	for l in raw.splitlines():
		c+=1
		l=l.strip()
		if len(l)>=12: #Avoid short dangerous regexps
			if l=='<pre>' or l=='</pre>': #Skip preformatted labels
				continue
			if l[0]=='#' or l[0]=='<': #Skip no regexps lines
				dontsort.append(l)
				continue
			l=l.lower() #Be careful with LoadMessages(), always lower or always upper
			dosort.append(l)
			try:
				l=re.sub(ur"(?im)^([^\#]*?)\#[^\n\r]*?$", ur"\1", l)#Clean inline comments
				t=l.split(';;')
				type=t[2]
				reg=t[0]
				score=int(t[1])
				regex=ur'%s%s%s' % (avbotglobals.preferences['context'], reg, avbotglobals.preferences['context'])
				avbotglobals.vandalRegexps[reg]={'type':type, 'compiled':re.compile(ur'(?im)%s' % regex), 'score':score}
			except:
				error+=u'** Regexp error: Line: %d\n' % c
	
	#Sorting list
	#dejo de funcionar con la api?
	#dosort.sort()
	#if not avbotglobals.preferences['nosave']:
	#ordenada=wikipedia.Page(avbotglobals.preferences['site'], u'User:%s/Lista del bien y del mal.css' % avbotglobals.preferences['botNick'])
	#ordenada.put(u'<pre>\n%s\n\n%s\n</pre>' % ('\n'.join(dontsort), '\n'.join(dosort)), u'BOT - Ordenando lista [[User:Emijrp/Lista del bien y del mal.css]]')
	
	wikipedia.output(u'%s\n Loaded %s regular expresions\n%s' % ('-'*50, len(avbotglobals.vandalRegexps.items()), '-'*50))
	
	return error

def reloadRegexpList(author, diff):
	""" Recarga lista de expresiones regulares """
	""" Reload regular expression list """
	oldVandalRegexps=avbotglobals.vandalRegexps
	error=loadRegexpList()
	ownerNick=avbotglobals.preferences['ownerNick']
	goodandevil=u'Lista del bien y del mal.css'
	if avbotglobals.preferences['site'].lang=='en':
		goodandevil=u'Good and evil list.css'
	elif avbotglobals.preferences['site'].lang=='pt':
		goodandevil=u'Expressões.css'
	p=wikipedia.Page(avbotglobals.preferences['site'], u'%s:%s/%s' % (avbotglobals.namespaces[3], ownerNick, goodandevil)) #[3] porque es User talk:
	if not avbotglobals.preferences['nosave'] and avbotglobals.preferences['site'].lang=='es':
		if p.exists() and not re.search(ur"%s" % diff, p.get()):
			if changedRegexpsList(oldVandalRegexps, avbotglobals.vandalRegexps):
				if error:
					p.put(u'* {{subst:CURRENTDAY}} de {{subst:CURRENTMONTHNAME}} de {{subst:CURRENTYEAR}}, {{subst:CURRENTTIME}} (UTC): {{u|%s}} ha modificado la lista ([http://%s.wikipedia.org/w/index.php?title=User:%s/Lista_del_bien_y_del_mal.css&diff=%s&oldid=prev ver diff]). Ahora hay %d expresiones regulares válidas.\n%s%s' % (author, avbotglobals.preferences['language'], ownerNick, diff, len(avbotglobals.vandalRegexps), error, p.get()), u'BOT - La lista ha cambiado. Total [%d]' % len(avbotglobals.vandalRegexps))
				else:
					p.put(u'* {{subst:CURRENTDAY}} de {{subst:CURRENTMONTHNAME}} de {{subst:CURRENTYEAR}}, {{subst:CURRENTTIME}} (UTC): {{u|%s}} ha modificado la lista ([http://%s.wikipedia.org/w/index.php?title=User:%s/Lista_del_bien_y_del_mal.css&diff=%s&oldid=prev ver diff]). Ahora hay %d expresiones regulares válidas.\n%s' % (author, avbotglobals.preferences['language'], ownerNick, diff, len(avbotglobals.vandalRegexps), p.get()), u'BOT - La lista ha cambiado. Total [%d]' % len(avbotglobals.vandalRegexps))
			else:
				if error:
					p.put(u'* {{subst:CURRENTDAY}} de {{subst:CURRENTMONTHNAME}} de {{subst:CURRENTYEAR}}, {{subst:CURRENTTIME}} (UTC): {{u|%s}} ha editado la página pero hay las mismas %d expresiones regulares válidas ([http://%s.wikipedia.org/w/index.php?title=User:%s/Lista_del_bien_y_del_mal.css&diff=%s&oldid=prev ver diff]).\n%s%s' % (author, len(avbotglobals.vandalRegexps), avbotglobals.preferences['language'], ownerNick, diff, error, p.get()), u'BOT - La lista no ha cambiado. Total [%d]' % len(avbotglobals.vandalRegexps))
				else:
					p.put(u'* {{subst:CURRENTDAY}} de {{subst:CURRENTMONTHNAME}} de {{subst:CURRENTYEAR}}, {{subst:CURRENTTIME}} (UTC): {{u|%s}} ha editado la página pero hay las mismas %d expresiones regulares válidas ([http://%s.wikipedia.org/w/index.php?title=User:%s/Lista_del_bien_y_del_mal.css&diff=%s&oldid=prev ver diff]).\n%s' % (author, len(avbotglobals.vandalRegexps), avbotglobals.preferences['language'], ownerNick, diff, p.get()), u'BOT - La lista no ha cambiado. Total [%d]' % len(avbotglobals.vandalRegexps))
	return

def loadUserEdits(author):
	""" Carga númeor de ediciones de un usuario en concreto """
	""" Load user edits number """
	author_=re.sub(' ', '_', author)
	try:
		rawdata=avbotglobals.preferences['site'].getUrl("/w/api.php?action=query&list=users&ususers=%s&usprop=editcount&format=xml" % urllib.quote(author_))
		if re.search(u"editcount", rawdata):
			m=re.compile(ur' editcount="(\d+)"').finditer(rawdata)
			for i in m:
				editsnum=int(i.group(1))
				if editsnum<1:
					return avbotglobals.preferences['newbie']+1
				else:
					return editsnum
		else:
			return avbotglobals.preferences['newbie']+1
	except:
		return avbotglobals.preferences['newbie']+1

def loadExclusions():
	""" Carga lista de páginas excluidas """
	""" Load excluded pages list """
	#p=wikipedia.Page(avbotglobals.preferences['site'], u'User:%s/Exclusiones.css' % avbotglobals.preferences['ownerNick'])
	tras=u'Exclusiones.css'
	if avbotglobals.preferences['site'].lang=='en':
		tras=u'Exclusions.css'
	elif avbotglobals.preferences['site'].lang=='pt':
		tras=u'Exclusões.css'
	ownerNick=avbotglobals.preferences['ownerNick']
	p=wikipedia.Page(avbotglobals.preferences['site'], u'%s:%s/%s' % (avbotglobals.namespaces[2], ownerNick, tras))
	raw=''
	if p.exists():
		if not p.isRedirectPage() and not p.isDisambig():
			raw=p.get()
	else:
		wikipedia.output('A preferences page is needed in [[%s]]' % p.title())
		wikipedia.output('Introduce an excluded page per line. Without [[]]')
		wikipedia.output('You can skip this with -force parameter')
		if not avbotglobals.preferences['force']:
			sys.exit()
	
	for l in raw.splitlines():
		l=l.strip()
		if len(l)>=1:
			if l[0]=='#' or l[0]=='<':
				continue
			l=re.sub(ur"(?im)^([^\#]*?)\#[^\n\r]*?$", ur"\1", l)#Clean inline comments
			t=l.split(';;')
			exclusion=t[0]
			if not avbotglobals.excludedPages.has_key(exclusion):
				avbotglobals.excludedPages[exclusion]=True
	
	wikipedia.output(u"Loaded %d page excluded pages..." % (len(avbotglobals.excludedPages.items())))
