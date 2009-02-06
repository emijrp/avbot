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

## @package avbotsave
# Module for data saving: user edits and stats\n
# Módulo para guardar datos: ediciones de usuarios y estadísticas

# AVBOT modules
import avbotglobals
import wikipedia

def saveEdits(ediciones):
	""" Guarda el número de ediciones de los usuarios en un fichero """
	""" Saves user edits number in a file """
	f=open('ediciones.txt', 'w')
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
	resumen=u'V[%d], BL[%d], P[%d], S[%d], B[%d], M[%d], T[%d], D[%d]' % (stats[hours]['V'], stats[hours]['BL'], stats[hours]['P'], stats[hours]['S'], stats[hours]['B'], stats[hours]['M'], stats[hours]['T'], stats[hours]['D'])
	wikipedia.output(u"\03{lightgreen}Resumen últimas %d horas: %s\03{default}" % (hours, resumen))
	wii=wikipedia.Page(site, u"User:AVBOT/Stats/%d" % hours)
	wii.put(u"{{#switch:{{{1|T}}}|V=%d|BL=%d|P=%d|S=%d|B=%d|M=%d|T=%d|D=%d}}" % (stats[hours]['V'], stats[hours]['BL'], stats[hours]['P'], stats[hours]['S'], stats[hours]['B'], stats[hours]['M'], stats[hours]['T'], stats[hours]['D']), u"BOT - Actualizando estadísticas de las últimas %d horas: %s" % (hours, resumen))
