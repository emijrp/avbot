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

## @package avbotsave
# Module for data saving: user edits and stats\n
# Módulo para guardar datos: ediciones de usuarios y estadísticas

# AVBOT modules
import avbotglobals
import wikipedia

def saveEdits(ediciones):
	""" Guarda el número de ediciones de los usuarios en un fichero """
	""" Saves user edits number in a file """
	f=open(avbotglobals.preferences['editsFilename'], 'w')
	for k, v in ediciones.items():
		try:
			linea=u"%s;%s;\n" % (k, v)
			f.write(linea.encode('utf-8'))
		except:
			pass
	f.close()

def saveStats(stats, hours, site):
	""" Guarda las estadísticas en una página con motivos históricos """
	""" Saves statistics in a page for historical purposes """
	resumen=u'V[%d], BL[%d], P[%d], S[%d], B[%d], M[%d], T[%d], D[%d]' % (stats[hours]['v'], stats[hours]['bl'], stats[hours]['p'], stats[hours]['s'], stats[hours]['b'], stats[hours]['m'], stats[hours]['t'], stats[hours]['d'])
	wikipedia.output(u"\03{lightgreen}Resumen últimas %d horas: %s\03{default}" % (hours, resumen))
	if not avbotglobals.preferences['nosave']:
		wii=wikipedia.Page(site, u"User:AVBOT/Stats/%d" % hours)
		wii.put(u"{{#switch:{{{1|T}}}|V=%d|BL=%d|P=%d|S=%d|B=%d|M=%d|T=%d|D=%d}}" % (stats[hours]['v'], stats[hours]['bl'], stats[hours]['p'], stats[hours]['s'], stats[hours]['b'], stats[hours]['m'], stats[hours]['t'], stats[hours]['d']), u"BOT - Actualizando estadísticas de las últimas %d horas: %s" % (hours, resumen))
