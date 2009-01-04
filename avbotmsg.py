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

## @package avbotload
# Module for send messages to users

import re
import wikipedia
import os

# AVBOT modules
import avbotglobals
import avbotcomb

def msgVandalismoEnCurso(dic_vand, author, userclass):
	artis=u""
	for k, v in dic_vand.items():
		if k!='avisos':
			wtitle=v[0]
			wtitle_=re.sub(" ", "_", wtitle)
			artis+=u"[http://es.wikipedia.org/w/index.php?title=%s&diff=%s&oldid=prev %s], " % (wtitle_, k, wtitle)
	wikipedia.output(u"El usuario %s ha vandalizado varias veces" % author)
	wii=wikipedia.Page(avbotglobals.preferences['site'], u"Wikipedia:Vandalismo en curso")
	restopag=wii.get()
	#evitamos avisar dos veces
	if re.search(ur'(?i)\=\=\= *%s *\=\=\=' % author, restopag): #xiste ya un aviso
		return
	aviso=u''
	if userclass=='reg':
		aviso+=u'<!-- completa los datos tras las "flechitas" -->\n{{subst:Reportevandalismo\n| 1 = %s\n| 2 = %s\n| 3 = ~~~~\n}}' % (author, artis)
	else:
		aviso+=u'<!-- completa los datos tras las "flechitas" -->\n{{subst:ReportevandalismoIP\n| 1 = %s\n| 2 = %s\n| 3 = ~~~~\n}}' % (author, artis)
	wii.put(u'%s\n\n%s' % (restopag, aviso), u'BOT - Añadiendo aviso de vandalismo reincidente de [[Special:Contributions/%s|%s]]' % (author, author))

def msgGenerico(author, wtitle, diff, n, tipo):
	if avbotglobals.preferences['site'].lang!='es':
		return
	aviso=wikipedia.Page(avbotglobals.preferences['site'], u"User talk:%s" % author)
	avisotexto=u""
	wtitle2=wtitle
	if re.search(ur'(?i)Categor(ía|y)\:', wtitle2):
		wtitle2=u':%s' % wtitle2
	if aviso.exists():
		avisotexto+=u"%s\n\n" % aviso.get()
	if n==3: #If n>3, no messages
		avisotexto+=u"{{subst:User:AVBOT/Aviso%sInminente|%s|%s}}" % (re.sub(' ', '', tipo), wtitle2, diff)
	elif n<3:
		avisotexto+=u"{{subst:User:AVBOT/Aviso%s|%s|%s|%s}}" % (re.sub(' ', '', tipo), wtitle2, diff, n)
	if tipo.lower()=='prueba':
		aviso.put(avisotexto, u"BOT - Avisando a [[Special:Contributions/%s|%s]] de que su %s en [[%s]] ha sido revertida (Aviso #%d)" % (author, author, tipo.lower(), wtitle, n))
	else:
		aviso.put(avisotexto, u"BOT - Avisando a [[Special:Contributions/%s|%s]] de que su %s en [[%s]] ha sido revertido (Aviso #%d)" % (author, author, tipo.lower(), wtitle, n))

def msgBlanqueo(author, wtitle, diff, n):
	return msgGenerico(author, wtitle, diff, n, u'Blanqueo')

def msgVandalismo(author, wtitle, diff, n):
	return msgGenerico(author, wtitle, diff, n, u'Vandalismo')
	
def msgContenidoChocante(author, wtitle, diff, n):
	return msgGenerico(author, wtitle, diff, n, u'Contenido chocante')

def msgPrueba(author, wtitle, diff, n):
	return msgGenerico(author, wtitle, diff, n, u'Prueba')

def msgEnlaceIrrelevante(author, wtitle, diff, n):
	return msgGenerico(author, wtitle, diff, n, u'Enlace irrelevante')

def msgFechaImposible(author, wtitle, diff, n):
	return msgGenerico(author, wtitle, diff, n, u'Fecha imposible')

def msgBloqueo(blocked, blocker):
	aviso=wikipedia.Page(avbotglobals.preferences['site'], u"User talk:%s" % blocked)
	avisotexto=u""
	if aviso.exists():
		avisotexto+=u"%s\n\n" % aviso.get()
	avisotexto+=u"{{subst:User:AVBOT/AvisoBloqueo|%s}}" % blocker
	aviso.put(avisotexto, u"BOT - Avisando a [[Special:Contributions/%s|%s]] de que ha sido bloqueado por [[User:%s|%s]]" % (blocked, blocked, blocker, blocker))
