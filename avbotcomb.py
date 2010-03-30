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

## @package avbotcomb
# Module for miscellany functions\n
# Módulo para funciones varias

import wikipedia
import re
import datetime
import time
import random
import sys
import urllib
import os

# AVBOT modules
import avbotglobals
import avbotmsg
import avbotload
import avbotsave

def blockedUser(blocker, blocked, castigo):
	""" Carga Vandalismo en curso y gestionar bloqueo  """
	""" Load Vandalismo en curso and manage block """
	
	blocker_=re.sub(u' ', u'_', blocker)
	blocked_=re.sub(u' ', u'_', blocked)
	#desactivado por http://es.wikipedia.org/w/index.php?title=Usuario%3AAVBOT%2FSugerencias&diff=21583774&oldid=21539840
	#avbotmsg.msgBlock(blocked, blocker) #Send message to vandal's talk page
	pvec=wikipedia.Page(avbotglobals.preferences['site'], u'Wikipedia:Vandalismo en curso')
	if pvec.exists():
		if pvec.isRedirectPage():
			return 0
		else:
			vectext=pvec.get()
			trozos=trozos2=vectext.split('===')
			c=0
			for trozo in trozos:
				if re.search(ur'%s' % blocked, re.sub('_', ' ', trozo)) and c+1<=len(trozos)-1: #deberia ser re.sub(ur'\.', ur'\.', blocked) para mas seguridad
					wikipedia.output(u'\03{lightblue}%s was found :)\03{default}' % (blocked))
					arellenar=ur'(?i)\(? *\'{,3} *a rellenar por un bibliotecario *\'{,3} *\)?'
					if re.search(arellenar, trozos2[c+1]):
						trozos2[c+1]=re.sub(arellenar, ur"{{Vb|1=%s ([http://%s.wikipedia.org/w/index.php?title=Special:Log&type=block&user=%s&page=User:%s&year=&month=-1 ver log])|2=c|3=%s}} --~~~~" % (castigo, avbotglobals.preferences['site'].lang, blocker_, blocked_, blocker), trozos2[c+1])
						break
				c+=1
			
			#reunimos los trozos de nuevo con ===
			newvectext="===".join(trozos2)
			
			#Updating vandalism board
			if newvectext!=vectext:
				#wikipedia.showDiff(vectext, newvectext)
				if not avbotglobals.preferences['nosave']:
					pvec.put(newvectext, u'BOT - [[Special:Contributions/%s|%s]] acaba de ser bloqueado por [[User:%s|%s]] %s' % (blocked, blocked, blocker, blocker, castigo))
				wikipedia.output(u'\03{lightblue}Alerta: Tachando [[User:%s]] de WP:VEC. Gestionado por [[User:%s]]\03{default}' % (blocked, blocker))
			else:
				wikipedia.output(u'\03{lightblue}No se ha modificado WP:VEC.\03{default}')
			
			#si ha sido bloqueado para siempre, redirigimos a su pagina de usuario
			"""if re.search(ur'(para siempre|indefinite|infinite|infinito)', castigo):
				userpage=wikipedia.Page(avbotglobals.preferences['site'], u'User:%s' % blocked)
				if not avbotglobals.preferences['nosave']:
					userpage.put(u'#REDIRECT [[Wikipedia:Usuario expulsado]]', u'BOT - El usuario ha sido expulsado %s' % castigo)
				wikipedia.output(u'\03{lightblue}Redirigiendo página de usuario a [[Wikipedia:Usuario expulsado]]\03{default}')"""
			

def semiprotect(titulo, protecter):
	""" Pone la plantilla {{semiprotegido}} si no la tiene ya """
	""" Put {{semiprotegido}} if it doesn't exist """
	p=wikipedia.Page(avbotglobals.preferences['site'], titulo)
	if p.exists():
		if p.isRedirectPage() or p.namespace()!=0:
			return 0
		else:
			semitext=p.get()
			if not re.search(ur'(?i)\{\{ *(Semiprotegida|Semiprotegido|Semiprotegida2|Pp\-semi\-template)', semitext):
				if not avbotglobals.preferences['nosave']:
					p.put(u'{{Semiprotegida|pequeño=sí}}\n%s' % semitext, u'BOT - Añadiendo {{Semiprotegida|pequeño=sí}} a la página recién semiprotegida por [[Special:Contributions/%s|%s]]' % (protecter, protecter))
				wikipedia.output(u'\03{lightblue}Aviso: Poniendo {{Semiprotegida}} en [[%s]]\03{default}' % titulo)
			else:
				wikipedia.output(u'\03{lightblue}Aviso:[[%s]] ya tiene {{Semiprotegida}}\03{default}' % titulo)

def vtee(text, resumen):
	""" Algunos cambios menores según el manual de estilo """
	""" Minor changes from style manual """
	newtext=text
	newtext=re.sub(ur'(?i)=(\s*)(v[íi]nculos?\s*e[xs]ternos?|l[íi]gas?\s*e[xs]tern[oa]s?|l[íi]nks?\s*e[xs]tern[oa]s?|enla[cs]es\s*e[xs]ternos|external\s*links?)(\s*)=', ur'=\1Enlaces externos\3=', newtext)
	newtext=re.sub(ur'(?i)=(\s*)([vb]er\s*tam[bv]i[ée]n|[vb][ée]a[cs]e\s*t[aá]mbi[ée]n|vea\s*tambi[eé]n|\{\{ver\}\})(\s*)=', ur'=\1Véase también\3=', newtext)
	if text==newtext:
		return newtext, resumen
	else:
		return newtext, u"%s VT && EE," % resumen

def magicInterwiki(page, resumen, idioma):
	""" Buscar interwikis que pueden venirle bien al artículo """
	""" Check for userful interwikis """
	wtext=page.get()
	wtitle=page.title()
	
	pex=wikipedia.Page(wikipedia.Site(idioma, "wikipedia"), wtitle)
	
	if pex.exists() and not pex.isRedirectPage() and not pex.isDisambig():
		#descartamos articulos con interwikis a la española
		iws=pex.interwiki()
		for iw in iws:
			if iw.site().lang=='es':
				return wtext, resumen
		
		linked=page.linkedPages()
		linkedex=pex.linkedPages()
		
		aux=[]
		for link in linkedex:
			aux.append(link.title())
		linkedex=aux
		
		cont=0
		total=0
		for link in linked:
			if link.exists() and not link.isRedirectPage() and not link.isDisambig():
				linkiws=link.interwiki()
				for linkiw in linkiws:
					if linkiw.site().lang==idioma:
						total+=1
						if linkedex.count(linkiw.title())!=0:
							cont+=1
		#wikipedia.output(u"Total=%s | Contador=%s" % (str(total), str(cont)))
		
		if cont>=total/2 and cont>0: #50% de margen
			iws=pex.interwiki()
			iws.append(pex)
			iws.sort()
			nuevo=u"%s\n" % wtext
			for iw in iws:
				nuevo+=u"\n[[%s:%s]]" % (iw.site().lang, iw.title())
			if len(nuevo)>len(wtext)+5:
				#wikipedia.showDiff(wtext, nuevo)
				return nuevo, u"%s interwikis mágicos," % resumen

	if idioma=='en':
		magicInterwiki(page, resumen, 'de')
	elif idioma=='de':
		magicInterwiki(page, resumen, 'fr')
	elif idioma=='fr':
		magicInterwiki(page, resumen, 'pt')
	else:
		return nuevo, resumen

def namespaceTranslator(namespace):
	""" Carga espacios de nombres por idioma """
	""" Load namespace per language """
	data=avbotglobals.preferences['site'].getUrl("/w/index.php?title=Special:RecentChanges")
	data=data.split('<select id="namespace" name="namespace" class="namespaceselector">')[1].split('</select>')[0]
	m=re.compile(ur'<option value="([1-9]\d*)">(.*?)</option>').finditer(data)
	wikipedianm=u''
	for i in m:
		number=int(i.group(1))
		name=i.group(2)
		if number==namespace:
			wikipedianm+=name
	return wikipedianm

def resumeTranslator(editData):
	""" Traductor de resúmenes de edición primitivo """
	""" Beta summaries translator """
	resume=u''
	type=editData['type']
	
	if avbotglobals.preferences['language']=='es':
		resume=u'BOT - Posible %s de [[Special:Contributions/%s|%s]], revirtiendo hasta la edición %s de [[User:%s|%s]]. ¿[[User:AVBOT/Errores|Hubo un error]]?' % (avbotglobals.preferences['msg'][type]['meaning'].lower(), editData['author'], editData['author'], editData['stableid'], editData['stableAuthor'], editData['stableAuthor'])
	else:
		resume=u'BOT - Reverting possible %s by [[Special:Contributions/%s|%s]] to %s version by [[User:%s|%s]]. False positive? [[User:AVBOT/FalsePositives|Report it]]' % (avbotglobals.preferences['msg'][type]['meaning'].lower(), editData['author'], editData['author'], editData['stableid'], editData['stableAuthor'], editData['stableAuthor'])
	
	return resume

def getParameters():
	""" Gestionar parámetros capturados de la consola """
	""" Manage console parameters """
	args=sys.argv
	
	obligatory=2
	for arg in args[1:]:
		if arg.startswith('-language'):
			if len(arg) == 9:
				avbotglobals.preferences['language'] = wikipedia.input(u'Please enter the language (es, en, de, fr, ...):')
			else:
				avbotglobals.preferences['language'] = arg[10:]
		elif arg.startswith('-lang'):
			if len(arg) == 5:
				avbotglobals.preferences['language'] = wikipedia.input(u'Please enter the language (es, en, de, fr, ...):')
			else:
				avbotglobals.preferences['language'] = arg[6:]
		elif arg.startswith('-family'):
			if len(arg) == 7:
				avbotglobals.preferences['family'] = wikipedia.input(u'Please enter the family project (wikipedia, wiktionary, ...):')
			else:
				avbotglobals.preferences['family'] = arg[8:]
		elif arg.startswith('-newbie'):
			if len(arg) == 7:
				avbotglobals.preferences['newbie'] = int(wikipedia.input(u'Please enter the number of edits for newbie users:'))
			else:
				avbotglobals.preferences['newbie'] = int(arg[8:])
		elif arg.startswith('-botnick'):
			if len(arg) == 8:
				avbotglobals.preferences['botNick'] = wikipedia.input(u'Please enter bot username:')
			else:
				avbotglobals.preferences['botNick'] = arg[9:]
			obligatory-=1
		elif arg.startswith('-statsdelay'):
			if len(arg) == 11:
				avbotglobals.preferences['statsDelay'] = int(wikipedia.input(u'Please enter stats delay (in seconds):'))
			else:
				avbotglobals.preferences['statsDelay'] = int(arg[12:])
		elif arg.startswith('-network'):
			if len(arg) == 8:
				avbotglobals.preferences['network'] = wikipedia.input(u'Please enter IRC network:')
			else:
				avbotglobals.preferences['network'] = arg[9:]
		elif arg.startswith('-channel'):
			if len(arg) == 8:
				avbotglobals.preferences['channel'] = wikipedia.input(u'Please enter IRC channel (with #):')
			else:
				avbotglobals.preferences['channel'] = arg[9:]
		elif arg.startswith('-ownernick'):
			if len(arg) == 10:
				avbotglobals.preferences['ownerNick'] = wikipedia.input(u'Please enter owner username:')
			else:
				avbotglobals.preferences['ownerNick'] = arg[11:]
			obligatory-=1
		elif arg.startswith('-nosave'):
			if len(arg) == 7:
				avbotglobals.preferences['nosave'] = True
		elif arg.startswith('-notsave'):
			if len(arg) == 8:
				avbotglobals.preferences['nosave'] = True
		elif arg.startswith('-force'):
			if len(arg) == 6:
				avbotglobals.preferences['force'] = True
		elif arg.startswith('-trial'):
			if len(arg) == 6:
				avbotglobals.preferences['trial'] = True
	
	if obligatory:
		wikipedia.output(u"Not all obligatory parameters were found. Please, check (*) parameters.")
		sys.exit()

def getTime():
	""" Coge la hora del sistema """
	""" Get system time """
	return time.strftime('%H:%M:%S')

def encodeLine(line):
	""" Codifica una cadena en UTF-8 a poder ser """
	""" Encode string into UTF-8 """
	
	try:
		line2=unicode(line,'utf-8')
	except UnicodeError:
		try:
			line2=unicode(line,'iso8859-1')
		except UnicodeError:
			print u'Unknown codification'
			return ''
	return line2

def getUserClass(editData):
	""" Averigua el tipo de usuario del que se trata """
	""" Check user class """
	
	userClass='anon'
	if avbotglobals.userData['sysop'].count(editData['author'])!=0:
		userClass='sysop'
	elif avbotglobals.userData['bot'].count(editData['author'])!=0:
		userClass='bot'
	elif not re.search(avbotglobals.parserRegexps['ip'], editData['author']):
		userClass='reg'
	return userClass

def cleanLine(line):
	""" Limpia una línea de IRC de basura """
	""" Clean IRC line """
	
	line=re.sub(ur'\x03\d{0,2}', ur'', line) #No colors
	line=re.sub(ur'\x02\d{0,2}', ur'', line) #No bold
	return line

def updateUserDataIfNeeded(editData):
	if editData['userClass']!='anon':
		if avbotglobals.userData['edits'].has_key(editData['author']):
			if not random.randint(0,25) or avbotglobals.userData['edits'][editData['author']]<=avbotglobals.preferences['newbie']: #X faces dice, true if zero or newbie
				avbotglobals.userData['edits'][editData['author']]=avbotload.loadUserEdits(editData['author'])
		else:
			#Requesting edits number to server
			avbotglobals.userData['edits'][editData['author']]=avbotload.loadUserEdits(editData['author'])
		
		#Saving user edits file...
		if not random.randint(0,200):
			avbotsave.saveEdits(avbotglobals.userData['edits'])

def checkBlockInEnglishWikipedia(editData):
	comment=""
	isProxy=False
	if re.search(ur'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', editData['author']): #Is it an IP?
		enwiki=wikipedia.Site('en', 'wikipedia')
		
		data=enwiki.getUrl("/w/index.php?title=Special:BlockList&ip=%s" % editData['author'])
		data=data.split('<!-- start content -->')
		data=data[1].split('<!-- end content -->')[0]
		
		data=data.split('<li>')
		if len(data)>1:
			m=re.compile(ur"</span> *\((?P<expires>[^<]*?)\) *<span class=\"comment\">\((?P<comment>[^<]*?)\)</span>").finditer(data[1])
			for i in m:
				comment=u"''Bloqueado en Wikipedia en inglés ([http://en.wikipedia.org/w/index.php?title=Special:BlockList&ip=%s bloqueo vigente], [http://en.wikipedia.org/w/index.php?title=Special:Log&type=block&page=User:%s historial de bloqueos]): %s''" % (editData['author'], editData['author'], i.group("expires"))
				if re.search(ur'(?i)proxy', i.group('comment')):
					isProxy=True
				break #con el primero basta
	
	return comment, isProxy

def checkForUpdates():
	svn='http://avbot.googlecode.com/svn/trunk/'
	f=urllib.urlopen(svn)
	html=f.read()
	m=re.compile(ur">(?P<filename>[^<]+?\.py)</a>").finditer(html)
	for i in m:
		filename=i.group("filename")
		wikipedia.output(u"Checking file %s..." % filename)
		g=open(filename, 'r')
		h=urllib.urlopen(svn+filename)
		if g.read()!=h.read():
			wikipedia.output(u"%s has changed!!!" % filename)
			return True
		else:
			wikipedia.output(u"[OK]")
	f.close()
	return False

def existenceFile():
	while True:
		if not os.path.isfile(avbotglobals.existFile):
			existFile=open(avbotglobals.existFile, 'w')
			existFile.write(str("hi"))
			existFile.close()
		time.sleep(60) # debe ser menor que el time del cron / 2

"""
def put(pageobject, newtext, summary):
	if not avbotglobals.preferences['nosave']:
		pageobject.put(newtext, summary)
"""
