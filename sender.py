#!/usr/bin/python
from __future__ import division
import sys
import os
from socket import *
import time
import random
import math

debug = False

if(len(sys.argv)!=9):
    print "Error Usage:"
    print "python sender.py <receiver_host_ip> <receiver_port> <file.txt> <MWS> <MSS> <timeout> <pdrop> <seed>"
    exit(1)


#save the input arguments
receiver_host = sys.argv[1]
receiver_port = int(sys.argv[2])
file_name = sys.argv[3]
MWS = int(sys.argv[4])
MSS = int(sys.argv[5])
timeout = float(sys.argv[6])
pdrop = float(sys.argv[7])
seed = int(sys.argv[8])


#global variables
offset = 0
header_size = 4
Client_ISN = 0
fileSize = os.path.getsize(file_name)
window = []
start_time = time.clock()
      
if(debug):
    print " receiver_host: ",receiver_host
    print " receiver_port: ",receiver_port
    print "     file_name: ",file_name
    print "           MWS: ",MWS
    print "           MSS: ",MSS
    print "       timeout: ",timeout
    print "         pdrop: ",pdrop
    print "          seed: ",seed
    print

def getTime():
    pass
    return (time.clock() - start_time)*1000      

class pkt:
    def __init__(self, packet, pktOffset):
        self.header = ""
        self.data = packet
        self.acked = False
        self.pktOffset = pktOffset
        self.seq = pktOffset + Client_ISN
        self.numSent = 0
    
    def getPacket(self):
        return (self.header + self.data)
    
#stats
dataTransfered = os.path.getsize(file_name)
numDataSegs = int(math.ceil(dataTransfered/MSS))
totalOutgoingSegs = 0
numPacketsDropped = 0    
numDuplicateAcks = 0 

def printStats():
    print ""
    print "Data Transfered: ", dataTransfered
    print "Data Segments Sent: ", numDataSegs
    print "Packets Dropped: ", numPacketsDropped
    print "Retransmitted Segments: ", (totalOutgoingSegs - (numDataSegs + 1)) #3 neccessary setup segments
    print "Duplicate Acknowledgements: ", numDuplicateAcks

newLineCount = 0
def nextDataSeg():
    global offset
    global newLineCount
    
    if(offset > fileSize):
        return ""
        
    dataSeg = ""
    FILE = open(file_name, 'r')
    FILE.seek(offset + newLineCount,0)
    dataSeg = pkt(FILE.read(MSS),offset)

    FILE.close()
    
    newLineCount += dataSeg.data.count('\n')
    offset += MSS
    return dataSeg
             
def nextSTPSeg():    
    global fileSize
    global offset
    global Client_ISN
    
    if(offset >= fileSize):
        return None
  
    p = nextDataSeg()
    
    if(p.data == ""):
        return None
    
    
    #create header
    if(p.pktOffset == 0):
        p.header = newHeader("ACK", p.seq)
    else:
        p.header = newHeader("", p.seq)
    
    return p
    
def getWindowSize():
    global window
    size = 0
    for p in window:
        size += len(p.data)
    return size

def updateWindow():
    global window
    
    #delete acknowledged packets from the window
    numToRemove = 0
    for p in window:
        if(p.acked == False):
            break
        else:
            numToRemove += 1
            
    del window[:numToRemove]
            
    
    #update the window with new packets
    size = getWindowSize()
    while(size+MSS <= MWS):
        s = nextSTPSeg()
        if(s is None):
            break
        window.append(s)
        size += len(s.data)
    return

def windowAllAcked():
    for w in window:
        if(w.acked == False):
            return False
    return True 

def ackPacket(seqNum):
    for w in window:
        if(int(seqNum) - Client_ISN >= w.pktOffset + len(w.data)):
            w.acked = True
    return
 
def displayWindow():
    print "windowsize: ", getWindowSize()
    for s in window:
        sys.stdout.write('\n')
        sys.stdout.write(s.header)
        print    
   
def newHeader(type, seq=None):
    global seed
    global Client_ISN
    
    if(seq == None):
        seq = ""
    
    if(type == "SYN"):
        header = (
                "STP Header\n"
                "seqNum:" + str(Client_ISN) + "\n"
                "ackNum:" + "\n"
                "flag:"   + "SYN" + "\n"
             )
        return header
        
    elif(type == "ACK"):
        header = (
                "STP Header\n"
                "seqNum:" + str(seq) + "\n"
                "ackNum:" + "\n"
                "flag:"   + "ACK" + "\n"
             )
        return header
        
    elif(type == "FIN"):
        header = (
                "STP Header\n"
                "seqNum:" + "\n"
                "ackNum:" + "\n"
                "flag:"   + "FIN" + "\n"
             )
        return header
        
    elif(type == "FINACK"):
        header = (
                "STP Header\n"
                "seqNum:" + "\n"
                "ackNum:" + "\n"
                "flag:"   + "FINACK" + "\n"
             )
        return header    
    
    elif(type == ""):
        header = (
                "STP Header\n"
                "seqNum:" + str(seq) + "\n"
                "ackNum:" + "\n"
                "flag:"   + "\n"
             )
        return header
    else:
        return ""
     
def headerField(field, header):
    for s in header:
        f = s.split(':')[0]
        if(len(s.split(':'))>1):
            v = s.split(':')[1]
        else:
            v = ""
        if(field == f):
            return v
    return ""

def handshake():
    #update window before starting
    updateWindow()

    #create syn packet
    synPKT = newHeader("SYN")
    
    clientSocket.settimeout(0.01)

    synack = False
    while(synack == False):
        try:
            PLD(synPKT) #send SYN
            if(receive().flg == "SYNACK"):
                synack = True
                
        except:
            pass

    return   

def PLD(message):

    global totalOutgoingSegs
    totalOutgoingSegs += 1

    header = message.split('\n')[:header_size]
    body = message[headerLen(header):]

    seq = headerField("seqNum", header)
    ack = headerField("ackNum", header)

    flg = headerField("flag", header)

    if(flg == ""):
        flgDisp = "D"
    if(flg == "SYN"):
        flgDisp = "S"
    if(flg == "ACK"):
        flgDisp = "A"
    if(flg == "FIN"):
        flgDisp = "F"
    if(flg == "FINACK"):
        flgDisp = "FA"

    dispACK = ack
    if(ack == ""):
        dispACK = "0"

    dispSEQ = seq
    if(seq == ""):
        dispSEQ = "0"


    status = "snd "
    

    if(flg == ""):
        if(random.random() > pdrop):
            clientSocket.sendto(message,(receiver_host, receiver_port))
        else:
            global numPacketsDropped
            numPacketsDropped += 1
            status = "drop"
    else:
        clientSocket.sendto(message,(receiver_host, receiver_port))

    s = '{0:<5} {1:<9} {2:<3} {3:<6} {4:<6} {5:<6}'\
        .format(status,str("%.2f" % getTime()),flgDisp,dispSEQ,str(len(body)),dispACK)

    print s
    with open("Sender_log.txt", "a") as myfile:
            myfile.write(s)   
            myfile.write("\n")

def headerLen(header):
    l = 0
    for s in header:
        l += len(s)+1
    return l

def sendData():
    clientSocket.settimeout(0.01)
    updateWindow()
    while(len(window)>0):
        
        #send all packets in window
        for w in window:
            if(w.acked == False):
                PLD(w.getPacket())
            
        #record acknowledgements
        start = int(round(time.time() * 1000))
        cur = int(round(time.time() * 1000))

        global numDuplicateAcks
        lastAck = 0
        ackTally = 1
        fastRetransmited = []
        while(cur - start < timeout):
            try:
                r = receive()
                if(r.flg == "ACK"):
                    ackPacket(r.ack)

                    #update last ack and tally
                    if(int(lastAck) == int(r.ack)):
                        ackTally += 1
                        numDuplicateAcks += 1
                    else:
                        lastAck = int(r.ack)
                        ackTally = 1
                    
                    #fast retransmit
                    if(ackTally>=3):
                        #set a flag to true if this has already been fast retransmitted
                        flg = True
                        for s in fastRetransmited:
                            if(s == lastAck):
                                flg = False

                        if(flg):
                            for w in window:
                                if(w.seq >= lastAck):
                                    fastRetransmited.append(w.seq)
                                    PLD(w.getPacket())
                                    break

            except:
                pass
            finally:
                cur = int(round(time.time() * 1000))

                if(windowAllAcked == True):
                    break
        updateWindow()
         
def terminate():
    clientSocket.settimeout(0.01)

    #initiate connection termination and wait for response
    flg = False
    while(flg == False):
        try:
            PLD(newHeader("FIN"))
            
            if(receive().flg == "FINACK"):
                flg = True
                
        except:
            pass
         
    #wait for the Sever to send FIN and continue
    flg = False
    while(flg == False):
        try:
            if(receive().flg == "FIN"):
                flg = True
        except:
            pass
            
    #send the final acknowledgement and wait to see there is no reply
    clientSocket.settimeout(3*round(timeout/1000))
    flg = False
    while(flg == False):
        PLD(newHeader("FINACK"))
        try:
            receive()
        except:
            flg = True
  
class response:
    def __init__(self, message):
        self.header = message.split('\n')[:header_size]
        self.data = ""
        self.seq = headerField("seqNum", self.header)
        self.ack = headerField("ackNum", self.header)
        self.flg = headerField("flag", self.header)
        self.len = 0
        self.time = getTime()

        dispACK = self.ack
        if(self.ack == ""):
            dispACK = "0"

        dispSEQ = self.seq
        if(self.seq == ""):
            dispSEQ = "0"



        if(self.flg == "SYNACK"):
            flgDisp = "SA"
        if(self.flg == "ACK"):
            flgDisp = "A"
        if(self.flg == "FIN"):
            flgDisp = "F"
        if(self.flg == "FINACK"):
            flgDisp = "FA"


        s = '{0:<5} {1:<9} {2:<3} {3:<6} {4:<6} {5:<6}'\
            .format("rcv",str("%.2f" % self.time),flgDisp,dispSEQ,str(self.len),dispACK)

        print s

        with open("Sender_log.txt", "a") as myfile:
            myfile.write(s)   
            myfile.write("\n")

def receive():
    message, address = clientSocket.recvfrom(2048)
    r = response(message)
    return r
    

#clear the log file before starting     
with open("Sender_log.txt", "w") as myfile:
    myfile.write("")  

#start client socket  
clientSocket = socket(AF_INET, SOCK_DGRAM)

#seed the random number generator for the pld module
random.seed(seed)

#create random ISN
Client_ISN = random.randint(0,1000)


handshake()

sendData()

terminate()

printStats()

exit(0)      
        