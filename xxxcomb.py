# -*- coding: utf-8 -*-

import wikipedia
import re


def bloqueo(site, blocker, blocked, castigo):
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
					if re.search(ur'(?i)\(a rellenar por un bibliotecario\)', trozos2[c+1]):
						trozos2[c+1]=re.sub(ur'(?i)\( *\'{,3} *a rellenar por un bibliotecario *\'{,3} *\)', ur"{{Vb|1=%s ([http://es.wikipedia.org/w/index.php?title=Especial:Log&type=block&user=%s&page=Usuario:%s&year=&month=-1 ver log])|2=c|3=%s}} --~~~~" % (castigo, re.sub(u' ', u'_', blocker), re.sub(u' ', u'_', blocked), blocker), trozos2[c+1])
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
				wikipedia.showDiff(vectext, newvectext)
				pvec.put(newvectext, u'BOT - [[Special:Contributions/%s|%s]] acaba de ser bloqueado por [[Usuario:%s|%s]] %s' % (blocked, blocked, blocker, blocker, castigo))
				wikipedia.output(u'\03{lightblue}Alerta: Tachando [[Usuario:%s]] de WP:VEC. Gestionado por [[Usuario:%s]]\03{default}' % (blocked, blocker))
			else:
				wikipedia.output(u'\03{lightblue}No se ha modificado WP:VEC :(\03{default}')
			
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
				wikipedia.output(u'\03{lightblue}Alerta:Poniendo {{Semiprotegida}} en [[%s]]\03{default}' % titulo)
			else:
				wikipedia.output(u'\03{lightblue}Alerta:[[%s]] ya tiene {{Semiprotegida}}\03{default}' % titulo)

def traslado(site, usuario, origen, destino):
	#es un traslado vandálico?
	"""if usuario==u'Emijrp':
		p=wikipedia.Page(site, destino)
		p.move(origen, reason=u'BOT - Probando módulo antitraslados')"""

