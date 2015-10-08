#!/usr/bin/env python3

import re
import socket
import json
import threading
import sys
import os

os.system('clear')

# --------------------------------------------- Connection Settings ----------------------------------------------------

HOST = "irc.twitch.tv"                          # Hostname of the IRC-Server in this case twitch's
wHOST = "199.9.253.119"                         # Hostname of the group chat IRC-Server so we can whisper
PORT = 6667                                     # Default IRC-Port
CHAN = "#pillowzac"                             # Channelname = #{name}
NICK = "pillowbot"                              # Nickname = Twitch username for the BOT
PASS = "oauth:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"   # www.twitchapps.com/tmi/ will help to retrieve the required BOT authkey

# --------------------------------------------- Data Containers -------------------------------------------------------
rawdata = ""
users = []
moderators = ['pillowzac']

# Listening Switch
listening = True

# --------------------------------------------- Messaging Functions ----------------------------------------------------

def send_pong(msg):
    print('PONG: Main')
    con.send(bytes('PONG %s\r\n' % msg, 'UTF-8'))
    save_hugs('')
    saveUserAndModArrays()
    command_hugs('pillowzac')
		
def send_wpong(msg):
    print('PONG: Whisper')
    wcon.send(bytes('PONG %s\r\n' % msg, 'UTF-8'))


def send_message(chan, msg):
    con.send(bytes('PRIVMSG %s :%s\r\n' % (chan, msg), 'UTF-8'))

def send_whisper(chan, msg):
     wcon.send(bytes('PRIVMSG %s :/w %s\r\n' % (chan, msg), 'UTF-8'))


def send_nick(nick):
    print('Sending nickname')
    con.send(bytes('NICK %s\r\n' % nick, 'UTF-8'))
    wcon.send(bytes('NICK %s\r\n' % nick, 'UTF-8'))


def send_pass(password):
    print('Sending password')
    con.send(bytes('PASS %s\r\n' % password, 'UTF-8'))
    wcon.send(bytes('PASS %s\r\n' % password, 'UTF-8'))


def join_channel(chan):
    print('Joining ' + chan)
    con.send(bytes('JOIN %s\r\n' % chan, 'UTF-8'))
    wcon.send(bytes('JOIN %s\r\n' % chan, 'UTF-8'))


def part_channel(chan):
    print('Parting ' + chan)
    con.send(bytes('PART %s\r\n' % chan, 'UTF-8'))
    wcon.send(bytes('PART %s\r\n' % chan, 'UTF-8'))


def send_cap():
    con.send(bytes('CAP REQ :twitch.tv/membership\r\n', 'UTF-8'))

# --------------------------------------------- File Functions -----------------------------------------------

def load_hugs():
    print ('Loading hugs')
    with open('hugs.json', 'r') as f:
        hugs = json.load(f)
        if not hugs:
            return {}
        else:
            return hugs

def save_hugs(sndr):
    print ('Saving hugs')
    with open('hugs.json', 'w') as outfile:
        json.dump(hugDict, outfile)
    #send_whisper(CHAN, "pillowzac I\'ve saved the hugs.")

def clear_hugs(sndr):
    hugDict.clear()
    send_message(CHAN,'Okay, ' + sndr + '. I\'ve reset the hug counter.')

def saveUserAndModArrays():
    print ('Saving arrays')
    moderators.sort()
    users.sort()
    with open("users.txt", "w") as text_file:
        print('\n'.join(users), file=text_file)
    with open("mods.txt", "w") as text_file:
        print('\n'.join(moderators), file=text_file)
    
# --------------------------------------------- Command Functions --------------------------------------------

def command_toplist(sndr):
	#print the hug total and top 3 users
	
    sortedHugs = sorted(hugDict, key=hugDict.get, reverse=True)[:4]
    print (sortedHugs)

    totalhugs = ''
    msg = ''
    i=0
    
    if len(sortedHugs)>0:
        for hugger in sortedHugs:
            suffix = ' hugs'
            
            if hugDict[hugger] == 1:
                suffix = ' hug'

            if i==0:
                msg = "Top Snugglers --> "
            elif i==1:
                msg += hugger + ": " + str(hugDict[hugger]) + suffix
            else:
                msg += " -- " + hugger + ": " + str(hugDict[hugger]) + suffix

            i += 1
            msg += totalhugs
    else:
        msg = "Nothing to show, bro. Noone is hugging."
        
    send_message(CHAN, msg)


def command_hugs(sndr):
	
    numHugs = get_totalhugs()
    msg = 'I\'ve witnessed ' + str(numHugs) + ' hugs since I\'ve been here. :)'
    if numHugs == 0:
        msg = 'I haven\'t seen any hugs yet, boss. :('
    if numHugs == 1:
        msg = 'I\'ve seen only one hug. Where\'s the love?!'
    
    if not sndr == 'pillowzac':
    	send_message(CHAN, msg)
    else:
    	send_whisper(CHAN, sndr + ' ' + msg)


def command_addhug(sndr, msg):
    
    print ("Adding hug: " + sndr)
    totalHugs = get_totalhugs()
    hugDict['totalhugs'] += 1
    
    if sndr in hugDict:
        hugDict[sndr] += 1
    else:
        hugDict[sndr] = 1

    save_hugs(sndr)

    
def get_hugs(sndr):
    if sndr in hugDict:
        return hugDict[sndr]
    else:
        return 0


def get_totalhugs():
     if not 'totalhugs' in hugDict:
        hugDict['totalhugs'] = 0

     return hugDict['totalhugs']

# --------------------------------------------- Message Helper Functions ---------------------------------------------

def get_sender(msg):
    result = ""
    for char in msg:
        if char == "!":
            break
        if char != ":":
            result += char
    return result


def get_message(msg):
    result = ""
    i = 3
    length = len(msg)
    while i < length:
        result += msg[i] + " "
        i += 1
    result = result.lstrip(':')
    return result

def findWholeWord(w):
    return re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search

# --------------------------------------------- Message Parser ------------------------------------------------------

def parse_message(sndr, msg):

    global listening

    hug_list = ['hug','hugs']

    if len(msg) >= 1:

        amsg = msg.split(' ')
        options = {'!hugs': command_hugs, '!snuggleboard': command_toplist, '!clearhugs': clear_hugs, '!savehugs': save_hugs}

        #check commands
        if findWholeWord(NICK)(msg) and sndr in moderators:
            if sndr == "pillowzac":
                sndr = "pZ"
                
            if findWholeWord("leave")(msg) or findWholeWord("beat it")(msg) or findWholeWord("get out")(msg) or findWholeWord("jet")(msg) or findWholeWord("bail")(msg) or findWholeWord("stop")(msg) or findWholeWord("quit")(msg):
                send_message(CHAN, 'Allright. I\'m out.')
                listening = False
            if findWholeWord("sleep")(msg):
                send_message(CHAN, 'Goodnight, ' + sndr + '. ~zzzz')
                listening = False
            if findWholeWord("watch")(msg) or findWholeWord("look")(msg) or findWholeWord("work")(msg):
                send_message(CHAN, 'Ok. I\'ll keep an eye out, '+ sndr + '.')
                listening = True
            if findWholeWord("wake")(msg) or findWholeWord("kicks")(msg) or findWholeWord("start")(msg) or findWholeWord("starts")(msg):
                send_message(CHAN, 'I\'m up! I\'ll watch for hugs, '+ sndr + '.')
                listening = True
            return
        
        if amsg[0] in options:
            if not listening:
                return
            if sndr in moderators:
                #mods
                if sndr == "pillowzac":
                    sndr = "pZ"
                options[amsg[0]](sndr)
            else:                
                #others
                if amsg[0] == '!hugs':
                    numHugs = get_hugs(sndr)
                    hugString = 'You have given out ' + str(numHugs) + ' hugs.'

                    if numHugs==0:
                        hugString = 'You haven\'t given out any hugs.'
                    if numHugs==1:
                        hugString = 'You have given one hug.'

                    whisper = sndr + ' ' + hugString
                    #send_whisper(CHAN, whisper)
        else:
            #check for a hug
            addHug = False
            for word in hug_list:
                 if findWholeWord(word)(msg):
                    #print("found " + word)
                    addHug = True
            if addHug == True:
                command_addhug(sndr, msg)

# --------------------------------------------- Kill Function -----------------------------------------------

def stopEverything():
    print('')
    print('Bailout!')
    printStatus()
    save_hugs(NICK)
    print("Exiting")
    raise SystemExit(0)


# --------------------------------------------- Status Function -----------------------------------------------

def printStatus():
    print ('There are ' + str(len(users)) +' users and ' + str(len(moderators))  + ' moderators in ' + CHAN + '.')



# --------------------------------------------------------------------------------------------------------------
#                                               Main Program Loop
# --------------------------------------------------------------------------------------------------------------

#main connection
con = socket.socket()
con.connect((HOST, PORT))

#whisper connection
wcon = socket.socket()
wcon.connect((wHOST, PORT))

#authenticate ourselves
send_pass(PASS)
send_nick(NICK)

#set our capabilities
send_cap()

#join the channel
join_channel(CHAN)

#load our dataset
hugDict = load_hugs()

#we'll save our datasets when we get a PONG message

# start listening for messages on the main connection
while True:
    try:

        #get the raw message data from the connection at 1024byte length
        rawdata = rawdata+con.recv(1024).decode('UTF-8')
        
        #pop off the last carraige return
        data_split = re.split(r"[~\r\n]+", rawdata)
        rawdata = data_split.pop()
        
        for line in data_split:

            line = str.rstrip(line)
            line = str.split(line)

            if len(line) >= 1:

                #are we still here here?
                if line[0] == 'PING':
                    send_pong(line[1])
                    
                #is this something we'd like to parse?
                if len(line) >= 2:
 
                    #space splitting is the easiest way to get the message type
                    mType = line[1]

                    #find the sender and message text
                    sender = get_sender(line[0])
                    message = get_message(line)
                    
                    #Do something based on message type
                    if mType == 'PRIVMSG':
                        #print("* " + sender + ": " + message)
                        parse_message(sender, message)
                    
                    if mType == '353':
                        #base user list
                        msgUsers = message.split(':')[1].split()
                        users.extend(msgUsers)
                        
                    if mType == '366':
                    	#done sending user names
                        saveUserAndModArrays()
                        
                    if mType == 'MODE':
                        #we have a mod - add them to our mods array
                        mod = str(line[4])
                        if not mod in moderators:
                            moderators.append(mod)
                        if not mod in users:
                            users.append(mod)
                        print('Mod:\t'+mod)

                    if mType == 'JOIN':
                        #a user joined - add them to our users array
                        if not sender in users:
                            users.append(sender)

                    if mType == 'PART':
                        #someone left - remove them from our user/mod arrays
                        if sender in users:
                            users.remove(sender)
                        if sender in moderators:
                            moderators.remove(sender)


    except socket.error:
        print("Socket died")
        stopEverything()

    except socket.timeout:
        print("Socket timeout")
        stopEverything()

    except KeyboardInterrupt:
    	#ctrl-c will gracefully exit the program
        stopEverything()


