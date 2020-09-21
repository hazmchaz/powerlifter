#!/usr/bin/python
from __future__ import division
import sys
import os
from socket import *
import time
import random


#Global Variables
header_size = 4
clientAddresss = ""
serverPort = int(sys.argv[1])
fileName = sys.argv[2]
Client_ISN = 0


#set up server socket
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', serverPort))


fileOffset = 0
msgBuffer = []
def addPacket(p):
    
    #already written to file
    if(p.offset < fileOffset):
        print p.seq," Duplicate Packet (F)"
        return
    
    #alredy in buffer
    for b in msgBuffer:
        if(b.offset == p.offset):
            print p.seq," Duplicate Packet (B)"
            return
            
    
    print p.seq," Packet Received"

    
    msgBuffer.append(p)
    msgBuffer.sort()
    refreshBuffer()
    
def refreshBuffer():
    global fileOffset
    global msgBuffer
        
    numToRemove = 0
    for m in msgBuffer:
        if(m.offset == fileOffset):
            with open(fileName, "a") as myfile:
                myfile.write(m.data)
            fileOffset += len(m.data)
            numToRemove += 1
        else:
            break
    msgBuffer = msgBuffer[numToRemove:]


def shouldAck():
    if(lastAck == int(fileOffset)+int(Client_ISN)):
        return False
    else:
        return True

lastAck = -1
def getAck():
    lastAck = int(fileOffset)+int(Client_ISN)
    return newHeader("ACK", int(fileOffset)+int(Client_ISN))
 
class pkt:
    def __init__(self, data, seq):
        self.offset = int(seq) - int(Client_ISN)
        self.seq = seq
        self.data = data
        
    def __lt__(self, other):
         return self.offset < other.offset
    
def headerField(field, header):
    for s in header:
        f = s.split(':')[0]
        if(len(s.split(':'))>1):
            v = s.split(':')[1]
        else:
            v = ""
        if(field == f):
            return v
    return None

def headerLen(header):
    l = 0
    for s in header:
        l += len(s)+1
    return l

def newHeader(type, seq=None):
    global seed
    global Client_ISN
    
    header = ""
    
    if(seq == None):
        seq = ""
    
    if(type == "ACK"):
        header = (
                "STP Header\n"
                "seqNum:" + "\n"
                "ackNum:" + str(seq) + "\n"
                "flag:"   + "ACK" + "\n"
             )
    
    elif(type == "SYNACK"):
        header = (
                  "STP Header\n"
                  "seqNum:" + "\n"
                  "ackNum:" + "\n"
                  "flag:"   + "SYNACK" + "\n"
                  )
    
    elif(type == "FIN"):
        header = (
                "STP Header\n"
                "seqNum:" + "\n"
                "ackNum:" + "\n"
                "flag:"   + "FIN" + "\n"
             )
        
    elif(type == "FINACK"):
        header = (
                "STP Header\n"
                "seqNum:" + "\n"
                "ackNum:" + "\n"
                "flag:"   + "FINACK" + "\n"
             )

    return header
        
def handshake():
    global Client_ISN
    global clientAddress
    
    #set timeout
    serverSocket.settimeout(1);

    #wait for the SYN packet
    syn = False
    while(syn == False):
        try:
            message, address = serverSocket.recvfrom(2048)
            header = message.split('\n')[:header_size]
            body = message[headerLen(header):]
            if(headerField("flag",header) == "SYN"):
                Client_ISN = headerField("seqNum",header)
                clientAddress = address
                syn = True
        except:
            pass


    #reply with the SYNACK
    synack = False
    while(synack == False):
        try:
            serverSocket.sendto(newHeader("SYNACK"),clientAddress)
            message, address = serverSocket.recvfrom(2048)
            header = message.split('\n')[:header_size]
            body = message[headerLen(header):]
            if(headerField("flag",header) == "ACK"):
                addPacket(pkt(body,headerField("seqNum",header)))
                serverSocket.sendto(getAck(),clientAddress)
                synack = True
        except:
            pass           
      
def terminate():
    serverSocket.settimeout(0.01)
    #send acknowlegement
    flg = False
    while(flg == False):
        try:
            serverSocket.sendto(newHeader("FINACK"),clientAddress)
            serverSocket.sendto(newHeader("FIN"),clientAddress)
                        
            message, address = serverSocket.recvfrom(2048)
            header = message.split('\n')[:header_size]
            if(headerField("flag",header) == "FINACK"):
                serverSocket.close()
                flg = True
        except:
            pass
           
def receiveData():
    serverSocket.settimeout(0.2);
    while True: 
        try:
            message, address = serverSocket.recvfrom(2048)
            header = message.split('\n')[:header_size]
            body = message[headerLen(header):]
            
            if(headerField("flag", header) == "FIN"):
                return
            
            addPacket(pkt(body,headerField("seqNum",header)))

            serverSocket.sendto(getAck(),clientAddress)

        except:
            pass
   
def main():

    #clear file before starting     
    with open(fileName, "w") as myfile:
        myfile.write("")   

    print "Receiver Started on Port ",serverPort
    handshake()
    receiveData()
    terminate()
    print "connection terminated"
    exit(0)

try:
    main()
except:
    exit(1)
