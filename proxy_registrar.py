#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import json
import socketserver
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


class SIPRegistrerHandler(socketserver.DatagramRequestHandler):
    dicc = {}

    def registered2json(self):
        with open(config['database_path'], 'w') as reg_file:
            json.dump(self.dicc, reg_file, indent=3)

    def json2registered(self):
        try:
            with open(config['database_path'], 'r') as reg_file:
                self.dicc = json.load(reg_file)
            with open(config['database_passwdpath'], 'r') as passwd_file:
                self.passwd = json.load(passwd_file)
        except(FileNotFoundError):
            pass

    def handle(self):
        self.json2registered()
        receive = self.rfile.read().decode('utf-8')
        if method == 'REGISTER':
            pass
        elif method == 'INVITE':
            pass
        elif method == 'ACK':
            pass
        elif method == 'BYE':
            pass
        else:
            pass
        self.registered2json()


if __name__ == "__main__":

    if len(sys.argv) == 2:
        xml_file = get_file()
    else:
        sys.exit('usage: python3 proxy_registrar.py <fichero xml>')

    conf = {'server': ['name', 'ip', 'puerto'],
            'database': ['path', 'passwdpath'],
            'log': ['path']}

    parser = make_parser()
    xmlhandler = XMLHandler(conf)
    parser.setContentHandler(xmlhandler)
    parser.parse(open(xml_file))
    config = xmlhandler.get_tags()
    address = (config['server_ip'], int(config['server_puerto']))

    serv = socketserver.UDPServer(address, SIPRegistrerHandler)

    print('Register SIP server: ' + config['server_name'] + '\n')
    try:
        write_log('Starting...')
    except KeyboardInterrupt:
        print('\nEnd server: ' + config['server_name'])
