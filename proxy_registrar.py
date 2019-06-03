#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import socket
import socketserver
from hashlib import md5
from random import randint
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


def digest_nonce(proxy_name):
    digest = md5()
    digest.update(bytes(proxy_name, 'utf-8'))
    digest.digest()
    return digest.hexdigest()


def digest_response(nonce, passwd, username):
    digest = md5()
    digest.update(bytes(nonce, 'utf-8'))
    digest.update(bytes(passwd, 'utf-8'))
    digest.update(bytes(username, 'utf-8'))
    digest.digest()
    return digest.hexdigest()


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


class SIPRegistrerHandler(socketserver.DatagramRequestHandler):
    dicc = {}
    passwd = {}

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

    def expiration(self):
        expired = []
        time_exp = strftime('%Y-%m-%d %H:%M:%S', gmtime(time() + 3600))
        for user in self.dicc:
            if self.dicc[user][1] <= time_exp:
                expired.append(user)
        for user in expired:
            del self.dicc[user]

    def handle(self):
        self.json2registered()
        receive = self.rfile.read().decode('utf-8')
        ip = self.client_address[0]
        port = str(self.client_address[1])
        log_mess = 'Received from ' + ip + ':' + port
        log_mess += ': ' + receive.replace('\r\n', ' ')
        write_log(log_mess)
        method = receive.split()[0]
        print('Recibido -- ', receive)
        if method == 'REGISTER':
            user = receive.split('\r\n')[0].split()[1].split(':')[1]
            if user in self.dicc:
                expires = receive.split('\r\n')[1].split()[-1]
                if int(expires) == 0:
                    del self.dicc[user]
                else:
                    time_exp = gmtime(time() + 3600 + int(expires))
                    date_format = '%Y-%m-%d %H:%M:%S'
                    self.dicc[user][2] = strftime(date_format, time_exp)
                self.wfile.write(b'SIP/2.0 200 OK\r\n')
                ip = self.client_address[0]
                port = str(self.client_address[1])
                log_mess = 'Sent to ' + ip + ':' + port
                log_mess += ': SIP/2.0 200 OK'
                write_log(log_mess)
                print('Enviado -- 200 OK')
            else:
                if 'Digest response' in receive:
                    nonce = digest_nonce(config['server_name'])
                    response = digest_response(nonce, self.passwd[user], user)
                    resp_user = receive.split('\r\n')[2].split('"')[-2]
                    if response == resp_user:
                        ip = self.client_address[0]
                        port = receive.split('\r\n')[0]
                        port = port.split()[1].split(':')[2]
                        caddress = ip + ':' + port
                        expires = receive.split('\r\n')[1].split()[-1]
                        time_exp = gmtime(time() + 3600 + int(expires))
                        exp = strftime('%Y-%m-%d %H:%M:%S', time_exp)
                        self.dicc[user] = [ip, port, exp]
                        self.wfile.write(b'SIP/2.0 200 OK\r\n')
                        log_mess = 'Sent to ' + caddress
                        log_mess += ': SIP/2.0 200 OK'
                        write_log(log_mess)
                        print('Enviado -- 200 OK')
                    else:
                        self.wfile.write(b'SIP/2.0 400 Bad Request\r\n')
                        ip = self.client_address[0]
                        port = str(self.client_address[1])
                        caddress = ip + ':' + port
                        log_mess = 'Sent to ' + caddress
                        log_mess += ': SIP/2.0 400 Bad Request'
                        write_log(log_mess)
                        print('Enviado -- 400 Bad Request')
                else:
                    nonce = digest_nonce(config['server_name'])
                    mess = 'SIP/2.0 401 Unauthorized\r\nWWW Authenticate: '
                    mess += 'Digest nonce="' + nonce + '"\r\n'
                    self.wfile.write(bytes(mess, 'utf-8'))
                    ip = self.client_address[0]
                    port = str(self.client_address[1])
                    caddress = ip + ':' + port
                    log_mess = 'Sent to ' + caddress
                    log_mess += ': ' + mess.replace('\r\n', ' ')
                    write_log(log_mess)
                    print('Enviado -- 401 Unauthorized')
        elif method == 'INVITE':
            user_dst = receive.split('\r\n')[0].split()[1].split(':')[1]
            user_src = receive.split('\r\n')[4].split('=')[1].split()[0]
            ip = self.client_address[0]
            port = str(self.client_address[1])
            caddress = ip + ':' + port
            if user_src in self.dicc:
                if user_dst in self.dicc:
                    ip_dst = self.dicc[user_dst][0]
                    port_dst = int(self.dicc[user_dst][1])
                    address = (ip_dst, port_dst)
                    mess = self.add_headers(receive)
                    resp = self.sent(mess, address)
                    if resp:
                        self.wfile.write(bytes(resp, 'utf-8'))
                        log_mess = 'Sent to ' + caddress + ': '
                        log_mess += resp.replace('\r\n', ' ')
                        write_log(log_mess)
                else:
                    self.wfile.write(b'SIP/2.0 404 User Not Found\r\n')
                    log_mess = 'Sent to ' + caddress
                    log_mess += ': SIP/2.0 404 User Not Found'
                    write_log(log_mess)
                    print('Enviado -- 404 User Not Found')
            else:
                self.wfile.write(b'SIP/2.0 404 User Not Found\r\n')
                log_mess = 'Sent to ' + caddress
                log_mess += ': SIP/2.0 404 User Not Found'
                write_log(log_mess)
                print('Enviado -- 404 User Not Found')
        elif method == 'ACK':
            user_dst = receive.split()[1].split(':')[1]
            ip = self.client_address[0]
            port = str(self.client_address[1])
            caddress = ip + ':' + port
            if user_dst in self.dicc:
                address = (self.dicc[user_dst][0], int(self.dicc[user_dst][1]))
                mess = self.add_headers(receive)
                resp = self.sent(mess, address)
            else:
                self.wfile.write(b'SIP/2.0 404 User Not Found\r\n')
                log_mess = 'Sent to ' + caddress
                log_mess += ': SIP/2.0 404 User Not Found'
                write_log(log_mess)
                print('Enviado -- 404 User Not Found')
        elif method == 'BYE':
            user_dst = receive.split()[1].split(':')[1]
            ip = self.client_address[0]
            port = str(self.client_address[1])
            caddress = ip + ':' + port
            if user_dst in self.dicc:
                address = (self.dicc[user_dst][0], int(self.dicc[user_dst][1]))
                mess = self.add_headers(receive)
                resp = self.sent(mess, address)
                self.wfile.write(bytes(resp, 'utf-8'))
            else:
                self.wfile.write(b'SIP/2.0 404 User Not Found\r\n')
                log_mess = 'Sent to ' + caddress
                log_mess += ': SIP/2.0 404 User Not Found'
                write_log(log_mess)
                print('Enviado -- 404 User Not Found')
        else:
            self.wfile.write(b'SIP/2.0 405 Method Not Allowed\r\n')
            ip = self.client_address[0]
            port = str(self.client_address[1])
            caddress = ip + ':' + port
            log_mess = 'Sent to ' + caddress
            log_mess += ': SIP/2.0 405 Method Not Allowed'
            write_log(log_mess)
            print('Enviado -- 405 Method Not Allowed')
        self.expiration()
        self.registered2json()

    def sent(self, mess, address):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
            my_socket.connect(address)
            my_socket.send(bytes(mess, 'utf-8'))
            caddress = address[0] + ':' + str(address[1])
            log_mess = 'Sent to ' + caddress + ': ' + mess.replace('\r\n', ' ')
            write_log(log_mess)
            method = mess.split()[0]
            print('Reenviado -- ', method)
            try:
                data = my_socket.recv(1024).decode('utf-8')
                log_mess = 'Receive from ' + caddress + ': '
                log_mess += data.replace('\r\n', ' ')
                write_log(log_mess)
                return data
            except:
                log_mess = 'No server listening at ' + address[0]
                log_mess += ' port ' + str(address[1])
                write_log(log_mess)
                return ''

    def add_headers(self, receive):
        headers = 'Call-Id: ' + str(randint(0,9)) + ' ' 
        headers += receive.split()[0] + '\r\n' + 'To: ' 
        headers += receive.split('\r\n')[0].split()[1].split(':')[1] + '\r\n'
        mess = ''
        for line in receive.split('\r\n'):
            if 'SIP/2.0' in line:
                mess += line + '\r\n' + headers
            else:
                mess += line + '\r\n'
        return mess

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
        serv.serve_forever()
    except KeyboardInterrupt:
        print('\nEnd server: ' + config['server_name'])
        write_log('Finishing.')
