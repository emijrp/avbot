# -*- coding: utf-8 -*-

import wikipedia
import re
import datetime

import avbotmsg

def bloqueo(site, blocker, blocked, castigo):
	#desactivado por http://es.wikipedia.org/w/index.php?title=Usuario%3AAVBOT%2FSugerencias&diff=21583774&oldid=21539840
	#avbotmsg.msgBloqueo(blocked, site, blocker) #Send message to vandal's talk page
	pvec=wikipedia.Page(site, u'Wikipedia:Vandalismo en curso')
	if pvec.exists():
		if pvec.isRedirectPage():
			return 0
		else:
			vectext=pvec.get()
			trozos=trozos2=vectext.split('===')
			c=0
			for trozo in trozos:
				if re.search(ur'%s' % blocked, trozo) and c+1<=len(trozos)-1: #deberia ser re.sub(ur'\.', ur'\.', blocked) para mas seguridad
					wikipedia.output(u'\03{lightblue}Se ha encontrado a %s :)\03{default}' % (blocked))
					arellenar=ur'(?i)\( *\'{,3} *a rellenar por un bibliotecario *\'{,3} *\)'
					if re.search(arellenar, trozos2[c+1]):
						trozos2[c+1]=re.sub(arellenar, ur"{{Vb|1=%s ([http://es.wikipedia.org/w/index.php?title=Especial:Log&type=block&user=%s&page=Usuario:%s&year=&month=-1 ver log])|2=c|3=%s}} --~~~~" % (castigo, re.sub(u' ', u'_', blocker), re.sub(u' ', u'_', blocked), blocker), trozos2[c+1])
						break
				c+=1
			
			#reunimos los trozos de nuevo con ===
			newvectext=u''
			c=0
			for trozo in trozos2:
				if c!=0:
					newvectext+=u'===%s' % trozo
				else:
					newvectext+=trozo
				c+=1
			
			#enviamos
			if newvectext!=vectext:
				#wikipedia.showDiff(vectext, newvectext)
				pvec.put(newvectext, u'BOT - [[Special:Contributions/%s|%s]] acaba de ser bloqueado por [[Usuario:%s|%s]] %s' % (blocked, blocked, blocker, blocker, castigo))
				wikipedia.output(u'\03{lightblue}Alerta: Tachando [[Usuario:%s]] de WP:VEC. Gestionado por [[Usuario:%s]]\03{default}' % (blocked, blocker))
			else:
				wikipedia.output(u'\03{lightblue}No se ha modificado WP:VEC.\03{default}')
			
			#si ha sido bloqueado para siempre, redirigimos su pagina de usuario
			"""if re.search(ur'(para siempre|indefinite|infinite|infinito)', castigo):
				userpage=wikipedia.Page(site, u'User:%s' % blocked)
				userpage.put(u'#REDIRECT [[Wikipedia:Usuario expulsado]]', u'BOT - El usuario ha sido expulsado %s' % castigo)
				wikipedia.output(u'\03{lightblue}Redirigiendo página de usuario a [[Wikipedia:Usuario expulsado]]\03{default}')"""
			

def semiproteger(site, titulo, protecter):
	p=wikipedia.Page(site, titulo)
	if p.exists():
		if p.isRedirectPage() or p.namespace()!=0:
			return 0
		else:
			semitext=p.get()
			if not re.search(ur'(?i)\{\{ *(Semiprotegida|Semiprotegido|Semiprotegida2|Pp\-semi\-template)', semitext):
				p.put(u'{{Semiprotegida|pequeño=sí}}\n%s' % semitext, u'BOT - Añadiendo {{Semiprotegida|pequeño=sí}} a la página recién semiprotegida por [[Special:Contributions/%s|%s]]' % (protecter, protecter))
				wikipedia.output(u'\03{lightblue}Aviso: Poniendo {{Semiprotegida}} en [[%s]]\03{default}' % titulo)
			else:
				wikipedia.output(u'\03{lightblue}Aviso:[[%s]] ya tiene {{Semiprotegida}}\03{default}' % titulo)

def traslado(site, usuario, origen, destino):
	#es un traslado vandálico?
	"""if usuario==u'Emijrp':
		p=wikipedia.Page(site, destino)
		p.move(origen, reason=u'BOT - Probando módulo antitraslados')"""

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

def namespaceTranslator(site, namespace):
	data=site.getUrl("/w/index.php?title=Special:RecentChanges&limit=0")
	data=data.split('<select id="namespace" name="namespace" class="namespaceselector">')[1].split('</select>')[0]
	m=re.compile(ur'<option value="([1-9]\d*)">(.*?)</option>').finditer(data)
	wikipedianm=u''
	for i in m:
		number=i.group(1)
		name=i.group(2)
		if number=='%s' % namespace:
			wikipedianm+=name
	return wikipedianm
	

def resumeTranslator(site,type,vandal,stableid,stableauthor):
	resume=u''
	
	if site.lang=='en':
		if type=='blanking':
			resume=u'BOT - Blanking by [[Special:Contributions/%s|%s]], reverting to %s edit by [[User:%s|%s]].' % (vandal, vandal, str(stableid), stableauthor, stableauthor)
	else:
		if type=='blanking':
			resume=u'BOT - Blanqueo de [[Special:Contributions/%s|%s]], revirtiendo hasta la edición %s de [[User:%s|%s]]. ¿[[User:AVBOT/Errores|Hubo un error]]?' % (vandal, vandal, str(stableid), stableauthor, stableauthor)
	
	return resume
