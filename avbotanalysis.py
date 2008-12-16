# -*- coding: utf-8 -*-

#############################################
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
#############################################

import re, wikipedia, datetime

import avbotload
import avbotsave
import avbotmsg
import avbotcomb

def sameOldid(editData):
	#return id, p.getOldVersion(id) #mientras averiguo lo de abajo
	
	#este metodo falla? http://es.wikipedia.org/w/index.php?title=Usuario:AVBOT/Errores&diff=prev&oldid=21309979
	if editData['oldid']!=editData['stableid']:
		editData['stableText']=editData['page'].getOldVersion(editData['stableid'])
		return editData
	else:
		editData['stableText']=editData['oldText']
		return editData

def isSameVandalism(regexlistold, regexlistnew):
	if len(regexlistold)!=len(regexlistnew):
		return False
	else:
		for r in regexlistold:
			if regexlistold.count(r)!=regexlistnew.count(r):
				return False
	return True

def incrementaStats(stats, type):
	type2=type
	if re.search(ur'(?i)blanking', type):
		type2='BL'
	if re.search(ur'(?i)test', type):
		type2='P'
	if re.search(ur'(?i)vandalism', type):
		type2='V'
	
	stats[2][type2]+=1
	stats[12][type2]+=1
	stats[24][type2]+=1
	
	return stats

def watch(editData, preferences, userClass, authorEditsNum):
	if (editData['namespace']==0 or editData['namespace']==4 or editData['namespace']==10 or editData['namespace']==12 or editData['namespace']==14 or editData['namespace']==100 or editData['namespace']==102 or editData['namespace']==104 or (editData['namespace']==2 and not re.search(ur'\/', editData['pageTitle']) and not re.search(ur'(?i)%s' % re.sub('_', ' ', editData['author']), re.sub('_', ' ', editData['pageTitle'])))):
		if userClass=='anon' or (userClass=='reg' and authorEditsNum<=preferences['newbie']):
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
			p.put(u'{{RobotDestruir|%s|%s}}\n%s' % (author, motivo, newText), u'Marcando para destruir. Motivo: %s. Página creada por [[User:%s|%s]] ([[Usuario Discusión:%s|disc]] · [[Special:Contributions/%s|cont]])' % (motivo, author, author, author, author))
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

def revertAllEditsByUser(editData, preferences, controlvand, userClass, statsDic):
	c=0
	for i in editData['pageHistory']:
		if i[2]!=editData['author']: 
			if i[2]==preferences['botNick']:#evitar que el bot entre en guerras de ediciones, ni aunque la puntuacion sea muy baja
				if re.search(ur'(?i)blanking', editData['type']):
					#para blanqueos no comprobamos si tiene la misma lista de regex (regexlist) que el anterior blanqueo, sino cual fue la logintud que tenia el texto final del blanqueo anterior
					if len(editData['pageHistory'])-1>=c+1 and controlvand[editData['author']].has_key(editData['pageHistory'][c+1][0]) and controlvand[editData['author']][editData['pageHistory'][c+1][0]][1]==editData['score']: #pageHistory[c+1][0] es la id de la edicion anterior a i[0]
						#evitamos revertir dos veces el mismo blanqueo, misma puntuacion
						break
				if re.search(ur'(?i)vandalism', editData['type']):
					regexlist=controlvand[editData['author']][editData['diff']][2]
					if len(editData['pageHistory'])-1>=c+1 and controlvand[editData['author']].has_key(editData['pageHistory'][c+1][0]) and isSameVandalism(controlvand[editData['author']][editData['pageHistory'][c+1][0]][2], regexlist): #pageHistory[c+1][0] es la id de la edicion anterior a i[0]
						#evitamos revertir dos veces el mismo vandalismo, misma puntuacion, excepto si es muy baja
						break
			
			editData['stableid']=i[0]
			editData['stableAuthor']=i[2]
			editData=sameOldid(editData)
			
			statsDic=incrementaStats(statsDic, editData['type'])
			
			#restauramos version estable del articulo
			editData['page'].put(editData['stableText'], avbotcomb.resumeTranslator(preferences,editData))
			
			#avisamos al usuario
			controlvand[editData['author']]['avisos']+=1
			if re.search(ur'(?i)blanking', editData['type']):
				avbotmsg.msgBlanqueo(editData['author'], preferences['site'], editData['pageTitle'], editData['diff'], controlvand[editData['author']]['avisos'])
			if re.search(ur'(?i)test', editData['type']):
				avbotmsg.msgPrueba(editData['author'], preferences['site'], editData['pageTitle'], editData['diff'], controlvand[editData['author']]['avisos'])
			if re.search(ur'(?i)vandalism', editData['type']):
				avbotmsg.msgVandalismo(editData['author'], preferences['site'], editData['pageTitle'], editData['diff'], controlvand[editData['author']]['avisos'])
			
			#guardamos log
			log=open('/home/emijrp/logs/avbot/%s.txt' % datetime.date.today(), 'a')
			logentry=u'\n%s\nArtículo: [[%s]]\nFecha: %s\nPuntuación: %d\nExpresiones regulares:\n%s\n%s' % ('-'*100, editData['pageTitle'], datetime.datetime.today(), editData['score'], editData['details'], '-'*100)
			log.write(logentry.encode('utf-8'))
			log.close()
			
			#avisamos en WP:VEC
			if len(controlvand[editData['author']].items())==4:
				avbotmsg.msgVandalismoEnCurso(controlvand[editData['author']], editData['author'], userClass, preferences['site'])
			
			return True, controlvand, statsDic, editData
		c+=1
	return False, controlvand, statsDic, editData

def isBlanking(preferences, editData, userClass, patterns, controlvand, statsDic):
	editData['score']=0
	regexlist=[]
	reverted=False
	
	if editData['lenOld']>=1000 and editData['lenNew']<editData['lenOld']/7 and not re.search(patterns['blanqueos'], editData['newText']): # 1/7 es un buen numero?
		editData['type']='blanking'
		editData['score']=-(editData['lenNew']+1) #la puntuacion de los blanqueos es la nueva longitud + 1, negada, para evitar el -0
		editData['details']=u''
		#añadimos al control de vandalismos
		if controlvand.has_key(editData['author']):
			controlvand[editData['author']][editData['diff']]=[editData['pageTitle'], editData['score'], regexlist] #metemos regexlist que es una lista vacia, para mantener consistencia con is_Vandalism()
		else:
			controlvand[editData['author']]={'avisos': 0, editData['diff']: [editData['pageTitle'], editData['score'], regexlist]}
		
		#revertimos todas las ediciones del menda
		[reverted, controlvand, statsDic, editData]=revertAllEditsByUser(editData, preferences, controlvand, userClass, statsDic)
		
	return reverted, controlvand, statsDic, editData

def isSectionBlanking(namespace, pageTitle, author, userClass, authorEditsNum, newbie, data, controlvand, diff, oldid, site, nickdelbot, stats, p, oldText, pageHistory, currentYear):
	#data contiene el diff sin limpiar
	score=0
	regexlist=[]
	
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
					p.put(oldText, u'BOT - Blanqueo de sección de [[Special:Contributions/%s|%s]], revirtiendo hasta la edición %s de [[User:%s|%s]]. ¿[[User:AVBOT/Errores|Hubo un error]]?' % (author, author, str(oldid), i[2], i[2]))
					
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
					p.put(oldText, u'BOT - Vandalismo de sección de [[Special:Contributions/%s|%s]], revirtiendo hasta la edición %s de [[User:%s|%s]]. ¿[[User:AVBOT/Errores|Hubo un error]]?' % (author, author, str(oldid), i[2], i[2]))
					
					#avisamos al usuario
					controlvand[author]['avisos']+=1
					avbotmsg.msgVandalismo(author, site, pageTitle, diff, controlvand[author]['avisos'])
					
					#avisamos en WP:VEC
					if len(controlvand[author].items())==4:
						avbotmsg.msgVandalismoEnCurso(controlvand[author], author, userClass, site)
					
					return True, controlvand, stats
				c+=1
	
	return False, controlvand, stats

def isVandalism(preferences, editData, vandalismos, cleandata, userClass, patterns, controlvand, statsDic):
	editData['score']=0
	regexlist=[]
	reverted=False
	type='test'
	editData['type']=u''
	editData['details']=u''
	
	for k, v in vandalismos.items():
		m=v['compiled'].finditer(cleandata)
		added=False #para que no se desborde el log
		for i in m:
			if v['type']=='V':
				type='vandalism'
			editData['score']+=v['score']
			regexlist.append(k)
			if not added:
				editData['details']+=u'%s\n' % (k)
				added=True
		
	if editData['score']<0 and ((editData['score']>-5 and len(cleandata)<editData['score']*-150) or editData['score']<-4): #en fase de pruebas, densidad len(data)<score*-100
		editData['type']=type
		
		#añadimos al control de vandalismos
		if controlvand.has_key(editData['author']):
			controlvand[editData['author']][editData['diff']]=[editData['pageTitle'], editData['score'], regexlist]
		else:
			controlvand[editData['author']]={'avisos': 0, editData['diff']: [editData['pageTitle'], editData['score'], regexlist]}
		
		#revertimos todas las ediciones del menda
		[reverted, controlvand, statsDic, editData]=revertAllEditsByUser(editData, preferences, controlvand, userClass, statsDic)
		
	return reverted, controlvand, statsDic, editData

def isShockingContent(namespace, pageTitle, author, userClass, authorEditsNum, newbie, imageneschocantes, cleandata, controlvand, p, pageHistory, diff, oldid, site, nickdelbot, oldText, stats, currentYear):
	if imageneschocantes['exceptions'].count(pageTitle)==0:
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
						p.put(oldText, u'BOT - Contenido chocante de [[Special:Contributions/%s|%s]], revirtiendo hasta la edición %s de [[User:%s|%s]]. ¿[[User:AVBOT/Errores|Hubo un error]]?' % (author, author, str(oldid), i[2], i[2]))
						
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
			p.put(oldText, u'BOT - Prueba de [[Special:Contributions/%s|%s]], revirtiendo hasta la edición %s de [[User:%s|%s]]. ¿[[User:AVBOT/Errores|Hubo un error]]?' % (author, author, str(pageHistory[1][0]), pageHistory[1][2], pageHistory[1][2]))
			
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
					p.put(oldText, u'BOT - %s en la edición de [[Special:Contributions/%s|%s]], revirtiendo hasta la edición %s de [[User:%s|%s]]. ¿[[User:AVBOT/Errores|Hubo un error]]?' % (motivo, author, author, str(oldid), i[2], i[2]))
					
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
