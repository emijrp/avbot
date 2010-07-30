# -*- coding: utf-8 -*-

#todo
#ircbot https://fisheye.toolserver.org/browse/~raw,r=720/Bryan/TsLogBot/TsLogBot.py
#capacidad para leer CR de irc o de api

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
    else:
        pass

def dangerous():
    return False

def run():
    #irc or api
    pass

def main():
    welcome()
    
    loadData()
    
    run()
    
    bye()

if __name__ == '__main__':
    main()
