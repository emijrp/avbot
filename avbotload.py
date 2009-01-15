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

## @package avbotload
# Module for data loads: user edits list, admins list, bots list, regexp list and excludedPages list

import re
import urllib
import wikipedia
import catlib

""" AVBOT modules """
import avbotglobals
import avbotcomb

def changedRegexpsList(dic1, dic2):
	"""  """
	"""  """
	#funcion que devuelve si las dos listas de expresiones regualres son distintas
	#se sabe que las listas son en realidad diccionarios, y su clave es la expresion regular. Mas detalles en loadRegexpList()
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
	try:
		f=open("ediciones.txt", "r")
	except:
		f=open("ediciones.txt", "w")
		f.write('')
		f.close()
		f=open("ediciones.txt", "r")
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
	
	wikipedia.output(u"Loaded info for %d users..." % len(ediciones.items()))
	
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
	wikipedia.output(u"Loaded info for %d %ss..." % (len(users), type))
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
	"""  """
	"""  """
	wiii=wikipedia.Page(avbotglobals.preferences['site'], u'User:Emijrp/Mensajes.css')
	raw=''
	if wiii.exists() and not wiii.isRedirectPage() and not wiii.isDisambig():
		raw=wiii.get()
	
	avbotglobals.preferences['msg']={} #empty
	for l in raw.splitlines():
		if len(l)>=3: #evitamos lineas demasiado pequenas
			if l[0]=='#' or l[0]=='<':
				continue
			trozos=l.split(';;')
			type=trozos[0]
			priority=int(trozos[1])
			meaning=trozos[2]
			template=trozos[3]
			avbotglobals.preferences['msg'][type]={'priority': priority, 'meaning': meaning, 'template': template,}

def loadRegexpList():
	"""  """
	"""  """
	wiii=wikipedia.Page(avbotglobals.preferences['site'], u'User:Emijrp/Lista del bien y del mal.css')
	raw=''
	if wiii.exists() and not wiii.isRedirectPage() and not wiii.isDisambig():
		raw=wiii.get()
	
	c=0
	error=u''
	avbotglobals.vandalRegexps={}
	for l in raw.splitlines():
		c+=1
		if len(l)>=3: #evitamos regex demasiado pequenas
			if l[0]=='#' or l[0]=='<':
				continue
			trozos=l.split(';;')
			type=trozos[0]
			reg=trozos[1]
			score=int(trozos[2])
			regex=ur'%s%s%s' % (avbotglobals.preferences['context'], reg, avbotglobals.preferences['context'])
			try:
				avbotglobals.vandalRegexps[reg]={'type':type, 'compiled':re.compile(ur'(?im)%s' % regex), 'score':score}
			except:
				error+=u'=== Error en regexp ===\n'
				error+=u'* Línea: %d' % c
				error+=u'\n* Regexp errónea: %s' % reg
				error+=u'\n* Regexp errónea (con contexto): %s' % regex
				error+=u'\n* Puntuación: %d\n\n' % score
	
	return error

def reloadRegexpList(author, diff):
	"""  """
	"""  """
	oldVandalRegexps=avbotglobals.vandalRegexps
	error=loadRegexpList()
	if changedRegexpsList(oldVandalRegexps, avbotglobals.vandalRegexps):
		wiii=wikipedia.Page(avbotglobals.preferences['site'], u'User talk:Emijrp/Lista del bien y del mal.css')
		if error:
			wiii.put(u'== {{subst:LOCALDAYNAME}}, {{subst:CURRENTDAY}} de {{subst:CURRENTMONTHNAME}} de {{subst:CURRENTYEAR}}, {{subst:CURRENTTIME}} (UTC) ==\n{{u|%s}} ha modificado la lista ([http://%s.wikipedia.org/w/index.php?title=User:Emijrp/Lista_del_bien_y_del_mal.css&diff=%s&oldid=prev ver diff]). Ahora hay %d expresiones regulares válidas.\n\n%s%s' % (author, avbotglobals.preferences['language'], diff, len(avbotglobals.vandalRegexps), error, wiii.get()), u'BOT - La lista del bien y del mal ha cambiado. Total [%d]' % len(avbotglobals.vandalRegexps))
		else:
			wiii.put(u'== {{subst:LOCALDAYNAME}}, {{subst:CURRENTDAY}} de {{subst:CURRENTMONTHNAME}} de {{subst:CURRENTYEAR}}, {{subst:CURRENTTIME}} (UTC) ==\n{{u|%s}} ha modificado la lista ([http://%s.wikipedia.org/w/index.php?title=User:Emijrp/Lista_del_bien_y_del_mal.css&diff=%s&oldid=prev ver diff]). Ahora hay %d expresiones regulares válidas.\n\n%s' % (author, avbotglobals.preferences['language'], diff, len(avbotglobals.vandalRegexps), wiii.get()), u'BOT - La lista del bien y del mal ha cambiado. Total [%d]' % len(avbotglobals.vandalRegexps))
	else:
		wiii=wikipedia.Page(avbotglobals.preferences['site'], u'User talk:Emijrp/Lista del bien y del mal.css')
		if error:
			wiii.put(u'== {{subst:LOCALDAYNAME}}, {{subst:CURRENTDAY}} de {{subst:CURRENTMONTHNAME}} de {{subst:CURRENTYEAR}}, {{subst:CURRENTTIME}} (UTC) ==\n{{u|%s}} ha editado la página pero hay las mismas %d expresiones regulares válidas ([http://%s.wikipedia.org/w/index.php?title=User:Emijrp/Lista_del_bien_y_del_mal.css&diff=%s&oldid=prev ver diff]).\n\n%s%s' % (author, len(avbotglobals.vandalRegexps), avbotglobals.preferences['language'], diff, error, wiii.get()), u'BOT - La lista del bien y del mal no ha cambiado. Total [%d]' % len(avbotglobals.vandalRegexps))
		else:
			wiii.put(u'== {{subst:LOCALDAYNAME}}, {{subst:CURRENTDAY}} de {{subst:CURRENTMONTHNAME}} de {{subst:CURRENTYEAR}}, {{subst:CURRENTTIME}} (UTC) ==\n{{u|%s}} ha editado la página pero hay las mismas %d expresiones regulares válidas ([http://%s.wikipedia.org/w/index.php?title=User:Emijrp/Lista_del_bien_y_del_mal.css&diff=%s&oldid=prev ver diff]).\n\n%s' % (author, len(avbotglobals.vandalRegexps), avbotglobals.preferences['language'], diff, wiii.get()), u'BOT - La lista del bien y del mal ha cambiado. Total [%d]' % len(avbotglobals.vandalRegexps))
	return

def loadShockingImages():
	"""  """
	"""  """
	imageneschocantes={'exceptions':[], 'images':{}}
	
	#todas las categorias deben ser de Commons
	cats=[u'Anal sex', u'Anus', u'Doggy style positions', u'Fisting', u'Intramammal sex', u'Man-on-top positions', u'Missionary positions', u'Multiple penetration', u'Mutual masturbation', u'Oral sex', u'Penis', u'Rear-entry positions', u'Side-by-side positions', u'Sitting sex positions', u'Spooning positions', u'Standing sex positions', u'Tribadic positions', u'Woman-on-top positions']
	
	#excepciones
	excepcat=catlib.Category(avbotglobals.preferences['site'], u'Category:Sexualidad')
	imageneschocantes['exceptions']=excepcat.articlesList(recurse=1)
	
	error=u''
	for cat in cats:
		try:
			raw=wikipedia.query.GetData({'action':'query', 'generator':'categorymembers', 'gcmtitle':'Category:%s' % cat, 'gcmprop':'title', 'gcmnamespace':'6', 'gcmlimit':'500'},site=wikipedia.Site('commons','commons'),useAPI=True)
			
			for k, v in raw['query']['pages'].items():
				filename=v['title'].split('Image:')[1]
				filename_=re.sub(ur'([\(\)\.\,\-\:\;\$\'\"\_\?\!\&\¿\¡\+])', ur'\\\1', filename)
				filename__=re.sub(u' ', u'_', filename_)
				regexp=u'(?i)(%s|%s)' % (filename_, filename__)
				try:
					imageneschocantes['images'][filename]=re.compile(regexp)
					#wikipedia.output(filename)
				except:
					error+=u'Error al compilar: %s' % regexp
		
		except:
			pass
	
	return imageneschocantes, error

def loadUserEdits(author):
	"""  """
	"""  """
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
	p=wikipedia.Page(avbotglobals.preferences['site'], u'User:Emijrp/Exclusiones.css')
	raw=''
	if p.exists() and not p.isRedirectPage() and not p.isDisambig():
		raw=p.get()
	
	for l in raw.splitlines():
		if len(l)>=1:
			if l[0]=='#' or l[0]=='<':
				continue
			if not avbotglobals.excludedPages.has_key(l):
				avbotglobals.excludedPages[l]=True
	
	wikipedia.output(u"Loaded %d page excludedPages..." % (len(avbotglobals.excludedPages.items())))
