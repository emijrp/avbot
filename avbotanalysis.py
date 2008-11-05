# -*- coding: utf-8 -*-

import re, wikipedia, datetime

import avbotload
import avbotsave
import avbotmsg
import avbotcomb

def sameOldid(oldid, id, oldText, p):
	#return id, p.getOldVersion(id) #mientras averiguo lo de abajo
	
	#este metodo falla? http://es.wikipedia.org/w/index.php?title=Usuario:AVBOT/Errores&diff=prev&oldid=21309979
	if oldid!=id:
		return id, p.getOldVersion(id)
	else:
		return id, oldText

def isSameVandalism(regexlistold, regexlistnew):
	if len(regexlistold)!=len(regexlistnew):
		return False
	else:
		for r in regexlistold:
			if regexlistold.count(r)!=regexlistnew.count(r):
				return False
	return True

def incrementaStats(stats, tipo):
	stats[2][tipo]+=1
	stats[12][tipo]+=1
	stats[24][tipo]+=1
	
	return stats

def vigilar(namespace, pageTitle, author, userClass, authorEditsNum, newbie):
	if (namespace==0 or namespace==10 or namespace==12 or namespace==14 or namespace==100 or namespace==102 or namespace==104 or (namespace==2 and not re.search(ur'\/', pageTitle) and not re.search(ur'(?i)%s' % re.sub('_', ' ', author), re.sub('_', ' ', pageTitle))) or (namespace==4 and not re.search(ur'Wikipedia\:Café', pageTitle))) and (userClass=='anon' or (userClass=='reg' and authorEditsNum<=newbie)):
		return True
	return False

def isRubbish(p, userClass, pageTitle, newText, colors, author, authorEditsNum, newbie, namespace, pruebas, vandalismos, stats):
	destruir=False
	motivo=u'Otros'
	score=0
	
	if userClass=='anon' or (userClass=='reg' and authorEditsNum<=newbie):
		if (namespace==0) and not p.isRedirectPage() and not p.isDisambig():
			if not re.search(ur'(?i)\{\{|redirect', newText):
				for k, v in vandalismos.items():
					m=v['compiled'].finditer(newText)
					for i in m:
						score+=v['score']
				
				if score<0 and ((score>-5 and len(newText)<score*-150) or score<-4): #igualar a  densidad de isVandalism()?
					destruir=True
					motivo=u'Vandalismo'
				else:
					if len(newText)<200:
						for k, v in pruebas.items():
							if re.search(v['compiled'], newText):
								destruir=True
								motivo=u'Pruebas'
				if len(newText)<=75 and not destruir:
					if not re.search(ur'\[', newText):
						destruir=True
						motivo=u'Demasiado corto'
		if destruir:
			stats=incrementaStats(stats, 'D')
			p.put(u'{{RobotDestruir|%s|%s}}\n%s' % (author, motivo, newText), u'Marcando para destruir. Motivo: %s. Página creada por [[Usuario:%s|%s]] ([[Usuario Discusión:%s|disc]] · [[Special:Contributions/%s|cont]])' % (motivo, author, author, author, author))
			return True, motivo, stats
	return False, motivo, stats

def improveNewArticle(namespace, p):
	newText=p.get()
	if (namespace==0) and not p.isRedirectPage() and not p.isDisambig():
		if not re.search(ur'(?i)\{\{ *(destruir|plagio|copyvio)|redirect', newText): #descarta demasiado? destruir|plagio|copyvio
			if len(newText)>=500:
				resumen=u''
				newnewText=u''
				if not p.interwiki():
					try:
						[newnewText, resumen]=avbotcomb.magicInterwiki(p, resumen, 'en')
					except:
						pass
				[newnewText, resumen]=avbotcomb.vtee(newnewText, resumen)
				#[newnewText, resumen]=avbotcomb.cosmetic(newnewText, resumen)
				if len(newnewText)>len(newText):
					p.put(newnewText, u'BOT - Aplicando %s... al artículo recién creado' % resumen)
					return True, resumen
	return False, u''

def isBlanking(namespace, pageTitle, author, userClass, authorEditsNum, newbie, lenOld, lenNew, patterns, newText, controlvand, diff, site, pageHistory, nickdelbot, oldText, p, oldid, stats, currentYear):
	score=0
	regexlist=[]
	if vigilar(namespace, pageTitle, author, userClass, authorEditsNum, newbie):
		if lenOld>=1000 and lenNew<lenOld/7 and not re.search(patterns['blanqueos'], newText): # 1/7 es un buen numero?
			score=-(lenNew+1) #la puntuacion de los blanqueos es la nueva longitud + 1, negada, para evitar el -0
			#añadimos al control de vandalismos
			if controlvand.has_key(author):
				controlvand[author][diff]=[pageTitle, score, regexlist] #metemos regexlist que es una lista vacia, para mantener consistencia con is_Vandalism()
			else:
				controlvand[author]={'avisos': 0, diff: [pageTitle, score, regexlist]}
			
			#revertimos todas las ediciones del menda
			c=0
			for i in pageHistory:
				if i[2]!=author: 
					if i[2]==nickdelbot:#evitar que el bot entre en guerras de ediciones
						#para blanqueos no comprobamos si tiene la misma lista de regex (regexlist) que el anterior blanqueo, sino cual fue la logintud que tenia el texto final del blanqueo anterior
						if len(pageHistory)-1>=c+1 and controlvand[author].has_key(pageHistory[c+1][0]) and controlvand[author][pageHistory[c+1][0]][1]==score: #pageHistory[c+1][0] es la id de la edicion anterior a i[0]
							#evitamos revertir dos veces el mismo blanqueo, misma puntuacion
							break
					[oldid, oldText]=sameOldid(oldid, i[0], oldText, p)
					stats=incrementaStats(stats, 'BL')
					p.put(oldText, u'BOT - Blanqueo de [[Special:Contributions/%s|%s]], revirtiendo hasta la edición %s de [[Usuario:%s|%s]]. ¿[[User:AVBOT/Errores|Hubo un error]]?' % (author, author, str(oldid), i[2], i[2]))
					
					#avisamos al usuario
					controlvand[author]['avisos']+=1
					avbotmsg.msgBlanqueo(author, site, pageTitle, diff, controlvand[author]['avisos'])
					
					#avisamos en WP:VEC
					if len(controlvand[author].items())==4:
						avbotmsg.msgVandalismoEnCurso(controlvand[author], author, userClass, site)
					return True, controlvand, stats
				c+=1
	return False, controlvand, stats

def isSectionBlanking(namespace, pageTitle, author, userClass, authorEditsNum, newbie, data, controlvand, diff, oldid, site, nickdelbot, stats, p, oldText, pageHistory, currentYear):
	#data contiene el diff sin limpiar
	score=0
	regexlist=[]
	if vigilar(namespace, pageTitle, author, userClass, authorEditsNum, newbie):
		#quitamos los saltos de linea para facilitar regex
		data=re.sub(ur'\n|\r', ur'', data)
		m=re.findall(ur'(?im)<td class\="diff\-deletedline"><div>(\={2,} *[^\=]+ *\={2,} *)</div></td>', data)
		n=re.findall(ur'(?im)<td class\="diff\-addedline"><div>(\={2,} *[^\=]+ *\={2,} *)</div></td>', data)
		o=re.findall(ur'(?im)<td class\="diff\-marker">\+</td>', data) #que no se añada ninguna linea nueva
		if len(m)==1 and len(n)==0 and len(o)==0: #si ha eliminado una seccion, pero eliminado de verdad, no solo modificar http://es.wikipedia.org/w/index.php?title=Australasia_en_los_Juegos_Ol%EDmpicos&diff=19338323&oldid=19338321&diffonly=1
			izqda=re.findall(ur'(?im)(<tr><td colspan\="2">&nbsp;</td>)', data)
			dcha=re.findall(ur'(?im)(<td colspan\="2">&nbsp;</td></tr>)', data) #tienen que ir pegados a un </tr> para que la linea eliminada este en la derecha del diff http://es.wikipedia.org/w/index.php?title=Australasia_en_los_Juegos_Ol%EDmpicos&diff=19338323&oldid=19338321&diffonly=1
			if len(izqda)==0 and len(dcha)>0: #que haya blanqueado al menos 1 lineas sin contar la seccion == ==
				score=-len(m[0])
				if controlvand.has_key(author):
					controlvand[author][diff]=[pageTitle, score, regexlist]
				else:
					controlvand[author]={'avisos': 0, diff: [pageTitle, score, regexlist]}
				
				#revertimos todas las ediciones del menda
				c=0
				for i in pageHistory:
					if i[2]!=author: 
						if i[2]==nickdelbot:#evitar que el bot entre en guerras de ediciones
							#para blanqueos no comprobamos si tiene la misma lista de regex (regexlist) que el anterior blanqueo, sino cual fue la logintud que tenia el texto final del blanqueo anterior
							if len(pageHistory)-1>=c+1 and controlvand[author].has_key(pageHistory[c+1][0]) and controlvand[author][pageHistory[c+1][0]][1]==score: #pageHistory[c+1][0] es la id de la edicion anterior a i[0]
								#evitamos revertir dos veces el mismo vandalismo, misma puntuacion
								break
						[oldid, oldText]=sameOldid(oldid, i[0], oldText, p)
						stats=incrementaStats(stats, 'BL')
						p.put(oldText, u'BOT - Blanqueo de sección de [[Special:Contributions/%s|%s]], revirtiendo hasta la edición %s de [[Usuario:%s|%s]]. ¿[[User:AVBOT/Errores|Hubo un error]]?' % (author, author, str(oldid), i[2], i[2]))
						
						#avisamos al usuario
						controlvand[author]['avisos']+=1
						avbotmsg.msgBlanqueo(author, site, pageTitle, diff, controlvand[author]['avisos'])
						
						#avisamos en WP:VEC
						if len(controlvand[author].items())==4:
							avbotmsg.msgVandalismoEnCurso(controlvand[author], author, userClass, site)
						
						return True, controlvand, stats
					c+=1
		
	return False, controlvand, stats

def isSectionVandalism(namespace, pageTitle, author, userClass, authorEditsNum, newbie, data, controlvand, diff, oldid, site, nickdelbot, stats, p, oldText, pageHistory, currentYear):
	#data contiene el diff sin limpiar
	score=0
	regexlist=[]
	if vigilar(namespace, pageTitle, author, userClass, authorEditsNum, newbie):
		#quitamos los saltos de linea para facilitar regex
		data=re.sub(ur'\n|\r', ur'', data)
		m=re.findall(ur'(?im)<td class\="diff\-addedline"><div>\={2,} *[^\=]+ *\={2,} *<span class\="diffchange diffchange\-inline">([^<]+)</span>', data)
		if len(m)==1: #uno y solo uno
			if len(m[0])>0 and len(m[0])<50: #cuidado que m[0][0] devuelve un caracter solo?
				score=-len(m[0])
				if controlvand.has_key(author):
					controlvand[author][diff]=[pageTitle, score, regexlist]
				else:
					controlvand[author]={'avisos': 0, diff: [pageTitle, score, regexlist]}
				
				#revertimos todas las ediciones del menda
				c=0
				for i in pageHistory:
					if i[2]!=author: 
						if i[2]==nickdelbot:#evitar que el bot entre en guerras de ediciones
							#para blanqueos no comprobamos si tiene la misma lista de regex (regexlist) que el anterior blanqueo, sino cual fue la logintud que tenia el texto final del blanqueo anterior
							if len(pageHistory)-1>=c+1 and controlvand[author].has_key(pageHistory[c+1][0]) and controlvand[author][pageHistory[c+1][0]][1]==score: #pageHistory[c+1][0] es la id de la edicion anterior a i[0]
								#evitamos revertir dos veces el mismo vandalismo, misma puntuacion
								break
						[oldid, oldText]=sameOldid(oldid, i[0], oldText, p)
						stats=incrementaStats(stats, 'V')
						p.put(oldText, u'BOT - Vandalismo de sección de [[Special:Contributions/%s|%s]], revirtiendo hasta la edición %s de [[Usuario:%s|%s]]. ¿[[User:AVBOT/Errores|Hubo un error]]?' % (author, author, str(oldid), i[2], i[2]))
						
						#avisamos al usuario
						controlvand[author]['avisos']+=1
						avbotmsg.msgVandalismo(author, site, pageTitle, diff, controlvand[author]['avisos'])
						
						#avisamos en WP:VEC
						if len(controlvand[author].items())==4:
							avbotmsg.msgVandalismoEnCurso(controlvand[author], author, userClass, site)
						
						return True, controlvand, stats
					c+=1
		
	return False, controlvand, stats

def isVandalism(namespace, pageTitle, author, userClass, authorEditsNum, newbie, vandalismos, cleandata, controlvand, p, pageHistory, diff, oldid, site, nickdelbot, oldText, stats, currentYear):
	score=0
	regexlist=[]
	typeText={u'V': u'Vandalismo', u'P': u'Prueba'}
	details=u''
	if vigilar(namespace, pageTitle, author, userClass, authorEditsNum, newbie):
		type='P'
		for k, v in vandalismos.items():
			m=v['compiled'].finditer(cleandata)
			added=False #para que no se desborde el log
			for i in m:
				if v['type']=='V':
					type='V'
				score+=v['score']
				regexlist.append(k)
				if not added:
					details+=u'%s\n' % (k)
					added=True
			
		if score<0 and ((score>-5 and len(cleandata)<score*-150) or score<-4): #en fase de pruebas, densidad len(data)<score*-100
			#añadimos al control de vandalismos
			if controlvand.has_key(author):
				controlvand[author][diff]=[pageTitle, score, regexlist]
			else:
				controlvand[author]={'avisos': 0, diff: [pageTitle, score, regexlist]}
			
			#revertimos todas las ediciones del menda
			c=0
			for i in pageHistory:
				if i[2]!=author: 
					if i[2]==nickdelbot and score>-30:#evitar que el bot entre en guerras de ediciones, excepto si la puntuacion es muy baja
						if len(pageHistory)-1>=c+1 and controlvand[author].has_key(pageHistory[c+1][0]) and isSameVandalism(controlvand[author][pageHistory[c+1][0]][2], regexlist): #pageHistory[c+1][0] es la id de la edicion anterior a i[0]
							#evitamos revertir dos veces el mismo vandalismo, misma puntuacion, excepto si es muy baja
							break
					[oldid, oldText]=sameOldid(oldid, i[0], oldText, p)
					stats=incrementaStats(stats, type)
					p.put(oldText, u'BOT - %s de [[Special:Contributions/%s|%s]], revirtiendo hasta la edición %s de [[Usuario:%s|%s]]. ¿[[User:AVBOT/Errores|Hubo un error]]?' % (typeText[type], author, author, str(oldid), i[2], i[2]))
					
					#avisamos al usuario
					controlvand[author]['avisos']+=1
					if type=='V':
						avbotmsg.msgVandalismo(author, site, pageTitle, diff, controlvand[author]['avisos'])
					else:
						avbotmsg.msgPrueba(author, site, pageTitle, diff, controlvand[author]['avisos'])
					
					#avisamos en WP:VEC
					if len(controlvand[author].items())==4:
						avbotmsg.msgVandalismoEnCurso(controlvand[author], author, userClass, site)
					
					#guardamos log
					log=open('/home/emijrp/public_html/avbot/%s.txt' % datetime.date.today(), 'a')
					logentry=u'\n%s\nArtículo: [[%s]]\nFecha: %s\nPuntuación: %d\nExpresiones regulares:\n%s\n%s' % ('-'*100, pageTitle, datetime.datetime.today(), score, details, '-'*100)
					log.write(logentry.encode('utf-8'))
					log.close()
					
					return True, score, details, controlvand, stats
				c+=1
	return False, score, details, controlvand, stats

def isShockingContent(namespace, pageTitle, author, userClass, authorEditsNum, newbie, imageneschocantes, cleandata, controlvand, p, pageHistory, diff, oldid, site, nickdelbot, oldText, stats, currentYear):
	if imageneschocantes['exceptions'].count(pageTitle)==0 and vigilar(namespace, pageTitle, author, userClass, authorEditsNum, newbie):
		for filename, compiled in imageneschocantes['images'].items():
			m=re.findall(compiled, cleandata)
			if m: #reveritmos y salimos
				#añadimos al control de vandalismos
				if controlvand.has_key(author):
					controlvand[author][diff]=[pageTitle, -9999, [filename]]
				else:
					controlvand[author]={'avisos': 0, diff: [pageTitle, -9999, [filename]]}
				
				#revertimos todas las ediciones del menda
				c=0
				for i in pageHistory:
					if i[2]!=author: 
						if i[2]==nickdelbot:#evitar que el bot entre en guerras de ediciones
							if len(pageHistory)-1>=c+1 and controlvand[author].has_key(pageHistory[c+1][0]) and isSameVandalism(controlvand[author][pageHistory[c+1][0]][2], [filename]): #pageHistory[c+1][0] es la id de la edicion anterior a i[0]
								#evitamos revertir dos veces el mismo vandalismo, misma puntuacion
								break
						[oldid, oldText]=sameOldid(oldid, i[0], oldText, p)
						stats=incrementaStats(stats, 'V')
						p.put(oldText, u'BOT - Contenido chocante de [[Special:Contributions/%s|%s]], revirtiendo hasta la edición %s de [[Usuario:%s|%s]]. ¿[[User:AVBOT/Errores|Hubo un error]]?' % (author, author, str(oldid), i[2], i[2]))
						
						#avisamos al usuario
						controlvand[author]['avisos']+=1
						avbotmsg.msgContenidoChocante(author, site, pageTitle, diff, controlvand[author]['avisos'])
						
						#avisamos en WP:VEC
						if len(controlvand[author].items())==4:
							avbotmsg.msgVandalismoEnCurso(controlvand[author], author, userClass, site)
						
						return True, controlvand, stats
					c+=1
	return False, controlvand, stats

def isTest(namespace, pageTitle, author, userClass, authorEditsNum, newbie, pruebas, cleandata, controlvand, diff, site, nickdelbot, stats, p, oldText, pageHistory, currentYear):
	details=u''
	regexlist=[]
	score=0
	if vigilar(namespace, pageTitle, author, userClass, authorEditsNum, newbie):
		#no calculamos score, con una vale
		restaurar=False
		for k, v in pruebas.items():
			m=v['compiled'].finditer(cleandata)
			for i in m:
				score+=v['score']
				regexlist.append(k) #aunque despues no la usamos para nada, es para mantener consistencia
				details+=u'%s\n' % (k)
			
		if score<0 and ((score>-5 and len(cleandata)<score*-150) or score<-4): #en fase de pruebas, densidad len(data)<score*-100
			restaurar=True
			#añadimos al control de vandalismos
			if controlvand.has_key(author):
				controlvand[author][diff]=[pageTitle, score, regexlist]
			else:
				controlvand[author]={'avisos': 0, diff: [pageTitle, score, regexlist]}
			
			for i in pageHistory: #lo ponemos con el is_vandalism()?
				if i[2]==nickdelbot: #evitar que el bot entre en guerras de ediciones
					restaurar=False
					break
				if i[2]==author: #presumir buena fe
					restaurar=False
					break
			
			#no meter dentro del bucle de pageHistory para presumir buena fe
			if restaurar:
				stats=incrementaStats(stats, 'P')
				p.put(oldText, u'BOT - Prueba de [[Special:Contributions/%s|%s]], revirtiendo hasta la edición %s de [[Usuario:%s|%s]]. ¿[[User:AVBOT/Errores|Hubo un error]]?' % (author, author, str(pageHistory[1][0]), pageHistory[1][2], pageHistory[1][2]))
				
				#avisamos al usuario
				controlvand[author]['avisos']+=1
				avbotmsg.msgPrueba(author, site, pageTitle, diff, controlvand[author]['avisos'])
				
				#avisamos en WP:VEC
				if len(controlvand[author].items())==4:
					avbotmsg.msgVandalismoEnCurso(controlvand[author], author, userClass, site)
				
				return True, details, controlvand, stats
	return False, details, controlvand, stats

def antiBirthday(pageTitle, userClass, authorEditsNum, newbie, namespace, oldText, newText, cleandata, controlvand, site, pageHistory, diff, nickdelbot, author, oldid, stats, p, currentYear):
	if re.search(ur'(?m)^\d{1,2} de (enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)$', pageTitle) and (userClass=='anon' or (userClass=='reg' and authorEditsNum<=newbie)) and namespace==0:
		#wikipedia.output(u'ha entrado')
		restaurar=False
		enlaceexiste=False
		motivo=u''
		tmp=newText.split('==')
		acontecimientos=u''
		nacimientos=u''
		fallecimientos=u''
		cont=0
		for i in tmp:
			cont+=1 #evitamos hacer +1 despues
			if re.search(ur'(?i)acontecimientos', i):
				acontecimientos=tmp[cont]
			if re.search(ur'(?i)nacimientos', i):
				nacimientos=tmp[cont]
			if re.search(ur'(?i)fallecimientos', i):
				fallecimientos=tmp[cont]
		
		#wikipedia.output(u'%s' % acontecimientos[:50])
		#wikipedia.output(u'%s' % nacimientos[:50])
		#wikipedia.output(u'%s' % fallecimientos[:50])
		
		#anticumpleanos
		#wikipedia.output(cleandata)
		#no poner (?im) ya que cleandata no es wtext
		m=re.compile(ur'(?i)\* *\[?\[?(\d{4})\]?\]? *?[\:\-] *?[^\[]*?\[\[([^\|\]]*?)(\|[^\]]*?)?\]\]').finditer(cleandata)
		for i in m: #controlar si se ha metido mas de un cumpleaños?
			anyo=i.group(1)
			enlace=i.group(2)
			#wikipedia.output(u'--->[[%s]] - [[%s]]' % (anyo, enlace))
			wii={}
			wii['es']=wikipedia.Page(site, u'%s' % enlace)
			try:
				if wii['es'].exists():
					enlaceexiste=True
			except:
				pass
			
			if not enlaceexiste and not restaurar and (re.search(u'(?i)%s.*%s' % (anyo, enlace), nacimientos) or re.search(u'(?i)%s.*%s' % (anyo, enlace), fallecimientos)): #poner anyos futuros en los acontecimientos es posible
				if int(anyo)>int(currentYear):
					restaurar=True
					motivo=u'Fecha imposible (Año %s)' % anyo
			
			if not enlaceexiste and not restaurar and re.search(u'(?i)%s.*%s' % (anyo, enlace), nacimientos):
				if int(anyo)>=int(currentYear)-20:
					#que chico mas precoz, comprobemos su relevancia
					wii['en']=wikipedia.Page(wikipedia.Site('en', 'wikipedia'), u'%s' % enlace)
					#wii['de']=wikipedia.Page(wikipedia.Site('de', 'wikipedia'), u'%s' % enlace)
					#wii['fr']=wikipedia.Page(wikipedia.Site('fr', 'wikipedia'), u'%s' % enlace)
					
					#la inglesa da error a veces, gestionamos la excepcion
					try:
						if wii['en'].exists():
							restaurar=False #reescribimos, bleh
					except:
						restaurar=True
						motivo=u'Eliminando enlace irrelevante'
		
		if restaurar and not enlaceexiste:
			#añadimos al control de vandalismos
			if controlvand.has_key(author):
				controlvand[author][diff]=[pageTitle, score, regexlist]
			else:
				controlvand[author]={'avisos': 0, diff: [pageTitle, score, regexlist]}
			
			#mismo codigo que en vandalismos
			#wikipedia.output(u'intenta restaurar')
			for i in pageHistory:
				if i[2]==nickdelbot: #evitar que el bot entre en guerras de ediciones
					break
				if i[2]!=author:
					[oldid, oldText]=sameOldid(oldid, i[0], oldText, p)
					stats=incrementaStats(stats, 'V')
					p.put(oldText, u'BOT - %s en la edición de [[Special:Contributions/%s|%s]], revirtiendo hasta la edición %s de [[Usuario:%s|%s]]. ¿[[User:AVBOT/Errores|Hubo un error]]?' % (motivo, author, author, str(oldid), i[2], i[2]))
					
					#avisamos al usuario
					controlvand[author]['avisos']+=1
					if re.search(ur'(?i)irrelevante', motivo):
						avbotmsg.msgEnlaceIrrelevante(author, site, pageTitle, diff, controlvand[author]['avisos'])
					elif re.search(ur'(?i)imposible', motivo):
						avbotmsg.msgFechaImposible(author, site, pageTitle, diff, controlvand[author]['avisos'])
					
					#avisamos en WP:VEC
					if len(controlvand[author].items())==4:
						avbotmsg.msgVandalismoEnCurso(controlvand[author], author, userClass, site)
					
					return True, motivo, controlvand, stats
	return False, u'', controlvand, stats

def autoSign(userClass, authorEditsNum, newbie, namespace, p, pageHistory, author, nickdelbot, data, patterns, site, pageTitle, diff, newText):
	if (userClass=='anon' or (userClass=='reg' and authorEditsNum<=newbie)) and (namespace==1 or namespace==3 or namespace==5 or namespace==7 or namespace==9 or namespace==11 or namespace==13 or namespace==15 or namespace==101 or namespace==103 or namespace==105 or re.search(ur'Wikipedia:Café/Portal/Archivo/.*?/Actual', p.title())):
		oldauthor=pageHistory[1][2]
		if oldauthor!=author and oldauthor!=nickdelbot and not re.search(u'<td class="diff-deletedline">', data) and not re.search(ur'(?i)(<span class="diffchange">|<span class="diffchange diffchange-inline">|<ins class="diffchange diffchange-inline">)', data): #evitamos que el bot edite muy frecuentemente la discusion, y evitamos firmar falsos positivos como borrados de texto, archivados, o modificaciones de comentarios ya firmados
			firmado=False
			ultimalinea=u''
			m=patterns['firmas1'].finditer(data)
			if not m:
				wikipedia.output(u'No es un comentario nuevo')
				firmado=True
			cuantas=0
			for i in m:
				minidiff=i.group(1)
				cuantas+=1
				if re.search(ur'(?i)(\d\d:\d\d \d{1,2}( de)? (ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)( del?)? 200\d|%s|\-\- ?\[\[|Special:Contributions|Usuario Discusión)' % author, minidiff):
					wikipedia.output(u'Comentario firmado')
					firmado=True
				ultimalinea=minidiff #se va machacando
			if not firmado:
				if not re.search(ur'==', ultimalinea) and cuantas>=1 and len(ultimalinea)>20 and not re.search(ur'\{\{', ultimalinea):
					temp=re.sub(re.escape(ultimalinea), u'%s {{No firmado|%s|{{subst:CURRENTTIME}} {{subst:CURRENTDAY}} {{subst:CURRENTMONTHNAME}} {{subst:CURRENTYEAR}} (UTC)}}' % (ultimalinea, author), newText)
					p.put(temp, u'BOT - Firmando el comentario de [[Usuario:%s|%s]] ([[Usuario Discusión:%s|disc]] · [[Special:Contributions/%s|cont]])' % (author, author, author, author))
					#avisamos al usuario
					avbotmsg.msgFirma(p, author, site, pageTitle, diff)
					return True
	return False
