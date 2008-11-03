# -*- coding: utf-8 -*-

import wikipedia
import re
import datetime

def vtee(text, resumen):
	newtext=text
	newtext=re.sub(ur'(?i)=(\s*)(v[íi]nculos?\s*e[xs]ternos?|l[íi]gas?\s*e[xs]tern[oa]s?|l[íi]nks?\s*e[xs]tern[oa]s?|enla[cs]es\s*e[xs]ternos|external\s*links?)(\s*)=', ur'=\1Enlaces externos\3=', newtext)
	newtext=re.sub(ur'(?i)=(\s*)([vb]er\s*tam[bv]i[ée]n|[vb][ée]a[cs]e\s*t[aá]mbi[ée]n|vea\s*tambi[eé]n|\{\{ver\}\})(\s*)=', ur'=\1Véase también\3=', newtext)
	if text==newtext:
		return newtext, resumen
	else:
		return newtext, u"%s VT && EE," % resumen

def cosmetic(text, resumen):
	newtext=text
	#nada por ahora, cosmetic_changes.py puede ser util
	
	if text==newtext:
		return newtext, resumen
	else:
		return newtext, u"%s cosméticos," % resumen

def magicInterwiki(page, resumen, idioma):
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
		return newtext, resumen

def mes(num):
	if num==1:
		return 'Enero'
	elif num==2:
		return 'Febrero'
	elif num==5:
		return 'Mayo'
	elif num==6:
		return 'Junio'
	elif num==7:
		return 'Julio'
	elif num==8:
		return 'Agosto'
	

def archiveVEC(site):
	#calculo de fecha
	mesactual=mes(datetime.date.today().month)
	anyoactual=datetime.date.today().year
	
	vec=wikipedia.Page(site, u"Wikipedia:Vandalismo en curso")
	vectext=vec.get()
	
	trozos=vectext.split('===')
	cabecera=trozos[0]
	avisos=trozos[1:]
	
	if len(avisos) % 2 !=0:
		return False
	
	c=0
	archivo=[]
	vecactual=[]
	for i in avisos:
		if c % 2 == 0:
			if re.search(ur'Acción administrativa.*?%d' % anyoactual, avisos[c+1]):
				archivo.append(avisos[c])
				archivo.append(avisos[c+1])
			else:
				vecactual.append(avisos[c])
				vecactual.append(avisos[c+1])
		c+=1
	
	if len(archivo)>=6: #archivamos cuando haya 3 resueltos
		vecnewtext=u'%s\n' % cabecera
		for i in vecactual:
			vecnewtext+=u'===%s' % i
		archivotext=u''
		for i in archivo:
			archivotext+=u'===%s' % i
		
		cuantos=len(vecactual)/2
		
		vec.put(vecnewtext, u'BOT - Archivando %d avisos resueltos (bot en pruebas)' % cuantos)
		arc=wikipedia.Page(site, u"Wikipedia:Vandalismo en curso/%s %s" % (mesactual, anyoactual))
		arc.put(u'%s\n%s' % (arc.get(), archivotext), u'BOT - Archivando %d avisos resueltos (bot en pruebas)' % cuantos)
		return True
	
	return False
	
	