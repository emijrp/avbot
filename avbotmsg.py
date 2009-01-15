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

## @package avbotmsg
# Module for send messages to users

import re
import wikipedia
import os

# AVBOT modules
import avbotglobals
import avbotcomb

def msgVandalismoEnCurso(dic_vand, author, userclass, blockedInEnglishWikipedia):
	"""  """
	"""  """
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
	wii.put(u'%s\n\n%s' % (restopag, report), u'BOT - Añadiendo aviso de vandalismo reincidente de [[Special:Contributions/%s|%s]]%s' % (author, author, resume))

def sendMessage(author, wtitle, diff, n, tipo):
	"""  """
	"""  """
	if avbotglobals.preferences['site'].lang!='es':
		return
	talkpage=wikipedia.Page(avbotglobals.preferences['site'], u"User talk:%s" % author)
	avisotexto=u""
	wtitle2=wtitle
	wtext=u""
	if re.search(ur'(?i)Categor(ía|y)\:', wtitle2):
		wtitle2=u':%s' % wtitle2
	if talkpage.exists():
		wtext=talkpage.get()
	
	if n==3: #If n>3, no more messages
		avisotexto+=u"{{subst:%sInminente|%s|%s}}" % (avbotglobals.preferences['msg'][tipo]['template'], wtitle2, diff)
	elif n<3:
		avisotexto+=u"{{subst:%s|%s|%s|%s}}" % (avbotglobals.preferences['msg'][tipo]['template'], wtitle2, diff, n)
	
	if avisotexto:
		if wtext:
			wtext+="\n\n"
		wtext+=avisotexto
		talkpage.put(wtext, u"BOT - Avisando a [[Special:Contributions/%s|%s]] de que su edición en [[%s]] ha sido revertida (Aviso #%d)" % (author, author, wtitle, n))

def msgContenidoChocante(author, wtitle, diff, n):
	"""  """
	"""  """
	return sendMessage(author, wtitle, diff, n, u'Contenido chocante')

def msgEnlaceIrrelevante(author, wtitle, diff, n):
	"""  """
	"""  """
	return sendMessage(author, wtitle, diff, n, u'Enlace irrelevante')

def msgFechaImposible(author, wtitle, diff, n):
	"""  """
	"""  """
	return sendMessage(author, wtitle, diff, n, u'Fecha imposible')

def msgBloqueo(blocked, blocker):
	"""  """
	"""  """
	aviso=wikipedia.Page(avbotglobals.preferences['site'], u"User talk:%s" % blocked)
	avisotexto=u""
	if aviso.exists():
		avisotexto+=u"%s\n\n" % aviso.get()
	avisotexto+=u"{{subst:User:AVBOT/AvisoBloqueo|%s}}" % blocker
	aviso.put(avisotexto, u"BOT - Avisando a [[Special:Contributions/%s|%s]] de que ha sido bloqueado por [[User:%s|%s]]" % (blocked, blocked, blocker, blocker))
