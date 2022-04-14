from socket import *
import os
import sys
import struct
import time
import select
import math
import binascii
ICMP_ECHO_REQUEST = 8

packet_min = 0
packet_max = 0
packet_avg = 0


def checksum(string):
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0

    while count < countTo:
        thisVal = (string[count + 1]) * 256 + (string[count])
        csum += thisVal
        csum &= 0xffffffff
        count += 2

    if countTo < len(string):
        csum += (string[len(string) - 1])
        csum &= 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer



def receiveOnePing(mySocket, ID, timeout, destAddr):
   timeLeft = timeout

   while 1:
       startedSelect = time.time()
       whatReady = select.select([mySocket], [], [], timeLeft)
       howLongInSelect = (time.time() - startedSelect)
       if whatReady[0] == []:
           return "Request timed out."

       timeReceived = time.time()
       recPacket, addr = mySocket.recvfrom(1024)


       icmpHeader = recPacket[20:28]
       icmpType, code, mychecksum, packetID, sequence = struct.unpack("bbHHh", icmpHeader)

       if icmpType != 0 and packetID == ID:
           bytesInDouble = struct.calcsize("d")
           timeSent = struct.unpack("d", recPacket[28:28 + bytesInDouble])[0]
           delay = timeReceived - timeSent
           ttl = ord(struct.unpack("c", recPacket[8,9])[0].decode())

           return (delay, ttl, bytesInDouble)

       timeLeft = timeLeft - howLongInSelect

       if timeLeft <= 0:
           return "Request timed out."


def sendOnePing(mySocket, destAddr, ID):
   myChecksum = 0
   header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
   data = struct.pack("d", time.time())
   myChecksum = checksum(header + data)
   if sys.platform == 'darwin':
       myChecksum = htons(myChecksum) & 0xffff
   else:
       myChecksum = htons(myChecksum)


   header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
   packet = header + data
   mySocket.sendto(packet, (destAddr, 1))

def doOnePing(destAddr, timeout):
   icmp = getprotobyname("icmp")
   mySocket = socket(AF_INET, SOCK_RAW, icmp)

   myID = os.getpid() & 0xFFFF
   sendOnePing(mySocket, destAddr, myID)
   delay = receiveOnePing(mySocket, myID, timeout, destAddr)

   mySocket.close()
   return delay


def ping(host, timeout=1):

   dest = gethostbyname(host)
   print("Pinging " + dest + " using Python:")
   print("")

   lst = []
   for i in range(0,4):
       delay = doOnePing(dest, timeout)
       print(delay)
       lst.append(round(delay[0]*1000,8))
       time.sleep(1)

   packet_min = min(lst)
   packet_max = max(lst)
   packet_avg = sum(lst)/len(lst)
   stddev = 0
   for i in lst:
       stddev += (i - packet_avg)**2
       stddev.math.sqrt((stddev/len(lst)))

       vars = [str(round(packet_min, 8)), str(round(packet_avg, 8)), str(round(packet_max, 8)),
            str(round(stdev(stdev_var), 8))]

   return vars

if __name__ == '_main_':
   ping("google.co.il")
