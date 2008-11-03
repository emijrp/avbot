# -*- coding: utf-8 -*-

import re
import wikipedia
import os

import xxxchan

def msgVandalismoEnCurso(dic_vand, author, userclass, site):
	#hasta que lo arregle, lo comento
	"""#archivamos
	if not random.randint(0,4): #afirmativo si sale cero
		archivado=xxxchan.archiveVEC(site)
		if archivado:
			wikipedia.output(u"\03{lightblue}Archivando WP:VEC\03{default}")
	
	#purge
	os.system('wget "http://es.wikipedia.org/w/index.php?title=Wikipedia:Vandalismo_en_curso&action=purge" -O wpvec.html')
	os.system('rm wpvec.html')
	"""
	
	artis=u""
	for k, v in dic_vand.items():
		if k!='avisos':
			wtitle=v[0]
			wtitle_=re.sub(" ", "_", wtitle)
			artis+=u"[http://es.wikipedia.org/w/index.php?title=%s&diff=%s&oldid=prev %s], " % (wtitle_, k, wtitle)
	wikipedia.output(u"El usuario %s ha vandalizado varias veces" % author)
	wii=wikipedia.Page(site, u"Wikipedia:Vandalismo en curso")
	restopag=wii.get()
	#evitamos avisar dos veces
	if re.search(ur'(?i)\=\=\= *%s *\=\=\=' % author, restopag):
		return
	aviso=u''
	if userclass=='reg':
		aviso+=u'<!-- completa los datos tras las "flechitas" -->\n{{subst:Reportevandalismo\n| 1 = %s\n| 2 = %s\n| 3 = ~~~~\n}}' % (author, artis)
	else:
		aviso+=u'<!-- completa los datos tras las "flechitas" -->\n{{subst:ReportevandalismoIP\n| 1 = %s\n| 2 = %s\n| 3 = ~~~~\n}}' % (author, artis)
	wii.put(u'%s\n\n%s' % (restopag, aviso), u'BOT - Añadiendo aviso de vandalismo reincidente de [[Special:Contributions/%s|%s]]' % (author, author))

def msgGenerico(author, site, wtitle, diff, n, tipo):
	aviso=wikipedia.Page(site, u"User talk:%s" % author)
	avisotexto=u""
	wtitle2=wtitle
	if re.search(ur'(?i)Categor(ía|y)\:', wtitle2):
		wtitle2=u':%s' % wtitle2
	if aviso.exists():
		avisotexto+=u"%s\n\n" % aviso.get()
	if n>=3:
		avisotexto+=u"{{subst:User:Toolserver/Aviso%sInminente|%s|%s}}" % (re.sub(' ', '', tipo), wtitle2, diff)
	else:
		avisotexto+=u"{{subst:User:Toolserver/Aviso%s|%s|%s|%s}}" % (re.sub(' ', '', tipo), wtitle2, diff, n)
	aviso.put(avisotexto, u"BOT - Avisando a [[Special:Contributions/%s|%s]] de que su %s en [[%s]] ha sido revertido (Aviso #%d)" % (author, author, tipo.lower(), wtitle, n))

def msgBlanqueo(author, site, wtitle, diff, n):
	return msgGenerico(author, site, wtitle, diff, n, u'Blanqueo')

def msgVandalismo(author, site, wtitle, diff, n):
	return msgGenerico(author, site, wtitle, diff, n, u'Vandalismo')
	
def msgContenidoChocante(author, site, wtitle, diff, n):
	return msgGenerico(author, site, wtitle, diff, n, u'Contenido chocante')

def msgPrueba(author, site, wtitle, diff, n):
	return msgGenerico(author, site, wtitle, diff, n, u'Prueba')

def msgEnlaceIrrelevante(author, site, wtitle, diff, n):
	return msgGenerico(author, site, wtitle, diff, n, u'Enlace irrelevante')

def msgFechaImposible(author, site, wtitle, diff, n):
	return msgGenerico(author, site, wtitle, diff, n, u'Fecha imposible')

def msgImageHost(author, site, wtitle, diff):
	aviso=wikipedia.Page(site, u"User talk:%s" % author)
	avisotexto=u''
	if aviso.exists() and not aviso.isRedirectPage():
		avisotexto+=u'%s\n\n{{subst:User:Toolserver/AvisoImageshack|%s|%s}}' % (aviso.get(), wtitle, diff)
	else:
		avisotexto+=u'{{subst:User:Toolserver/AvisoImageshack|%s|%s}}' % (wtitle, diff)
	if re.search(ur'(?i)Categor(ía|y)\:', wtitle):
		wtitle=':%s' % wtitle
	aviso.put(avisotexto, u'BOT - Avisando a [[Special:Contributions/%s|%s]] de cómo subir imágenes correctamente' % (author, author))
	
def msgFirma(p, author, site, wtitle, diff):
	aviso=wikipedia.Page(site, u"User talk:%s" % author)
	if p!=aviso: #evitamos avisar comentarios sin firmar en la discusion del menda
		avisotexto=u''
		if aviso.exists():
			avisotexto+=u'%s\n\n{{subst:User:Toolserver/AvisoNoFirmado|%s|%s}}' % (aviso.get(), wtitle, diff)
		else:
			avisotexto+=u'{{subst:User:Toolserver/AvisoNoFirmado|%s|%s}}' % (wtitle, diff)
		aviso.put(avisotexto, u'BOT - Avisando a [[Usuario:%s|%s]] de que su comentario en [[%s]] ha sido firmado' % (author, author, wtitle))
		