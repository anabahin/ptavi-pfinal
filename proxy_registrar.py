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
        ip = self.client_address[0]
        port = str(self.client_address[1])
        method = receive.split()[0]
        print('Recibido -- ', method)
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
                print('Enviado -- 200 OK')
            else:
                if 'Digest response' in receive:
                    nonce = digest_nonce(config['server_name'])
                    response = digest_response(nonce, self.passwd[user], user)
                    resp_user = receive.split('\r\n')[2].split('"')[-2]
                    if response == resp_user:
                        ip = self.client_address[0]
                        port = receive.split('\r\n')[0].split()[1].split(':')[2]
                        caddress = ip + ':' + port
                        expires = receive.split('\r\n')[1].split()[-1]
                        time_exp = gmtime(time() + 3600 + int(expires))
                        exp = strftime('%Y-%m-%d %H:%M:%S', time_exp)
                        self.dicc[user] = [ip, port, exp]
                        self.wfile.write(b'SIP/2.0 200 OK\r\n')
                        print('Enviado -- 200 OK')
                    else:
                        self.wfile.write(b'SIP/2.0 400 Bad Request\r\n')
                        print('Enviado -- 400 Bad Request')
                else:
                    nonce = digest_nonce(config['server_name'])
                    mess = 'SIP/2.0 401 Unauthorized\r\nWWW Authenticate: '
                    mess += 'Digest nonce="' + nonce + '"\r\n'
                    self.wfile.write(bytes(mess, 'utf-8'))
                    print('Enviado -- 401 Unauthorized')
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
