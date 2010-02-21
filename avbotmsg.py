# -*- coding: utf-8 -*-

# AVBOT - Anti-Vandalism BOT for MediaWiki projects
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

## @package avbotmsg
# Module for send messages\n
# Módulo para enviar mensajes

import re
import wikipedia
import os
import sys
import time
import random

# AVBOT modules
import avbotglobals
import avbotcomb

def msgVandalismoEnCurso(dic_vand, author, userclass, blockedInEnglishWikipedia):
	""" Gestiona la página de Vandalismo en curso """
	""" Manage Vandalismo en curso page """
	if avbotglobals.preferences['site'].lang!='es':
		return
	explanation=u""
	report=u''
	resume=u''
	for k, v in dic_vand.items():
		if k!='avisos':
			wtitle=v[0]
			wtitle_=re.sub(" ", "_", wtitle)
			explanation+=u"[http://es.wikipedia.org/w/index.php?title=%s&diff=%s&oldid=prev %s], " % (wtitle_, k, wtitle)
	wikipedia.output(u"El usuario %s ha vandalizado varias veces" % author)
	wii=wikipedia.Page(avbotglobals.preferences['site'], u"Wikipedia:Vandalismo en curso")
	restopag=wii.get()
	
	#evitamos avisar dos veces
	if re.search(ur'(?im)^\=* *%s *\=*' % author, restopag): #existe ya un aviso
		return
	
	if userclass=='reg':
		report+=u'<!-- completa los datos tras las "flechitas" -->\n{{subst:Reportevandalismo\n| 1 = %s\n| 2 = %s\n| 3 = ~~~~\n}}' % (author, explanation)
	else:
		if blockedInEnglishWikipedia[1]: #esta bloqueado en la inglesa y es proxy?
			explanation+=blockedInEnglishWikipedia[0]
			resume+=u". Bloqueado en Wikipedia en inglés"
			explanation+=u" (Posible proxy)"
			resume+=u" (Posible proxy)"
		report+=u'<!-- completa los datos tras las "flechitas" -->\n{{subst:ReportevandalismoIP\n| 1 = %s\n| 2 = %s\n| 3 = ~~~~\n}}' % (author, explanation)
	if not avbotglobals.preferences['nosave']:
		wii.put(u'%s\n\n%s' % (restopag, report), u'BOT - Añadiendo aviso de vandalismo reincidente de [[Special:Contributions/%s|%s]]%s' % (author, author, resume))

def haveIRevertedThisVandalism(wtitle, diff):
	""" Verifica que ha sido este bot el que ha revertido el vandalismo """
	""" Check if this bot has reverted this vandalism """
	vandalisedPage=wikipedia.Page(avbotglobals.preferences['site'], wtitle)
	vandalisedPageHistory=vandalisedPage.getVersionHistory(revCount=10)
	c=0
	while vandalisedPageHistory[c][0]!=diff and c<len(vandalisedPageHistory):
		c+=1
	if c>0 and vandalisedPageHistory[c-1][2]==avbotglobals.preferences['botNick']:
		return True
	else:
		return False

def sendMessage(author, wtitle, diff, n, tipo):
	""" Envía mensajes de advertencia a un usuario """
	""" Send messages to an user  """
	#esperamos un tiempo aleatorio para evitar lag, conflictos de edición...
	time.sleep(random.randint(5,10))
	
	if avbotglobals.preferences['site'].lang!='es':
		return
	talkpage=wikipedia.Page(avbotglobals.preferences['site'], u"User talk:%s" % author)
	
	avisotexto=u""
	wtitle2=wtitle
	wtext=u""
	if re.search(ur'(?i)Categor(ía|y)\:', wtitle2):
		wtitle2=u':%s' % wtitle2
	if talkpage.exists() and not talkpage.isRedirectPage():
		wtext=talkpage.get()
	
	#he revertido yo u otro usuario?
	if not haveIRevertedThisVandalism(wtitle, diff):
		return
	#evitamos avisar dos veces
	if re.search(ur'(?im)%s' % diff, wtext): #existe ya un aviso para esta oldid?
		return
	
	if n==3: #If n>3, no more messages
		template=u"%sInminente.css" % avbotglobals.preferences['msg'][tipo]['template']
		templatepage=wikipedia.Page(avbotglobals.preferences['site'], template)
		if templatepage.exists():
			avisotexto+=u"{{subst:%s|%s|%s}}" % (template, wtitle2, diff)
		else:
			wikipedia.output(u'"%s" page doesnt exist. Please create it. Parameter 1: Title, Parameter 2: Diff' % template)
			sys.exit()
	elif n<3:
		template=u"%s.css" % avbotglobals.preferences['msg'][tipo]['template']
		templatepage=wikipedia.Page(avbotglobals.preferences['site'], template)
		if templatepage.exists():
			avisotexto+=u"{{subst:%s|%s|%s|%s}}" % (template, wtitle2, diff, n)
		else:
			wikipedia.output(u'"%s" page doesnt exist. Please create it. Parameter 1: Title, Parameter 2: Diff, Parameter 3: Message #number' % template)
			sys.exit()
	
	if avisotexto:
		if wtext:
			wtext+="\n\n"
		wtext+=avisotexto
		if not avbotglobals.preferences['nosave']:
			talkpage.put(wtext, u"BOT - Avisando a [[Special:Contributions/%s|%s]] de que su edición en [[%s]] ha sido revertida (Aviso #%d)" % (author, author, wtitle, n))

def msgBlock(blocked, blocker):
	""" Envía mensaje de bloqueo a un usuario """
	""" Send block message to an user """
	if avbotglobals.preferences['site'].lang!='es':
		return
	aviso=wikipedia.Page(avbotglobals.preferences['site'], u"User talk:%s" % blocked)
	avisotexto=u""
	if aviso.exists():
		avisotexto+=u"%s\n\n" % aviso.get()
	avisotexto+=u"{{subst:User:%s/AvisoBloqueo.css|%s}}" % (avbotglobals.preferences['ownerNick'], blocker)
	if not avbotglobals.preferences['nosave']:
		aviso.put(avisotexto, u"BOT - Avisando a [[Special:Contributions/%s|%s]] de que ha sido bloqueado por [[User:%s|%s]]" % (blocked, blocked, blocker, blocker))
