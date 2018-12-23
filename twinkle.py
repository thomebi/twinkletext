#!/usr/bin/env python
import requests
import socket
import struct
import asyncio
import base64
import cv2  
import numpy as np
import time

devices = []

class twinkly:
    
    def __init__(self, ip, name):
        self.name = name
        self.ip   = ip 

    def gestalt(self):
        q="http://" + self.ip + "/xled/v1/gestalt"
        r = requests.get( q )
        print(r.json())
        self.leds = r.json()["number_of_led"]

    def login(self):
        CHALLENGE='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\a'
        challenge = {'challenge': CHALLENGE}
        q="http://" + self.ip + "/xled/v1/login"
        r = requests.post( q, json=challenge)
        print(r)
        rjson = r.json();
        self.token=rjson["authentication_token"]
        self.challenge_response = rjson["challenge-response"]

    def verify(self):
        auth = {"X-Auth-Token": self.token}
        response = {'challenge-response': self.challenge_response}
        q="http://" + self.ip + "/xled/v1/verify"
        r = requests.post( q, headers=auth, json=response)
        print(r)

    def mode(self, mode):
        auth = {"X-Auth-Token": self.token}
        response = {'mode': mode}
        q="http://" + self.ip + "/xled/v1/led/mode"
        r = requests.post( q, headers=auth, json=response)
        print(r)

    def show(self, image):
        UDP_PORT = 7777 
        stx=b'\x01'
        msg = b"".join([stx,base64.b64decode(self.token)])
        msg = b"".join([msg,struct.pack('B', self.leds)])
        msg = b"".join([msg,image.tobytes()])
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.sendto(msg, (self.ip, UDP_PORT))
   


def discover():
    UDP_BCAST_IP = "255.255.255.255"
    UDP_PORT = 5555 
    MESSAGE = '\x01discover'
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(bytes(MESSAGE, "utf-8"), (UDP_BCAST_IP, UDP_PORT))
    data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
    print(data)          
    D,C,B,A,ok =struct.unpack('BBBB2s', data[:6])
    name = data[6:-1]
    ip=".".join((str(A),str(B),str(C),str(D)))
    print(ok)
    if ok == b'OK' :      
        devices.append( twinkly(ip, name) )
        print(ip)        


def anim(dev):
    ## lines are top to bottom:
    #height=11;
    width=11
    #width =20
    height=20
    image = np.zeros((height,width,3), np.uint8)
    for x in range(0,width):
        for y in range(0,height):
            image[x,y] = (255,0,0)
            dev.show(image)
            print( str(x) + ", " + str(y) )
            time.sleep(1)  

 
def write(dev, text):
    t_height=11
    t_width =20
    img_width=t_height
    img_height=t_width
    #font = cv2.FONT_HERSHEY_SIMPLEX
    #font = cv2.FONT_HERSHEY_COMPLEX_SMALL
    font = cv2.FONT_HERSHEY_DUPLEX
    WINDOW_NAME = 'Preview'
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)
    cv2.startWindowThread()
    textsize, baseline = cv2.getTextSize(text,font,0.5,1)
    for x in range(0,textsize[0]+t_width):
        img = np.zeros((img_height,img_width,3), np.uint8)
        t_img = np.zeros((t_height,t_width,3), np.uint8)
        cv2.putText(t_img,text,(t_width-x,t_height-1), font, 0.5,(255,255,255)) 
        t_img = cv2.transpose(t_img)
        #cv2.flip(t_img,t_img)
        img = img + t_img   
        cv2.imshow(WINDOW_NAME,t_img)
        cv2.waitKey(1) 
        dev.show(img)
        time.sleep(0.2)
    cv2.destroyAllWindows()

   
discover()
for dev in devices:
    dev.gestalt()
    dev.login()
    dev.verify()
    dev.mode("rt")
    write(dev, "Merry X-Mas")
    dev.mode("movie")
 #   anim(dev)
