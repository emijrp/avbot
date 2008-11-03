# -*- coding: utf-8 -*-

import re
import urllib
import wikipedia
import catlib

def changedRegexpsList(list1, list2):
	#funcion que devuelve si las dos listas de expresiones regualres son distintas
	#se sabe que las listas son en realidad diccionarios, y su clave es la expresion regular. Mas detalles en loadVandalism() y loadTests()
	if len(list1)!=len(list2):
		return True
	else:
		changed=False
		for k, v in list1.items():
			if not list2.has_key(k):
				return True
	return False

def loadEdits(novato):
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
				numero=novato+1
			ediciones[usuario]=numero
		l=f.readline()
	wikipedia.output(u"Cargada información de %d usuarios..." % len(ediciones.items()))
	return ediciones

def loadAdmins(site):
	admins=[]
	data=site.getUrl("/w/index.php?title=Especial:Listusers&limit=5000&group=sysop")
	data=data.split('<!-- start content -->')
	data=data[1].split('<!-- end content -->')[0]
	m=re.compile(ur" title=\"Usuario:(.*?)\">").finditer(data)
	for i in m:
		admins.append(i.group(1))
	wikipedia.output(u"Cargados %d usuarios con flag de admin..." % len(admins))
	return admins

def loadBots(site):
	bots=[]
	data=site.getUrl("/w/index.php?title=Especial:Listusers&limit=5000&group=bot")
	data=data.split('<!-- start content -->')
	data=data[1].split('<!-- end content -->')[0]
	m=re.compile(ur" title=\"Usuario:(.*?)\">").finditer(data)
	for i in m:
		bots.append(i.group(1))
	wikipedia.output(u"Cargados %d usuarios con flag de bot..." % len(bots))
	return bots

def loadTests(pruebas_viejo, contexto, site, nickdelbot):
	pruebas={}
	f=open("pruebas.txt", "r")
	l=f.readline()
	while l:
		l=unicode(l, "utf-8")
		l=l[:len(l)-1] #necesario para no cargar los satlos de linea
		if len(l)>3: #evitamos regex demasiado pequenas
			if l[0]=='#':
				l=f.readline()
				continue
			#wikipedia.output(u'%s' % l)
			trozos=l.split(';;')
			reg=trozos[0]
			score=int(trozos[1])
			regex=ur'%s%s%s' % (contexto, reg, contexto)
			pruebas[reg]={'compiled':re.compile(ur'(?im)%s' % regex), 'score':score}
		l=f.readline()
	f.close()
	
	#if changedRegexpsList(pruebas_viejo, pruebas):
	#	#aqui deberiamos salvar cmo en loadVandalism
	
	return pruebas
	
def loadVandalism(contexto, site, nickdelbot):
	vandalismos={}
	
	wiii=wikipedia.Page(site, u'Usuario:Emijrp/Lista del bien y del mal.css')
	raw=wiii.get()
	
	c=0
	error=u''
	for l in raw.splitlines():
		c+=1
		if len(l)>=3: #evitamos regex demasiado pequenas
			if l[0]=='#' or l[0]=='<':
				continue
			trozos=l.split(';;')
			reg=trozos[0]
			score=int(trozos[1])
			regex=ur'%s%s%s' % (contexto, reg, contexto)
			try:
				vandalismos[reg]={'compiled':re.compile(ur'(?im)%s' % regex), 'score':score}
			except:
				error+=u'=== Error en regexp ===\n'
				error+=u'* Línea: %d' % c
				error+=u'\n* Regexp errónea: %s' % reg
				error+=u'\n* Regexp errónea (con contexto): %s' % regex
				error+=u'\n* Puntuación: %d\n\n' % score
	
	return vandalismos, error

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
	

def loadUserEdits(author, site, novato):
	try:
		data=site.getUrl("/w/api.php?action=query&list=users&ususers=%s&usprop=editcount&format=xml" % urllib.quote(re.sub(' ', '_', author)))
		if re.search(u"editcount", data):
			m=re.compile(ur' editcount="(\d+)"').finditer(data)
			for i in m:
				numero=int(i.group(1))
				if numero<1:
					return novato+1
				else:
					return numero
		else:
			return novato+1
	except:
		return novato+1
		