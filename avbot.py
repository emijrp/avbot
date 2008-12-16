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

# TODO:  comprobar que ultimalinea del apartado firmar no esta mas de 1 vez
# revertir anidados por parte de varios usuarios, 
# no ha introducido url alguna http://es.wikipedia.org/w/index.php?diff=16088818&oldid=prev&diffonly=1
# comprobar que al revertir no se esta revirtiendo a un vandalismo de otro usuario
# proteccion especial para destacados, buenos, y plantillas de la portada
# controlar http://en.wikipedia.org/wiki/MediaWiki:Bad_image_list
# lista de articulos mas vandalizados, para que los semiprotejan
# revierte prueba a edicion mala http://es.wikipedia.org/w/index.php?title=Aparato_circulatorio&diff=16610029&oldid=16610024
# no revertir a una version en blanco http://es.wikipedia.org/w/index.php?title=Aristas&diff=prev&oldid=16807904
#controlar eliminacion de categorias e iws en masa, deleted-lines http://es.wikipedia.org/w/index.php?title=Tik%C3%BAn_Olam&diff=prev&oldid=16896350
# estadisticas de vandalismos mas frecuentes
#error frecuente: WARNING: No character set found.
#avisar en el tablon de 3RR
#Línea no gestionada ---> 14[[07Especial:Log/protect14]]4 protect10 02 5* 03Edmenb 5*  10protegió [[02Discusión:W.A.S.P.10]] [edit=autoconfirmed] (caduca el 14:10 10 nov 2008) [move=autoconfirmed] (caduca el 14:10 10 nov 2008): [[Wikipedia:Vandalismo|Vandalismo]] excesivo
# quitar los colores msg=msg.decode("utf-8")  msg=re.sub("\x03\d{2}?","",msg) 

# External modules
import os,sys,re
import threading,thread
import httplib,urllib,urllib2
import time,datetime
import string,math,random
from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_h, irc_lower, ip_numstr_to_quad, ip_quad_to_numstr
import random
import wikipedia, difflib

# My modules
import avbotload     #Information and regexp loader
import avbotsave     #
import avbotmsg      #Send messages to vandals
import avbotanalysis #Edit analysis to find vandalisms, blanking, and similar malicious edits
import avbotcomb     #Trivia functions
import avbotpatterns #Patterns to scan Recent Changes RSS

# Variables
global exclusions
global context
global pruebas
pruebas={}
global vandalismos
vandalismos={}
global imageneschocantes
imageneschocantes={}
global controlspam
controlspam={}
global controlvand
controlvand={}
global whitelist
global colors
global edits
global speed
global statsDic
global timeStatsDic
global currentYear

# Default bot preferences
preferences = {
	'botNick':    u'AVBOT',             #Bot name
	'language':   u'es',                #Default language is Spanish
	'family':     u'wikipedia',         #Default project family is Wikipedia
	'site':       0,
	'network':    u'irc.wikimedia.org', #IRC network where is the IRC channel with recent changes
	'port':       6667,                 #Port number
	'newbie':     25,                   #Who is a newbie user? How many edits?
	'statsDelay': 60,
}
preferences         = avbotcomb.getParameters(preferences, sys.argv)
preferences['site'] = wikipedia.Site(preferences['language'], preferences['family'])

colors ={'admin':'lightblue', 'bot':'lightpurple', 'reg':'lightgreen', 'anon':'lightyellow'}
edits={'admin':0,'bot':0,'reg':0,'anon':0}
today=datetime.date.today()
currentYear=today.year

# Statistics
speed        = 0
statsDic     = {}
statsDic[2]  = {'V':0,'BL':0,'P':0,'S':0,'B':0,'M':0,'T':0,'D':0}
statsDic[12] = {'V':0,'BL':0,'P':0,'S':0,'B':0,'M':0,'T':0,'D':0}
statsDic[24] = {'V':0,'BL':0,'P':0,'S':0,'B':0,'M':0,'T':0,'D':0}
timeStatsDic = {2: time.time(), 12: time.time(), 24: time.time(), 'tvel': time.time()}

# Header message
header  = u"\nAVBOT Copyright (C) 2008 Emilio José Rodríguez Posada\n"
header += u"This program comes with ABSOLUTELY NO WARRANTY; for details type `show w'.\n"
header += u"This is free software, and you are welcome to redistribute it\n"
header += u"under certain conditions; type `show c' for details.\n\n"
header += u"############################################################################\n"
header += u"# Name:    AVBOT (AntiVandal BOT)                                          #\n"
header += u"# Version: 0.7                                                             #\n"
header += u"# Tasks:   To revert vandalism, blanking and test edits                    #\n"
header += u"#          To improve new articles                                         #\n"
header += u"#          Anti-birthday protection                                        #\n"
header += u"#          Shocking images control                                         #\n"
header += u"############################################################################\n\n"
header += u"Loading data for %s: language of %s project" % (preferences['language'], preferences['family'])
wikipedia.output(header)

# Data loaders
site                   = wikipedia.Site(preferences['language'], preferences['family'])
userData               = {}
userData['edits']      = avbotload.loadEdits(preferences)
userData['admins']     = avbotload.loadAdmins(site)
userData['bots']       = avbotload.loadBots(site)
exclusions             = avbotload.loadExclusions(site)
patterns               = avbotpatterns.loadPatterns(preferences['language']) #Patterns for RSS Recent Changes
#Shocking images list
#[imageneschocantes, error]=avbotload.loadShockingImages(site)
#wikipedia.output(u"Cargadas %d imágenes chocantes y %d excepciones...%s" % (len(imageneschocantes['images'].items()), len(imageneschocantes['exceptions']), error))

context=ur'[ \@\º\ª\·\#\~\$\<\>\/\(\)\'\-\_\:\;\,\.\r\n\?\!\¡\¿\"\=\[\]\|\{\}\+\&]'
#Regular expresions for vandalism edits
[vandalismos, error]=avbotload.loadVandalism(context, site)
wikipedia.output(u"Loaded and compiled %d regular expresions for vandalism edits...%s" % (len(vandalismos.items()), error))

# WHITE LIST
whitelist=[
re.compile(ur'(?i)http://commons.wikimedia\.org'),
re.compile(ur'(?i)http://[a-z]{2,3}\.wikipedia\.org'),
re.compile(ur'(?i)http://[a-z]{2,3}\.wiktionary\.org'),
re.compile(ur'(?i)http://[a-z]{2,3}\.wikisource\.org'),
re.compile(ur'(?i)http://[a-z]{2,3}\.wikiquote\.org'),
re.compile(ur'(?i)http://[a-z]{2,3}\.wikiversity\.org'),
]

# IMAGE HOSTINGS TO AVOID
imagehostings=[
re.compile(ur'(?i)http://img\d{1,3}\.imageshack\.us/'),
re.compile(ur'(?i)http://i\d{1,3}\.photobucket\.com/'),
]

wikipedia.output(u'Joining to recent changes IRC channel...\n')

def cleandiff(pageTitle, data, patterns):
	#TODO
	#evitar que diffdelete y diffaddedline coincidan
	#http://es.wikipedia.org/w/index.php?title=Lenguaje_ensamblador&diff=prev&oldid=16735402
	
	clean=u';;'
	
	trozos=data.split('<td class="diff-addedline"><div>')[1:]

	for trozo in trozos:
		trozo=trozo.split('</div></td>')[0]
		#if re.search(ur'<span class="diffchange">', trozo): #estilo antiguo
		if re.search(patterns['diffstylebegin'], trozo):
			#m=re.compile(ur'<span class="diffchange">([^<]*?)</span>').finditer(trozo) #antiguo estilo
			m=re.compile(patterns['diffstyleend']).finditer(trozo) #diff punteados ¬¬'
			for i in m:
				clean+=u';;%s;;' % i.group(2) #<------- cuidado 2 por el diff style nuevo
		else:
			if not re.search(ur'<', trozo): #necesario para descartar el/los ultimos trozos de contexto
				clean+=u';;%s;;' % trozo
	
	return re.sub(ur'[\n\r]', ur';;', clean)


def editAnalysis(preferences,userData,patterns,editData):
	global exclusions
	global context
	global pruebas
	global vandalismos
	global imageneschocantes
	global controlspam
	global controlvand
	global whitelist
	global colors
	global edits
	global statsDic
	global currentYear
	
	editData['page']=wikipedia.Page(preferences['site'], editData['pageTitle'])
	if editData['page'].exists():
		editData['pageTitle']=editData['page'].title()
		editData['namespace']=editData['page'].namespace()
		
		#Avoid analysis of excluded pages
		if exclusions.has_key(editData['pageTitle']):
			return
		
		#Reload vandalism regular expresions
		if editData['pageTitle']==u'Usuario:Emijrp/Lista del bien y del mal.css':
			vandalismos=avbotload.reloadVandalism(context, preferences['site'], preferences['botNick'], vandalismos, editData['author'], editData['diff'])
			return #Exit
		
		if editData['pageTitle']==u'Usuario:Emijrp/Exclusiones.css':
			exclusions=avbotload.loadExclusions(preferences['site'])
			return #Exit
		
		if editData['page'].isRedirectPage(): #Do not analysis redirect pages
			return
		else:
			nm=u''
			authorEditsNum=0
			if editData['new']:
				nm+=u'\03{lightred}N\03{default}'
			if editData['minor']:
				nm+=u'\03{lightred}m\03{default}'
			if nm:
				nm+=u' '
			
			userClass='anon'
			if userData['admins'].count(editData['author'])!=0:
				userClass='admin'
			elif userData['bots'].count(editData['author'])!=0:
				userClass='bot'
			elif not re.search(patterns['ip'], editData['author']):
				userClass='reg'
			
			#Update user edits if it is necessary
			if userClass!='anon':
				if userData['edits'].has_key(editData['author']):
					if not random.randint(0,10): #10 faces dic, true if zero
						userData['edits'][editData['author']]=avbotload.loadUserEdits(editData['author'], preferences['site'], preferences['newbie'])
						if not random.randint(0,10): 
							avbotsave.saveEdits(userData['edits'])
				else:
					#cargamos
					userData['edits'][editData['author']]=avbotload.loadUserEdits(editData['author'], preferences['site'], preferences['newbie'])
					if not random.randint(0,10): #afirmativo si sale cero
						avbotsave.saveEdits(userData['edits'])
				authorEditsNum=userData['edits'][editData['author']]
			
			timeEdit=u'['+time.strftime('%H:%M:%S')+']'
			
			#New pages analysis
			if editData['new'] and preferences['language']=='es':
				editData['newText']=editData['page'].get()
				editData['lenNew']=len(editData['newText'])
				if userClass=='anon':
					wikipedia.output(u'%s %s[[%s]] (%s bytes) {\03{%s}%s\03{default}}' % (timeEdit, nm, editData['pageTitle'], editData['lenNew'], colors[userClass], editData['author']))
				else:
					wikipedia.output(u'%s %s[[%s]] (%s bytes) {\03{%s}%s\03{default}, %s ed.}' % (timeEdit, nm, editData['pageTitle'], editData['lenNew'], colors[userClass], editData['author'], authorEditsNum))
				
				[done, motivo, statsDic]=avbotanalysis.isRubbish(editData['page'], userClass, editData['pageTitle'], editData['newText'], colors, editData['author'], authorEditsNum, preferences['newbie'], editData['namespace'], pruebas, vandalismos, statsDic)
				
				if done:
					wikipedia.output(u'\03{lightred}Alert!: Putting destroy template in [[%s]]. Motive: %s\03{default}' % (editData['pageTitle'], motivo))
					return
				
				[done, resumen]=avbotanalysis.improveNewArticle(editData['namespace'], editData['page'])
				if done:
					wikipedia.output(u'\03{lightred}Alert!: Aplicando %s... a [[%s]]\03{default}' % (resumen, editData['pageTitle']))
					return
					
				return #End of analysis for this new page, Exit
			
			if userClass=='anon':
				wikipedia.output(u'%s %s[[%s]] {\03{%s}%s\03{default}}' % (timeEdit, nm, editData['pageTitle'], colors[userClass], editData['author']))
			else:
				wikipedia.output(u'%s %s[[%s]] {\03{%s}%s\03{default}, %s ed.}' % (timeEdit, nm, editData['pageTitle'], colors[userClass], editData['author'], authorEditsNum))
				if authorEditsNum>preferences['newbie']:
					return #Exit
			
			#To get history
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
			
			if editData['author']==preferences['botNick']: #Avoid to check our edits
				return
			
			if re.search(patterns['destruir'], editData['newText']): #Proposed to delete? Skip
				wikipedia.output(u'Alguien ha marcado [[%s]] para destruir. Saltamos.' % editData['pageTitle'])
				return
			
			if re.search(patterns['conflictivos'], editData['newText']): #Avoid to check false positives pages
				wikipedia.output(u'[[%s]] es un artículo conflictivo, no lo analizamos' % editData['pageTitle'])
				return
			
			try: #Try to catch diff
				data=site.getUrl('/w/index.php?diff=%s&oldid=%s&diffonly=1' % (editData['diff'], editData['oldid']))
				data=data.split('<!-- start content -->')[1]
				data=data.split('<!-- end content -->')[0] #No change
			except:
				return #No diff, exit
			
			cleandata=cleandiff(editData['pageTitle'], data, patterns) #To clean diff text
			
			if not avbotanalysis.watch(editData, preferences, userClass, authorEditsNum):
				return
			
			#Vandalism analysis
			#1) Blanking all
			[reverted, controlvand, statsDic, editData]=avbotanalysis.isBlanking(preferences, editData, userClass, patterns, controlvand, statsDic)
			if reverted:
				wikipedia.output(u'%s\n\03{lightred}Alert!: Possible %s edit by %s in [[%s]]\nDetalles:\n%s\n%s\03{default}%s' % ('-'*50, editData['type'], editData['author'], editData['pageTitle'], editData['score'], editData['details'], '-'*50))
				return
			
			#2) Section blanking
			#No se puede distinguir cuando el blanqueo de una sección es legítimo o no
			"""[done, controlvand, statsDic]=avbotanalysis.isSectionBlanking(namespace, editData['pageTitle'], editData['author'], userClass, authorEditsNum, preferences['newbie'], data, controlvand, diff, oldid, site, preferences['botNick'], statsDic, p, oldText, pageHistory, currentYear)
			if done:
				wikipedia.output(u'\03{lightred}Alerta: Posible blanqueo de sección de %s en [[%s]]\03{default}' % (editData['author'], editData['pageTitle']))
				return
			
			
			#3) Section vandalisms
			[done, controlvand, statsDic]=avbotanalysis.isSectionVandalism(namespace, editData['pageTitle'], editData['author'], userClass, authorEditsNum, preferences['newbie'], data, controlvand, diff, oldid, site, preferences['botNick'], statsDic, p, oldText, pageHistory, currentYear)
			if done:
				wikipedia.output(u'\03{lightred}Alerta: Posible vandalismo de sección de %s en [[%s]]\03{default}' % (editData['author'], editData['pageTitle']))
				return
			
			#deteccion vandalismos
			#
			#llamo a cleandiff, cuando isBlanking este unificado, poner data=cleandiff(pageTitle, data, patterns) arriba
			#unificar el autoSign, controlspam y todas las de este modulo tambien
			#
			#4) Common vandalism
			[done, score, details, controlvand, statsDic, type]=avbotanalysis.isVandalism(namespace, pageTitle, editData['author'], userClass, authorEditsNum, preferences['newbie'], vandalismos, cleandata, controlvand, p, pageHistory, diff, oldid, site, preferences['botNick'], oldText, statsDic, currentYear)
			"""
			[reverted, controlvand, statsDic, editData]=avbotanalysis.isVandalism(preferences, editData, vandalismos, cleandata, userClass, patterns, controlvand, statsDic)
			if reverted: 
				wikipedia.output(u'%s\n\03{lightred}Alert!: %s by %s in [[%s]]\nDetalles:\n%s\n%s\03{default}%s' % ('-'*50, editData['type'], editData['author'], editData['pageTitle'], editData['score'], editData['details'], '-'*50))
				return
			
			"""
			#5) Shocking images
			[done, controlvand, statsDic]=avbotanalysis.isShockingContent(namespace, pageTitle, editData['author'], userClass, authorEditsNum, preferences['newbie'], imageneschocantes, cleandata, controlvand, p, pageHistory, diff, oldid, site, preferences['botNick'], oldText, statsDic, currentYear)
			if done: 
				wikipedia.output(u'\03{lightred}Alerta: Posible imagen chocante de %s en [[%s]]\03{default}' % (editData['author'], editData['pageTitle']))
				return
			
			#6) Anti-hoygans protection
			
			
			#deteccion vandalismos repetitivos
			# cambiar nacimientos por fallecimientos
			
			#7) Anti-birthday protection
			[done, motivo, controlvand, statsDic]=avbotanalysis.antiBirthday(pageTitle, userClass, authorEditsNum, preferences['newbie'], namespace, oldText, newText, cleandata, controlvand, site, pageHistory, diff, preferences['botNick'], editData['author'], oldid, statsDic, p, currentYear)
			if done:
				wikipedia.output(u'\03{lightred}Alerta: %s en [[%s]]\03{default}' % (motivo, editData['pageTitle']))
				return
			
			
			#control de spam e imagenes de hostings ajenos
			if editData['namespace']==0 and (userClass=='anon' or (userClass=='reg' and authorEditsNum<=preferences['newbie'])):
				m=patterns['spam'].finditer(cleandata)
				if m:
					for i in m:
						url=i.group(1)
						#seguro que la url ha sido introducida ahora y no estaba ya?
						#if re.search(ur'(?i)<td class="diff-deletedline"><div>[^<]*%s[^<]*</div></td>' % url, data):
						#	continue
						#elif re.search(ur'(?i)<td class="diff-deletedline"><div>[^<]*<span class="diffchange">[^<]*%s[^<]*</span>[^<]*</div></td>' % url, data):
						#	continue
						#fin comprobacion
						white=False
						imagehost=False
						#hacer una lista blanca otro dia
						for j in whitelist:
							if re.search(j, url):
								white=True
								break
						for j in imagehostings:
							if re.search(j, url):
								imagehost=True
								break
						if imagehost:
							wikipedia.output(u'\03{lightred}Alerta: Avisando de cómo subir imágenes correctamente a [[User:%s]]\03{default}' % editData['author'])
							#avisamos al usuario
							avbotmsg.msgImageHost(editData['author'], site, pageTitle, diff)
							return"""
			
	else:
		wikipedia.output(u'[[%s]] has been deleted' % editData['pageTitle'])

def parseaentrada(entrada):
	try:
		salida=unicode(entrada,'utf-8')
	except UnicodeError:
		try:
			salida=unicode(entrada,'iso8859-1')
		except UnicodeError:
			c.privmsg(self.channel, 'Usa utf-8, por favor')
			print 'Codificación indeterminada.'
			return
	return salida

class BOT(SingleServerIRCBot):
	def __init__(self, preferences, userData, patterns):
		self.preferences = preferences
		self.userData    = userData
		self.patterns    = patterns
		channel          = '#%s.%s' % (preferences['language'], preferences['family'])        #RSS channel for recent changes in Wikipedia
		self.channel     = channel
		nickname         = '%s%s' % (preferences['botNick'], str(random.randint(1000, 9999))) #Bot nick in channel, with random numbers to avoid nick collisions
		self.nickname    = nickname
		SingleServerIRCBot.__init__(self, [(preferences['network'], preferences['port'])], nickname, nickname)
	
	def on_welcome(self, c, e):
		c.join(self.channel)
	
	def on_pubmsg(self, c, e):
		preferences = self.preferences
		userData    = self.userData
		patterns    = self.patterns
		global speed
		global timeStatsDic
		global statsDic
		global context
		global pruebas
		global vandalismos
		global colors
		
		editData={}
		
		line = (e.arguments()[0])
		line = parseaentrada(line)
		nick = nm_to_n(e.source())
		
		line=re.sub(ur'\x03\d{0,2}', ur'', line) #No colors
		line=re.sub(ur'\x02\d{0,2}', ur'', line) #No bold
		
		editData['line']=line
		if re.search(patterns['edit'], line):
			match=patterns['edit'].finditer(line)
			for m in match:
				editData['pageTitle'] = m.group('pageTitle')
				editData['diff']      = m.group('diff')
				editData['oldid']     = m.group('oldid')
				editData['author']    = m.group('author')
				nm=m.group('nm')
				editData['new']       = editData['minor']=False
				if re.search('N', nm): #si es nuevo entraria en patterns['nuevo']
					editData['new']   = True
				if re.search('M', nm):
					editData['minor'] = True
				editData['resume']    = m.group('resume')
				
				statsDic = avbotanalysis.incrementaStats(statsDic, 'T')
				speed   += 1
				
				thread.start_new_thread(editAnalysis,(preferences,userData,patterns,editData))
				
				#Check resume for reverts
				if re.search(ur'(?i)(Revertidos los cambios de.*%s.*a la última edición de|Deshecha la edición \d+ de.*%s)' % (preferences['botNick'], preferences['botNick']), editData['resume']):
					wiii=wikipedia.Page(preferences['site'], u'User:AVBOT/Errores/Automático')
					wiii.put(u'%s\n\n== [[%s]] ({{subst:CURRENTDAY}} de {{subst:CURRENTMONTHNAME}} de {{subst:CURRENTYEAR}}) ==\n* Diff: http://%s.wikipedia.org/w/index.php?diff=%s&oldid=%s\n* Autor de la reversión: {{u|%s}}' % (wiii.get(), editData['pageTitle'], preferences['language'], editData['diff'], editData['oldid'], editData['author']), u'BOT - Informe automático. [[User:%s|%s]] ha revertido a [[User:%s|%s]] en [[%s]]' % (editData['author'], editData['author'], preferences['botNick'], preferences['botNick'], editData['pageTitle']))
				break
		elif re.search(patterns['newpage'], line):
			match=patterns['newpage'].finditer(line)
			for m in match:
				editData['pageTitle']=m.group('pageTitle')
				editData['diff']=editData['oldid']=0
				editData['author']=m.group('author')
				nm=m.group('nm')
				editData['new']=True
				editData['minor']=False
				if re.search('M', nm):
					editData['minor']=True
				editData['resume']=u''
				#time.sleep(5) #sino esperamos un poco, es posible que exists() devuelva false, hace que se quede indefinidamente intentando guardar la pagina, despues de q la destruyan
				thread.start_new_thread(editAnalysis,(preferences,userData,patterns,editData))
				speed+=1
				break
		elif re.search(patterns['block'], line):
			match=patterns['block'].finditer(line)
			for m in match:
				blocker=m.group('blocker')
				blocked=m.group('blocked')
				block=m.group('block')
				wikipedia.output(u'\03{lightblue}Registro combinado: [[User:%s]] (%d) ha sido bloqueado por [[User:%s]] (%d) por un plazo de %s\03{default}' % (blocked, len(blocked), blocker, len(blocker), block))
				thread.start_new_thread(avbotcomb.bloqueo,(preferences['site'],blocker,blocked,block))
				break
		elif re.search(patterns['nuevousuario'], line):
			match=patterns['nuevousuario'].finditer(line)
			for m in match:
				usuario=m.group('usuario')
				wikipedia.output(u'\03{lightblue}Registro combinado: [[User:%s]] (%d) se acaba de registrar.\03{default}' % (usuario, len(usuario)))
				break
		elif re.search(patterns['borrado'], line):
			match=patterns['borrado'].finditer(line)
			for m in match:
				pageTitle=m.group('pageTitle')
				usuario=m.group('usuario')
				wikipedia.output(u'\03{lightblue}Registro combinado: [[%s]] ha sido borrado por [[User:%s]]\03{default}' % (pageTitle, usuario))
				break
		elif re.search(patterns['traslado'], line):
			match=patterns['traslado'].finditer(line)
			for m in match:
				usuario=m.group('usuario')
				origen=m.group('origen')
				destino=m.group('destino')
				wikipedia.output(u'\03{lightblue}Registro combinado: [[%s]] ha sido trasladado a [[%s]] por [[User:%s]]\03{default}' % (origen, destino, usuario))
				thread.start_new_thread(avbotcomb.traslado,(preferences['site'],usuario,origen,destino))
				break
		elif re.search(patterns['protegida'], line):
			match=patterns['protegida'].finditer(line)
			for m in match:
				pageTitle=m.group('pageTitle')
				protecter=m.group('protecter')
				edit=m.group('edit')
				move=m.group('move')
				wikipedia.output(u'\03{lightblue}Registro combinado: [[%s]] (%d) ha sido protegida por [[User:%s]] (%d), edit=%s (%d), move=%s (%d)\03{default}' % (pageTitle, len(pageTitle), protecter, len(protecter), edit, len(edit), move, len(move)))
				if re.search(ur'autoconfirmed', edit) and re.search(ur'autoconfirmed', move):
					thread.start_new_thread(avbotcomb.semiproteger,(preferences['site'],pageTitle,protecter))
				break
				
		else:
			wikipedia.output(u'No gestionada ---> %s' % line)
			f=open('lineasnogestionadas.txt', 'a')
			line=u'%s\n' % line
			try:
				f.write(line)
			except:
				try:
					f.write(line.encode('utf-8'))
				except:
					pass
			f.close()
		
		#Calculating and showing statistics
		if time.time()-timeStatsDic['tvel']>=preferences['statsDelay']: #Showing information in console every 60 seconds
			intervalo = int(time.time()-timeStatsDic['tvel'])
			wikipedia.output(u'\03{lightgreen}AVBOT working for %s: language of %s project\03{default}' % (preferences['language'], preferences['family']))
			wikipedia.output(u'\03{lightgreen}Average speed: %d edits/minute\03{default}' % int(speed/(intervalo/60.0)))
			wikipedia.output(u'\03{lightgreen}Last 2 hours: V[%d], BL[%d], P[%d], S[%d], B[%d], M[%d], T[%d], D[%d]\03{default}' % (statsDic[2]['V'], statsDic[2]['BL'], statsDic[2]['P'], statsDic[2]['S'], statsDic[2]['B'], statsDic[2]['M'], statsDic[2]['T'], statsDic[2]['D']))
			legend=u''
			for k,v in colors.items():
				legend+=u'\03{%s}%s\03{default}, ' % (v, k)
			wikipedia.output(u'Legend: %s...' % legend)
			timeStatsDic['tvel'] = time.time()
			speed                = 0
		
		#Recalculating statistics
		for period in [2, 12, 24]: #Every 2, 12 and 24 hours
			statsDic[period]['M']=statsDic[period]['V']+statsDic[period]['BL']+statsDic[period]['P']+statsDic[period]['S']
			statsDic[period]['B']=statsDic[period]['T']-statsDic[period]['M']
			
			if time.time()-timeStatsDic[period]>=3600*period:
				avbotsave.saveStats(statsDic, period, preferences['site'])          #Saving statistics in Wikipedia pages for historical reasons
				timeStatsDic[period]=time.time()                                    #Saving time begin
				statsDic[period]={'V':0,'BL':0,'P':0,'S':0,'B':0,'M':0,'T':0,'D':0} #Blanking statistics for a new period

def main(preferences, userData, patterns):
	bot = BOT(preferences, userData, patterns)
	bot.start()

if __name__ == '__main__':
	main(preferences, userData, patterns)
