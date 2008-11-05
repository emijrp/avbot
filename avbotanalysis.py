# -*- coding: utf-8 -*-

import re, wikipedia, datetime

import avbotload
import avbotsave
import avbotmsg
import avbotcomb

def sameOldid(oldid, id, oldtext, p):
	#return id, p.getOldVersion(id) #mientras averiguo lo de abajo
	
	#este metodo falla? http://es.wikipedia.org/w/index.php?title=Usuario:AVBOT/Errores&diff=prev&oldid=21309979
	if oldid!=id:
		return id, p.getOldVersion(id)
	else:
		return id, oldtext

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

def vigilar(namespace, wtitle, author, userclass, edicionesauthor, novato):
	if (namespace==0 or namespace==10 or namespace==12 or namespace==14 or namespace==100 or namespace==102 or namespace==104 or (namespace==2 and not re.search(ur'\/', wtitle) and not re.search(ur'(?i)%s' % re.sub('_', ' ', author), re.sub('_', ' ', wtitle))) or (namespace==4 and not re.search(ur'Wikipedia\:Café', wtitle))) and (userclass=='anon' or (userclass=='reg' and edicionesauthor<=novato)):
		return True
	return False

def isRubbish(p, userclass, wtitle, newtext, colors, author, edicionesauthor, novato, namespace, pruebas, vandalismos, stats):
	destruir=False
	motivo=u'Otros'
	score=0
	
	if userclass=='anon' or (userclass=='reg' and edicionesauthor<=novato):
		if (namespace==0) and not p.isRedirectPage() and not p.isDisambig():
			if not re.search(ur'(?i)\{\{|redirect', newtext):
				for k, v in vandalismos.items():
					m=v['compiled'].finditer(newtext)
					for i in m:
						score+=v['score']
				
				if score<0 and ((score>-5 and len(newtext)<score*-150) or score<-4): #igualar a  densidad de isVandalism()?
					destruir=True
					motivo=u'Vandalismo'
				else:
					if len(newtext)<200:
						for k, v in pruebas.items():
							if re.search(v['compiled'], newtext):
								destruir=True
								motivo=u'Pruebas'
				if len(newtext)<=75 and not destruir:
					if not re.search(ur'\[', newtext):
						destruir=True
						motivo=u'Demasiado corto'
		if destruir:
			stats=incrementaStats(stats, 'D')
			p.put(u'{{RobotDestruir|%s|%s}}\n%s' % (author, motivo, newtext), u'Marcando para destruir. Motivo: %s. Página creada por [[Usuario:%s|%s]] ([[Usuario Discusión:%s|disc]] · [[Special:Contributions/%s|cont]])' % (motivo, author, author, author, author))
			return True, motivo, stats
	return False, motivo, stats

def improveNewArticle(namespace, p):
	newtext=p.get()
	if (namespace==0) and not p.isRedirectPage() and not p.isDisambig():
		if not re.search(ur'(?i)\{\{ *(destruir|plagio|copyvio)|redirect', newtext): #descarta demasiado? destruir|plagio|copyvio
			if len(newtext)>=500:
				resumen=u''
				newnewtext=u''
				if not p.interwiki():
					try:
						[newnewtext, resumen]=avbotcomb.magicInterwiki(p, resumen, 'en')
					except:
						pass
				[newnewtext, resumen]=avbotcomb.vtee(newnewtext, resumen)
				#[newnewtext, resumen]=avbotcomb.cosmetic(newnewtext, resumen)
				if len(newnewtext)>len(newtext):
					p.put(newnewtext, u'BOT - Aplicando %s... al artículo recién creado' % resumen)
					return True, resumen
	return False, u''

def isBlanking(namespace, wtitle, author, userclass, edicionesauthor, novato, lenold, lennew, patterns, newtext, controlvand, diff, site, vh, nickdelbot, oldtext, p, oldid, stats, anyoactual):
	score=0
	regexlist=[]
	if vigilar(namespace, wtitle, author, userclass, edicionesauthor, novato):
		if lenold>=1000 and lennew<lenold/7 and not re.search(patterns['blanqueos'], newtext): # 1/7 es un buen numero?
			score=-(lennew+1) #la puntuacion de los blanqueos es la nueva longitud + 1, negada, para evitar el -0
			#añadimos al control de vandalismos
			if controlvand.has_key(author):
				controlvand[author][diff]=[wtitle, score, regexlist] #metemos regexlist que es una lista vacia, para mantener consistencia con is_Vandalism()
			else:
				controlvand[author]={'avisos': 0, diff: [wtitle, score, regexlist]}
			
			#revertimos todas las ediciones del menda
			c=0
			for i in vh:
				if i[2]!=author: 
					if i[2]==nickdelbot:#evitar que el bot entre en guerras de ediciones
						#para blanqueos no comprobamos si tiene la misma lista de regex (regexlist) que el anterior blanqueo, sino cual fue la logintud que tenia el texto final del blanqueo anterior
						if len(vh)-1>=c+1 and controlvand[author].has_key(vh[c+1][0]) and controlvand[author][vh[c+1][0]][1]==score: #vh[c+1][0] es la id de la edicion anterior a i[0]
							#evitamos revertir dos veces el mismo blanqueo, misma puntuacion
							break
					[oldid, oldtext]=sameOldid(oldid, i[0], oldtext, p)
					stats=incrementaStats(stats, 'BL')
					p.put(oldtext, u'BOT - Blanqueo de [[Special:Contributions/%s|%s]], revirtiendo hasta la edición %s de [[Usuario:%s|%s]]. ¿[[User:AVBOT/Errores|Hubo un error]]?' % (author, author, str(oldid), i[2], i[2]))
					
					#avisamos al usuario
					controlvand[author]['avisos']+=1
					avbotmsg.msgBlanqueo(author, site, wtitle, diff, controlvand[author]['avisos'])
					
					#avisamos en WP:VEC
					if len(controlvand[author].items())==4:
						avbotmsg.msgVandalismoEnCurso(controlvand[author], author, userclass, site)
					return True, controlvand, stats
				c+=1
	return False, controlvand, stats

def isSectionBlanking(namespace, wtitle, author, userclass, edicionesauthor, novato, data, controlvand, diff, oldid, site, nickdelbot, stats, p, oldtext, vh, anyoactual):
	#data contiene el diff sin limpiar
	score=0
	regexlist=[]
	if vigilar(namespace, wtitle, author, userclass, edicionesauthor, novato):
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
					controlvand[author][diff]=[wtitle, score, regexlist]
				else:
					controlvand[author]={'avisos': 0, diff: [wtitle, score, regexlist]}
				
				#revertimos todas las ediciones del menda
				c=0
				for i in vh:
					if i[2]!=author: 
						if i[2]==nickdelbot:#evitar que el bot entre en guerras de ediciones
							#para blanqueos no comprobamos si tiene la misma lista de regex (regexlist) que el anterior blanqueo, sino cual fue la logintud que tenia el texto final del blanqueo anterior
							if len(vh)-1>=c+1 and controlvand[author].has_key(vh[c+1][0]) and controlvand[author][vh[c+1][0]][1]==score: #vh[c+1][0] es la id de la edicion anterior a i[0]
								#evitamos revertir dos veces el mismo vandalismo, misma puntuacion
								break
						[oldid, oldtext]=sameOldid(oldid, i[0], oldtext, p)
						stats=incrementaStats(stats, 'BL')
						p.put(oldtext, u'BOT - Blanqueo de sección de [[Special:Contributions/%s|%s]], revirtiendo hasta la edición %s de [[Usuario:%s|%s]]. ¿[[User:AVBOT/Errores|Hubo un error]]?' % (author, author, str(oldid), i[2], i[2]))
						
						#avisamos al usuario
						controlvand[author]['avisos']+=1
						avbotmsg.msgBlanqueo(author, site, wtitle, diff, controlvand[author]['avisos'])
						
						#avisamos en WP:VEC
						if len(controlvand[author].items())==4:
							avbotmsg.msgVandalismoEnCurso(controlvand[author], author, userclass, site)
						
						return True, controlvand, stats
					c+=1
		
	return False, controlvand, stats

def isSectionVandalism(namespace, wtitle, author, userclass, edicionesauthor, novato, data, controlvand, diff, oldid, site, nickdelbot, stats, p, oldtext, vh, anyoactual):
	#data contiene el diff sin limpiar
	score=0
	regexlist=[]
	if vigilar(namespace, wtitle, author, userclass, edicionesauthor, novato):
		#quitamos los saltos de linea para facilitar regex
		data=re.sub(ur'\n|\r', ur'', data)
		m=re.findall(ur'(?im)<td class\="diff\-addedline"><div>\={2,} *[^\=]+ *\={2,} *<span class\="diffchange diffchange\-inline">([^<]+)</span>', data)
		if len(m)==1: #uno y solo uno
			if len(m[0])>0 and len(m[0])<50: #cuidado que m[0][0] devuelve un caracter solo?
				score=-len(m[0])
				if controlvand.has_key(author):
					controlvand[author][diff]=[wtitle, score, regexlist]
				else:
					controlvand[author]={'avisos': 0, diff: [wtitle, score, regexlist]}
				
				#revertimos todas las ediciones del menda
				c=0
				for i in vh:
					if i[2]!=author: 
						if i[2]==nickdelbot:#evitar que el bot entre en guerras de ediciones
							#para blanqueos no comprobamos si tiene la misma lista de regex (regexlist) que el anterior blanqueo, sino cual fue la logintud que tenia el texto final del blanqueo anterior
							if len(vh)-1>=c+1 and controlvand[author].has_key(vh[c+1][0]) and controlvand[author][vh[c+1][0]][1]==score: #vh[c+1][0] es la id de la edicion anterior a i[0]
								#evitamos revertir dos veces el mismo vandalismo, misma puntuacion
								break
						[oldid, oldtext]=sameOldid(oldid, i[0], oldtext, p)
						stats=incrementaStats(stats, 'V')
						p.put(oldtext, u'BOT - Vandalismo de sección de [[Special:Contributions/%s|%s]], revirtiendo hasta la edición %s de [[Usuario:%s|%s]]. ¿[[User:AVBOT/Errores|Hubo un error]]?' % (author, author, str(oldid), i[2], i[2]))
						
						#avisamos al usuario
						controlvand[author]['avisos']+=1
						avbotmsg.msgVandalismo(author, site, wtitle, diff, controlvand[author]['avisos'])
						
						#avisamos en WP:VEC
						if len(controlvand[author].items())==4:
							avbotmsg.msgVandalismoEnCurso(controlvand[author], author, userclass, site)
						
						return True, controlvand, stats
					c+=1
		
	return False, controlvand, stats

def isVandalism(namespace, wtitle, author, userclass, edicionesauthor, novato, vandalismos, cleandata, controlvand, p, vh, diff, oldid, site, nickdelbot, oldtext, stats, anyoactual):
	score=0
	regexlist=[]
	details=u''
	if vigilar(namespace, wtitle, author, userclass, edicionesauthor, novato):
		for k, v in vandalismos.items():
			m=v['compiled'].finditer(cleandata)
			added=False #para que no se desborde el log
			for i in m:
				score+=v['score']
				regexlist.append(k)
				if not added:
					details+=u'%s\n' % (k)
					added=True
			
		if score<0 and ((score>-5 and len(cleandata)<score*-150) or score<-4): #en fase de pruebas, densidad len(data)<score*-100
			#añadimos al control de vandalismos
			if controlvand.has_key(author):
				controlvand[author][diff]=[wtitle, score, regexlist]
			else:
				controlvand[author]={'avisos': 0, diff: [wtitle, score, regexlist]}
			
			#revertimos todas las ediciones del menda
			c=0
			for i in vh:
				if i[2]!=author: 
					if i[2]==nickdelbot and score>-30:#evitar que el bot entre en guerras de ediciones, excepto si la puntuacion es muy baja
						if len(vh)-1>=c+1 and controlvand[author].has_key(vh[c+1][0]) and isSameVandalism(controlvand[author][vh[c+1][0]][2], regexlist): #vh[c+1][0] es la id de la edicion anterior a i[0]
							#evitamos revertir dos veces el mismo vandalismo, misma puntuacion, excepto si es muy baja
							break
					[oldid, oldtext]=sameOldid(oldid, i[0], oldtext, p)
					stats=incrementaStats(stats, 'V')
					p.put(oldtext, u'BOT - Vandalismo de [[Special:Contributions/%s|%s]], revirtiendo hasta la edición %s de [[Usuario:%s|%s]]. ¿[[User:AVBOT/Errores|Hubo un error]]?' % (author, author, str(oldid), i[2], i[2]))
					
					#avisamos al usuario
					controlvand[author]['avisos']+=1
					avbotmsg.msgVandalismo(author, site, wtitle, diff, controlvand[author]['avisos'])
					
					#avisamos en WP:VEC
					if len(controlvand[author].items())==4:
						avbotmsg.msgVandalismoEnCurso(controlvand[author], author, userclass, site)
					
					#guardamos log
					log=open('/home/emijrp/public_html/avbot/%s.txt' % datetime.date.today(), 'a')
					logentry=u'\n%s\nArtículo: [[%s]]\nFecha: %s\nPuntuación: %d\nExpresiones regulares:\n%s\n%s' % ('-'*100, wtitle, datetime.datetime.today(), score, details, '-'*100)
					log.write(logentry.encode('utf-8'))
					log.close()
					
					return True, score, details, controlvand, stats
				c+=1
	return False, score, details, controlvand, stats

def isShockingContent(namespace, wtitle, author, userclass, edicionesauthor, novato, imageneschocantes, cleandata, controlvand, p, vh, diff, oldid, site, nickdelbot, oldtext, stats, anyoactual):
	if imageneschocantes['exceptions'].count(wtitle)==0 and vigilar(namespace, wtitle, author, userclass, edicionesauthor, novato):
		for filename, compiled in imageneschocantes['images'].items():
			m=re.findall(compiled, cleandata)
			if m: #reveritmos y salimos
				#añadimos al control de vandalismos
				if controlvand.has_key(author):
					controlvand[author][diff]=[wtitle, -9999, [filename]]
				else:
					controlvand[author]={'avisos': 0, diff: [wtitle, -9999, [filename]]}
				
				#revertimos todas las ediciones del menda
				c=0
				for i in vh:
					if i[2]!=author: 
						if i[2]==nickdelbot:#evitar que el bot entre en guerras de ediciones
							if len(vh)-1>=c+1 and controlvand[author].has_key(vh[c+1][0]) and isSameVandalism(controlvand[author][vh[c+1][0]][2], [filename]): #vh[c+1][0] es la id de la edicion anterior a i[0]
								#evitamos revertir dos veces el mismo vandalismo, misma puntuacion
								break
						[oldid, oldtext]=sameOldid(oldid, i[0], oldtext, p)
						stats=incrementaStats(stats, 'V')
						p.put(oldtext, u'BOT - Contenido chocante de [[Special:Contributions/%s|%s]], revirtiendo hasta la edición %s de [[Usuario:%s|%s]]. ¿[[User:AVBOT/Errores|Hubo un error]]?' % (author, author, str(oldid), i[2], i[2]))
						
						#avisamos al usuario
						controlvand[author]['avisos']+=1
						avbotmsg.msgContenidoChocante(author, site, wtitle, diff, controlvand[author]['avisos'])
						
						#avisamos en WP:VEC
						if len(controlvand[author].items())==4:
							avbotmsg.msgVandalismoEnCurso(controlvand[author], author, userclass, site)
						
						return True, controlvand, stats
					c+=1
	return False, controlvand, stats

def isTest(namespace, wtitle, author, userclass, edicionesauthor, novato, pruebas, cleandata, controlvand, diff, site, nickdelbot, stats, p, oldtext, vh, anyoactual):
	details=u''
	regexlist=[]
	score=0
	if vigilar(namespace, wtitle, author, userclass, edicionesauthor, novato):
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
				controlvand[author][diff]=[wtitle, score, regexlist]
			else:
				controlvand[author]={'avisos': 0, diff: [wtitle, score, regexlist]}
			
			for i in vh: #lo ponemos con el is_vandalism()?
				if i[2]==nickdelbot: #evitar que el bot entre en guerras de ediciones
					restaurar=False
					break
				if i[2]==author: #presumir buena fe
					restaurar=False
					break
			
			#no meter dentro del bucle de vh para presumir buena fe
			if restaurar:
				stats=incrementaStats(stats, 'P')
				p.put(oldtext, u'BOT - Prueba de [[Special:Contributions/%s|%s]], revirtiendo hasta la edición %s de [[Usuario:%s|%s]]. ¿[[User:AVBOT/Errores|Hubo un error]]?' % (author, author, str(vh[1][0]), vh[1][2], vh[1][2]))
				
				#avisamos al usuario
				controlvand[author]['avisos']+=1
				avbotmsg.msgPrueba(author, site, wtitle, diff, controlvand[author]['avisos'])
				
				#avisamos en WP:VEC
				if len(controlvand[author].items())==4:
					avbotmsg.msgVandalismoEnCurso(controlvand[author], author, userclass, site)
				
				return True, details, controlvand, stats
	return False, details, controlvand, stats

def antiBirthday(wtitle, userclass, edicionesauthor, novato, namespace, oldtext, newtext, cleandata, controlvand, site, vh, diff, nickdelbot, author, oldid, stats, p, anyoactual):
	if re.search(ur'(?m)^\d{1,2} de (enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)$', wtitle) and (userclass=='anon' or (userclass=='reg' and edicionesauthor<=novato)) and namespace==0:
		#wikipedia.output(u'ha entrado')
		restaurar=False
		enlaceexiste=False
		motivo=u''
		tmp=newtext.split('==')
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
				if int(anyo)>int(anyoactual):
					restaurar=True
					motivo=u'Fecha imposible (Año %s)' % anyo
			
			if not enlaceexiste and not restaurar and re.search(u'(?i)%s.*%s' % (anyo, enlace), nacimientos):
				if int(anyo)>=int(anyoactual)-20:
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
				controlvand[author][diff]=[wtitle, score, regexlist]
			else:
				controlvand[author]={'avisos': 0, diff: [wtitle, score, regexlist]}
			
			#mismo codigo que en vandalismos
			#wikipedia.output(u'intenta restaurar')
			for i in vh:
				if i[2]==nickdelbot: #evitar que el bot entre en guerras de ediciones
					break
				if i[2]!=author:
					[oldid, oldtext]=sameOldid(oldid, i[0], oldtext, p)
					stats=incrementaStats(stats, 'V')
					p.put(oldtext, u'BOT - %s en la edición de [[Special:Contributions/%s|%s]], revirtiendo hasta la edición %s de [[Usuario:%s|%s]]. ¿[[User:AVBOT/Errores|Hubo un error]]?' % (motivo, author, author, str(oldid), i[2], i[2]))
					
					#avisamos al usuario
					controlvand[author]['avisos']+=1
					if re.search(ur'(?i)irrelevante', motivo):
						avbotmsg.msgEnlaceIrrelevante(author, site, wtitle, diff, controlvand[author]['avisos'])
					elif re.search(ur'(?i)imposible', motivo):
						avbotmsg.msgFechaImposible(author, site, wtitle, diff, controlvand[author]['avisos'])
					
					#avisamos en WP:VEC
					if len(controlvand[author].items())==4:
						avbotmsg.msgVandalismoEnCurso(controlvand[author], author, userclass, site)
					
					return True, motivo, controlvand, stats
	return False, u'', controlvand, stats

def autoSign(userclass, edicionesauthor, novato, namespace, p, vh, author, nickdelbot, data, patterns, site, wtitle, diff, newtext):
	if (userclass=='anon' or (userclass=='reg' and edicionesauthor<=novato)) and (namespace==1 or namespace==3 or namespace==5 or namespace==7 or namespace==9 or namespace==11 or namespace==13 or namespace==15 or namespace==101 or namespace==103 or namespace==105 or re.search(ur'Wikipedia:Café/Portal/Archivo/.*?/Actual', p.title())):
		oldauthor=vh[1][2]
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
					temp=re.sub(re.escape(ultimalinea), u'%s {{No firmado|%s|{{subst:CURRENTTIME}} {{subst:CURRENTDAY}} {{subst:CURRENTMONTHNAME}} {{subst:CURRENTYEAR}} (UTC)}}' % (ultimalinea, author), newtext)
					p.put(temp, u'BOT - Firmando el comentario de [[Usuario:%s|%s]] ([[Usuario Discusión:%s|disc]] · [[Special:Contributions/%s|cont]])' % (author, author, author, author))
					#avisamos al usuario
					avbotmsg.msgFirma(p, author, site, wtitle, diff)
					return True
	return False
