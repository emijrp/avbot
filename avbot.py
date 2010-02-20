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

#TODO
#sameoldid, evitar que cargue siempr y aproveche el oldtext anterior
#evitar guerras de edicion por clones de avbot, sol: pagina que liste los clones? lin 135 avbotanalysis
#subpaginas centralizadas y sin centralizar en el avbotload
#que no conflicteen las subpáginas de estadisticas
#que se baje el codigo de rediris y lo compruebe con los fucheros locales
#hacer independiente de verdad lo de 'v', 'bl', 'c', etc


## @package avbot
# Main module\n
# Módulo principal

""" External modules """
""" Python modules """
import os,sys,re
import threading,thread
import httplib,urllib,urllib2
import time,datetime
import string,math,random
import random

""" irclib modules """
from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_h, irc_lower, ip_numstr_to_quad, ip_quad_to_numstr

""" pywikipediabot modules """
import wikipedia, difflib

""" AVBOT modules """
import avbotglobals  #Shared info
import avbotload     #Data and regexp loader
import avbotsave     #Saving info in files
import avbotmsg      #Send messages to vandals
import avbotanalysis #Edit analysis to find vandalisms, blanking, and similar malicious edits
import avbotcomb     #Trivia functions

""" Continue header message """
header =  u"Loading data for %s: language of %s project\n" % (avbotglobals.preferences['language'], avbotglobals.preferences['family'])
header += u"Newbie users are those who have done %s edits or less" % avbotglobals.preferences['newbie']
wikipedia.output(header)

class BOT(SingleServerIRCBot):
	""" Clase BOT """
	""" BOT class """
	
	def __init__(self):
		"""  """
		"""  """
		self.channel       = avbotglobals.preferences['channel']
		self.nickname      = avbotglobals.preferences['nickname']
		
		""" Data loaders """
		avbotload.loadEdits()
		avbotload.loadSysops()
		avbotload.loadBots()
		avbotload.loadExclusions()
		
		"""Messages"""
		avbotload.loadMessages()
		wikipedia.output(u"Loaded %d messages..." % (len(avbotglobals.preferences['msg'].items())))
		
		"""Regular expresions for vandalism edits """
		error=avbotload.loadRegexpList()
		wikipedia.output(u"Loaded and compiled %d regular expresions for vandalism edits...%s" % (len(avbotglobals.vandalRegexps.items()), error))
		
		wikipedia.output(u'Joining to recent changes IRC channel...\n')
		SingleServerIRCBot.__init__(self, [(avbotglobals.preferences['network'], avbotglobals.preferences['port'])], self.nickname, self.nickname)
	
	def on_welcome(self, c, e):
		""" Se une al canal de IRC de Cambios recientes """
		""" Joins to IRC channel with Recent changes """
		
		c.join(self.channel)
	
	def on_privmsg(self, c, e):
		line = (e.arguments()[0])
		line = avbotcomb.encodeLine(line)
		nick = nm_to_n(e.source())
		
		f=open('privados.txt', 'a')
		timestamp=time.strftime('%X %x')
		line=timestamp+' '+nick+' > '+line+'\n'
		f.write(line.encode('utf-8'))
		f.close()
	
	def on_pubmsg(self, c, e):
		""" Captura cada línea del canal de IRC """
		""" Fetch and parse each line in the IRC channel """
		
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
				editData['userClass'] = avbotcomb.getUserClass(editData)
				
				avbotcomb.updateUserDataIfNeeded(editData)
				
				nm=m.group('nm')
				editData['new']       = editData['minor']=False
				if re.search('N', nm):
					editData['new']   = True
				if re.search('M', nm):
					editData['minor'] = True
				editData['resume']    = m.group('resume')
				
				avbotanalysis.updateStats('t')
				avbotglobals.statsTimersDic['speed'] += 1
				
				#Avoid to check our edits
				if editData['author'] == avbotglobals.preferences['botNick']: 
					return #Exit
				
				#Reload vandalism regular expresions
				if re.search(ur'%s\:%s\/Lista del bien y del mal\.css' %(avbotglobals.namespaces[2], avbotglobals.preferences['ownerNick']), editData['pageTitle']):
					avbotload.reloadRegexpList(editData['author'], editData['diff'])
				
				#Reload exclusion list
				if re.search(ur'%s\:%s\/Exclusiones\.css' % (avbotglobals.namespaces[2], avbotglobals.preferences['ownerNick']), editData['pageTitle']):
					avbotload.loadExclusions()
				
				thread.start_new_thread(avbotanalysis.editAnalysis,(editData,))
				
				#Check resume for reverts
				if re.search(ur'(?i)(Revertidos los cambios de.*%s.*a la última edición de|Deshecha la edición \d+ de.*%s)' % (avbotglobals.preferences['botNick'], avbotglobals.preferences['botNick']), editData['resume']) and editData['pageTitle']!='Usuario:AVBOT/Errores/Automático':
					wiii=wikipedia.Page(avbotglobals.preferences['site'], u'User:AVBOT/Errores/Automático')
					wiii.put(u'%s\n# [[%s]], {{subst:CURRENTDAY}} de {{subst:CURRENTMONTHNAME}} de {{subst:CURRENTYEAR}}, http://%s.wikipedia.org/w/index.php?diff=%s&oldid=%s, {{u|%s}}' % (wiii.get(), editData['pageTitle'], avbotglobals.preferences['language'], editData['diff'], editData['oldid'], editData['author']), u'BOT - Informe automático. [[User:%s|%s]] ha revertido a [[User:%s|%s]] en [[%s]]' % (editData['author'], editData['author'], avbotglobals.preferences['botNick'], avbotglobals.preferences['botNick'], editData['pageTitle']))
		elif re.search(avbotglobals.parserRegexps['newpage'], line):
			match=avbotglobals.parserRegexps['newpage'].finditer(line)
			for m in match:
				editData['pageTitle']=m.group('pageTitle')
				
				#Avoid analysis of excluded pages
				if avbotglobals.excludedPages.has_key(editData['pageTitle']):
					return #Exit
				
				editData['diff']=editData['oldid']=0
				editData['author']=m.group('author')
				editData['userClass'] = avbotcomb.getUserClass(editData)
				
				avbotcomb.updateUserDataIfNeeded(editData)
				
				nm=m.group('nm')
				editData['new']=True
				editData['minor']=False
				if re.search('M', nm):
					editData['minor']=True
				editData['resume']=u''
				
				#Avoid analysis of excluded pages
				if avbotglobals.excludedPages.has_key(editData['pageTitle']):
					return #Exit
				
				avbotanalysis.updateStats('t')
				avbotglobals.statsTimersDic['speed'] += 1
				
				#time.sleep(5) #sino esperamos un poco, es posible que exists() devuelva false, hace que se quede indefinidamente intentando guardar la pagina, despues de q la destruyan
				thread.start_new_thread(avbotanalysis.editAnalysis,(editData,))
		elif re.search(avbotglobals.parserRegexps['block'], line):
			match=avbotglobals.parserRegexps['block'].finditer(line)
			for m in match:
				blocker=m.group('blocker')
				blocked=m.group('blocked')
				block=m.group('block')
				wikipedia.output(u'\03{lightblue}Registro combinado: [[User:%s]] (%d) ha sido bloqueado por [[User:%s]] (%d) por un plazo de %s\03{default}' % (blocked, len(blocked), blocker, len(blocker), block))
				thread.start_new_thread(avbotcomb.blockedUser,(blocker,blocked,block))
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
		elif re.search(avbotglobals.parserRegexps['protegida'], line):
			match=avbotglobals.parserRegexps['protegida'].finditer(line)
			for m in match:
				pageTitle=m.group('pageTitle')
				protecter=m.group('protecter')
				edit=m.group('edit')
				move=m.group('move')
				wikipedia.output(u'\03{lightblue}Registro combinado: [[%s]] (%d) ha sido protegida por [[User:%s]] (%d), edit=%s (%d), move=%s (%d)\03{default}' % (pageTitle, len(pageTitle), protecter, len(protecter), edit, len(edit), move, len(move)))
				#http://es.wikipedia.org/w/index.php?oldid=23222363#Candados
				#if re.search(ur'autoconfirmed', edit) and re.search(ur'autoconfirmed', move):
				#	thread.start_new_thread(avbotcomb.semiprotect,(pageTitle,protecter))
		else:
			#wikipedia.output(u'No gestionada ---> %s' % line)
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
		if time.time()-avbotglobals.statsTimersDic['tvel']>=avbotglobals.preferences['statsDelay']: #Showing information in console every X seconds
			intervalo = int(time.time()-avbotglobals.statsTimersDic['tvel'])
			wikipedia.output(u'\03{lightgreen}%s working for %s: language of %s project\03{default}' % (avbotglobals.preferences['botNick'], avbotglobals.preferences['language'], avbotglobals.preferences['family']))
			wikipedia.output(u'\03{lightgreen}Average speed: %d edits/minute\03{default}' % int(avbotglobals.statsTimersDic['speed']/(intervalo/60.0)))
			wikipedia.output(u'\03{lightgreen}Last 2 hours: V[%d], BL[%d], P[%d], S[%d], B[%d], M[%d], T[%d], D[%d]\03{default}' % (avbotglobals.statsDic[2]['v'], avbotglobals.statsDic[2]['bl'], avbotglobals.statsDic[2]['p'], avbotglobals.statsDic[2]['s'], avbotglobals.statsDic[2]['b'], avbotglobals.statsDic[2]['m'], avbotglobals.statsDic[2]['t'], avbotglobals.statsDic[2]['d']))
			legend=u''
			for k,v in avbotglobals.preferences['colors'].items():
				legend+=u'\03{%s}%s\03{default}, ' % (v, k)
			wikipedia.output(u'Colors meaning: %s...' % legend)
			avbotglobals.statsTimersDic['tvel'] = time.time()
			avbotglobals.statsTimersDic['speed'] = 0
		
		#Recalculating statistics
		for period in [2, 12, 24]: #Every 2, 12 and 24 hours
			avbotglobals.statsDic[period]['m']=avbotglobals.statsDic[period]['v']+avbotglobals.statsDic[period]['bl']+avbotglobals.statsDic[period]['p']+avbotglobals.statsDic[period]['s']
			avbotglobals.statsDic[period]['b']=avbotglobals.statsDic[period]['t']-avbotglobals.statsDic[period]['m']
			
			if time.time()-avbotglobals.statsTimersDic[period]>=3600*period:
				avbotsave.saveStats(avbotglobals.statsDic, period, avbotglobals.preferences['site'])     #Saving statistics in Wikipedia pages for historical reasons
				avbotglobals.statsTimersDic[period] = time.time()                                        #Saving start time
				avbotglobals.statsDic[period]       = {'v':0,'bl':0,'p':0,'s':0,'b':0,'m':0,'t':0,'d':0} #Blanking statistics for a new period

def main():
	""" Crea un objeto BOT y lo lanza """
	""" Creates and launches a bot object """
	
	if os.path.isfile(avbotglobals.existFile):
		os.system("rm %s" % avbotglobals.existFile)
		wikipedia.output(u"Eliminado fichero %s" % avbotglobals.existFile)
		sys.exit()
	else:
		try:
			PID=open(avbotglobals.pidFile, 'r')
			oldpid=PID.read()
			PID.close()
			os.system("kill -9 %s" % oldpid)
		except:
			wikipedia.output(u"Hubo un error al intentar matar el proceso anterior")
		
		#Writing current PID
		PID=open(avbotglobals.pidFile, 'w')
		PID.write(str(os.getpid()))
		PID.close()
	
	#launching existence file generator
	thread.start_new_thread(avbotcomb.existenceFile,())
	
	#Starting bot...
	bot = BOT()
	bot.start()

if __name__ == '__main__':
	main()
