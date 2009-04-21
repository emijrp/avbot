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
# Module for detect vandalisms, blanking, testing edits, new pages analysis\n
# Módulo para detectar vandalismos, blanqueos, ediciones de prueba, y analizar páginas nuevas

import re, wikipedia, datetime
import random

# AVBOT modules
import avbotglobals
import avbotload
import avbotsave
import avbotmsg
import avbotcomb

def sameOldid(editData):
	""" Are both the same oldid? """
	""" ¿Es el mismo oldid? """
	if editData['oldid']!=editData['stableid']:
		editData['stableText']=editData['page'].getOldVersion(editData['stableid'])
		return editData
	else:
		#editData['stableText']=editData['oldText'] #no sé porqué pero a veces oldtext almacena el primer vandalismo de una serie de vandalismos en cascada http://es.wikipedia.org/w/index.php?title=Dedo&limit=6&action=history
		editData['stableText']=editData['page'].getOldVersion(editData['stableid'])
		return editData

def isSameVandalism(regexlistold, regexlistnew):
	""" Is same vandalism? """
	""" ¿Se trata del mismo vandalismo? """
	
	if len(regexlistold)!=len(regexlistnew):
		return False
	else:
		for r in regexlistold:
			if regexlistold.count(r)!=regexlistnew.count(r):
				return False
	return True

def updateStats(type):
	""" Incrementa variables de estadísticas """
	""" Increase stats variables """
	
	avbotglobals.statsDic[2][type]+=1
	avbotglobals.statsDic[12][type]+=1
	avbotglobals.statsDic[24][type]+=1

def watch(editData):
	""" ¿Debe ser analizada esta página? """
	""" Check if it may watch and analysis edit in editData """
	
	if (editData['namespace'] in [0, 4, 10, 12, 14, 100, 102, 104] or (editData['namespace']==2 and not re.search(ur'\/', editData['pageTitle']) and not re.search(ur'(?i)%s' % re.sub('_', ' ', editData['author']), re.sub('_', ' ', editData['pageTitle'])))):
		if editData['userClass']=='anon' or (editData['userClass']=='reg' and avbotglobals.userData['edits'][editData['author']]<=avbotglobals.preferences['newbie']):
			return True
	return False

def isRubbish(editData):
	""" Analiza si se trata de un artículo nuevo inservible """
	""" Check if the new article is useless """
	
	destruir=False
	motive=u'Otros'
	score=0
	
	if editData['userClass']=='anon' or (editData['userClass']=='reg' and avbotglobals.userData['edits'][editData['author']]<=avbotglobals.preferences['newbie']):
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
			updateStats('d')
			editData['page'].put(u'{{RobotDestruir|%s|%s}}\n%s' % (editData['author'], motive, editData['newText']), u'Marcando para destruir. Motivo: %s. Página creada por [[User:%s|%s]] ([[User talk:%s|disc]] · [[Special:Contributions/%s|cont]])' % (motive, editData['author'], editData['author'], editData['author'], editData['author']))
			return True, motive
	return False, motive

def improveNewArticle(editData):
	""" Intenta mejorar el artículo según unos consejos básicos del manual de estilo """
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
				if len(newnewText)>len(newText):
					editData['page'].put(newnewText, u'BOT - Aplicando %s... al artículo recién creado' % resumen)
					return True, resumen
	return False, u''

def revertAllEditsByUser(editData, userClass, regexplist):
	""" Revierte todas las ediciones de un usuario en un mismo artículo """
	""" Revert all edits in a same article by a same author """
	
	#añadimos al control de vandalismos
	if avbotglobals.vandalControl.has_key(editData['author']):
		avbotglobals.vandalControl[editData['author']][editData['diff']]=[editData['pageTitle'], editData['score'], regexplist]
	else:
		avbotglobals.vandalControl[editData['author']]={'avisos': 0, editData['diff']: [editData['pageTitle'], editData['score'], regexplist]}
	
	c=0
	for i in editData['pageHistory']:
		if i[2]!=editData['author']: 
			if i[2]==avbotglobals.preferences['botNick']:#evitar que el bot entre en guerras de ediciones, ni aunque la puntuacion sea muy baja, CUIDADO CON LOS CLONES!!!
				#excepto si es un blanqueo distinto del anterior
				if editData['type']=='bl':
					#para blanqueos no comprobamos si tiene la misma lista de regexp (regexplist) que el anterior blanqueo, sino cual fue la logintud que tenia el texto final del blanqueo anterior
					if len(editData['pageHistory'])-1>=c+1:
						if avbotglobals.vandalControl[editData['author']].has_key(editData['pageHistory'][c+1][0]):
							if avbotglobals.vandalControl[editData['author']][editData['pageHistory'][c+1][0]][1]==editData['score']: #pageHistory[c+1][0] es la id de la edicion anterior a i[0]
								#evitamos revertir dos veces el mismo blanqueo, misma puntuacion
								break
				#excepto si es un vandalismo con otras palabras
				if editData['type']=='v' or editData['type']=='p':
					regexplist=avbotglobals.vandalControl[editData['author']][editData['diff']][2]
					if len(editData['pageHistory'])-1>=c+1:
						if avbotglobals.vandalControl[editData['author']].has_key(editData['pageHistory'][c+1][0]):
							if isSameVandalism(avbotglobals.vandalControl[editData['author']][editData['pageHistory'][c+1][0]][2], regexplist): #pageHistory[c+1][0] es la id de la edicion anterior a i[0]
								#evitamos revertir dos veces el mismo vandalismo, misma puntuacion, excepto si es muy baja
								break
			
			editData['stableid']=i[0]
			editData['stableAuthor']=i[2]
			editData=sameOldid(editData)
			
			updateStats(editData['type'])
			
			#restauramos version estable del articulo
			editData['page'].put(editData['stableText'], avbotcomb.resumeTranslator(editData))
			
			#avisamos al usuario
			avbotglobals.vandalControl[editData['author']]['avisos']+=1
			avbotmsg.sendMessage(editData['author'], editData['pageTitle'], editData['diff'], avbotglobals.vandalControl[editData['author']]['avisos'], editData['type'])
			
			#guardamos log
			log=open('%s%s.txt' % (avbotglobals.preferences['logsDirectory'], datetime.date.today()), 'a')
			logentry=u'\n%s\nArtículo: [[%s]]\nFecha: %s\nPuntuación: %d\nExpresiones regulares:\n%s\n%s' % ('-'*100, editData['pageTitle'], datetime.datetime.today(), editData['score'], editData['details'], '-'*100)
			log.write(logentry.encode('utf-8'))
			log.close()
			
			#avisamos en WP:VEC
			blockedInEnglishWikipedia=avbotcomb.checkBlockInEnglishWikipedia(editData)
			if len(avbotglobals.vandalControl[editData['author']].items())==4 or blockedInEnglishWikipedia[1]: #al tercer aviso o cuando es proxy
				#dentro de esta funcion se evita avisar mas de 1 vez
				avbotmsg.msgVandalismoEnCurso(avbotglobals.vandalControl[editData['author']], editData['author'], userClass, blockedInEnglishWikipedia)
			
			return True, editData
		c+=1
	return False, editData

def mustBeReverted(editData, cleandata, userClass):
	""" ¿Debe ser revertida la edición? ¿Es vandalismo, prueba de edición o blanqueo? """
	""" Checks if an edit is a vandalism, test or blanking edit """
	
	editData['score']=0
	regexplist=[]
	reverted=False
	
	#blanking edit?
	if editData['lenOld']>=1000 and editData['lenNew']<=500 and editData['lenNew']<editData['lenOld']/7 and not re.search(avbotglobals.parserRegexps['blanqueos'], editData['newText']): # 1/7 es un buen numero
		editData['type']='bl'
		editData['score']=-(editData['lenNew']+1) #la puntuacion de los blanqueos es la nueva longitud + 1, negada, para evitar el -0
		editData['details']=u''
		
		#revertimos todas las ediciones del usuario
		return revertAllEditsByUser(editData, userClass, regexplist)
	
	#vandalism or test edit?
	editData['type']='c' #dummie, contrapeso
	editData['details']=u''
	
	for k, v in avbotglobals.vandalRegexps.items():
		m=v['compiled'].finditer(cleandata)
		added=False #para que no se desborde el log
		for i in m:
			if avbotglobals.preferences['msg'][v['type']]['priority']>avbotglobals.preferences['msg'][editData['type']]['priority']:
				editData['type']=v['type']
			editData['score']+=v['score']
			regexplist.append(k)
			if not added:
				editData['details']+=u'%s\n' % (k)
				added=True
	
	if editData['score']<0 and ((editData['score']>-5 and len(cleandata)<editData['score']*-150) or editData['score']<-4): #densidad
		#revertimos todas las ediciones del usuario en esa página
		return revertAllEditsByUser(editData, userClass, regexplist)
	
	return reverted, editData

def newArticleAnalysis(editData):
	""" Análisis de artículos nuevos """
	""" New articles analysis """
	editData['newText']=editData['page'].get()
	editData['lenNew']=len(editData['newText'])
	
	[done, motive]=isRubbish(editData)
	
	if done:
		wikipedia.output(u'\03{lightred}Alert!: Putting destroy template in [[%s]]. Motive: %s\03{default}' % (editData['pageTitle'], motive))
		return
	
	[done, resume]=improveNewArticle(editData)
	if done:
		wikipedia.output(u'\03{lightred}Alert!: Aplicando %s... a [[%s]]\03{default}' % (resume, editData['pageTitle']))
		return
		
	return

def cleandiff(pageTitle, data):
	""" Extrae el texto que ha sido insertado en la edición """
	""" Clean downloaded diff page """
	
	marker=';;;'
	clean=marker
	
	trozos=data.split('<tr>')[2:] #el 1 contiene el numero de linea, nos lo saltamos
	for trozo in trozos:
		try:
			trozo=trozo.split('</tr>')[0] #no es que sea necesario pero...
			if re.search(ur'diff-context', trozo): #linea de contexto, nos la saltamos
				continue
			elif re.search(ur'diff-addedline', trozo):
				if re.search(ur'diff-deletedline', trozo): #sustitucion/añadido/eliminacion de algo, nos quedamos con lo de dentro del diffchange, dentro del diff-addedline
					trozo=((trozo.split('<td class="diff-addedline">')[1]).split('</td>'))[0]
					m=re.compile(ur'(<span class="diffchange">|<span class="diffchange diffchange-inline">|<ins class="diffchange diffchange-inline">)(?P<text>[^<]*?)</(ins|span)>').finditer(trozo)
					for i in m:
						clean+=u'%s%s%s' % (marker, i.group('text'), marker)
				else: #se trata de una linea nueva añadida, nos quedamos con lo de dentro del diff-addedline
					if re.search(ur'<td class="diff-addedline"><div>', trozo):
						trozo=((trozo.split('<td class="diff-addedline"><div>')[1]).split('</div></td>'))[0]
					else:
						trozo=((trozo.split('<td class="diff-addedline">')[1]).split('</td>'))[0]
					clean+=u'%s%s%s' % (marker, trozo, marker)
		except:
			wikipedia.output(u'ERROR: %s' % trozo)
	
	clean=re.sub(ur'[\n\r]', marker, clean)
	
	#if len(clean)<3000:
	#	wikipedia.output(clean)
	
	if clean==marker:
		clean=''
	return clean

def editAnalysis(editData):
	""" Lanzamiento de funciones de análisis previo descarte de páginas/ediciones que no deben ser analizadas """
	""" Checks edit to search vandalisms, blanking, tests, etc """
	
	#Getting page object for this edit
	editData['page']=wikipedia.Page(avbotglobals.preferences['site'], editData['pageTitle'])
	if editData['page'].exists():
		editData['pageTitle']=editData['page'].title()
		editData['namespace']=editData['page'].namespace()
		
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
			if avbotglobals.userData['edits'].has_key(editData['author']):
				wikipedia.output(u'[%s] %s[[%s]] {\03{%s}%s\03{default}, %s ed.}' % (avbotcomb.getTime(), nm, editData['pageTitle'], avbotglobals.preferences['colors'][editData['userClass']], editData['author'], avbotglobals.userData['edits'][editData['author']]))
				if avbotglobals.userData['edits'][editData['author']]>avbotglobals.preferences['newbie']:
					return #Exit
			else:
				wikipedia.output(u'Ha habido un error con el número de ediciones de [[User:%s]]' % editData['author'])
		
		if editData['page'].isRedirectPage(): #Do not analysis redirect pages
			return #Exit
		
		# Must be analysed?
		if not watch(editData):
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
			newArticleAnalysis(editData)
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
		
		cleandata=cleandiff(editData['pageTitle'], data) #To clean diff text and to extract inserted lines and words
		
		#Vandalism analysis
		[reverted, editData]=mustBeReverted(editData, cleandata, editData['userClass'])
		if reverted: 
			wikipedia.output(u'%s\n\03{lightred}Alert!: Possible %s by %s in [[%s]]\nDetails:\n%s\n%s\03{default}%s' % ('-'*50, avbotglobals.preferences['msg'][editData['type']]['meaning'].lower(), editData['author'], editData['pageTitle'], editData['score'], editData['details'], '-'*50))
			return
	else:
		wikipedia.output(u'[[%s]] has been deleted' % editData['pageTitle'])
