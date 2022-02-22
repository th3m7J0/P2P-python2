#!/usr/bin/python
# -*- coding: utf-8 -*- 

import socket
import os
import sys
import select

host = ''
port = 9896
backlog = 10
size = 4096

#function to send file
def sendf(soc,uname):
    #print "uname in sendf: {}".format(uname)
    data = soc.recv(size)
    user_input = raw_input(data)
    soc.send(user_input)   
    file=open('{}/{}'.format(uname,user_input),'rb')
    data=file.read()
    soc.send(data)
    print 'File sent'

#function to receive file
def recvf(soc,uname):
    #print "uname in recvf: {}".format(uname)
    soc.send('file name: ')
    fname = soc.recv(size) 
    print "fname is : {}".format(fname)
    data = soc.recv(40960)
    file=open('{}/{}'.format(uname,fname),'w')
    file.write(str(data))
    file.close()
    print 'File received'

#function for client to listen for other client connections
def clisten(user_input,uname):
    cport = int(user_input)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #binding the socket to localhost and port
    s.bind((host,cport))
    print 'listening'
    s.listen(backlog)
    clist=[s]
    while 1:
    # Using Select to handle multiplexing
        inready,outready,exceptready = select.select(clist,[],[])
        for sock in inready:
            if sock == s:
                client, address = s.accept()
                clist.append(client)
                print 'connected'
                client.send('Start typing')
            else:
                try:
                    data = sock.recv(size)
                    if data:
                        print data
                        if data == '\SEND_FILE':
                            recvf(client,uname) 
                        if data == '\CLOSE_SESSION':
                            print 'session ended'
                            client.close()
                            break
                        user_input = raw_input('<{}> '.format(uname))
                        client.send(user_input)
                        if user_input == '\SEND_FILE':
                            sendf(client,uname)
                        if user_input == '\CLOSE_SESSION':
                            print 'session ended'
                            client.close()
                            break
                except:
                    client.close()
                    input.remove(client)
                    #continue                
    return             

#function for client to connect to listening client                
def cconnect(data,uname):
    cport = int(data)
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        soc.connect((host,cport))
    except:
        print 'Unable to connect to client'
    print 'now connected'
    while 1:
        data = soc.recv(size)
        print data
        if data == '\SEND_FILE':
            recvf(soc,uname) 
        if data == '\CLOSE_SESSION':
            print 'session ended'
            soc.close()
            break
        user_input = raw_input('<{}> '.format(uname))
        soc.send(user_input)
        if user_input == '\SEND_FILE':
            sendf(soc,uname) 
        if user_input == '\CLOSE_SESSION':
            print 'session ended'
            soc.close()
            break
    return

#main to handle connection between server and client
def main():
    #creating a socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.connect((host,port))
    except:
        print 'Unable to connect to chat server'
        sys.exit()
    # tmp variable to save username    
    uname = ''
    while 1:
        data = sock.recv(size)
        if(len(data.split('--'))==2): #we sent the uname from the server
            uname = data.split('--')[1]
            sock.send("\n")
            continue
        
        if data.isdigit() and int(data)>2000:
            cconnect(data,uname)
        user_input = raw_input(data)
        sock.send(user_input)
        if user_input.isdigit() and int(user_input)>2000:
            clisten(user_input,uname)
        if user_input == '\DISCONNECT_CLIENT':
            sock.close()
            break

if __name__ == '__main__':
    sys.exit(main())
