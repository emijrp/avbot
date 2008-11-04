# -*- coding: utf-8 -*-

#############################################
# TODO:  comprobar que ultimalinea del apartado firmar no esta mas de 1 vez
# modulo bienvenidas: tus pruebas de edicion en la WP:ZP se realizaron correctamente, revisar si ha sido revertido, si ha incluido imagenes de otros servidores .jpg, ultimas modificaciones
# revertir anidados por parte de varios usuarios, 
# categorias magicas, antiblanqueos de secciones
# no ha introducido url alguna http://es.wikipedia.org/w/index.php?diff=16088818&oldid=prev&diffonly=1
# comprobar que al revertir no se esta revirtiendo a un vandalismo de otro usuario
# poner quitar {{semiprotegido|pequeño=sí}}
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
# detectar por resumen cuando alguien revierte al bot, y dejar un aviso para ser revisado
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
import xxxload #
import xxxsave #
import xxxmsg #
import xxxchan #
import xxxanalysis #
import xxxcomb #

#-----------------------------------------------------------------------------------------------------------------------
# VARIABLES
#-----------------------------------------------------------------------------------------------------------------------
global ediciones
global admins
global bots
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
global obviar
global whitelist
global colors
global edits
global site
global botNick
global speed
global tvel
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
site=wikipedia.Site(language, 'wikipedia')
colors={'admin':'lightblue', 'bot':'lightpurple', 'reg':'lightgreen', 'anon':'lightyellow'}
edits={'admin':0,'bot':0,'reg':0,'anon':0}
today=datetime.date.today()
currentYear=today.year

#-----------------------------------------------------------------------------------------------------------------------
# PARAMETROS DE REVERSION
#-----------------------------------------------------------------------------------------------------------------------
# cuidado al incrementar el numero, que puede hacer que usuarios con acento parezcan novatos, Amadís=26
newbie=25 #hasta cuando se considera novato a un usuario

#-----------------------------------------------------------------------------------------------------------------------
# ESTADISTICAS
#-----------------------------------------------------------------------------------------------------------------------
speed=0
statsDic={}
statsDic[2]={'V':0,'BL':0,'P':0,'S':0,'B':0,'M':0,'T':0,'D':0}
statsDic[12]={'V':0,'BL':0,'P':0,'S':0,'B':0,'M':0,'T':0,'D':0}
statsDic[24]={'V':0,'BL':0,'P':0,'S':0,'B':0,'M':0,'T':0,'D':0}
timeStatsDic={2: time.time(), 12: time.time(), 24: time.time()}
tvel=time.time()
tact=time.time()

#-----------------------------------------------------------------------------------------------------------------------
# OTROS
#-----------------------------------------------------------------------------------------------------------------------
obviar=[u'Anexo:Diferencias de jerga o argot entre países hispanohablantes', u'Wikipedia:Zona de pruebas', u'Wikipedia:Cambiar el nombre de usuario']

wikipedia.output(u'%s\n# NOMBRE: AVBOT\n# VERSIÓN: 0.6\n# MISIÓN: REVERTIR VANDALISMOS, BLANQUEOS Y PRUEBAS DE EDICIÓN\n#         CONTROLAR EL SPAM\n#         FIRMAR COMENTARIOS ANONIMOS\n#         ACICALAR ARTÍCULOS NUEVOS\n#         FILTRO ANTICUMPLEAÑOS\n#         AVISAR DE VANDALISMO REINCIDENTE\n#         CONTROL DE IMÁGENES CHOCANTES\n%s\nCargando datos...' % ('#'*78, '#'*78))

#-----------------------------------------------------------------------------------------------------------------------
# CARGANDO DATOS...
#-----------------------------------------------------------------------------------------------------------------------
ediciones=xxxload.loadEdits(newbie)
admins=xxxload.loadAdmins(site)
bots=xxxload.loadBots(site)

contexto=ur'[ \@\º\ª\·\#\~\$\<\>\/\(\)\'\-\_\:\;\,\.\r\n\?\!\¡\¿\"\=\[\]\|\{\}\+\&]' #mejor no incluir \[ \] y \|  \{\} ???
pruebas=xxxload.loadTests(pruebas, contexto, site, botNick)
wikipedia.output(u"Cargadas y compiladas %d expresiones regulares para pruebas..." % len(pruebas.items()))
[vandalismos, error]=xxxload.loadVandalism(contexto, site, botNick)
wikipedia.output(u"Cargadas y compiladas %d expresiones regulares para vandalismos...%s" % (len(vandalismos.items()), error))
#[imageneschocantes, error]=xxxload.loadShockingImages(site)
#wikipedia.output(u"Cargadas %d imágenes chocantes y %d excepciones...%s" % (len(imageneschocantes['images'].items()), len(imageneschocantes['exceptions']), error))

#-----------------------------------------------------------------------------------------------------------------------
# PRECOMPILAMOS REGEXS
#-----------------------------------------------------------------------------------------------------------------------
patterns={
'blanqueos': re.compile(ur'(?i)redirect|desamb|\{\{ *(copyvio|destruir|plagio|robotdestruir|wikificar)'),
#14[[07Especial:Log/block14]]4 block10 02 5* 03Yeza 5*  10bloqueó a "02Usuario:87.219.206.12310" (sólo anónimos) durante un plazo de "31 horas".: [[WP:VAND|Vandalismo]] de páginas
#'bloqueo': re.compile(ur'(?i)\[\[...Usuario:(?P<blocked>.*?)..\]\].*?block.*?\*.....(?P<blocker>.*?)...\*'),
#[[Especial:Log/block]] block  * Alhen *  bloqueó a "Usuario:Tocapelotas" (desactivada la creación de cuentas) durante un plazo de "para siempre".: Cuenta creada para vandalizar
'bloqueo': re.compile(ur'(?i)\[\[Especial:Log/block\]\] +block +\* +(?P<blocker>.*?) +\* +bloqueó a +\"Usuario\:(?P<blocked>.*?)\" +.*?durante un plazo de \"(?P<castigo>.*?)\"'),
#[[Especial:Log/delete]] delete  * Snakeyes * borró "Discusión:Gastronomía en Estados Unidos": borrado rápido usando [[w:es:User:Axxgreazz/Monobook-Suite|monobook-suite]] el contenido era: «{{delete|Vandalismo}} {{fuenteprimaria|6|mayo}} Copia y pega el siguiente código en la página de discusión del creador del artículo: == Ediciones con investigac
#'borrado': re.compile(ur'(?i)\[\[...(?P<titulo>.*?)..\]\].*?delete.*?\*.....(?P<usuario>.*?)...\*'),
'borrado': re.compile(ur'(?i)\[\[Especial:Log/delete\]\] +delete +\* +(?P<usuario>.*?) +\* +borró +.(?P<titulo>.*?).\:'),
'conflictivos': re.compile(ur'(?i)\{\{ *(autotrad|maltrad|mal traducido|wikci|al? (wikcionario|wikicitas|wikinoticias|wikiquote|wikisource)) *\}\}'),
'destruir': re.compile(ur'(?i)\{\{ *destruir'),
#diffstylebegin y end va relacionado
'diffstylebegin': re.compile(ur'(<span class="diffchange">|<span class="diffchange diffchange-inline">|<ins class="diffchange diffchange-inline">)'),
'diffstyleend': re.compile(ur'(<span class="diffchange">|<span class="diffchange diffchange-inline">|<ins class="diffchange diffchange-inline">)([^<]*?)</(ins|span)>'),
'ip': re.compile(ur'(?im)^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'),
'firmas1': re.compile(ur'<td class="diff-addedline"><div>([^<]*?)</div>'),
'normal': re.compile(ur'(?i)\[\[(?P<titulo>.*?)\]\] +(?P<nm>.*?) +http\://es\.wikipedia\.org/w/index\.php\?title\=.*?diff\=(?P<diff>\d+)\&oldid\=(?P<oldid>\d+) +\* +(?P<author>.*?) +\* +\(.*?\) +(?P<resumen>.*)'),
'nuevo': re.compile(ur'(?i)\[\[(?P<titulo>.*?)\]\] +(?P<nm>.*?) +http\://es\.wikipedia\.org/wiki/.*? +\* (?P<author>.*?) +\*'),
'nuevousuario': re.compile(ur'(?i)\[\[Especial:Log/newusers\]\] +create +\* +(?P<usuario>.*?) +\* +Usuario nuevo'),
'protegida': re.compile(ur'(?i)\[\[Especial:Log/protect\]\] +protect +\* +(?P<protecter>.*?) +\* +protegió +\[\[(?P<titulo>.*?)\]\] +\[edit\=(?P<edit>sysop|autoconfirmed)\][^\[]*?\[move\=(?P<move>sysop|autoconfirmed)\]'),
#protegidacreacion [[Especial:Log/protect]] protect  * Snakeyes *  protegió [[Tucupido cincuentero]] [create=sysop]  (indefinido): Artículo ensayista reincidente
'desprotegida': re.compile(ur'(?i)\[\[.*?Especial\:Log/protect.*?\]\].*?unprotect'),
'spam': re.compile(ur'(?im)<td class="diff-addedline"><div>[^<]*?(http://[a-z0-9\.\-\=\?\_\/]+)[^<]*?</div></td>'),
#[[Especial:Log/move]] move_redir  * Manuel González Olaechea y Franco * [[Anexo:Presidente del Perú]] ha sido trasladado a [[Anexo:Presidentes del Perú]] sobre una redirección.
#[[Especial:Log/move]] move  * Dhidalgo *  [[Macizo Etíope]] ha sido trasladado a [[Macizo etíope]]
'traslado': re.compile(ur'(?i)\[\[Especial:Log/move\]\] +move +\* +(?P<usuario>.*?) +\* +\[\[(?P<origen>.*?)\]\] +ha sido trasladado a +\[\[(?P<destino>.*?)\]\]'),
}

#-----------------------------------------------------------------------------------------------------------------------
# LISTAS DE URLS, BLANCAS, IMAGE HOSTINGS...
#-----------------------------------------------------------------------------------------------------------------------
whitelist=[
re.compile(ur'(?i)http://commons.wikimedia\.org'),
re.compile(ur'(?i)http://[a-z]{2,3}\.wikipedia\.org'),
re.compile(ur'(?i)http://[a-z]{2,3}\.wiktionary\.org'),
re.compile(ur'(?i)http://[a-z]{2,3}\.wikisource\.org'),
re.compile(ur'(?i)http://[a-z]{2,3}\.wikiquote\.org'),
re.compile(ur'(?i)http://[a-z]{2,3}\.wikiversity\.org'),
]

imagehostings=[
re.compile(ur'(?i)http://img\d{1,3}\.imageshack\.us/'),
re.compile(ur'(?i)http://i\d{1,3}\.photobucket\.com/'),
]

wikipedia.output(u'Entrando al canal de IRC de cambios recientes...')

def cleandiff(wtitle, data, patterns):
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


def edicion(titulo, author, new, minor, diff, oldid, resumen):
	global ediciones
	global admins
	global bots
	global contexto
	global pruebas
	global vandalismos
	global imageneschocantes
	global controlspam
	global controlvand
	global obviar
	global whitelist
	global colors
	global edits
	global site
	global botNick
	global newbie
	global patterns
	global statsDic
	global currentYear
	
	p=wikipedia.Page(site, titulo)
	if p.exists():
		wtitle=p.title()
		namespace=p.namespace()
		
		if obviar.count(wtitle)!=0:
			return
		
		#recarga de expresiones regulares de vandalismos
		if wtitle==u'Usuario:Emijrp/Lista del bien y del mal.css':
			vandalismos=xxxload.reloadVandalism(contexto, site, botNick, vandalismos, author, diff)
			return #salimos
		
		if p.isRedirectPage():
			return
		else: #si es articulo o desambiguacion, analizamos
			nm=u''
			edicionesauthor=0
			if new:
				nm+=u'\03{lightred}N\03{default}'
			if minor:
				nm+=u'\03{lightred}m\03{default}'
			if nm:
				nm+=u' '
			userclass='anon'
			if admins.count(author)!=0:
				userclass='admin'
			elif bots.count(author)!=0:
				userclass='bot'
			elif not re.search(patterns['ip'], author):
				userclass='reg'
			
			#actualizando info de ediciones si se necesita
			if userclass!='anon':
				if ediciones.has_key(author):
					#actualizamos? dado de 10 caras
					if not random.randint(0,10): #afirmativo si sale cero
						ediciones[author]=xxxload.loadUserEdits(author, site, newbie)
						xxxsave.saveedits(ediciones)
				else:
					#cargamos
					ediciones[author]=xxxload.loadUserEdits(author, site, newbie)
					xxxsave.saveedits(ediciones)
				edicionesauthor=ediciones[author]
			
			#analisis de paginas nuevas
			if new:
				newtext=p.get()
				if userclass=='anon':
					wikipedia.output(u'%s[[%s]] {\03{%s}%s\03{default}} (+%d)' % (nm, wtitle, colors[userclass], author, len(newtext)))
				else:
					wikipedia.output(u'%s[[%s]] {\03{%s}%s\03{default}, %s ed.} (+%d)' % (nm, wtitle, colors[userclass], author, edicionesauthor, len(newtext)))
				
				[done, motivo, statsDic]=xxxanalysis.isRubbish(p, userclass, wtitle, newtext, colors, author, edicionesauthor, newbie, namespace, pruebas, vandalismos, statsDic)
				
				if done:
					wikipedia.output(u'\03{lightred}Alerta: Poniendo destruir en [[%s]]. Motivo: %s\03{default}' % (wtitle, motivo))
					return
				
				[done, resumen]=xxxanalysis.improveNewArticle(namespace, p)
				if done:
					wikipedia.output(u'\03{lightred}Alerta: Aplicando %s... a [[%s]]\03{default}' % (resumen, wtitle))
					return
					
				return #obligatorio si ha entrado en el if
			
			#coger historial
			oldtext=u''
			newtext=u''
			try:
				vh=p.getVersionHistory(revCount=10) #evitar que el bot entre en guerras de ediciones
				oldtext=p.getOldVersion(p.previousRevision()) #es la nueva forma
				newtext=p.get()
			except:
				return #es pagina nueva, deberia haber sido analizada antes
			
			lenold=len(oldtext)
			lennew=len(newtext)
			
			#diferencia de tamaños
			lendiff=lennew-lenold
			signo=u''
			if lendiff>0:
				signo=u'+'
			
			if userclass=='anon':
				wikipedia.output(u'%s[[%s]] {\03{%s}%s\03{default}} (%d/%d %s%d)' % (nm, wtitle, colors[userclass], author, lenold, lennew, signo, lendiff))
			else:
				wikipedia.output(u'%s[[%s]] {\03{%s}%s\03{default}, %s ed.} (%d/%d %s%d)' % (nm, wtitle, colors[userclass], author, edicionesauthor, lenold, lennew, signo, lendiff))
			
			return
			#evitamos analizar nuestras propias ediciones
			if author==botNick:
				return
			
			#destruires
			if re.search(patterns['destruir'], newtext):
				wikipedia.output(u'Alguien ha marcado [[%s]] para destruir' % wtitle)
				return
			
			#evitamos analizar articulos que pueden dar falsos positivos
			if re.search(patterns['conflictivos'], newtext):
				wikipedia.output(u'[[%s]] es un artículo conflictivo, no lo analizamos' % wtitle)
				return
			
			#capturamos diff
			try:
				data=site.getUrl('/w/index.php?diff=%s&oldid=%s&diffonly=1' % (diff, oldid))
				data=data.split('<!-- start content -->')[1]
				data=data.split('<!-- end content -->')[0] #no cambiar
			except:
				return #salimos
			
			cleandata=cleandiff(wtitle, data, patterns)
			#wikipedia.output(cleandata)
			
			#deteccion de blanqueos
			[done, controlvand, statsDic]=xxxanalysis.isBlanking(namespace, wtitle, author, userclass, edicionesauthor, newbie, lenold, lennew, patterns, newtext, controlvand, diff, site, vh, botNick, oldtext, p, oldid, statsDic, currentYear)
			if done:
				wikipedia.output(u'\03{lightred}Alerta: Posible blanqueo de %s en [[%s]]\03{default}' % (author, wtitle))
				return
			
			#deteccion de blanqueo de secciones
			"""[done, controlvand, statsDic]=xxxanalysis.isSectionBlanking(namespace, wtitle, author, userclass, edicionesauthor, newbie, data, controlvand, diff, oldid, site, botNick, statsDic, p, oldtext, vh, currentYear)
			if done:
				wikipedia.output(u'\03{lightred}Alerta: Posible blanqueo de sección de %s en [[%s]]\03{default}' % (author, wtitle))
				return"""
			
			#deteccion de pruebas
			"""[done, details, controlvand, statsDic]=xxxanalysis.isTest(namespace, wtitle, author, userclass, edicionesauthor, newbie, pruebas, cleandata, controlvand, diff, site, botNick, statsDic, p, oldtext, vh, currentYear)
			if done:
				wikipedia.output(u'%s\n\03{lightred}Alerta: Posible edición de prueba de %s en [[%s]]\03{default}\nDetalles:\n%s\n%s' % ('-'*50, author, wtitle, details, '-'*50))
				return"""
			
			#deteccion de texto vandalico tras ==Secciones== blabla................
			[done, controlvand, statsDic]=xxxanalysis.isSectionVandalism(namespace, wtitle, author, userclass, edicionesauthor, newbie, data, controlvand, diff, oldid, site, botNick, statsDic, p, oldtext, vh, currentYear)
			if done:
				wikipedia.output(u'\03{lightred}Alerta: Posible vandalismo de sección de %s en [[%s]]\03{default}' % (author, wtitle))
				return
			
			#deteccion vandalismos
			#
			#llamo a cleandiff, cuando isBlanking este unificado, poner data=cleandiff(wtitle, data, patterns) arriba
			#unificar el autoSign, controlspam y todas las de este modulo tambien
			#
			#
			[done, score, details, controlvand, statsDic]=xxxanalysis.isVandalism(namespace, wtitle, author, userclass, edicionesauthor, newbie, vandalismos, cleandata, controlvand, p, vh, diff, oldid, site, botNick, oldtext, statsDic, currentYear)
			if done: 
				wikipedia.output(u'%s\n\03{lightred}Alerta: Posible vandalismo de %s en [[%s]] (%d puntos)\03{default}\nDetalles:\n%s\n%s' % ('-'*50, author, wtitle, score, details, '-'*50))
				return
			
			#imagenes chocantes
			"""[done, controlvand, statsDic]=xxxanalysis.isShockingContent(namespace, wtitle, author, userclass, edicionesauthor, newbie, imageneschocantes, cleandata, controlvand, p, vh, diff, oldid, site, botNick, oldtext, statsDic, currentYear)
			if done: 
				wikipedia.output(u'\03{lightred}Alerta: Posible imagen chocante de %s en [[%s]]\03{default}' % (author, wtitle))
				return"""
			
			#antihoygans
			
			
			#deteccion vandalismos repetitivos
			# cambiar nacimientos por fallecimientos
			
			#proteccion anticumpleaños
			[done, motivo, controlvand, statsDic]=xxxanalysis.antiBirthday(wtitle, userclass, edicionesauthor, newbie, namespace, oldtext, newtext, cleandata, controlvand, site, vh, diff, botNick, author, oldid, statsDic, p, currentYear)
			if done:
				wikipedia.output(u'\03{lightred}Alerta: %s en [[%s]]\03{default}' % (motivo, wtitle))
				return
			
			
			#autofirmas solo en discusiones solo para anonimos y novatos
			"""done=xxxanalysis.autoSign(userclass, edicionesauthor, newbie, namespace, p, vh, author, botNick, data, patterns, site, wtitle, diff, newtext)
			if done:
				wikipedia.output(u'\03{lightred}Alerta: Comentario sin firmar de %s en [[%s]]\03{default}' % (author, wtitle))
				return"""
			
			#control de spam e imagenes de hostings ajenos
			if namespace==0 and (userclass=='anon' or (userclass=='reg' and edicionesauthor<=newbie)):
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
									controlspam[author][url][wtitle]=diff
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
									controlspam[author][url]={wtitle: diff, 'SPAMAVISADO': False}
							else:
								controlspam[author]={url: {wtitle: diff, 'SPAMAVISADO': False}}
							xxxsave.saveControlSpam(controlspam)"""
						if imagehost:
							wikipedia.output(u'\03{lightred}Alerta: Avisando de cómo subir imágenes correctamente a [[Usuario:%s]]\03{default}' % author)
							#avisamos al usuario
							xxxmsg.msgImageHost(author, site, wtitle, diff)
							return
			
	else:
		wikipedia.output(u'LA HAN BORRADO? :/ [[%s]]' % titulo)

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
		global tvel
		global timeStatsDic
		global site
		global statsDic
		global contexto
		global pruebas
		global vandalismos
		
		#a=parseaentrada(a).encode('utf-8')
		linea = (e.arguments()[0])
		linea = parseaentrada(linea)
		nick = nm_to_n(e.source())
		#print '['+time.strftime('%H:%M:%S')+'] <'+nick+'> '+linea
		
		linea=re.sub(ur'\x03\d{0,2}', ur'', linea) #colores
		linea=re.sub(ur'\x02\d{0,2}', ur'', linea) #negritas
		#wikipedia.output(linea)
		if re.search(patterns['normal'], linea):
			match=patterns['normal'].finditer(linea)
			for m in match:
				titulo=m.group('titulo')
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
				resumen=m.group('resumen')
				
				statsDic[2]['T']+=1
				statsDic[12]['T']+=1
				statsDic[24]['T']+=1
				speed+=1
				
				thread.start_new_thread(edicion,(titulo,author,new,minor,diff,oldid,resumen))
				break
		elif re.search(patterns['nuevo'], linea):
			match=patterns['nuevo'].finditer(linea)
			for m in match:
				titulo=m.group('titulo')
				#wikipedia.output(u'->%s<- (%d)' % (titulo, len(titulo)))
				diff=0
				oldid=0
				author=m.group('author')
				nm=m.group('nm')
				new=True
				minor=False
				if re.search('M', nm):
					minor=True
				resumen=''
				time.sleep(5) #sino esperamos un poco, es posible que exists() devuelva false
				thread.start_new_thread(edicion,(titulo,author,new,minor,diff,oldid,resumen))
				speed+=1
				break
		elif re.search(patterns['bloqueo'], linea):
			match=patterns['bloqueo'].finditer(linea)
			for m in match:
				blocker=m.group('blocker')
				blocked=m.group('blocked')
				castigo=m.group('castigo')
				wikipedia.output(u'\03{lightblue}Registro combinado: [[Usuario:%s]] (%d) ha sido bloqueado por [[Usuario:%s]] (%d) por un plazo de %s\03{default}' % (blocked, len(blocked), blocker, len(blocker), castigo))
				thread.start_new_thread(xxxcomb.bloqueo,(site,blocker,blocked,castigo))
				break
		elif re.search(patterns['nuevousuario'], linea):
			match=patterns['nuevousuario'].finditer(linea)
			for m in match:
				usuario=m.group('usuario')
				wikipedia.output(u'\03{lightblue}Registro combinado: [[Usuario:%s]] (%d) se acaba de registrar.\03{default}' % (usuario, len(usuario)))
				break
		elif re.search(patterns['borrado'], linea):
			match=patterns['borrado'].finditer(linea)
			for m in match:
				titulo=m.group('titulo')
				usuario=m.group('usuario')
				wikipedia.output(u'\03{lightblue}Registro combinado: [[%s]] ha sido borrado por [[Usuario:%s]]\03{default}' % (titulo, usuario))
				break
		elif re.search(patterns['traslado'], linea):
			match=patterns['traslado'].finditer(linea)
			for m in match:
				usuario=m.group('usuario')
				origen=m.group('origen')
				destino=m.group('destino')
				wikipedia.output(u'\03{lightblue}Registro combinado: [[%s]] ha sido trasladado a [[%s]] por [[Usuario:%s]]\03{default}' % (origen, destino, usuario))
				thread.start_new_thread(xxxcomb.traslado,(site,usuario,origen,destino))
				break
		elif re.search(patterns['protegida'], linea):
			match=patterns['protegida'].finditer(linea)
			for m in match:
				titulo=m.group('titulo')
				protecter=m.group('protecter')
				edit=m.group('edit')
				move=m.group('move')
				wikipedia.output(u'\03{lightblue}Registro combinado: [[%s]] (%d) ha sido protegida por [[Usuario:%s]] (%d), edit=%s (%d), move=%s (%d)\03{default}' % (titulo, len(titulo), protecter, len(protecter), edit, len(edit), move, len(move)))
				if re.search(ur'autoconfirmed', edit) and re.search(ur'autoconfirmed', move):
					thread.start_new_thread(xxxcomb.semiproteger,(site,titulo,protecter))
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
		if time.time()-tvel>=60: #Showing information in console every 60 seconds
			intervalo=int(time.time()-tvel)
			wikipedia.output(u'\03{lightgreen}Velocidad media: %d ediciones/minuto\03{default}' % int(speed/(intervalo/60.0)))
			wikipedia.output(u'\03{lightgreen}Resumen últimas 2 horas: V[%d], BL[%d], P[%d], S[%d], B[%d], M[%d], T[%d], D[%d]\03{default}' % (statsDic[2]['V'], statsDic[2]['BL'], statsDic[2]['P'], statsDic[2]['S'], statsDic[2]['B'], statsDic[2]['M'], statsDic[2]['T'], statsDic[2]['D']))
			tvel=time.time()
			speed=0
		
		#Recalculating statistics
		for period in [2, 12, 24]: #Every 2, 12 and 24 hours
			statsDic[period]['M']=statsDic[period]['V']+statsDic[period]['BL']+statsDic[period]['P']+statsDic[period]['S']
			statsDic[period]['B']=statsDic[period]['T']-statsDic[period]['M']
		
		#Saving statistics
		for period in [2, 12, 24]: #Every 2, 12 and 24 hours
			if time.time()-timeStatsDic[period]>=60*60*period:
				xxxsave.savestats(statsDic, period, site) #Saving statistics in Wikipedia pages for historical reasons
				timeStatsDic[period]=time.time() #Saving time begin
				statsDic[period]={'V':0,'BL':0,'P':0,'S':0,'B':0,'M':0,'T':0,'D':0} #Blanking statistics for a new period

def main(botNick, language):
	channel = '#%s.wikipedia' % language #RSS channel for recent changes in Wikipedia
	nickname = '%s%s' % (botNick, str(random.randint(1000, 9999))) #Bot nick in channel, with random numbers to avoid nick collisions
	
	bot = AVBOT(channel, nickname, 'irc.wikimedia.org', 6667) #Creating bot object
	bot.start() #Starting bot

if __name__ == '__main__':
	main(botNick, language)
