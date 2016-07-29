# -*- coding: utf-8 -*-

# AVBOT - Anti-vandalism bot for MediaWiki wikis
# Copyright (C) 2008-2016 emijrp <emijrp@gmail.com>
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
# Module for data loads: user edits list, admins list, bots list, regexp list and excluded pages list\n
# Módulo para carga de datos: lista de usuarios por número de ediciones, administradores, bots, lista de expresiones regulares y de páginas excluidas

import re
import urllib
import sys

""" pywikipediabot modules """
import wikipedia

""" AVBOT modules """
import avbotglobals
import avbotcomb

def changedRegexpsList(dic1, dic2):
    """ ¿Los dos diccionarios de expresiones regulares son distintos? """
    """ Check if both dictionaries are not equal """
    if len(dic1.items())!=len(dic2.items()):
        return True
    else:
        changed=False
        for k, v in dic1.items():
            if not dic2.has_key(k):
                return True
    return False

def loadMessages():
    """ Carga preferencias sobre mensajes """
    """ Load messages preferences """
    #p=wikipedia.Page(avbotglobals.preferences['site'], u'User:%s/Mensajes.css' % avbotglobals.preferences['ownerNick'])
    p=""
    if avbotglobals.preferences['site'].lang=='es':
        p=wikipedia.Page(avbotglobals.preferences['site'], u'%s:Emijrp/%s' % (avbotglobals.namespaces[2], avbotglobals.preferences['messages'])) #Fijo a Emijrp para los clones de es:
    else:
        p=wikipedia.Page(avbotglobals.preferences['site'], u'%s:%s/%s' % (avbotglobals.namespaces[2], avbotglobals.preferences['ownerNick'], avbotglobals.preferences['messages'])) 
    raw=''
    if p.exists():
        if not p.isRedirectPage() and not p.isDisambig():
            raw=p.get()
    else:
        ownerNick=avbotglobals.preferences['ownerNick']
        wikipedia.output(u'A preferences page is needed in [[%s]]' % p.title())
        wikipedia.output(u'<pre>\n\n#Insert one message per line.\n\nV;;100;;Vandalismo;;User:%s/AvisoVandalismo;;\nBL;;50;;Blanqueo;;User:%s/AvisoBlanqueo;;\nP;;10;;Prueba;;User:%s/AvisoPrueba;;\n#dummie\nC;;-100;;Contrapeso;;User:%s/AvisoContrapeso;;\n\n</pre>' % (ownerNick, ownerNick, ownerNick, ownerNick))
        #wikipedia.output('A preferences page is needed. Please, look last bot edits.')
        if not avbotglobals.preferences['force']:
            sys.exit()
    
    avbotglobals.preferences['msg']={} #empty
    for l in raw.splitlines():
        l=l.strip()
        if len(l)>=3: #evitamos lineas demasiado pequenas
            if l[0]=='#' or l[0]=='<':
                continue
            trozos=l.split(';;')
            #print trozos
            type=trozos[0].lower()
            priority=int(trozos[1])
            meaning=trozos[2].lower()
            template=trozos[3]
            avbotglobals.preferences['msg'][type]={'priority': priority, 'meaning': meaning, 'template': template,}

def loadRegexpList():
    """ Carga lista de expresiones regulares """
    """ Load regular expression list """
    #p=wikipedia.Page(avbotglobals.preferences['site'], u'User:%s/Lista del bien y del mal.css' % avbotglobals.preferences['ownerNick'])
    p=""
    if avbotglobals.preferences['site'].lang=='es':
        p=wikipedia.Page(avbotglobals.preferences['site'], u'%s:Emijrp/%s' % (avbotglobals.namespaces[2], avbotglobals.preferences['goodandevil']))
    else:
        p=wikipedia.Page(avbotglobals.preferences['site'], u'%s:%s/%s' % (avbotglobals.namespaces[2], avbotglobals.preferences['ownerNick'], avbotglobals.preferences['goodandevil']))
    raw=''
    if p.exists():
        if not p.isRedirectPage() and not p.isDisambig():
            raw=p.get()
    else:
        wikipedia.output(u'A preferences page is needed in [[%s]]' % p.title())
        wikipedia.output(u'#Introduce one regexp per line. Format: REGEXP;;POINTS;;CLASS;;')
        if not avbotglobals.preferences['force']:
            sys.exit()
        
    c=0
    error=u''
    avbotglobals.vandalRegexps={}
    dontsort=[]
    dosort=[]
    rawlines=raw.splitlines()
    for l in rawlines:
        c+=1
        l=l.strip()
        if len(l)>=12: #Avoid short dangerous regexps
            if l=='<pre>' or l=='</pre>': #Skip preformatted labels
                continue
            if l[0]=='#' or l[0]=='<': #Skip no regexps lines
                dontsort.append(l)
                continue
            l=l.lower() #Be careful with LoadMessages(), always lower or always upper
            dosort.append(l)
            try:
                l=re.sub(ur"(?im)^([^\#]*?)\#[^\n\r]*?$", ur"\1", l)#Clean inline comments
                t=l.split(';;')
                type=t[2]
                reg=t[0]
                score=int(t[1])
                regex=ur'%s%s%s' % (avbotglobals.preferences['context'], reg, avbotglobals.preferences['context'])
                avbotglobals.vandalRegexps[reg]={'type':type, 'compiled':re.compile(ur'(?im)%s' % regex), 'score':score}
            except:
                error+=u'** Regexp error: Line: %d  %s\n' % (c, rawlines[c])
    
    #Sorting list
    dosort.sort()
    goodandevil=avbotglobals.preferences['goodandevil'].split('.')[0] #quitamos .css de momento falla
    if not avbotglobals.preferences['nosave']:
        ordenada=wikipedia.Page(avbotglobals.preferences['site'], u'User:%s/%s/Sorted' % (avbotglobals.preferences['botNick'], goodandevil))
        output=u'<pre>\n%s\n\n%s\n</pre>' % ('\n'.join(dontsort), '\n'.join(dosort))
        if (ordenada.exists() and ordenada.get()!=output) or not ordenada.exists(): 
            ordenada.put(output, u'BOT - Ordenando lista [[User:%s/%s]]' % (avbotglobals.preferences['ownerNick'], goodandevil), botflag=False, maxTries=3)
    
    wikipedia.output(u'\nLoaded %s regular expresions...' % (len(avbotglobals.vandalRegexps.items())))
    
    return error

def reloadRegexpList(author, diff):
    """ Recarga lista de expresiones regulares """
    """ Reload regular expression list """
    oldVandalRegexps=avbotglobals.vandalRegexps
    error=loadRegexpList()
    ownerNick=avbotglobals.preferences['ownerNick']
    if avbotglobals.preferences['site'].lang=='es':
        ownerNick=u"Emijrp"
    goodandevil=avbotglobals.preferences['goodandevil']
    """mientras arreglan el bug de no poder editar las propias .css p=wikipedia.Page(avbotglobals.preferences['site'], u'%s:%s/%s' % (avbotglobals.namespaces[3], ownerNick, goodandevil)) #[3] porque es User talk:
    if not avbotglobals.preferences['nosave'] and avbotglobals.preferences['site'].lang=='es':
        if p.exists() and not re.search(ur"%s" % diff, p.get()):
            if changedRegexpsList(oldVandalRegexps, avbotglobals.vandalRegexps):
                if error:
                    p.put(u'* {{subst:CURRENTDAY}} de {{subst:CURRENTMONTHNAME}} de {{subst:CURRENTYEAR}}, {{subst:CURRENTTIME}} (UTC): {{u|%s}} ha modificado la lista ([http://%s.wikipedia.org/w/index.php?title=User:%s/Lista_del_bien_y_del_mal.css&diff=%s&oldid=prev ver diff]). Ahora hay %d expresiones regulares válidas.\n%s%s' % (author, avbotglobals.preferences['language'], ownerNick, diff, len(avbotglobals.vandalRegexps), error, p.get()), u'BOT - La lista ha cambiado. Total [%d]' % len(avbotglobals.vandalRegexps), botflag=False, maxTries=1)
                else:
                    p.put(u'* {{subst:CURRENTDAY}} de {{subst:CURRENTMONTHNAME}} de {{subst:CURRENTYEAR}}, {{subst:CURRENTTIME}} (UTC): {{u|%s}} ha modificado la lista ([http://%s.wikipedia.org/w/index.php?title=User:%s/Lista_del_bien_y_del_mal.css&diff=%s&oldid=prev ver diff]). Ahora hay %d expresiones regulares válidas.\n%s' % (author, avbotglobals.preferences['language'], ownerNick, diff, len(avbotglobals.vandalRegexps), p.get()), u'BOT - La lista ha cambiado. Total [%d]' % len(avbotglobals.vandalRegexps), botflag=False, maxTries=1)
            else:
                if error:
                    p.put(u'* {{subst:CURRENTDAY}} de {{subst:CURRENTMONTHNAME}} de {{subst:CURRENTYEAR}}, {{subst:CURRENTTIME}} (UTC): {{u|%s}} ha editado la página pero hay las mismas %d expresiones regulares válidas ([http://%s.wikipedia.org/w/index.php?title=User:%s/Lista_del_bien_y_del_mal.css&diff=%s&oldid=prev ver diff]).\n%s%s' % (author, len(avbotglobals.vandalRegexps), avbotglobals.preferences['language'], ownerNick, diff, error, p.get()), u'BOT - La lista no ha cambiado. Total [%d]' % len(avbotglobals.vandalRegexps), botflag=False, maxTries=1)
                else:
                    p.put(u'* {{subst:CURRENTDAY}} de {{subst:CURRENTMONTHNAME}} de {{subst:CURRENTYEAR}}, {{subst:CURRENTTIME}} (UTC): {{u|%s}} ha editado la página pero hay las mismas %d expresiones regulares válidas ([http://%s.wikipedia.org/w/index.php?title=User:%s/Lista_del_bien_y_del_mal.css&diff=%s&oldid=prev ver diff]).\n%s' % (author, len(avbotglobals.vandalRegexps), avbotglobals.preferences['language'], ownerNick, diff, p.get()), u'BOT - La lista no ha cambiado. Total [%d]' % len(avbotglobals.vandalRegexps), botflag=False, maxTries=1)"""
    return


