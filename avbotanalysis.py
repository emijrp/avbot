# -*- coding: utf-8 -*-

# AVBOT - Anti-Vandalism BOT for MediaWiki projects
# Copyright (C) 2008-2010 Emilio José Rodríguez Posada
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

import re
import datetime
import random
import time
import threading

""" pywikipediabot modules """
import wikipedia

""" AVBOT modules """
import avbotglobals
import avbotload
import avbotsave
import avbotmsg
import avbotcomb

class Diegus(threading.Thread):
	def __init__(self, page, fun, oldid, diff, revcount):
		threading.Thread.__init__(self)
		self.page=page
		self.fun=fun
		self.oldid=oldid
		self.diff=diff
		self.revcount=revcount
		self.oldText=""
		self.newText=""
		self.pageHistory=[]
		self.HTMLdiff=""
		
	def run(self):
		#print self.page.title(), self.fun
		if self.fun=='getOldVersionOldid':
			self.oldText = self.page.getOldVersion(self.oldid, get_redirect=True) #cogemos redirect si se tercia, y ya filtramos luego
			#print 'oldText', self.value, len(self.oldText)
		elif self.fun=='getOldVersionDiff':
			self.newText = self.page.getOldVersion(self.diff, get_redirect=True) #cogemos redirect si se tercia, y ya filtramos luego
			#print 'newText', self.value, len(self.newText)
		elif self.fun=='getVersionHistory':
			self.pageHistory = self.page.getVersionHistory(revCount=self.revcount)
		elif self.fun=='getUrl':
			self.HTMLDiff = avbotglobals.preferences['site'].getUrl('/w/index.php?diff=%s&oldid=%s&diffonly=1' % (self.diff, self.oldid))
	
	def getOldText(self):
		return self.oldText
	
	def getNewText(self):
		return self.newText
		
	def getPageHistory(self):
		return self.pageHistory
	
	def getHTMLDiff(self):
		return self.HTMLDiff
	

def sameOldid(editData):
	""" Are both the same oldid? """
	""" ¿Es el mismo oldid? """
	print editData['pageTitle'], '   oldid=', editData['oldid'], '    stableid=', editData['stableid']
	if editData['oldid']!=editData['stableid']:
		print 222
		editData['stableText']=editData['page'].getOldVersion(editData['stableid']) #costoso? pero no queda otra
	else:
		#editData['stableText']=editData['oldText'] #no sé porqué pero a veces oldtext almacena el primer vandalismo de una serie de vandalismos en cascada http://es.wikipedia.org/w/index.php?title=Dedo&offset=20090507213843&limit=10&action=history #fix fallaba esto realmente?
		print 333
		t1=time.time()
		editData['stableText']=editData['page'].getOldVersion(editData['stableid']) #costoso?
		print 4, editData['pageTitle'], time.time()-t1
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

	author=re.sub('_', ' ', editData['author'])
	pageTitle=re.sub('_', ' ', editData['pageTitle'])
	#cosas que no aparezcan en la lista de exclusiones pueden verse filtradas por este if, explicarlo en algún sitio? #fix
	if (editData['namespace'] in [0, 4, 10, 12, 14, 100, 102, 104] or (editData['namespace']==2 and not re.search(avbotglobals.parserRegexps['watch-1'], editData['pageTitle']) and not re.search(ur'(?i)%s' % author, pageTitle))): #este re.search no es costoso
		if editData['userClass']=='anon' or (editData['userClass']=='reg' and avbotglobals.userData['edits'][editData['author']]<=avbotglobals.preferences['newbie']):
			return True
	return False

def isRubbish(editData):
	""" Analiza si se trata de un artículo nuevo inservible """
	""" Check if the new article is useless """
	
	destruir=False
	motive=u'Otros'
	score=0
	
	if avbotglobals.preferences['language']=='es':
		if editData['userClass']=='anon' or (editData['userClass']=='reg' and avbotglobals.userData['edits'][editData['author']]<=avbotglobals.preferences['newbie']):#repetido ? #fix
			if (editData['namespace']==0) and not editData['page'].isRedirectPage() and not editData['page'].isDisambig():
				if not re.search(avbotglobals.parserRegexps['isrubbish-tl-red'], editData['newText']):
					for k, v in avbotglobals.vandalRegexps.items():
						m=v['compiled'].finditer(editData['newText'])
						for i in m:
							score+=v['score']
					
					if score<0 and ((score>-5 and len(editData['newText'])<score*-150) or score<-4): #igualar a  densidad de isVandalism()? #fix
						destruir=True
						motive=u'Vandalismo'
					if len(editData['newText'])<=75 and not destruir:
						if not re.search(avbotglobals.parserRegexps['isrubbish-link'], editData['newText']):
							destruir=True
							motive=u'Demasiado corto'
			if destruir:
				updateStats('d')
				if not avbotglobals.preferences['nosave']:
					if editData['page'].exists():
						editData['page'].put(u'{{RobotDestruir|%s|%s}}\n%s' % (editData['author'], motive, editData['newText']), u'Marcando para destruir. Motivo: %s. Página creada por [[User:%s|%s]] ([[User talk:%s|disc]] · [[Special:Contributions/%s|cont]])' % (motive, editData['author'], editData['author'], editData['author'], editData['author']))
					else:
						wikipedia.output(u'[[%s]] has been deleted' % editData['pageTitle'])
						return False, '' #Exit
				return True, motive
	return False, ''

def improveNewArticle(editData):
	""" Intenta mejorar el artículo según unos consejos básicos del manual de estilo """
	""" Make some changes in the new article to improve it """
	
	if avbotglobals.preferences['language']=='es':
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
						if not avbotglobals.preferences['nosave']:
							editData['page'].put(newnewText, u'BOT - Aplicando %s... al artículo recién creado' % resumen)
						return True, resumen
	return False, u''

def revertAllEditsByUser(editData, userClass, regexplist):
	""" Revierte todas las ediciones de un usuario en un mismo artículo """
	""" Revert all edits in a same article by a same author """
	
	#Add to vandalism control log
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
				elif editData['type']=='v' or editData['type']=='t' or editData['type']=='nn': #hace falta añadir las que no son BL para descartar C o entrará algún C alguna vez?
					regexplist=avbotglobals.vandalControl[editData['author']][editData['diff']][2]
					if len(editData['pageHistory'])-1>=c+1:
						if avbotglobals.vandalControl[editData['author']].has_key(editData['pageHistory'][c+1][0]):
							if isSameVandalism(avbotglobals.vandalControl[editData['author']][editData['pageHistory'][c+1][0]][2], regexplist): #pageHistory[c+1][0] es la id de la edicion anterior a i[0]
								#evitamos revertir dos veces el mismo vandalismo, misma puntuacion, ¿excepto si es muy baja?
								break
				elif editData['type']=='g': # if the sum is good, break and do not revert (a bit redundant, due to score will not be negative and not enter in this fun)
					break
			
			editData['stableid']=i[0]
			editData['stableAuthor']=i[2]
			editData=sameOldid(editData)
			
			updateStats(editData['type'])
			
			#Restore previous version of the page
			t1=time.time()
			if not avbotglobals.preferences['nosave']:
				if len(editData['pageHistory'])<avbotglobals.preferences['historyLength']: #es nueva? comprobamos antes de revertir, no vayamos a recrearla...
					if not editData['page'].exists():
						wikipedia.output(u'[[%s]] has been deleted' % editData['pageTitle'])
						return False, editData #Exit
				print "----> pageTitle", editData['pageTitle']
				print "----> obj page", editData['page'].title()
				editData['page']=wikipedia.Page(avbotglobals.preferences['site'], editData['pageTitle']) #por algún motivo pierde la "sesión" porqué? #fix 
				editData['page'].put(editData['stableText'], avbotcomb.resumeTranslator(editData), botflag=False, maxTries=1) #¡¡¡MANTENER BOTFLAG=FALSE!!! POR DEFECTO EN LA FUNCIÓN PUT DE WIKIPEDIA.PY ES TRUE, botflag=False, maxTries=1, 1 sólo intento y descartar, sin flag
			print 'put', time.time()-t1, editData['pageTitle']
			#wii=wikipedia.Page(wikipedia.Site('es', 'wikipedia'), u"User:AVBOT/Sandbox")
			#wii.put(editData['stableText'], "test", botflag=False, maxTries=1)
			
			#Send message to user
			avbotglobals.vandalControl[editData['author']]['avisos']+=1
			if not avbotglobals.preferences['nosave']:
				avbotmsg.sendMessage(editData['author'], editData['pageTitle'], editData['diff'], avbotglobals.vandalControl[editData['author']]['avisos'], editData['type'])
			
			#Save log for depuration purposes
			log=open('%s/%s.txt' % (avbotglobals.preferences['logsDirectory'], datetime.date.today()), 'a')
			logentry=u'\n%s\nPage: [[%s]]\nDate: %s\nPoints: %d\nRegular expressions:\n%s\n%s' % ('-'*100, editData['pageTitle'], datetime.datetime.today(), editData['score'], editData['details'], '-'*100)
			log.write(logentry.encode('utf-8'))
			log.close()
			
			#Send message to admins board
			if not avbotglobals.preferences['nosave']:
				blockedInEnglishWikipedia=avbotcomb.checkBlockInEnglishWikipedia(editData)
				if len(avbotglobals.vandalControl[editData['author']].items())==4 or blockedInEnglishWikipedia[1]: #al tercer aviso o cuando es proxy
					#Not send the message if vandals have been reported before
					avbotmsg.msgVandalismoEnCurso(avbotglobals.vandalControl[editData['author']], editData['author'], userClass, blockedInEnglishWikipedia)
			
			#Trial run?
			if avbotglobals.preferences['trial']:
				type=editData['type']
				msg=u"* %s: Possible [{{SERVER}}/w/index.php?diff=%s&oldid=%s %s] in [[%s]] by [[Special:Contributions/%s|%s]], reverting to [{{SERVER}}/w/index.php?oldid=%s %s] edit by [[User:%s|%s]]" % (datetime.datetime.now(), editData['diff'], editData['stableid'], avbotglobals.preferences['msg'][type]['meaning'], editData['pageTitle'], editData['author'], editData['author'], editData['stableid'], editData['stableid'], editData['stableAuthor'], editData['stableAuthor'])
				wiii=wikipedia.Page(avbotglobals.preferences['site'], u"User:%s/Trial" % (avbotglobals.preferences['botNick']), botflag=False, maxTries=1)
				wiii.put(u"%s\n%s" % (msg, wiii.get()), avbotcomb.resumeTranslator(editData))
			
			return True, editData
		c+=1
	return False, editData

def mustBeReverted(editData, cleandata, userClass):
	""" ¿Debe ser revertida la edición? ¿Es vandalismo, prueba de edición o blanqueo? """
	""" Checks if an edit is a vandalism, test or blanking edit """
	
	editData['score']=0
	#fix poner editData['type']='g' ?
	regexplist=[]
	reverted=False
	
	#inclusión de líneas cortas al final detrás de los iws http://es.wikipedia.org/w/index.php?title=La_vida_es_sue%C3%B1o&diff=35775982&oldid=35775819
	#al principio también http://es.wikipedia.org/w/index.php?title=Ingenier%C3%ADa_biom%C3%A9dica&diff=prev&oldid=35776392
	#junto a los interwikis [[es:Blabla]]isdfjisf sfdsf sdf
	#cuidado? los interwikis también los tocan IPs de otras wikis?
	#también entre párrafos o más propenso a falsos positivos? http://es.wikipedia.org/w/index.php?title=Termas_de_Caracalla&diff=prev&oldid=35776174
	oldTextSplit=editData['oldText'].splitlines()
	newTextSplit=editData['newText'].splitlines()
	if len(oldTextSplit)>10 and len(newTextSplit)>len(oldTextSplit): #que antes tuviera al menos 10 para evitar esbozos, redirecciones, desamb, ... propenso a errores
		equal=True
		c=0
		for line in oldTextSplit:
			if line!=newTextSplit[c]:
				equal=False
				break
			c+=1
		if equal:
			clines=len(newTextSplit)-len(oldTextSplit)
			cchars=0
			nocatsiws=True #hay ips que insertan iws o categorías (usuarios de otras wikis), cuidado con esto
			while c<len(newTextSplit):#recorremos las líneas nuevas y acumulamos cuantos caracteres ha insertado
				if re.search(avbotglobals.parserRegexps['catsiwslinkssec'], newTextSplit[c]):
					nocatsiws=False
					break
				cchars+=len(newTextSplit[c])
				c+=1
			#calculamos densidad
			#teniendo en cuenta que puede meter líneas en blanco http://es.wikipedia.org/w/index.php?title=La_vida_es_sue%C3%B1o&diff=35775982&oldid=35775819
			if nocatsiws and cchars/clines<50:
				editData['type']='t'
				editData['score']=-1 #poner algo proporcional como en los blanqueos?
				return revertAllEditsByUser(editData, userClass, regexplist) #Revert
		
	#Blanking edit?
	lenOld=editData['lenOld']
	lenNew=editData['lenNew']
	if lenNew<lenOld and not re.search(avbotglobals.parserRegexps['blanqueos'], editData['newText']): #Avoid articles converted into #REDIRECT [[...]] and other legitimate blankings
		percent=(lenOld-lenNew)/(lenOld/100.0)
		if (lenOld>=500 and lenOld<1000 and percent>=90) or \
			(lenOld>=1000 and lenOld<2500 and percent>=85) or \
			(lenOld>=2500 and lenOld<5000 and percent>=75) or \
			(lenOld>=5000 and lenOld<10000 and percent>=72.5) or \
			(lenOld>=10000 and lenOld<20000 and percent>=70) or \
			(lenOld>=20000 and percent>=65):
			editData['type']='bl'
			editData['score']=-(editData['lenNew']+1) #la puntuacion de los blanqueos es la nueva longitud + 1, negada, para evitar el -0
			editData['details']=u''
			
			return revertAllEditsByUser(editData, userClass, regexplist) #Revert
		"""
		if editData['lenOld']>=1000 and editData['lenNew']<=500 and editData['lenNew']<editData['lenOld']/7: # 1/7 es un buen numero, 85,7%
			editData['type']='bl'
			editData['score']=-(editData['lenNew']+1) #la puntuacion de los blanqueos es la nueva longitud + 1, negada, para evitar el -0
			editData['details']=u''
			
			return revertAllEditsByUser(editData, userClass, regexplist) #Revert
		"""
	#TODO: Blanking line like this, All glory to the hypnoto
	
	#Interwiki and categories blanking. Example: http://es.wikipedia.org/w/index.php?title=Reciclaje&diff=34127808&oldid=34116543
	oldCategoriesNumber=len(re.findall(avbotglobals.parserRegexps['categories'], editData['oldText']))
	newCategoriesNumber=len(re.findall(avbotglobals.parserRegexps['categories'], editData['newText']))
	oldInterwikisNumber=len(re.findall(avbotglobals.parserRegexps['interwikis'], editData['oldText']))
	newInterwikisNumber=len(re.findall(avbotglobals.parserRegexps['interwikis'], editData['newText']))
	
	if oldInterwikisNumber>=10 and newInterwikisNumber<=oldInterwikisNumber/2 and not re.search(avbotglobals.parserRegexps['blanqueos'], editData['newText']): #10 es un número conservador?
		editData['type']='bl'
		editData['score']=-(editData['lenNew']+1) #la puntuacion de los blanqueos es la nueva longitud + 1, negada, para evitar el -0
		editData['details']=u''
		
		return revertAllEditsByUser(editData, userClass, regexplist) #Revert
	
	#Vandalism or test edit?
	regexplist=[]
	editData['type']='' #dummie, contrapeso
	priority=99999999
	for type, msgprop in avbotglobals.preferences['msg'].items():
		if msgprop['priority']<priority:
			editData['type']=type
			priority=msgprop['priority']
	editData['details']=u''
	
	for k, v in avbotglobals.vandalRegexps.items(): #fix mirar si en la revisión anterior ya había tales palabras malsonantes? (evitamos que un copia/pega desplazado se considere como texto nuevo) no contar las positivas de la anterior
		m=v['compiled'].finditer(cleandata)
		added=False #Avoid duplicate entries in the log
		for i in m:
			if avbotglobals.preferences['msg'][v['type']]['priority']>avbotglobals.preferences['msg'][editData['type']]['priority']:
				#vandalism > test > contrapeso
				editData['type']=v['type']
			editData['score']+=v['score']
			regexplist.append(k)
			if not added:
				editData['details']+=u'%s\n' % (k)
				added=True
	
	threshold=-4 #lower points, automatically reverted
	density=150 #negative points allowed per length string
	if editData['score']<0 and ((editData['score']>=threshold and len(cleandata)<abs(editData['score']*density)) or editData['score']<threshold): 
		if avbotglobals.preferences['testmode']:
			return True, editData
		else:
			return revertAllEditsByUser(editData, userClass, regexplist) #Revert
	
	#Anti-birthday
	if re.search(avbotglobals.parserRegexps['anti-birthday-es'], editData['pageTitle']):
		if editData['namespace']==0:
			regexplist=[] # ¿Si la enviamos vacía al revertalledits funciona? o depende del editData['type']?
			enlaceexiste=False
			anyoactual=int(datetime.date.today().year)
			sections=editData['newText'].split("==")
			births=""
			deaths=""
			c=0
			for section in sections:
				if re.sub(ur"[ =]", ur"", section).lower()=="nacimientos" and len(sections)>c+1:
					births=sections[c+1]
				if re.sub(ur"[ =]", ur"", section).lower()=="fallecimientos" and len(sections)>c+1:
					deaths=sections[c+1]
				c+=1
			
			if births:
				m=re.compile(ur'(?i)\* *\[?\[?(?P<year>\d{4})\]?\]? *?[\:\-] *?[^\[]*?\[\[(?P<enlace>[^\|\]]+?)(\|[^\]]*?)?\]\]').finditer(cleandata)
				for i in m: #controlar si se ha metido mas de un cumpleaños?
					anyo=int(i.group("year"))
					enlace=i.group("enlace")
					wikipedia.output(u'---Efeméride rara en [[%s]]--->[[%s]] - [[%s]]' % (editData['pageTitle'], anyo, enlace))
					wii={} #por si quisieramos comprobar en otras wikis
					wii['es']=wikipedia.Page(avbotglobals.preferences['site'], u'%s' % enlace)
					try:
						if wii['es'].exists():
							enlaceexiste=True
					except:
						pass
				
					if enlaceexiste:
						wikipedia.output(u"El artículo al que apunta la efeméride sí existe  : )")
					else:
						anyoenlacecompiled=re.compile(ur'(?i)%d.*%s' % (anyo, enlace))
						if anyo>anyoactual: #poner anyos futuros en los acontecimientos es posible, pero no en births o deaths
							if re.search(anyoenlacecompiled, births) or re.search(anyoenlacecompiled, deaths): 
								editData['type']='nn'
								return revertAllEditsByUser(editData, userClass, regexplist) #Revert
								motivo=u'Fecha imposible (Año %d)' % anyo
								wikipedia.output(motivo)
				
						elif re.search(anyoenlacecompiled, births):
							if anyo>=anyoactual-20:
								#que chico mas precoz, comprobemos su relevancia
								wii['en']=wikipedia.Page(wikipedia.Site('en', 'wikipedia'), enlace)
								#wii['de']=wikipedia.Page(wikipedia.Site('de', 'wikipedia'), enlace)
								#wii['fr']=wikipedia.Page(wikipedia.Site('fr', 'wikipedia'), enlace)
								
								#la inglesa da error a veces, gestionamos la excepcion
								try:
									if not wii['en'].exists():
										editData['type']='nn'
										return revertAllEditsByUser(editData, userClass, regexplist) #Revert
										motivo=u'Posible efeméride irrelevante, no existe en la inglesa'
										wikipedia.output(motivo)
								except:
									pass
	
	return reverted, editData

def newArticleAnalysis(editData):
	""" Análisis de artículos nuevos """
	""" New articles analysis """
	if editData['page'].exists():
		editData['newText']=editData['page'].get()
	else:
		wikipedia.output(u"[[%s]] has been deleted!" % editData['pageTitle'])
		return
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
	
	marker=' ; ' #no poner ;;; porque da falsos positivos con regexp de repetición de caracteres
	clean=marker
	
	trozos=data.split('<tr>') 
	if len(trozos)>=3:
		trozos=trozos[2:] #....(0 cosas)<tr>(1 info sobre líneas</tr>)<tr>(2 lo que nos interesa... # el 1 contiene el numero de línea, nos lo saltamos
		for trozo in trozos:
			try:
				trozo=trozo.split('</tr>')[0] #no es que sea necesario pero...
				if re.search(avbotglobals.parserRegexps['cleandiff-diff-context'], trozo): #linea de contexto, nos la saltamos
					continue
				elif re.search(avbotglobals.parserRegexps['cleandiff-diff-addedline'], trozo):
					if re.search(avbotglobals.parserRegexps['cleandiff-diff-deletedline'], trozo): #sustitucion/añadido/eliminacion de algo, nos quedamos con lo de dentro del diffchange, dentro del diff-addedline
						trozo=((trozo.split('<td class="diff-addedline">')[1]).split('</td>'))[0]
						m=avbotglobals.parserRegexps['cleandiff-diffchange'].finditer(trozo)
						for i in m:
							clean+=u'%s%s%s' % (marker, i.group('text'), marker)
					else: #se trata de una linea nueva añadida, nos quedamos con lo de dentro del diff-addedline
						if re.search(avbotglobals.parserRegexps['cleandiff-diff-addedline-div'], trozo):
							trozo=((trozo.split('<td class="diff-addedline"><div>')[1]).split('</div></td>'))[0]
						else:
							trozo=((trozo.split('<td class="diff-addedline">')[1]).split('</td>'))[0]
						clean+=u'%s%s%s' % (marker, trozo, marker)
			except:
				wikipedia.output(u'ERROR: %s' % trozo)
	
	clean=re.sub(ur'(?m)[\n\r]', ur' ', clean) #no new lines
	
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
	
	#if editData['page'].exists(): #no es necesario para páginas antiguas (menos de 10 de historial), las nuevas ya se verifica justo antes de poner {{destruir}}
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
		avbotcomb.updateUserDataIfNeeded(editData) # Solo necesario para no anónimos
		if avbotglobals.userData['edits'].has_key(editData['author']):
			wikipedia.output(u'[%s] %s[[%s]] {\03{%s}%s\03{default}, %s ed.}' % (avbotcomb.getTime(), nm, editData['pageTitle'], avbotglobals.preferences['colors'][editData['userClass']], editData['author'], avbotglobals.userData['edits'][editData['author']]))
			if avbotglobals.userData['edits'][editData['author']]>avbotglobals.preferences['newbie']:
				return #Exit
		else:
			wikipedia.output(u'Ha habido un error con el número de ediciones de [[User:%s]]' % editData['author'])
			return #Exit

	if editData['page'].isRedirectPage(): #Do not analysis redirect pages
		return #Exit
	
	# Avoid to check our edits
	if editData['author'] == avbotglobals.preferences['botNick']: 
		return #Exit
		
	# Must be analysed?
	if not watch(editData):
		wikipedia.output(u'[[%s]] edit must not be checked' % editData['pageTitle'])
		return #Exit
		
	# Avoid analysis of excluded pages
	for exclusion, compiledexclusion in avbotglobals.excludedPages.items():
		if re.search(compiledexclusion, editData['pageTitle']):
			wikipedia.output(u'[[%s]] is in the exclusion list' % editData['pageTitle'])
			return #Exit
	
	# New pages analysis
	if editData['new'] and avbotglobals.preferences['language']=='es':
		time.sleep(5) #Para evitar que .exists() o .get() devuelva que no existe
		newArticleAnalysis(editData)
		return #Exit
	
	# To get history
	editData['oldText']=u''
	editData['newText']=u''
	#try: #costoso? pero no queda otra
	t1=time.time()
	#simplificar las llamas a los hilos? pasar todos los parámetros o solo los necesarios?
	threadHistory=Diegus(editData['page'], 'getVersionHistory', editData['oldid'], editData['diff'], avbotglobals.preferences['historyLength'])
	threadOldid=Diegus(editData['page'], 'getOldVersionOldid', editData['oldid'], editData['diff'], avbotglobals.preferences['historyLength'])
	threadDiff=Diegus(editData['page'], 'getOldVersionDiff', editData['oldid'], editData['diff'], avbotglobals.preferences['historyLength'])
	threadHTMLDiff=Diegus(editData['page'], 'getUrl', editData['oldid'], editData['diff'], avbotglobals.preferences['historyLength'])
	threadHistory.start()
	threadOldid.start()
	threadDiff.start()
	threadHTMLDiff.start()
	threadHistory.join()
	editData['pageHistory'] = threadHistory.getPageHistory()
	#print editData['pageHistory']
	threadOldid.join()
	editData['oldText'] = threadOldid.getOldText()
	threadDiff.join()
	editData['newText'] = threadDiff.getNewText()
	#hacer mi propio differ, tengo el oldText y el newText, pedir esto retarda la reversión unos segundos #fix #costoso?
	threadHTMLDiff.join()
	editData['HTMLDiff'] = threadHTMLDiff.getHTMLDiff()
	editData['HTMLDiff']=editData['HTMLDiff'].split('<!-- start content -->')[1]
	editData['HTMLDiff']=editData['HTMLDiff'].split('<!-- end content -->')[0] #No change
	cleandata=cleandiff(editData['pageTitle'], editData['HTMLDiff']) #To clean diff text and to extract inserted lines and words
	print 0, editData['pageTitle'], time.time()-t1, editData['pageHistory'][0][0], len(editData['oldText']), len(editData['newText']), len(editData['HTMLDiff'])
	
	"""t1=time.time()
	editData['pageHistory'] = editData['page'].getVersionHistory(revCount=10) #To avoid bot edit wars, 10 está bien?
	#editData['oldText']     = editData['page'].getOldVersion(editData['page'].previousRevision()) #Previous text
	print 1, editData['pageTitle'], time.time()-t1
	t1=time.time()
	editData['oldText']     = editData['page'].getOldVersion(editData['oldid']) #Previous text, oldid es la versión anterior a la actual que es diff
	print 2, editData['pageTitle'], time.time()-t1
	t1=time.time()
	editData['newText']     = editData['page'].getOldVersion(editData['diff']) #Current text, más lento que el .get() ?
	print 3, editData['pageTitle'], time.time()-t1"""
	
	#except:
	#	return #No previous text? New? Exit
	
	editData['lenOld']  = len(editData['oldText'])
	editData['lenNew']  = len(editData['newText'])
	editData['lenDiff'] = editData['lenNew']-editData['lenOld']
	
	# Proposed to delete? Skip
	if re.search(avbotglobals.parserRegexps['destruir'], editData['newText']): 
		wikipedia.output(u'Alguien ha marcado [[%s]] para destruir. Saltamos.' % editData['pageTitle'])
		return
	
	# Avoid to check false positives pages
	if re.search(avbotglobals.parserRegexps['conflictivos'], editData['newText']): 
		wikipedia.output(u'[[%s]] es un artículo conflictivo, no lo analizamos' % editData['pageTitle'])
		return
	
	#hacer mi propio differ, tengo el oldText y el newText, pedir esto retarda la reversión unos segundos #fix #costoso?
	"""try: #Try to catch diff
		t1=time.time()
		data=avbotglobals.preferences['site'].getUrl('/w/index.php?diff=%s&oldid=%s&diffonly=1' % (editData['diff'], editData['oldid']))
		print 5, editData['pageTitle'], time.time()-t1
		data=data.split('<!-- start content -->')[1]
		data=data.split('<!-- end content -->')[0] #No change
	except:
		return #No diff, exit
	"""
	
	#Analysis of this edit, must be reverted?
	[reverted, editData]=mustBeReverted(editData, cleandata, editData['userClass'])
	if reverted: 
		wikipedia.output(u'%s\n\03{lightred}Alert!: Possible %s by %s in [[%s]]\nDetails:\n%s\n%s\03{default}%s' % ('-'*50, avbotglobals.preferences['msg'][editData['type']]['meaning'].lower(), editData['author'], editData['pageTitle'], editData['score'], editData['details'], '-'*50))
		return
	