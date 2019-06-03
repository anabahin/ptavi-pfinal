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


def date():
    now = gmtime(time() + 3600)
    return strftime('%Y%m%d%H%M%S', now)


def write_log(line):
    with open(config['log_path'], 'a') as log:
        log.write(date() + ' ' + line + '\n')


def get_file():
    if os.path.exists(sys.argv[1]):
        return sys.argv[1]
    else:
        sys.exit('file', sys.argv[1], 'not found')

conf = {'account': ['username', 'passwd'],
        'uaserver': ['ip', 'puerto'],
        'rtpaudio': ['puerto'],
        'regproxy': ['ip', 'puerto'],
        'log': ['path'],
        'audio': ['path']}


class SIPUAHandler(socketserver.DatagramRequestHandler):
    rtp_ip = ''
    rtp_port = ''

    def handle(self):
        receive = self.rfile.read().decode('utf-8')
        caddress = self.client_address[0] + ':' + str(self.client_address[1])
        log_mess = 'Received from ' + caddress
        log_mess += ': ' + receive.replace('\r\n', ' ')
        write_log(log_mess)
        print('Recibido -- ', receive)
        method = receive.split()[0]
        if method == 'INVITE':
            ip_dst = receive.split('\r\n')[6].split()[-1]
            port_dst = receive.split('\r\n')[9].split()[1]
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
            log_mess = 'Sent to ' + caddress
            log_mess += ': ' + mess.replace('\r\n', ' ')
            write_log(log_mess)
        elif method == 'ACK':
            mp32rtp = './mp32rtp -i ' + self.rtp_ip + ' -p '
            mp32rtp += self.rtp_port + ' < ' + config['audio_path']
            cvlc = 'cvlc rtp://@' + self.rtp_ip + ':' + self.rtp_port
            print('Ejecutando -- ', mp32rtp, '&', cvlc)
            os.system(mp32rtp + ' & ' + cvlc)
            self.rtp_ip = ''
            self.rtp_port = ''
        elif method == 'BYE':
            self.wfile.write(b'SIP/2.0 200 OK\r\n')
            log_mess = 'Sent to ' + caddress + ': SIP/2.0 200 OK'
            write_log(log_mess)
        else:
            self.wfile.write(b'SIP/2.0 405 Method not Allowed\r\n')
            log_mess = 'Sent to ' + caddress
            log_mess += ': SIP/2.0 405 Method Not Allowed'
            write_log(log_mess)

if __name__ == "__main__":
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
        write_log('Starting server...')
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
        write_log('Finishing server.')
