# -*- coding: utf-8 -*-

import re
import urllib
import wikipedia
import catlib

import avbotcomb

def changedRegexpsList(list1, list2):
	#funcion que devuelve si las dos listas de expresiones regualres son distintas
	#se sabe que las listas son en realidad diccionarios, y su clave es la expresion regular. Mas detalles en loadVandalism()
	if len(list1)!=len(list2):
		return True
	else:
		changed=False
		for k, v in list1.items():
			if not list2.has_key(k):
				return True
	return False

def loadEdits(newbie):
	ediciones={}
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
	wikipedia.output(u"Loaded info for %d users..." % len(ediciones.items()))
	return ediciones

def loadUsers(site, type):
	users=[]
	data=site.getUrl("/w/index.php?title=Special:Listusers&limit=5000&group=%s" % type)
	data=data.split('<!-- start content -->')
	data=data[1].split('<!-- end content -->')[0]
	namespace=avbotcomb.namespaceTranslator(site, 2)
	m=re.compile(ur" title=\"%s:(.*?)\">" % namespace).finditer(data)
	for i in m:
		users.append(i.group(1))
	wikipedia.output(u"Loaded info for %d %ss..." % (len(users), type))
	return users

def loadAdmins(site):
	return loadUsers(site, 'sysop')

def loadBots(site):
	return loadUsers(site, 'bot')

def loadVandalism(contexto, site, nickdelbot):
	vandalismos={}
	
	wiii=wikipedia.Page(site, u'Usuario:Emijrp/Lista del bien y del mal.css')
	raw=''
	if wiii.exists() and not wiii.isRedirectPage() and not wiii.isDisambig():
		raw=wiii.get()
	
	c=0
	error=u''
	for l in raw.splitlines():
		c+=1
		if len(l)>=3: #evitamos regex demasiado pequenas
			if l[0]=='#' or l[0]=='<':
				continue
			trozos=l.split(';;')
			type=trozos[0]
			reg=trozos[1]
			score=int(trozos[2])
			regex=ur'%s%s%s' % (contexto, reg, contexto)
			try:
				vandalismos[reg]={'type':type, 'compiled':re.compile(ur'(?im)%s' % regex), 'score':score}
			except:
				error+=u'=== Error en regexp ===\n'
				error+=u'* Línea: %d' % c
				error+=u'\n* Regexp errónea: %s' % reg
				error+=u'\n* Regexp errónea (con contexto): %s' % regex
				error+=u'\n* Puntuación: %d\n\n' % score
	
	return vandalismos, error

def reloadVandalism(contexto, site, botNick, vandalismos, author, diff):
	[vandalismos_nuevo, error]=loadVandalism(contexto, site, botNick)
	if changedRegexpsList(vandalismos, vandalismos_nuevo):
		wiii=wikipedia.Page(site, u'Usuario Discusión:Emijrp/Lista del bien y del mal.css')
		if error:
			wiii.put(u'== {{subst:LOCALDAYNAME}}, {{subst:CURRENTDAY}} de {{subst:CURRENTMONTHNAME}} de {{subst:CURRENTYEAR}}, {{subst:CURRENTTIME}} (UTC) ==\n{{u|%s}} ha modificado la lista ([http://es.wikipedia.org/w/index.php?title=Usuario:Emijrp/Lista_del_bien_y_del_mal.css&diff=%s&oldid=prev ver diff]). Ahora hay %d expresiones regulares válidas.\n\n%s%s' % (author, diff, len(vandalismos_nuevo), error, wiii.get()), u'BOT - La lista del bien y del mal ha cambiado. Total [%d]' % len(vandalismos_nuevo))
		else:
			wiii.put(u'== {{subst:LOCALDAYNAME}}, {{subst:CURRENTDAY}} de {{subst:CURRENTMONTHNAME}} de {{subst:CURRENTYEAR}}, {{subst:CURRENTTIME}} (UTC) ==\n{{u|%s}} ha modificado la lista ([http://es.wikipedia.org/w/index.php?title=Usuario:Emijrp/Lista_del_bien_y_del_mal.css&diff=%s&oldid=prev ver diff]). Ahora hay %d expresiones regulares válidas.\n\n%s' % (author, diff, len(vandalismos_nuevo), wiii.get()), u'BOT - La lista del bien y del mal ha cambiado. Total [%d]' % len(vandalismos_nuevo))
		vandalismos=vandalismos_nuevo
	else:
		wiii=wikipedia.Page(site, u'Usuario Discusión:Emijrp/Lista del bien y del mal.css')
		if error:
			wiii.put(u'== {{subst:LOCALDAYNAME}}, {{subst:CURRENTDAY}} de {{subst:CURRENTMONTHNAME}} de {{subst:CURRENTYEAR}}, {{subst:CURRENTTIME}} (UTC) ==\n{{u|%s}} ha editado la página pero hay las mismas %d expresiones regulares válidas ([http://es.wikipedia.org/w/index.php?title=Usuario:Emijrp/Lista_del_bien_y_del_mal.css&diff=%s&oldid=prev ver diff]).\n\n%s%s' % (author, len(vandalismos), diff, error, wiii.get()), u'BOT - La lista del bien y del mal no ha cambiado. Total [%d]' % len(vandalismos))
		else:
			wiii.put(u'== {{subst:LOCALDAYNAME}}, {{subst:CURRENTDAY}} de {{subst:CURRENTMONTHNAME}} de {{subst:CURRENTYEAR}}, {{subst:CURRENTTIME}} (UTC) ==\n{{u|%s}} ha editado la página pero hay las mismas %d expresiones regulares válidas ([http://es.wikipedia.org/w/index.php?title=Usuario:Emijrp/Lista_del_bien_y_del_mal.css&diff=%s&oldid=prev ver diff]).\n\n%s' % (author, len(vandalismos), diff, wiii.get()), u'BOT - La lista del bien y del mal ha cambiado. Total [%d]' % len(vandalismos))
	return vandalismos

def loadShockingImages(site):
	imageneschocantes={'exceptions':[], 'images':{}}
	
	#todas las categorias deben ser de Commons
	cats=[u'Anal sex', u'Anus', u'Doggy style positions', u'Fisting', u'Intramammal sex', u'Man-on-top positions', u'Missionary positions', u'Multiple penetration', u'Mutual masturbation', u'Oral sex', u'Penis', u'Rear-entry positions', u'Side-by-side positions', u'Sitting sex positions', u'Spooning positions', u'Standing sex positions', u'Tribadic positions', u'Woman-on-top positions']
	
	#excepciones
	excepcat=catlib.Category(site, u'Category:Sexualidad')
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
	

def loadUserEdits(author, site, newbie):
	try:
		rawdata=site.getUrl("/w/api.php?action=query&list=users&ususers=%s&usprop=editcount&format=xml" % urllib.quote(re.sub(' ', '_', author)))
		if re.search(u"editcount", rawdata):
			m=re.compile(ur' editcount="(\d+)"').finditer(rawdata)
			for i in m:
				editsnum=int(i.group(1))
				if editsnum<1:
					return newbie+1
				else:
					return editsnum
		else:
			return newbie+1
	except:
		return newbie+1
		