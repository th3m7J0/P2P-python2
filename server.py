#!/usr/bin/python
# -*- coding: utf-8 -*- 

import socket
import os
import sys
import select
import thread
import subprocess
import bcrypt


host = ''
port = 9896
backlog = 10
size = 2048
temp = 0

#function for help command
def usage(client):
    msg= '''
----------------------------------------------------------------------------------------------------------------
Command List:                           (for P2P communication MASTER2: IRS)                                    |
----------------------------------------------------------------------------------------------------------------
\CONNECT connect client to another listening client                                                             |
----------------------------------------------------------------------------------------------------------------
\GET_CLIENT_LIST – to request list of connected clients                                                         |
----------------------------------------------------------------------------------------------------------------
\GET_CLIENT_IN_LISTEN to receive listening socket of the client to connect to                                   |
----------------------------------------------------------------------------------------------------------------
\DISPLAY_SHARED_FILES  show the shared files                                                                    |
----------------------------------------------------------------------------------------------------------------
\DISPLAY_SHARED_FILES_BY_USER <username> show the files that the user wants to share with the other clients     |
----------------------------------------------------------------------------------------------------------------
\SEARSH_IN_SHARED_FILES <keyword> - to search for specific shared file                                          |
----------------------------------------------------------------------------------------------------------------
\DISCONNECT_CLIENT –  to indicate that you are no longer connected to the chat service                          |
----------------------------------------------------------------------------------------------------------------

'''
    client.send(msg)

def get_hashed_password(plain_text_password):
    # Hash a password for the first time
    #   (Using bcrypt, the salt is saved into the hash itself)
    return bcrypt.hashpw(plain_text_password, bcrypt.gensalt())

def check_password(plain_text_password, hashed_password):
    # Check hashed password. Using bcrypt, the salt is saved into the hash itself
    return bcrypt.checkpw(plain_text_password, hashed_password)


#to store username and password in dictionary, to register user
def store(client,dict,uname,pswd,c_info):
    if dict.has_key(uname):
        client.send('username is already taken. Type "Y" to set new username\n')
    else:
        dict[uname]=get_hashed_password(pswd)
        corl(client,c_info,uname)
        client.send('\nType your request or type \help for help\n\n')

#to check if username and password is present in dictionary, to authenticate user
def check(client,dict,uname,pswd,c_info):
    if dict.has_key(uname) and check_password(pswd,dict[uname]):
        client.send('Welcome back ' +uname)
        corl(client,c_info,uname)
        temp = 0
    else:
        client.send('Incorrect username or password! Try again\n')
        temp = 1
    return temp






#ask if client wants to listen for connections or connect to existing client
def corl(client,c_info,uname):
    #sending current uname
    client.send('uname--{}'.format(uname))
    resp = client.recv(size)

    client.send('Do you want to "connect" or "listen"? ')
    resp = client.recv(size)
    if resp == 'listen':
        client.send('Enter your listening port: ')
        cport = client.recv(size)
        c_info[uname] = cport

def cconnect(client,c_info):
    client.send('username: ')
    uname = client.recv(size)
    if c_info.has_key(uname):
        client.send(c_info[uname])
        #log[uname]
    else:
        client.send('Incorrect username\n\n')


#provides client_info i.e. listening port
def info(client,c_info):
    client.send('\GET_CLIENT_IN_LISTEN: ' +str(c_info)+'\n\n')
    
    

# search in shared files
def search_shared_files(client):
    client.send('Send the keyword: ')
    resp = client.recv(size)
    proc = subprocess.Popen(["grep -Rn {}".format(resp)], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    client.send('\SEARSH_IN_SHARED_FILES:\n '+out)

# display shared files by user 
def display_shared_files(client):
    proc = subprocess.Popen(["tree"], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    client.send('\DISPLAY_SHARED_FILES:\n '+out)

# display shared files by user 
def display_shared_files_by_user(client):
    client.send('username: ')
    uname = client.recv(size)
    proc = subprocess.Popen(["tree {}".format(uname)], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    client.send('\DISPLAY_SHARED_FILES_BY_USER:\n '+out)

#function to process requests from client
def start(client,input,dict,c_info,log):
    try:
        uname=''
        data = client.recv(size)
        if data == 'y' or data == 'Y':    #requests new username and password if new user
            client.send('Set new username & password\nusername: ')
            uname = client.recv(size)
            os.system('mkdir {}'.format(uname))
            os.system('echo "this is a file for the {} " > {}/{}-init.txt'.format(uname,uname,uname))
            client.send('password: ')
            pswd = client.recv(size)
            store(client,dict,uname,pswd,c_info)
        
        elif data == 'n' or data == 'N':   #if existing user, it verifies the username and password
            for x in range(0, 3):          #provides three attempts for user to login
                client.send('Type your username and password\nusername: ')
                uname = client.recv(size)
                client.send('password: ')
                pswd = client.recv(size)
                if check(client,dict,uname,pswd,c_info)==0:
                    client.send('\nType your request or type \help for help\n')
                    break
                if x == 2:
                    client.send('You have exceeded the no. of retries') 
                    client.close()
                    input.remove(client)    
      
        if data == '\help':                 #if help command is given
            usage(client)   

        if data =='\CONNECT':       #client listen
            cconnect(client,c_info)
        

        if data =='\GET_CLIENT_LIST':       #send list of connected clients to user
            client.send('\GET_CLIENT_LIST: ' +str(dict.keys())+'\n\n')

        if data =='\GET_CLIENT_IN_LISTEN':       #sends listening port of client
            info(client,c_info) 
        
        if data == '\SEARSH_IN_SHARED_FILES':   
            search_shared_files(client)

        if data == '\DISPLAY_SHARED_FILES':   
            display_shared_files(client)

        if data == '\DISPLAY_SHARED_FILES_BY_USER':   
            display_shared_files_by_user(client)

        if data == '\DISCONNECT_CLIENT':    #disconnect client if requested
            client.close()
            input.remove(client)
        

        else:
            pass
    except:
        client.close()
        input.remove(client)
        
#main to create initial connection
def main():
    #creating a socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #binding the socket to localhost and port
    sock.bind((host,port))
    sock.listen(backlog)
    input = [sock]
    dict = {}    #to store username and password
    c_info = {}  #to store username and port nos.
    log = {}     #to store chat sessions
    print "Chat server is now running on port " + str(port)
    while 1:
        # Using Select to handle multiplexing
        inready,outready,exceptready = select.select(input,[],[])
        for s in inready:
            if s == sock:
                client, address = sock.accept()
                input.append(client)
                client.send('Are you a new user? Type Y or N: ')
            else:
                start(s,input,dict,c_info,log)

if __name__ == '__main__':
    main()
