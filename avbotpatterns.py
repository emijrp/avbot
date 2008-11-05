# -*- coding: utf-8 -*-

import re

def loadPatterns():
	patterns={
	'blanqueos': re.compile(ur'(?i)redirect|desamb|\{\{ *(copyvio|destruir|plagio|robotdestruir|wikificar)'),
	'block': re.compile(ur'(?i)\[\[Especial:Log/block\]\] +block +\* +(?P<blocker>.*?) +\* +bloqueó a +\"Usuario\:(?P<blocked>.*?)\" +.*?durante un plazo de \"(?P<block>.*?)\"'),
	#[[Especial:Log/delete]] delete  * Snakeyes * borró "Discusión:Gastronomía en Estados Unidos": borrado rápido usando [[w:es:User:Axxgreazz/Monobook-Suite|monobook-suite]] el contenido era: «{{delete|Vandalismo}} {{fuenteprimaria|6|mayo}} Copia y pega el siguiente código en la página de discusión del creador del artículo: == Ediciones con investigac
	#'borrado': re.compile(ur'(?i)\[\[...(?P<pageTitle>.*?)..\]\].*?delete.*?\*.....(?P<usuario>.*?)...\*'),
	'borrado': re.compile(ur'(?i)\[\[Especial:Log/delete\]\] +delete +\* +(?P<usuario>.*?) +\* +borró +«(?P<pageTitle>.*?)»\:'),
	'conflictivos': re.compile(ur'(?i)\{\{ *(autotrad|maltrad|mal traducido|wikci|al? (wikcionario|wikicitas|wikinoticias|wikiquote|wikisource)) *\}\}'),
	'destruir': re.compile(ur'(?i)\{\{ *destruir'),
	#diffstylebegin y end va relacionado
	'diffstylebegin': re.compile(ur'(<span class="diffchange">|<span class="diffchange diffchange-inline">|<ins class="diffchange diffchange-inline">)'),
	'diffstyleend': re.compile(ur'(<span class="diffchange">|<span class="diffchange diffchange-inline">|<ins class="diffchange diffchange-inline">)([^<]*?)</(ins|span)>'),
	'ip': re.compile(ur'(?im)^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'),
	'firmas1': re.compile(ur'<td class="diff-addedline"><div>([^<]*?)</div>'),
	'edit': re.compile(ur'(?i)\[\[(?P<pageTitle>.*?)\]\] +(?P<nm>.*?) +http\://es\.wikipedia\.org/w/index\.php\?title\=.*?diff\=(?P<diff>\d+)\&oldid\=(?P<oldid>\d+) +\* +(?P<author>.*?) +\* +\(.*?\) +(?P<resume>.*)'),
	'newpage': re.compile(ur'(?i)\[\[(?P<pageTitle>.*?)\]\] +(?P<nm>.*?) +http\://es\.wikipedia\.org/wiki/.*? +\* (?P<author>.*?) +\*'),
	'nuevousuario': re.compile(ur'(?i)\[\[Especial:Log/newusers\]\] +create +\* +(?P<usuario>.*?) +\* +Usuario nuevo'),
	'protegida': re.compile(ur'(?i)\[\[Especial:Log/protect\]\] +protect +\* +(?P<protecter>.*?) +\* +protegió +\[\[(?P<pageTitle>.*?)\]\] +\[edit\=(?P<edit>sysop|autoconfirmed)\][^\[]*?\[move\=(?P<move>sysop|autoconfirmed)\]'),
	#protegidacreacion [[Especial:Log/protect]] protect  * Snakeyes *  protegió [[Tucupido cincuentero]] [create=sysop]  (indefinido): Artículo ensayista reincidente
	'desprotegida': re.compile(ur'(?i)\[\[.*?Especial\:Log/protect.*?\]\].*?unprotect'),
	'spam': re.compile(ur'(?im)<td class="diff-addedline"><div>[^<]*?(http://[a-z0-9\.\-\=\?\_\/]+)[^<]*?</div></td>'),
	#[[Especial:Log/move]] move_redir  * Manuel González Olaechea y Franco * [[Anexo:Presidente del Perú]] ha sido trasladado a [[Anexo:Presidentes del Perú]] sobre una redirección.
	#[[Especial:Log/move]] move  * Dhidalgo *  [[Macizo Etíope]] ha sido trasladado a [[Macizo etíope]]
	'traslado': re.compile(ur'(?i)\[\[Especial:Log/move\]\] +move +\* +(?P<usuario>.*?) +\* +\[\[(?P<origen>.*?)\]\] +ha sido trasladado a +\[\[(?P<destino>.*?)\]\]'),
	}
	
	return patterns

