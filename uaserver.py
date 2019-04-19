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
        if method == 'INVITE':
            pass
        elif method == 'ACK':
            pass
        elif method == 'BYE':
            pass
        else:
            pass

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
