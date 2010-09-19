# -*- coding: utf-8 -*-

#todo
#ircbot https://fisheye.toolserver.org/browse/~raw,r=720/Bryan/TsLogBot/TsLogBot.py
#capacidad para leer CR de irc o de api

import re
import time
import thread

import wikipedia

usergroups = []
users = {}

preferences = {
    "rcAPI": True,
    "rcIRC": False,
}

def loadUsersFromUserGroup(usergroup):
    global users
    
    users[usergroup] = []

def loadUserGroups():
    global usergroups
    
    usergroups = ["admin", "bot"] #catch from api, no by default
    
    for usergroup in usergroups:
        loadUsersFromUserGroup(usergroup)

def loadUsers():
    if not usergroups:
        loadUserGroups()
    
    for usergroup in usergroups:
        loadUsersFromUserGroup(usergroup=usergroup)

def loadData():
    loadUserGroups()
    loadUsers()

def editIsBlanking(edit_props):
    return False

def editIsTest(edit_props):
    return False

def editIsVandalism(edit_props):
    return False

def editIsVanish(edit_props):
    return False

def userwarning():
    #enviar mensajes según el orden que ya tengan los de la discusión
    pass

def reverted():
    return False

def revert(edit_props, motive=""):
    print "Detected edit to revert: %s" % motive
    
    if reverted(): #a lo mejor lo ha revertido otro bot u otra persona
        userwarning() 
    else:
        print "Somebody was faster than us reverting. Reverting not needed"

def editWar(edit_props):
    #comprueba si esa edición ya existe previamente en el historial, por lo que el usuario está insistiendo en que permanezca
    #primero con la longitud, y si hay semejanzas, entonces se compara con el texto completo
    return False

def analize(edit_props):
    if editWar(edit_props):
        #http://es.wikipedia.org/w/api.php?action=query&prop=revisions&titles=Francia&rvprop=size&rvend=2010-07-25T14:54:54Z
        print "Saltamos para evitar guerra"
        return
    elif dangerous(edit_props):
        if editIsBlanking(edit_props):
            revert(edit_props, motive="blanking")
        elif editIsTest(edit_props):
            pass
        elif editIsVandalism(edit_props):
            pass
        elif editIsVanish(edit_props):
            pass
        else:
            pass

def isIP(user):
    if re.findall(ur"(?im)^\d+\.\d+\.\d+\.\d+$", user): #improve
        return True
    return False

def dangerous(edit_props):
    useredits = 0
    
    if isIP(edit_props['user']):
        return True
    
    if edit_props['user'] not in users["admin"] and \
       edit_props['user'] not in users["bot"] and \
       useredits < 25:
       return True
    return False

def rcAPI():
    site = wikipedia.Site("en", "wikipedia")
    
    rctimestamp = ""
    rcs = site.recentchanges(number=1)
    for rc in rcs:
        rctimestamp = rc[1]
    
    rcdir = "newer"
    rchistory = []
    while True:
        rcs = site.recentchanges(number=100, rcstart=rctimestamp, rcdir=rcdir) #no devuelve los oldid, mejor hacerme mi propia wikipedia.query
        
        for rc in rcs:
            rcsimple = [rc[0].title(), rc[1], rc[2], rc[3]]
            if rcsimple not in rchistory:
                rchistory = rchistory[-1000:]
                rchistory.append(rcsimple)
                edit_props = {'user': rc[2],}
                
                if not editWar(edit_props) and dangerous(edit_props):
                    wikipedia.output(u'\03{lightyellow}%s\03{default}' % ('\t'.join(rcsimple)))
                    thread.start_new_thread(analize, (edit_props,))
                else:
                    wikipedia.output(u'\03{lightgreen}%s\03{default}' % ('\t'.join(rcsimple)))
            rctimestamp = rc[1]
        time.sleep(3)

def rcIRC():
    pass

def run():
    #irc or api
    #por cada usuairo que llegue nuevo list=users (us) para saber cuando se registró
    #evitar que coja ediciones repetidas
    
    if preferences["rcAPI"]:
        rcAPI()
    elif preferences["rcIRC"]:
        rcIRC()

def welcome():
    print "#"*80
    print "# Welcome to AVBOT "
    print "#"*80

def bye():
    print "Bye, bye..."

def main():
    welcome()
    loadData()
    run()
    bye()

if __name__ == '__main__':
    main()
