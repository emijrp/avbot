# -*- coding: utf-8 -*-

#todo
#ircbot https://fisheye.toolserver.org/browse/~raw,r=720/Bryan/TsLogBot/TsLogBot.py
#capacidad para leer CR de irc o de api

import wikipedia

usergroups = []
users = {}

preferences = {

}

def loadUsersFromUserGroup(usergroup):
    users[usergroup] = []
    pass

def loadUserGroups():
    global usergroups
    
    usergroups = []
    
    pass

def loadUsers()
    if not usergroups:
        loadUserGroups()
    
    for usergroup in usergroups:
        loadUsersFromUserGroup(usergroup=usergroup)

def loadData():
    loadUserGroups()
    loadUsers()

def editIsBlanking(edit_props):
    return False

def revert(edit_props, motive=""):
    pass

def analize(edit_props):
    if editIsBlanking():
        revert(edit_props, motive="blanking")
    elif editIsTest():
        pass
    elif editIsVandalism():
        pass
    elif editIsVanish():
        pass
    else:
        pass

def dangerous(edit_props):
    if user not in users["admin"] and \
       user not in ... and \
       useredits < 25:
       return True
    return False

def run():
    #irc or api
    
    site = wikipedia.Site("es", "wikipedia")
    for rc in site.recentchanges():
        print rc
    
    for 
    
    if dangerous(edit_props):
        analize(edit_props)
    pass

def welcome():
    pass

def bye():
    pass

def main():
    welcome()
    
    loadData()
    
    run()
    
    bye()

if __name__ == '__main__':
    main()
