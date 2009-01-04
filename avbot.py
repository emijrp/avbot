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

## @package avbot
# Main module

# TODO:  revertir anidados por parte de varios usuarios, 
# no ha introducido url alguna http://es.wikipedia.org/w/index.php?diff=16088818&oldid=prev&diffonly=1
# comprobar que al revertir no se esta revirtiendo a un vandalismo de otro usuario
# revierte prueba a edicion mala http://es.wikipedia.org/w/index.php?title=Aparato_circulatorio&diff=16610029&oldid=16610024
# no revertir a una version en blanco http://es.wikipedia.org/w/index.php?title=Aristas&diff=prev&oldid=16807904
#controlar eliminacion de categorias e iws en masa, deleted-lines http://es.wikipedia.org/w/index.php?title=Tik%C3%BAn_Olam&diff=prev&oldid=16896350
#error frecuente: WARNING: No character set found.

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

# AVBOT modules
import avbotglobals
import avbotload     #Information and regexp loader
import avbotsave     #
import avbotmsg      #Send messages to vandals
import avbotanalysis #Edit analysis to find vandalisms, blanking, and similar malicious edits
import avbotcomb     #Trivia functions

# Variables
global imageneschocantes
imageneschocantes={}
global speed
global timeStatsDic
global currentYear

edits={'admin':0,'bot':0,'reg':0,'anon':0}
today=datetime.date.today()
currentYear=today.year

""" Statistics """
speed        = 0
timeStatsDic = {2: time.time(), 12: time.time(), 24: time.time(), 'tvel': time.time()}

""" Header message """
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
header += u"Loading data for %s: language of %s project" % (avbotglobals.preferences['language'], avbotglobals.preferences['family'])
wikipedia.output(header)

""" Data loaders """
userData               = {}
userData['edits']      = avbotload.loadEdits()
userData['admins']     = avbotload.loadAdmins()
userData['bots']       = avbotload.loadBots()
avbotload.loadExclusions()

"""Shocking images list """
#[imageneschocantes, error]=avbotload.loadShockingImages()
#wikipedia.output(u"Cargadas %d imágenes chocantes y %d excepciones...%s" % (len(imageneschocantes['images'].items()), len(imageneschocantes['exceptions']), error))

"""Regular expresions for vandalism edits """
error=avbotload.loadVandalism()
wikipedia.output(u"Loaded and compiled %d regular expresions for vandalism edits...%s" % (len(avbotglobals.vandalRegexps.items()), error))

wikipedia.output(u'Joining to recent changes IRC channel...\n')

class BOT(SingleServerIRCBot):
	""" BOT class """
	
	def __init__(self, userData):
		self.userData      = userData
		self.channel       = avbotglobals.preferences['channel']
		self.nickname      = avbotglobals.preferences['nickname']
		SingleServerIRCBot.__init__(self, [(avbotglobals.preferences['network'], avbotglobals.preferences['port'])], self.nickname, self.nickname)
	
	def on_welcome(self, c, e):
		""" Joins to IRC channel with Recent changes """
		
		c.join(self.channel)
	
	def on_pubmsg(self, c, e):
		""" Fetch and parse each line in the IRC channel """
		
		global speed
		global timeStatsDic
		
		editData={}
		
		line = (e.arguments()[0])
		line = avbotcomb.encodeLine(line)
		line = avbotcomb.cleanLine(line)
		nick = nm_to_n(e.source())
		
		editData['line']=line
		if re.search(avbotglobals.parserRegexps['edit'], line):
			match=avbotglobals.parserRegexps['edit'].finditer(line)
			for m in match:
				editData['pageTitle'] = m.group('pageTitle')
				editData['diff']      = m.group('diff')
				editData['oldid']     = m.group('oldid')
				editData['author']    = m.group('author')
				editData['userClass'] = avbotcomb.getUserClass(self.userData, editData)
				self.userData         = avbotcomb.updateUserDataIfNeeded(self.userData, editData)
				nm=m.group('nm')
				editData['new']       = editData['minor']=False
				if re.search('N', nm):
					editData['new']   = True
				if re.search('M', nm):
					editData['minor'] = True
				editData['resume']    = m.group('resume')
				
				#Reload vandalism regular expresions
				if editData['pageTitle']==u'Usuario:Emijrp/Lista del bien y del mal.css':
					avbotload.reloadVandalism(editData['author'], editData['diff'])
				
				#Reload exclusion list
				if editData['pageTitle']==u'Usuario:Emijrp/Exclusiones.css':
					avbotload.loadExclusions()
				
				avbotanalysis.incrementaStats('T')
				speed   += 1
				
				thread.start_new_thread(avbotanalysis.editAnalysis,(self.userData,editData))
				
				#Check resume for reverts
				if re.search(ur'(?i)(Revertidos los cambios de.*%s.*a la última edición de|Deshecha la edición \d+ de.*%s)' % (avbotglobals.preferences['botNick'], avbotglobals.preferences['botNick']), editData['resume']) and editData['pageTitle']!='Usuario:AVBOT/Errores/Automático':
					wiii=wikipedia.Page(avbotglobals.preferences['site'], u'User:AVBOT/Errores/Automático')
					wiii.put(u'%s\n\n== [[%s]] ({{subst:CURRENTDAY}} de {{subst:CURRENTMONTHNAME}} de {{subst:CURRENTYEAR}}) ==\n* Diff: http://%s.wikipedia.org/w/index.php?diff=%s&oldid=%s\n* Autor de la reversión: {{u|%s}}' % (wiii.get(), editData['pageTitle'], avbotglobals.preferences['language'], editData['diff'], editData['oldid'], editData['author']), u'BOT - Informe automático. [[User:%s|%s]] ha revertido a [[User:%s|%s]] en [[%s]]' % (editData['author'], editData['author'], avbotglobals.preferences['botNick'], avbotglobals.preferences['botNick'], editData['pageTitle']))
		elif re.search(avbotglobals.parserRegexps['newpage'], line):
			match=avbotglobals.parserRegexps['newpage'].finditer(line)
			for m in match:
				editData['pageTitle']=m.group('pageTitle')
				
				#Avoid analysis of excluded pages
				if avbotglobals.excludedPages.has_key(editData['pageTitle']):
					return #Exit
				
				editData['diff']=editData['oldid']=0
				editData['author']=m.group('author')
				editData['userClass'] = avbotcomb.getUserClass(userData, editData)
				
				nm=m.group('nm')
				editData['new']=True
				editData['minor']=False
				if re.search('M', nm):
					editData['minor']=True
				editData['resume']=u''
				
				#Avoid analysis of excluded pages
				if avbotglobals.excludedPages.has_key(editData['pageTitle']):
					return #Exit
				
				#time.sleep(5) #sino esperamos un poco, es posible que exists() devuelva false, hace que se quede indefinidamente intentando guardar la pagina, despues de q la destruyan
				thread.start_new_thread(avbotanalysis.editAnalysis,(self.userData,editData))
				speed+=1
		elif re.search(avbotglobals.parserRegexps['block'], line):
			match=avbotglobals.parserRegexps['block'].finditer(line)
			for m in match:
				blocker=m.group('blocker')
				blocked=m.group('blocked')
				block=m.group('block')
				wikipedia.output(u'\03{lightblue}Registro combinado: [[User:%s]] (%d) ha sido bloqueado por [[User:%s]] (%d) por un plazo de %s\03{default}' % (blocked, len(blocked), blocker, len(blocker), block))
				thread.start_new_thread(avbotcomb.bloqueo,(blocker,blocked,block))
		elif re.search(avbotglobals.parserRegexps['nuevousuario'], line):
			match=avbotglobals.parserRegexps['nuevousuario'].finditer(line)
			for m in match:
				usuario=m.group('usuario')
				wikipedia.output(u'\03{lightblue}Registro combinado: [[User:%s]] (%d) se acaba de registrar.\03{default}' % (usuario, len(usuario)))
		elif re.search(avbotglobals.parserRegexps['borrado'], line):
			match=avbotglobals.parserRegexps['borrado'].finditer(line)
			for m in match:
				pageTitle=m.group('pageTitle')
				usuario=m.group('usuario')
				wikipedia.output(u'\03{lightblue}Registro combinado: [[%s]] ha sido borrado por [[User:%s]]\03{default}' % (pageTitle, usuario))
		elif re.search(avbotglobals.parserRegexps['traslado'], line):
			match=avbotglobals.parserRegexps['traslado'].finditer(line)
			for m in match:
				usuario=m.group('usuario')
				origen=m.group('origen')
				destino=m.group('destino')
				wikipedia.output(u'\03{lightblue}Registro combinado: [[%s]] ha sido trasladado a [[%s]] por [[User:%s]]\03{default}' % (origen, destino, usuario))
				thread.start_new_thread(avbotcomb.traslado,(usuario,origen,destino))
		elif re.search(avbotglobals.parserRegexps['protegida'], line):
			match=avbotglobals.parserRegexps['protegida'].finditer(line)
			for m in match:
				pageTitle=m.group('pageTitle')
				protecter=m.group('protecter')
				edit=m.group('edit')
				move=m.group('move')
				wikipedia.output(u'\03{lightblue}Registro combinado: [[%s]] (%d) ha sido protegida por [[User:%s]] (%d), edit=%s (%d), move=%s (%d)\03{default}' % (pageTitle, len(pageTitle), protecter, len(protecter), edit, len(edit), move, len(move)))
				if re.search(ur'autoconfirmed', edit) and re.search(ur'autoconfirmed', move):
					thread.start_new_thread(avbotcomb.semiproteger,(pageTitle,protecter))
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
		if time.time()-timeStatsDic['tvel']>=avbotglobals.preferences['statsDelay']: #Showing information in console every 60 seconds
			intervalo = int(time.time()-timeStatsDic['tvel'])
			wikipedia.output(u'\03{lightgreen}AVBOT working for %s: language of %s project\03{default}' % (avbotglobals.preferences['language'], avbotglobals.preferences['family']))
			wikipedia.output(u'\03{lightgreen}Average speed: %d edits/minute\03{default}' % int(speed/(intervalo/60.0)))
			wikipedia.output(u'\03{lightgreen}Last 2 hours: V[%d], BL[%d], P[%d], S[%d], B[%d], M[%d], T[%d], D[%d]\03{default}' % (avbotglobals.statsDic[2]['V'], avbotglobals.statsDic[2]['BL'], avbotglobals.statsDic[2]['P'], avbotglobals.statsDic[2]['S'], avbotglobals.statsDic[2]['B'], avbotglobals.statsDic[2]['M'], avbotglobals.statsDic[2]['T'], avbotglobals.statsDic[2]['D']))
			legend=u''
			for k,v in avbotglobals.preferences['colors'].items():
				legend+=u'\03{%s}%s\03{default}, ' % (v, k)
			wikipedia.output(u'Legend: %s...' % legend)
			timeStatsDic['tvel'] = time.time()
			speed                = 0
		
		#Recalculating statistics
		for period in [2, 12, 24]: #Every 2, 12 and 24 hours
			avbotglobals.statsDic[period]['M']=avbotglobals.statsDic[period]['V']+avbotglobals.statsDic[period]['BL']+avbotglobals.statsDic[period]['P']+avbotglobals.statsDic[period]['S']
			avbotglobals.statsDic[period]['B']=avbotglobals.statsDic[period]['T']-avbotglobals.statsDic[period]['M']
			
			if time.time()-timeStatsDic[period]>=3600*period:
				avbotsave.saveStats(avbotglobals.statsDic, period, avbotglobals.preferences['site'])          #Saving statistics in Wikipedia pages for historical reasons
				timeStatsDic[period]=time.time()                                    #Saving time begin
				avbotglobals.statsDic[period]={'V':0,'BL':0,'P':0,'S':0,'B':0,'M':0,'T':0,'D':0} #Blanking statistics for a new period

def main(userData):
	""" Creates and launches a bot object """
	
	bot = BOT(userData)
	bot.start()

if __name__ == '__main__':
	main(userData)
