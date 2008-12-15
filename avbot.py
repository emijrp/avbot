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

#############################################
#############################################
# TODO:  comprobar que ultimalinea del apartado firmar no esta mas de 1 vez
# modulo bienvenidas: tus pruebas de edicion en la WP:ZP se realizaron correctamente, revisar si ha sido revertido, si ha incluido imagenes de otros servidores .jpg, ultimas modificaciones
# revertir anidados por parte de varios usuarios, 
# categorias magicas, antiblanqueos de secciones
# no ha introducido url alguna http://es.wikipedia.org/w/index.php?diff=16088818&oldid=prev&diffonly=1
# comprobar que al revertir no se esta revirtiendo a un vandalismo de otro usuario
# proteccion especial para destacados, buenos, y plantillas de la portada
# avisa dos veces de la misma ip, aunque con articulos distintos http://es.wikipedia.org/w/index.php?title=Usuario:AVBOT/Spam&diff=prev&oldid=16553707
# bbdd de imagenes chocantes en commons, controlar que no la pongan en paginas de usuario o artiulos que no vengan a cuento
# evitar camuflages de vandalismos http://es.wikipedia.org/w/index.php?title=Resistencia&diff=prev&oldid=16591958
# no firmar estas cosas http://es.wikipedia.org/w/index.php?title=Discusi%C3%B3n:Wikipedia&diff=16581592&oldid=16581591
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
#############################################

#-----------------------------------------------------------------------------------------------------------------------
# EXTERNAL FILES
#-----------------------------------------------------------------------------------------------------------------------
import os,sys,re
import threading,thread
import httplib,urllib,urllib2
import time,datetime
import string,math,random
from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_h, irc_lower, ip_numstr_to_quad, ip_quad_to_numstr
import random
import wikipedia, difflib
import datetime

#-----------------------------------------------------------------------------------------------------------------------
# MY FILES
#-----------------------------------------------------------------------------------------------------------------------
import avbotload     #Information and regexp loader
import avbotsave     #
import avbotmsg      #Send messages to vandals
import avbotanalysis #Edit analysis to find vandalisms, blanking, and similar malicious edits
import avbotcomb     #Trivia functions
import avbotpatterns #Patterns to scan Recent Changes RSS

#-----------------------------------------------------------------------------------------------------------------------
# VARIABLES
#-----------------------------------------------------------------------------------------------------------------------
global ediciones
global admins
global bots
global exclusions
global contexto
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
global site
global botNick
global speed
global statsDic
global timeStatsDic
global newbie
global patterns
global currentYear

#-----------------------------------------------------------------------------------------------------------------------
# BOT PREFERENCES
#-----------------------------------------------------------------------------------------------------------------------
botNick=u'AVBOT'
language=u'es'
family=u'wikipedia'
if len(sys.argv)>=2:
	language=sys.argv[1]
site=wikipedia.Site(language, family)
colors={'admin':'lightblue', 'bot':'lightpurple', 'reg':'lightgreen', 'anon':'lightyellow'}
edits={'admin':0,'bot':0,'reg':0,'anon':0}
today=datetime.date.today()
currentYear=today.year

#-----------------------------------------------------------------------------------------------------------------------
# PARAMETROS DE REVERSION
#-----------------------------------------------------------------------------------------------------------------------
newbie=25 #hasta cuando se considera novato a un usuario

#-----------------------------------------------------------------------------------------------------------------------
# STATISTICS
#-----------------------------------------------------------------------------------------------------------------------
speed=0
statsDic={}
statsDic[2]={'V':0,'BL':0,'P':0,'S':0,'B':0,'M':0,'T':0,'D':0}
statsDic[12]={'V':0,'BL':0,'P':0,'S':0,'B':0,'M':0,'T':0,'D':0}
statsDic[24]={'V':0,'BL':0,'P':0,'S':0,'B':0,'M':0,'T':0,'D':0}
timeStatsDic={2: time.time(), 12: time.time(), 24: time.time(), 'tvel': time.time()}

#-----------------------------------------------------------------------------------------------------------------------
# OTROS
#-----------------------------------------------------------------------------------------------------------------------

header =u"\nAVBOT Copyright (C) 2008 Emilio José Rodríguez Posada\n"
header+=u"This program comes with ABSOLUTELY NO WARRANTY; for details type `show w'.\n"
header+=u"This is free software, and you are welcome to redistribute it\n"
header+=u"under certain conditions; type `show c' for details.\n\n"
header+=u"############################################################################\n"
header+=u"# Name:    AVBOT (AntiVandal BOT)                                          #\n"
header+=u"# Version: 0.7                                                             #\n"
header+=u"# Purpose: To revert vandalism, blanking and test edits                    #\n"
header+=u"#          To improve new articles                                         #\n"
header+=u"#          Anti-birthday protection                                        #\n"
header+=u"#          Shocking images control                                         #\n"
header+=u"############################################################################\n\n"
header+=u"Loading data for %s.wikipedia.org..." % site.lang
wikipedia.output(header)

#-----------------------------------------------------------------------------------------------------------------------
# DATA LOADERS
#-----------------------------------------------------------------------------------------------------------------------
ediciones  = avbotload.loadEdits(newbie)
admins     = avbotload.loadAdmins(site)
bots       = avbotload.loadBots(site)
exclusions = avbotload.loadExclusions(site)

contexto=ur'[ \@\º\ª\·\#\~\$\<\>\/\(\)\'\-\_\:\;\,\.\r\n\?\!\¡\¿\"\=\[\]\|\{\}\+\&]'
#Regular expresions for vandalism edits
[vandalismos, error]=avbotload.loadVandalism(contexto, site, botNick)
wikipedia.output(u"Loaded and compiled %d regular expresions for vandalism edits...%s" % (len(vandalismos.items()), error))

#Shocking images list
#[imageneschocantes, error]=avbotload.loadShockingImages(site)
#wikipedia.output(u"Cargadas %d imágenes chocantes y %d excepciones...%s" % (len(imageneschocantes['images'].items()), len(imageneschocantes['exceptions']), error))

#Patterns for RSS Recent Changes
patterns=avbotpatterns.loadPatterns(language)

#-----------------------------------------------------------------------------------------------------------------------
# WHITE LIST
#-----------------------------------------------------------------------------------------------------------------------
whitelist=[
re.compile(ur'(?i)http://commons.wikimedia\.org'),
re.compile(ur'(?i)http://[a-z]{2,3}\.wikipedia\.org'),
re.compile(ur'(?i)http://[a-z]{2,3}\.wiktionary\.org'),
re.compile(ur'(?i)http://[a-z]{2,3}\.wikisource\.org'),
re.compile(ur'(?i)http://[a-z]{2,3}\.wikiquote\.org'),
re.compile(ur'(?i)http://[a-z]{2,3}\.wikiversity\.org'),
]

#-----------------------------------------------------------------------------------------------------------------------
# IMAGE HOSTINGS TO AVOID
#-----------------------------------------------------------------------------------------------------------------------
imagehostings=[
re.compile(ur'(?i)http://img\d{1,3}\.imageshack\.us/'),
re.compile(ur'(?i)http://i\d{1,3}\.photobucket\.com/'),
]

wikipedia.output(u'Joining to recent changes IRC channel...')

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


def edicion(pageTitle, author, new, minor, diff, oldid, resumen):
	global ediciones
	global admins
	global bots
	global exclusions
	global contexto
	global pruebas
	global vandalismos
	global imageneschocantes
	global controlspam
	global controlvand
	global whitelist
	global colors
	global edits
	global site
	global botNick
	global newbie
	global patterns
	global statsDic
	global currentYear
	
	p=wikipedia.Page(site, pageTitle)
	if p.exists():
		pageTitle=p.title()
		namespace=p.namespace()
		
		if exclusions.has_key(pageTitle):
			return
		
		#recarga de expresiones regulares de vandalismos
		if pageTitle==u'Usuario:Emijrp/Lista del bien y del mal.css':
			vandalismos=avbotload.reloadVandalism(contexto, site, botNick, vandalismos, author, diff)
			return #salimos
		
		if pageTitle==u'Usuario:Emijrp/Exclusiones.css':
			exclusions=avbotload.loadExclusions(site)
			return #salimos
		
		if p.isRedirectPage(): #Do not analysis redirect pages by now
			return
		else: #si es articulo o desambiguacion, analizamos
			nm=u''
			authorEditNum=0
			if new:
				nm+=u'\03{lightred}N\03{default}'
			if minor:
				nm+=u'\03{lightred}m\03{default}'
			if nm:
				nm+=u' '
			userClass='anon'
			if admins.count(author)!=0:
				userClass='admin'
			elif bots.count(author)!=0:
				userClass='bot'
			elif not re.search(patterns['ip'], author):
				userClass='reg'
			
			#actualizando info de ediciones si se necesita
			if userClass!='anon':
				if ediciones.has_key(author):
					#actualizamos? dado de 10 caras
					if not random.randint(0,10): #afirmativo si sale cero
						ediciones[author]=avbotload.loadUserEdits(author, site, newbie)
						if not random.randint(0,10): #afirmativo si sale cero
							avbotsave.saveedits(ediciones)
				else:
					#cargamos
					ediciones[author]=avbotload.loadUserEdits(author, site, newbie)
					if not random.randint(0,10): #afirmativo si sale cero
						avbotsave.saveedits(ediciones)
				authorEditNum=ediciones[author]
			
			#New pages analysis
			if new and site.lang=='es':
				newText=p.get()
				if userClass=='anon':
					wikipedia.output(u'%s[[%s]] {\03{%s}%s\03{default}} (+%d)' % (nm, pageTitle, colors[userClass], author, len(newText)))
				else:
					wikipedia.output(u'%s[[%s]] {\03{%s}%s\03{default}, %s ed.} (+%d)' % (nm, pageTitle, colors[userClass], author, authorEditNum, len(newText)))
				
				[done, motivo, statsDic]=avbotanalysis.isRubbish(p, userClass, pageTitle, newText, colors, author, authorEditNum, newbie, namespace, pruebas, vandalismos, statsDic)
				
				if done:
					wikipedia.output(u'\03{lightred}Alert!: Putting destroy template in [[%s]]. Motive: %s\03{default}' % (pageTitle, motivo))
					return
				
				[done, resumen]=avbotanalysis.improveNewArticle(namespace, p)
				if done:
					wikipedia.output(u'\03{lightred}Alert!: Aplicando %s... a [[%s]]\03{default}' % (resumen, pageTitle))
					return
					
				return #End of analysis for this new page, Exit
			
			if userClass=='anon':
				wikipedia.output(u'%s[[%s]] {\03{%s}%s\03{default}}' % (nm, pageTitle, colors[userClass], author))
			else:
				wikipedia.output(u'%s[[%s]] {\03{%s}%s\03{default}, %s ed.}' % (nm, pageTitle, colors[userClass], author, authorEditNum))
				if authorEditNum>newbie:
					return #Exit
			
			#To get history
			oldText=newText=u''
			try:
				pageHistory=p.getVersionHistory(revCount=10) #To avoid bot edit wars
				oldText=p.getOldVersion(p.previousRevision()) #Previous text
				newText=p.get() #Current text
			except:
				return #No previous text? New? Exit
			
			lenOld=len(oldText)
			lenNew=len(newText)
			
			#Size diff
			lenDiff=lenNew-lenOld
			signo=u''
			if lenDiff>0:
				signo=u'+'
			
			if author==botNick: #Avoid to check our edits
				return
			
			if re.search(patterns['destruir'], newText): #Proposed to delete? Skip
				wikipedia.output(u'Alguien ha marcado [[%s]] para destruir. Saltamos.' % pageTitle)
				return
			
			if re.search(patterns['conflictivos'], newText): #Avoid to check false positives pages
				wikipedia.output(u'[[%s]] es un artículo conflictivo, no lo analizamos' % pageTitle)
				return
			
			try: #Try to catch diff
				data=site.getUrl('/w/index.php?diff=%s&oldid=%s&diffonly=1' % (diff, oldid))
				data=data.split('<!-- start content -->')[1]
				data=data.split('<!-- end content -->')[0] #No change
			except:
				return #No diff, exit
			
			cleandata=cleandiff(pageTitle, data, patterns) #To clean diff text
			
			#Vandalism analysis
			#1) Blanking all
			[done, controlvand, statsDic]=avbotanalysis.isBlanking(namespace, pageTitle, author, userClass, authorEditNum, newbie, lenOld, lenNew, patterns, newText, controlvand, diff, site, pageHistory, botNick, oldText, p, oldid, statsDic, currentYear)
			if done:
				wikipedia.output(u'\03{lightred}Alert!: Blanking by %s in [[%s]]\03{default}' % (author, pageTitle))
				return
			
			#2) Section blanking
			#No se puede distinguir cuando el blanqueo de una sección es legítimo o no
			"""[done, controlvand, statsDic]=avbotanalysis.isSectionBlanking(namespace, pageTitle, author, userClass, authorEditNum, newbie, data, controlvand, diff, oldid, site, botNick, statsDic, p, oldText, pageHistory, currentYear)
			if done:
				wikipedia.output(u'\03{lightred}Alerta: Posible blanqueo de sección de %s en [[%s]]\03{default}' % (author, pageTitle))
				return"""
			
			
			#3) Section vandalisms
			[done, controlvand, statsDic]=avbotanalysis.isSectionVandalism(namespace, pageTitle, author, userClass, authorEditNum, newbie, data, controlvand, diff, oldid, site, botNick, statsDic, p, oldText, pageHistory, currentYear)
			if done:
				wikipedia.output(u'\03{lightred}Alerta: Posible vandalismo de sección de %s en [[%s]]\03{default}' % (author, pageTitle))
				return
			
			#deteccion vandalismos
			#
			#llamo a cleandiff, cuando isBlanking este unificado, poner data=cleandiff(pageTitle, data, patterns) arriba
			#unificar el autoSign, controlspam y todas las de este modulo tambien
			#
			#4) Common vandalism
			[done, score, details, controlvand, statsDic, type]=avbotanalysis.isVandalism(namespace, pageTitle, author, userClass, authorEditNum, newbie, vandalismos, cleandata, controlvand, p, pageHistory, diff, oldid, site, botNick, oldText, statsDic, currentYear)
			if done: 
				if type=='V':
					wikipedia.output(u'%s\n\03{lightred}Alerta: Posible vandalismo de %s en [[%s]] (%d puntos)\03{default}\nDetalles:\n%s\n%s' % ('-'*50, author, pageTitle, score, details, '-'*50))
				elif type=='P':
					wikipedia.output(u'%s\n\03{lightred}Alerta: Posible prueba de %s en [[%s]] (%d puntos)\03{default}\nDetalles:\n%s\n%s' % ('-'*50, author, pageTitle, score, details, '-'*50))
				return
			
			#5) Shocking images
			"""[done, controlvand, statsDic]=avbotanalysis.isShockingContent(namespace, pageTitle, author, userClass, authorEditNum, newbie, imageneschocantes, cleandata, controlvand, p, pageHistory, diff, oldid, site, botNick, oldText, statsDic, currentYear)
			if done: 
				wikipedia.output(u'\03{lightred}Alerta: Posible imagen chocante de %s en [[%s]]\03{default}' % (author, pageTitle))
				return"""
			
			#6) Anti-hoygans protection
			
			
			#deteccion vandalismos repetitivos
			# cambiar nacimientos por fallecimientos
			
			#7) Anti-birthday protection
			"""[done, motivo, controlvand, statsDic]=avbotanalysis.antiBirthday(pageTitle, userClass, authorEditNum, newbie, namespace, oldText, newText, cleandata, controlvand, site, pageHistory, diff, botNick, author, oldid, statsDic, p, currentYear)
			if done:
				wikipedia.output(u'\03{lightred}Alerta: %s en [[%s]]\03{default}' % (motivo, pageTitle))
				return"""
			
			
			#8) Auto-sign to anonymous users and newbies
			"""done=avbotanalysis.autoSign(userClass, authorEditNum, newbie, namespace, p, pageHistory, author, botNick, data, patterns, site, pageTitle, diff, newText)
			if done:
				wikipedia.output(u'\03{lightred}Alerta: Comentario sin firmar de %s en [[%s]]\03{default}' % (author, pageTitle))
				return"""
			
			#control de spam e imagenes de hostings ajenos
			if namespace==0 and (userClass=='anon' or (userClass=='reg' and authorEditNum<=newbie)):
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
						"""for j in whitelist:
							if re.search(j, url):
								white=True
								break"""
						for j in imagehostings:
							if re.search(j, url):
								imagehost=True
								break
						"""if not white:
							wikipedia.output(u'\03{lightgreen}Link por %s: %s\03{default}' % (author, url))
							if controlspam.has_key(author):
								if controlspam[author].has_key(url):
									controlspam[author][url][pageTitle]=diff
									if len(controlspam[author][url].items())==4 and not controlspam[author][url]['SPAMAVISADO']:
										controlspam[author][url]['SPAMAVISADO']=True #evitamos avisos duplicados que se producen cuando hay mucha actividad
										statsDic[2]['S']+=1
										statsDic[12]['S']+=1
										statsDic[24]['S']+=1
										artis=u''
										for k, v in controlspam[author][url].items():
											if k!='SPAMAVISADO':
												artis+=u'[http://es.wikipedia.org/w/index.php?diff=%s&oldid=prev %s], ' % (v, k)
										wikipedia.output(u'El usuario %s ha puesto al menos %d veces el link %s' % (author, len(controlspam[author][url].items())-1, url))
										wii=wikipedia.Page(site, u'User:AVBOT/Spam')
										restopag=wii.get()
										restopag=re.sub(ur'(?i)=== *Posible spam *===\n', ur'', restopag)
										wii.put(u'=== Posible spam ===\n;{{u|%s}} ha puesto %d veces %s: %s([http://es.wikipedia.org/w/index.php?title=Especial:Linksearch&target=%s ver todos]). No se avisará si continúa poniéndolo. [[Special:Blockip/%s|Bloquear]]. ({{subst:CURRENTTIME}} (UTC) del {{subst:CURRENTDAY}}/{{subst:CURRENTMONTH}}/{{subst:CURRENTYEAR}})\n\n%s' % (author, len(controlspam[author][url].items())-1, url, artis, url, author, restopag), u'BOT - Añadiendo aviso de posible spam')
								else:
									controlspam[author][url]={pageTitle: diff, 'SPAMAVISADO': False}
							else:
								controlspam[author]={url: {pageTitle: diff, 'SPAMAVISADO': False}}
							"""
						if imagehost:
							wikipedia.output(u'\03{lightred}Alerta: Avisando de cómo subir imágenes correctamente a [[User:%s]]\03{default}' % author)
							#avisamos al usuario
							avbotmsg.msgImageHost(author, site, pageTitle, diff)
							return
			
	else:
		wikipedia.output(u'LA HAN BORRADO? :/ [[%s]]' % pageTitle)

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

class AVBOT(SingleServerIRCBot):
	def __init__(self, channel, nickname, server, port=6667):
		SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
		self.channel = channel
		self.nickname = nickname
	
	def on_welcome(self, c, e):
		c.join(self.channel)
	
	def on_pubmsg(self, c, e):
		global speed
		global timeStatsDic
		global site
		global statsDic
		global contexto
		global pruebas
		global vandalismos
		global botNick
		
		#a=parseaentrada(a).encode('utf-8')
		linea = (e.arguments()[0])
		linea = parseaentrada(linea)
		nick = nm_to_n(e.source())
		#print '['+time.strftime('%H:%M:%S')+'] <'+nick+'> '+linea
		
		linea=re.sub(ur'\x03\d{0,2}', ur'', linea) #No colors
		linea=re.sub(ur'\x02\d{0,2}', ur'', linea) #No bold
		#wikipedia.output(linea)
		if re.search(patterns['edit'], linea):
			match=patterns['edit'].finditer(linea)
			for m in match:
				pageTitle=m.group('pageTitle')
				diff=m.group('diff')
				oldid=m.group('oldid')
				author=m.group('author')
				nm=m.group('nm')
				new=False
				minor=False
				if re.search('N', nm): #si es nuevo entraria en patterns['nuevo']
					new=True
				if re.search('M', nm):
					minor=True
				resume=m.group('resume')
				
				statsDic[2]['T']+=1
				statsDic[12]['T']+=1
				statsDic[24]['T']+=1
				speed+=1
				
				thread.start_new_thread(edicion,(pageTitle,author,new,minor,diff,oldid,resume))
				
				#Check resume for reverts
				if re.search(ur'(?i)(Revertidos los cambios de.*%s.*a la última edición de|Deshecha la edición \d+ de.*%s)' % (botNick, botNick), resume):
					wiii=wikipedia.Page(site, u'User:AVBOT/Errores/Automático')
					wiii.put(u'%s\n\n== [[%s]] ({{subst:CURRENTDAY}} de {{subst:CURRENTMONTHNAME}} de {{subst:CURRENTYEAR}}) ==\n* Diff: http://%s.wikipedia.org/w/index.php?diff=%s&oldid=%s\n* Autor de la reversión: {{u|%s}}' % (wiii.get(), pageTitle, site.lang, diff, oldid, author), u'BOT - Informe automático. [[User:%s|%s]] ha revertido a [[User:%s|%s]] en [[%s]]' % (author, author, botNick, botNick, pageTitle))
				break
		elif re.search(patterns['newpage'], linea):
			match=patterns['newpage'].finditer(linea)
			for m in match:
				pageTitle=m.group('pageTitle')
				diff=oldid=0
				author=m.group('author')
				nm=m.group('nm')
				new=True
				minor=False
				if re.search('M', nm):
					minor=True
				resume=''
				#time.sleep(5) #sino esperamos un poco, es posible que exists() devuelva false, hace que se quede indefinidamente intentando guardar la pagina, despues de q la destruyan
				thread.start_new_thread(edicion,(pageTitle,author,new,minor,diff,oldid,resume))
				speed+=1
				break
		elif re.search(patterns['block'], linea):
			match=patterns['block'].finditer(linea)
			for m in match:
				blocker=m.group('blocker')
				blocked=m.group('blocked')
				block=m.group('block')
				wikipedia.output(u'\03{lightblue}Registro combinado: [[User:%s]] (%d) ha sido bloqueado por [[User:%s]] (%d) por un plazo de %s\03{default}' % (blocked, len(blocked), blocker, len(blocker), block))
				thread.start_new_thread(avbotcomb.bloqueo,(site,blocker,blocked,block))
				break
		elif re.search(patterns['nuevousuario'], linea):
			match=patterns['nuevousuario'].finditer(linea)
			for m in match:
				usuario=m.group('usuario')
				wikipedia.output(u'\03{lightblue}Registro combinado: [[User:%s]] (%d) se acaba de registrar.\03{default}' % (usuario, len(usuario)))
				break
		elif re.search(patterns['borrado'], linea):
			match=patterns['borrado'].finditer(linea)
			for m in match:
				pageTitle=m.group('pageTitle')
				usuario=m.group('usuario')
				wikipedia.output(u'\03{lightblue}Registro combinado: [[%s]] ha sido borrado por [[User:%s]]\03{default}' % (pageTitle, usuario))
				break
		elif re.search(patterns['traslado'], linea):
			match=patterns['traslado'].finditer(linea)
			for m in match:
				usuario=m.group('usuario')
				origen=m.group('origen')
				destino=m.group('destino')
				wikipedia.output(u'\03{lightblue}Registro combinado: [[%s]] ha sido trasladado a [[%s]] por [[User:%s]]\03{default}' % (origen, destino, usuario))
				thread.start_new_thread(avbotcomb.traslado,(site,usuario,origen,destino))
				break
		elif re.search(patterns['protegida'], linea):
			match=patterns['protegida'].finditer(linea)
			for m in match:
				pageTitle=m.group('pageTitle')
				protecter=m.group('protecter')
				edit=m.group('edit')
				move=m.group('move')
				wikipedia.output(u'\03{lightblue}Registro combinado: [[%s]] (%d) ha sido protegida por [[User:%s]] (%d), edit=%s (%d), move=%s (%d)\03{default}' % (pageTitle, len(pageTitle), protecter, len(protecter), edit, len(edit), move, len(move)))
				if re.search(ur'autoconfirmed', edit) and re.search(ur'autoconfirmed', move):
					thread.start_new_thread(avbotcomb.semiproteger,(site,pageTitle,protecter))
				break
				
		else:
			wikipedia.output(u'No gestionada ---> %s' % linea)
			f=open('lineasnogestionadas.txt', 'a')
			linea=u'%s\n' % linea
			try:
				f.write(linea)
			except:
				try:
					f.write(linea.encode('utf-8'))
				except:
					pass
			f.close()
		
		#Calculating and showing statistics
		if time.time()-timeStatsDic['tvel']>=60: #Showing information in console every 60 seconds
			intervalo=int(time.time()-timeStatsDic['tvel'])
			wikipedia.output(u'\03{lightgreen}AVBOT working in %s.wikipedia.org\03{default}' % language)
			wikipedia.output(u'\03{lightgreen}Average speed: %d edits/minute\03{default}' % int(speed/(intervalo/60.0)))
			wikipedia.output(u'\03{lightgreen}Last 2 hours: V[%d], BL[%d], P[%d], S[%d], B[%d], M[%d], T[%d], D[%d]\03{default}' % (statsDic[2]['V'], statsDic[2]['BL'], statsDic[2]['P'], statsDic[2]['S'], statsDic[2]['B'], statsDic[2]['M'], statsDic[2]['T'], statsDic[2]['D']))
			timeStatsDic['tvel']=time.time()
			speed=0
		
		#Recalculating statistics
		for period in [2, 12, 24]: #Every 2, 12 and 24 hours
			statsDic[period]['M']=statsDic[period]['V']+statsDic[period]['BL']+statsDic[period]['P']+statsDic[period]['S']
			statsDic[period]['B']=statsDic[period]['T']-statsDic[period]['M']
			#Saving statistics
			if time.time()-timeStatsDic[period]>=60*60*period:
				avbotsave.saveStats(statsDic, period, site) #Saving statistics in Wikipedia pages for historical reasons
				timeStatsDic[period]=time.time() #Saving time begin
				statsDic[period]={'V':0,'BL':0,'P':0,'S':0,'B':0,'M':0,'T':0,'D':0} #Blanking statistics for a new period

def main(botNick, language):
	channel = '#%s.wikipedia' % language #RSS channel for recent changes in Wikipedia
	nickname = '%s%s' % (botNick, str(random.randint(10000, 99999))) #Bot nick in channel, with random numbers to avoid nick collisions
	
	bot = AVBOT(channel, nickname, 'irc.wikimedia.org', 6667) #Creating bot object
	bot.start() #Starting bot

if __name__ == '__main__':
	main(botNick, language)
