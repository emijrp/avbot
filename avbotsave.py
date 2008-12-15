# -*- coding: utf-8 -*-

import wikipedia

def saveedits(ediciones):
	f=open('ediciones.txt', 'w')
	for k, v in ediciones.items():
		try:
			linea=u"%s;%s;\n" % (k, v)
			f.write(linea.encode('utf-8'))
		except:
			pass
	f.close()
	

def saveStats(stats, hours, site):
	resumen=u'V[%d], BL[%d], P[%d], S[%d], B[%d], M[%d], T[%d], D[%d]' % (stats[hours]['V'], stats[hours]['BL'], stats[hours]['P'], stats[hours]['S'], stats[hours]['B'], stats[hours]['M'], stats[hours]['T'], stats[hours]['D'])
	wikipedia.output(u"\03{lightgreen}Resumen últimas %d horas: %s\03{default}" % (hours, resumen))
	wii=wikipedia.Page(site, u"User:AVBOT/Stats/%d" % hours)
	wii.put(u"{{#switch:{{{1|T}}}|V=%d|BL=%d|P=%d|S=%d|B=%d|M=%d|T=%d|D=%d}}" % (stats[hours]['V'], stats[hours]['BL'], stats[hours]['P'], stats[hours]['S'], stats[hours]['B'], stats[hours]['M'], stats[hours]['T'], stats[hours]['D']), u"BOT - Actualizando estadísticas de las últimas %d horas: %s" % (hours, resumen))
	