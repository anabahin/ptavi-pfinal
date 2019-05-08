#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import socketserver
from time import gmtime, strftime, time
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class XMLHandler(ContentHandler):

    def __init__(self, conf):
        self.tags = {}
        self.diccionario = conf

    def startElement(self, name, attrs):

        if name in self.diccionario:
            atributos = {}
            for atr in self.diccionario[name]:
                self.tags[name + '_' + atr] = attrs.get(atr, "")

    def get_tags(self):
        return self.tags


def get_file():
    if os.path.exists(sys.argv[1]):
        return sys.argv[1]
    else:
        sys.exit('file', sys.argv[1], 'not found')


class SIPUAHandler(socketserver.DatagramRequestHandler):

    def handle(self):
        receive = self.rfile.read().decode('utf-8')
        print('Recibido -- ', receive)
        method = receive.split()[0]
        if method == 'INVITE':
            ip_dst = receive.split('\r\n')[4].split()[-1]
            port_dst = receive.split('\r\n')[7].split()[1]
            self.rtp_ip = ip_dst
            self.rtp_port = port_dst
            user = config['account_username']
            rtpport = config['rtpaudio_puerto']
            ip = config['uaserver_ip']
            mess = 'SIP/2.0 100 Trying\r\n\r\nSIP/2.0 180 Ringing\r\n\r\n'
            mess += 'SIP/2.0 200 OK\r\nContent-Type: application/sdp\r\n\r\n'
            mess += 'v=0\r\no=' + user + ' ' + ip + '\r\ns=misesion\r\n'
            mess += 't=0\r\nm=audio ' + rtpport + ' RTP\r\n'
            self.wfile.write(bytes(mess, 'utf-8'))
        elif method == 'ACK':
            pass
        elif method == 'BYE':
            self.wfile.write(b'SIP/2.0 200 OK\r\n')
        else:
            self.wfile.write(b'SIP/2.0 405 Method not Allowed\r\n')

if __name__ == "__main__":
  
  conf = {'account': ['username', 'passwd'],
        'uaserver': ['ip', 'puerto'],
        'rtpaudio': ['puerto'],
        'regproxy': ['ip', 'puerto'],
        'log': ['path'],
        'audio': ['path']}
  
    if len(sys.argv) == 2:
        xml_file = get_file()
    else:
        sys.exit('usage: python3 uaserver.py <fichero xml>')

    parser = make_parser()
    xmlhandler = XMLHandler(conf)
    parser.setContentHandler(xmlhandler)
    parser.parse(open(xml_file))
    config = xmlhandler.get_tags()
    address = (config['uaserver_ip'], int(config['uaserver_puerto']))

    serv = socketserver.UDPServer(address, SIPUAHandler)

    print("Lanzando servidor SIP de user agent...")
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
