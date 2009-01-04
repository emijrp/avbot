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

## @package avbotanalysis
# Module for detect vandalisms, blanking, testing edits, new pages analysis

import re, wikipedia, datetime
import random

# AVBOT modules
import avbotglobals
import avbotload
import avbotsave
import avbotmsg
import avbotcomb

def sameOldid(editData):
	"""  """
	
	#return id, p.getOldVersion(id) #mientras averiguo lo de abajo
	
	#este metodo falla? http://es.wikipedia.org/w/index.php?title=Usuario:AVBOT/Errores&diff=prev&oldid=21309979
	if editData['oldid']!=editData['stableid']:
		editData['stableText']=editData['page'].getOldVersion(editData['stableid'])
		return editData
	else:
		editData['stableText']=editData['oldText']
		return editData

def isSameVandalism(regexlistold, regexlistnew):
	"""  """
	
	if len(regexlistold)!=len(regexlistnew):
		return False
	else:
		for r in regexlistold:
			if regexlistold.count(r)!=regexlistnew.count(r):
				return False
	return True

def incrementaStats(type):
	""" Increase stats variables """
	
	type2=type
	if re.search(ur'(?i)blanking', type):
		type2='BL'
	if re.search(ur'(?i)test', type):
		type2='P'
	if re.search(ur'(?i)vandalism', type):
		type2='V'
	
	avbotglobals.statsDic[2][type2]+=1
	avbotglobals.statsDic[12][type2]+=1
	avbotglobals.statsDic[24][type2]+=1

def watch(editData, userData):
	""" Check if it may watch and analysis edit in editData """
	
	if (editData['namespace'] in [0, 4, 10, 12, 14, 100, 102, 104] or (editData['namespace']==2 and not re.search(ur'\/', editData['pageTitle']) and not re.search(ur'(?i)%s' % re.sub('_', ' ', editData['author']), re.sub('_', ' ', editData['pageTitle'])))):
		if editData['userClass']=='anon' or (editData['userClass']=='reg' and userData['edits'][editData['author']]<=avbotglobals.preferences['newbie']):
			return True
	return False

def isRubbish(editData, userData):
	""" Check if the new article is useless """
	
	destruir=False
	motive=u'Otros'
	score=0
	
	if editData['userClass']=='anon' or (editData['userClass']=='reg' and userData['edits'][editData['author']]<=avbotglobals.preferences['newbie']):
		if (editData['namespace']==0) and not editData['page'].isRedirectPage() and not editData['page'].isDisambig():
			if not re.search(ur'(?i)\{\{|redirect', editData['newText']):
				for k, v in avbotglobals.vandalRegexps.items():
					m=v['compiled'].finditer(editData['newText'])
					for i in m:
						score+=v['score']
				
				if score<0 and ((score>-5 and len(editData['newText'])<score*-150) or score<-4): #igualar a  densidad de isVandalism()?
					destruir=True
					motive=u'Vandalismo'
				if len(editData['newText'])<=75 and not destruir:
					if not re.search(ur'\[', editData['newText']):
						destruir=True
						motive=u'Demasiado corto'
		if destruir:
			incrementaStats('D')
			editData['page'].put(u'{{RobotDestruir|%s|%s}}\n%s' % (editData['author'], motive, editData['newText']), u'Marcando para destruir. Motivo: %s. Página creada por [[User:%s|%s]] ([[User talk:%s|disc]] · [[Special:Contributions/%s|cont]])' % (motive, editData['author'], editData['author'], editData['author'], editData['author']))
			return True, motive
	return False, motive

def improveNewArticle(editData):
	""" Make some changes in the new article to improve it """
	
	newText=editData['page'].get()
	if (editData['namespace']==0) and not editData['page'].isRedirectPage() and not editData['page'].isDisambig():
		if not re.search(ur'(?i)\{\{ *(destruir|plagio|copyvio)|redirect', newText): #descarta demasiado? destruir|plagio|copyvio
			if len(newText)>=500:
				resumen=u''
				newnewText=u''
				if not editData['page'].interwiki():
					try:
						[newnewText, resumen]=avbotcomb.magicInterwiki(editData['page'], resumen, 'en')
					except:
						pass
				[newnewText, resumen]=avbotcomb.vtee(newnewText, resumen)
				#[newnewText, resumen]=avbotcomb.cosmetic(newnewText, resumen)
				if len(newnewText)>len(newText):
					editData['page'].put(newnewText, u'BOT - Aplicando %s... al artículo recién creado' % resumen)
					return True, resumen
	return False, u''

def revertAllEditsByUser(editData, userClass, regexlist):
	""" Revert all edits in a same article by a same author """
	
	#añadimos al control de vandalismos
	if avbotglobals.vandalControl.has_key(editData['author']):
		avbotglobals.vandalControl[editData['author']][editData['diff']]=[editData['pageTitle'], editData['score'], regexlist]
	else:
		avbotglobals.vandalControl[editData['author']]={'avisos': 0, editData['diff']: [editData['pageTitle'], editData['score'], regexlist]}
	
	c=0
	for i in editData['pageHistory']:
		if i[2]!=editData['author']: 
			if i[2]==avbotglobals.preferences['botNick']:#evitar que el bot entre en guerras de ediciones, ni aunque la puntuacion sea muy baja
				if re.search(ur'(?i)blanking', editData['type']):
					#para blanqueos no comprobamos si tiene la misma lista de regex (regexlist) que el anterior blanqueo, sino cual fue la logintud que tenia el texto final del blanqueo anterior
					if len(editData['pageHistory'])-1>=c+1 and avbotglobals.vandalControl[editData['author']].has_key(editData['pageHistory'][c+1][0]) and avbotglobals.vandalControl[editData['author']][editData['pageHistory'][c+1][0]][1]==editData['score']: #pageHistory[c+1][0] es la id de la edicion anterior a i[0]
						#evitamos revertir dos veces el mismo blanqueo, misma puntuacion
						break
				if re.search(ur'(?i)vandalism', editData['type']):
					regexlist=avbotglobals.vandalControl[editData['author']][editData['diff']][2]
					if len(editData['pageHistory'])-1>=c+1 and avbotglobals.vandalControl[editData['author']].has_key(editData['pageHistory'][c+1][0]) and isSameVandalism(avbotglobals.vandalControl[editData['author']][editData['pageHistory'][c+1][0]][2], regexlist): #pageHistory[c+1][0] es la id de la edicion anterior a i[0]
						#evitamos revertir dos veces el mismo vandalismo, misma puntuacion, excepto si es muy baja
						break
			
			editData['stableid']=i[0]
			editData['stableAuthor']=i[2]
			editData=sameOldid(editData)
			
			incrementaStats(editData['type'])
			
			#restauramos version estable del articulo
			editData['page'].put(editData['stableText'], avbotcomb.resumeTranslator(editData))
			
			#avisamos al usuario
			avbotglobals.vandalControl[editData['author']]['avisos']+=1
			if re.search(ur'(?i)blanking', editData['type']):
				avbotmsg.msgBlanqueo(editData['author'], editData['pageTitle'], editData['diff'], avbotglobals.vandalControl[editData['author']]['avisos'])
			if re.search(ur'(?i)test', editData['type']):
				avbotmsg.msgPrueba(editData['author'], editData['pageTitle'], editData['diff'], avbotglobals.vandalControl[editData['author']]['avisos'])
			if re.search(ur'(?i)vandalism', editData['type']):
				avbotmsg.msgVandalismo(editData['author'], editData['pageTitle'], editData['diff'], avbotglobals.vandalControl[editData['author']]['avisos'])
			
			#guardamos log
			log=open('/home/emijrp/logs/avbot/%s.txt' % datetime.date.today(), 'a')
			logentry=u'\n%s\nArtículo: [[%s]]\nFecha: %s\nPuntuación: %d\nExpresiones regulares:\n%s\n%s' % ('-'*100, editData['pageTitle'], datetime.datetime.today(), editData['score'], editData['details'], '-'*100)
			log.write(logentry.encode('utf-8'))
			log.close()
			
			#avisamos en WP:VEC
			if len(avbotglobals.vandalControl[editData['author']].items())==4:
				avbotmsg.msgVandalismoEnCurso(avbotglobals.vandalControl[editData['author']], editData['author'], userClass)
			
			return True, editData
		c+=1
	return False, editData

def isBlanking(editData, userClass):
	""" Checks if an edit is a blanking one """
	
	editData['score']=0
	regexlist=[]
	reverted=False
	
	if editData['lenOld']>=1000 and editData['lenNew']<=500 and editData['lenNew']<editData['lenOld']/7 and not re.search(avbotglobals.parserRegexps['blanqueos'], editData['newText']): # 1/7 es un buen numero?
		editData['type']='blanking'
		editData['score']=-(editData['lenNew']+1) #la puntuacion de los blanqueos es la nueva longitud + 1, negada, para evitar el -0
		editData['details']=u''
		
		#revertimos todas las ediciones del menda
		[reverted, editData]=revertAllEditsByUser(editData, userClass, regexlist)
		
	return reverted, editData

def isVandalism(editData, cleandata, userClass):
	""" Checks if an edit is a vandalism one """
	
	editData['score']=0
	regexlist=[]
	reverted=False
	type='test'
	editData['type']=u''
	editData['details']=u''
	
	for k, v in avbotglobals.vandalRegexps.items():
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
		
		#revertimos todas las ediciones del menda
		[reverted, editData]=revertAllEditsByUser(editData, userClass, regexlist)
		
	return reverted, editData

def isShockingContent(namespace, pageTitle, author, userClass, userData, imageneschocantes, cleandata, p, pageHistory, diff, oldid, site, oldText, currentYear):
	""" Checks if user has introduced a  shocking image in a bad place """
	
	if imageneschocantes['exceptions'].count(pageTitle)==0:
		for filename, compiled in imageneschocantes['images'].items():
			m=re.findall(compiled, cleandata)
			if m: #reveritmos y salimos
				#añadimos al control de vandalismos
				if avbotglobals.vandalControl.has_key(author):
					avbotglobals.vandalControl[author][diff]=[pageTitle, -9999, [filename]]
				else:
					avbotglobals.vandalControl[author]={'avisos': 0, diff: [pageTitle, -9999, [filename]]}
				
				#revertimos todas las ediciones del menda
				c=0
				for i in pageHistory:
					if i[2]!=author: 
						if i[2]==avbotglobals.preferences['botNick']:#evitar que el bot entre en guerras de ediciones
							if len(pageHistory)-1>=c+1 and avbotglobals.vandalControl[author].has_key(pageHistory[c+1][0]) and isSameVandalism(avbotglobals.vandalControl[author][pageHistory[c+1][0]][2], [filename]): #pageHistory[c+1][0] es la id de la edicion anterior a i[0]
								#evitamos revertir dos veces el mismo vandalismo, misma puntuacion
								break
						[oldid, oldText]=sameOldid(oldid, i[0], oldText, p)
						incrementaStats('V')
						p.put(oldText, u'BOT - Contenido chocante de [[Special:Contributions/%s|%s]], revirtiendo hasta la edición %s de [[User:%s|%s]]. ¿[[User:AVBOT/Errores|Hubo un error]]?' % (author, author, str(oldid), i[2], i[2]))
						
						#avisamos al usuario
						avbotglobals.vandalControl[author]['avisos']+=1
						avbotmsg.msgContenidoChocante(author, site, pageTitle, diff, avbotglobals.vandalControl[author]['avisos'])
						
						#avisamos en WP:VEC
						if len(avbotglobals.vandalControl[author].items())==4:
							avbotmsg.msgVandalismoEnCurso(avbotglobals.vandalControl[author], author, userClass, site)
						
						return True
					c+=1
	return False


def antiBirthday(pageTitle, userClass, userData, newbie, namespace, oldText, newText, cleandata, site, pageHistory, diff, nickdelbot, author, oldid, p, currentYear):
	if re.search(ur'(?m)^\d{1,2} de (enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)$', pageTitle) and (userClass=='anon' or (userClass=='reg' and userData['edits'][editData['author']]<=newbie)) and namespace==0:
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
			if avbotglobals.vandalControl.has_key(author):
				avbotglobals.vandalControl[author][diff]=[pageTitle, score, regexlist]
			else:
				avbotglobals.vandalControl[author]={'avisos': 0, diff: [pageTitle, score, regexlist]}
			
			#mismo codigo que en vandalismos
			#wikipedia.output(u'intenta restaurar')
			for i in pageHistory:
				if i[2]==nickdelbot: #evitar que el bot entre en guerras de ediciones
					break
				if i[2]!=author:
					[oldid, oldText]=sameOldid(oldid, i[0], oldText, p)
					incrementaStats('V')
					p.put(oldText, u'BOT - %s en la edición de [[Special:Contributions/%s|%s]], revirtiendo hasta la edición %s de [[User:%s|%s]]. ¿[[User:AVBOT/Errores|Hubo un error]]?' % (motivo, author, author, str(oldid), i[2], i[2]))
					
					#avisamos al usuario
					avbotglobals.vandalControl[author]['avisos']+=1
					if re.search(ur'(?i)irrelevante', motivo):
						avbotmsg.msgEnlaceIrrelevante(author, site, pageTitle, diff, avbotglobals.vandalControl[author]['avisos'])
					elif re.search(ur'(?i)imposible', motivo):
						avbotmsg.msgFechaImposible(author, site, pageTitle, diff, avbotglobals.vandalControl[author]['avisos'])
					
					#avisamos en WP:VEC
					if len(avbotglobals.vandalControl[author].items())==4:
						avbotmsg.msgVandalismoEnCurso(avbotglobals.vandalControl[author], author, userClass, site)
					
					return True, motivo
	return False, u''

def newArticleAnalysis(editData, userData):
	editData['newText']=editData['page'].get()
	editData['lenNew']=len(editData['newText'])
	
	[done, motive]=isRubbish(editData, userData)
	
	if done:
		wikipedia.output(u'\03{lightred}Alert!: Putting destroy template in [[%s]]. Motive: %s\03{default}' % (editData['pageTitle'], motive))
		return
	
	[done, resume]=improveNewArticle(editData)
	if done:
		wikipedia.output(u'\03{lightred}Alert!: Aplicando %s... a [[%s]]\03{default}' % (resume, editData['pageTitle']))
		return
		
	return

def cleandiff(pageTitle, data):
	""" Clean downloaded diff page """
	
	#TODO
	#evitar que diffdelete y diffaddedline coincidan
	#http://es.wikipedia.org/w/index.php?title=Lenguaje_ensamblador&diff=prev&oldid=16735402
	
	clean=u';;'
	
	trozos=data.split('<td class="diff-addedline"><div>')[1:]

	for trozo in trozos:
		trozo=trozo.split('</div></td>')[0]
		#if re.search(ur'<span class="diffchange">', trozo): #estilo antiguo
		if re.search(avbotglobals.parserRegexps['diffstylebegin'], trozo):
			#m=re.compile(ur'<span class="diffchange">([^<]*?)</span>').finditer(trozo) #antiguo estilo
			m=avbotglobals.parserRegexps['diffstyleend'].finditer(trozo) #diff punteados ¬¬'
			for i in m:
				clean+=u';;%s;;' % i.group(2) #<------- cuidado 2 por el diff style nuevo
		else:
			if not re.search(ur'<', trozo): #necesario para descartar el/los ultimos trozos de contexto
				clean+=u';;%s;;' % trozo
	
	return re.sub(ur'[\n\r]', ur';;', clean)

def editAnalysis(userData,editData):
	""" Checks edit to search vandalisms, blanking, tests, etc """
	
	global imageneschocantes
	global currentYear
	
	#Getting page object for this edit
	editData['page']=wikipedia.Page(avbotglobals.preferences['site'], editData['pageTitle'])
	if editData['page'].exists():
		editData['pageTitle']=editData['page'].title()
		editData['namespace']=editData['page'].namespace()
		
		if editData['page'].isRedirectPage(): #Do not analysis redirect pages
			return #Exit
		else:
			nm=u''
			if editData['new']:
				nm+=u'\03{lightred}N\03{default}'
			if editData['minor']:
				nm+=u'\03{lightred}m\03{default}'
			if nm:
				nm+=u' '
			
			if editData['userClass']=='anon':
				wikipedia.output(u'[%s] %s[[%s]] {\03{%s}%s\03{default}}' % (avbotcomb.getTime(), nm, editData['pageTitle'], avbotglobals.preferences['colors'][editData['userClass']], editData['author']))
			else:
				if userData['edits'].has_key(editData['author']):
					wikipedia.output(u'[%s] %s[[%s]] {\03{%s}%s\03{default}, %s ed.}' % (avbotcomb.getTime(), nm, editData['pageTitle'], avbotglobals.preferences['colors'][editData['userClass']], editData['author'], userData['edits'][editData['author']]))
					if userData['edits'][editData['author']]>avbotglobals.preferences['newbie']:
						return #Exit
				else:
					wikipedia.output(u'Ha habido un error con el número de ediciones de [[User:%s]]' % editData['author'])
			
			# Must be analysed?
			if not watch(editData, userData):
				wikipedia.output(u'[[%s]] no debe ser analizada' % editData['pageTitle'])
				return #Exit
			
			#Avoid analysis of excluded pages
			if avbotglobals.excludedPages.has_key(editData['pageTitle']):
				wikipedia.output(u'[[%s]] está en la lista de exclusión' % editData['pageTitle'])
				return #Exit
			
			# Avoid to check our edits
			if editData['author'] == avbotglobals.preferences['botNick']: 
				return #Exit
			
			# New pages analysis
			if editData['new'] and avbotglobals.preferences['language']=='es':
				newArticleAnalysis(editData, userData)
				return
			
			# To get history
			editData['oldText']=editData['newText']=u''
			try:
				editData['pageHistory'] = editData['page'].getVersionHistory(revCount=10) #To avoid bot edit wars
				editData['oldText']     = editData['page'].getOldVersion(editData['page'].previousRevision()) #Previous text
				editData['newText']     = editData['page'].get() #Current text
			except:
				return #No previous text? New? Exit
			
			editData['lenOld']  = len(editData['oldText'])
			editData['lenNew']  = len(editData['newText'])
			editData['lenDiff'] = editData['lenNew']-editData['lenOld']
			
			if re.search(avbotglobals.parserRegexps['destruir'], editData['newText']): #Proposed to delete? Skip
				wikipedia.output(u'Alguien ha marcado [[%s]] para destruir. Saltamos.' % editData['pageTitle'])
				return
			
			if re.search(avbotglobals.parserRegexps['conflictivos'], editData['newText']): #Avoid to check false positives pages
				wikipedia.output(u'[[%s]] es un artículo conflictivo, no lo analizamos' % editData['pageTitle'])
				return
			
			try: #Try to catch diff
				data=avbotglobals.preferences['site'].getUrl('/w/index.php?diff=%s&oldid=%s&diffonly=1' % (editData['diff'], editData['oldid']))
				data=data.split('<!-- start content -->')[1]
				data=data.split('<!-- end content -->')[0] #No change
			except:
				return #No diff, exit
			
			cleandata=cleandiff(editData['pageTitle'], data) #To clean diff text
			
			#Vandalism analysis
			#1) Blanking all
			
			[reverted, editData]=isBlanking(editData, editData['userClass'])
			
			if reverted:
				wikipedia.output(u'%s\n\03{lightred}Alert!: Possible %s edit by %s in [[%s]]\nDetalles:\n%s\n%s\03{default}%s' % ('-'*50, editData['type'], editData['author'], editData['pageTitle'], editData['score'], editData['details'], '-'*50))
				return
			
			#deteccion vandalismos
			#
			#llamo a cleandiff, cuando isBlanking este unificado, poner data=cleandiff(pageTitle, data) arriba
			#unificar el autoSign, controlspam y todas las de este modulo tambien
			
			[reverted, editData]=isVandalism(editData, cleandata, editData['userClass'])
			if reverted: 
				wikipedia.output(u'%s\n\03{lightred}Alert!: %s by %s in [[%s]]\nDetalles:\n%s\n%s\03{default}%s' % ('-'*50, editData['type'], editData['author'], editData['pageTitle'], editData['score'], editData['details'], '-'*50))
				return
			
			"""
			#5) Shocking images
			[done]=isShockingContent(namespace, pageTitle, editData['author'], editData['userClass'], userData['edits'][editData['author']], imageneschocantes, cleandata, p, pageHistory, diff, oldid, site, oldText, currentYear)
			if done: 
				wikipedia.output(u'\03{lightred}Alerta: Posible imagen chocante de %s en [[%s]]\03{default}' % (editData['author'], editData['pageTitle']))
				return
			
			#7) Anti-birthday protection
			[done, motivo]=antiBirthday(pageTitle, editData['userClass'], userData['edits'][editData['author']], avbotglobals.preferences['newbie'], namespace, oldText, newText, cleandata, site, pageHistory, diff, avbotglobals.preferences['botNick'], editData['author'], oldid, p, currentYear)
			if done:
				wikipedia.output(u'\03{lightred}Alerta: %s en [[%s]]\03{default}' % (motivo, editData['pageTitle']))
				return
			"""
	else:
		wikipedia.output(u'[[%s]] has been deleted' % editData['pageTitle'])
