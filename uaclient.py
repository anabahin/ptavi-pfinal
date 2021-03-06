#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import socket
from hashlib import md5
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


def digest_response(nonce, passwd, username):
    digest = md5()
    digest.update(bytes(nonce, 'utf-8'))
    digest.update(bytes(passwd, 'utf-8'))
    digest.update(bytes(username, 'utf-8'))
    digest.digest()
    return digest.hexdigest()


def send_register(socket, option):
    mess = 'REGISTER sip:' + config['account_username'] + ':'
    mess += config['uaserver_puerto'] + ' SIP/2.0\r\nExpires: ' + str(option)
    print('Enviado -- ', mess)
    log_mess = 'Sent to ' + proxy_address[0] + ':' + str(proxy_address[1])
    log_mess += ': ' + mess.replace('\r\n', ' ')
    write_log(log_mess)
    socket.send(bytes(mess, 'utf-8'))


def send_register_digest(socket, option, digest):
    mess = 'REGISTER sip:' + config['account_username'] + ':'
    mess += config['uaserver_puerto'] + ' SIP/2.0\r\nExpires: ' + str(option)
    mess += '\r\nAuthorization: Digest response="'
    mess += digest + '"\r\n'
    print('Enviado -- ', mess)
    log_mess = 'Sent to ' + proxy_address[0] + ':' + str(proxy_address[1])
    log_mess += ': ' + mess.replace('\r\n', ' ')
    write_log(log_mess)
    socket.send(bytes(mess, 'utf-8'))


def send_invite(socket, option):
    mess = 'INVITE sip:' + option + ' SIP/2.0\r\nContent-Type: '
    mess += 'application/sdp\r\n\r\nv=0\r\no=' + config['account_username']
    mess += ' ' + config['uaserver_ip'] + '\r\ns=misesion\r\nt=0\r\nm=audio '
    mess += config['rtpaudio_puerto'] + ' RTP\r\n'
    print('Enviado -- ', mess)
    log_mess = 'Sent to ' + proxy_address[0] + ':' + str(proxy_address[1])
    log_mess += ': ' + mess.replace('\r\n', ' ')
    write_log(log_mess)
    socket.send(bytes(mess, 'utf-8'))


def send_bye(socket, option):
    mess = 'BYE sip:' + option + ' SIP/2.0\r\n'
    print('Enviado -- ', mess)
    log_mess = 'Sent to ' + proxy_address[0] + ':' + str(proxy_address[1])
    log_mess += ': ' + mess.replace('\r\n', ' ')
    write_log(log_mess)
    socket.send(bytes(mess, 'utf-8'))


def send_ack(socket, option):
    mess = 'ACK sip:' + option + ' SIP/2.0\r\n'
    print('Enviado -- ', mess)
    log_mess = 'Sent to ' + proxy_address[0] + ':' + str(proxy_address[1])
    log_mess += ': ' + mess.replace('\r\n', ' ')
    write_log(log_mess)
    socket.send(bytes(mess, 'utf-8'))


def send_message(socket, method, option):
    mess = method.upper() + ' sip:' + option + ' SIP/2.0\r\n'
    print('Enviado -- ', mess)
    log_mess = 'Sent to ' + proxy_address[0] + ':' + str(proxy_address[1])
    log_mess += ': ' + mess.replace('\r\n', ' ')
    write_log(log_mess)
    socket.send(bytes(mess, 'utf-8'))


def receive_message(socket):
    pr_ip = proxy_address[0]
    pr_port = str(proxy_address[1])
    try:
        data = socket.recv(1024).decode('utf-8')
        print('Recibido -- ', data)
        log_mess = 'Received from ' + pr_ip + ':' + pr_port
        log_mess += ': ' + data.replace('\r\n', ' ')
        write_log(log_mess)
    except:
        log_mess = 'Error: No server listening at ' + pr_ip
        log_mess += ' port ' + pr_port
        write_log(log_mess)
        sys.exit(log_mess)
    return data


def date():
    now = time.gmtime(time.time() + 3600)
    return time.strftime('%Y%m%d%H%M%S', now)


def write_log(line):
    with open(config['log_path'], 'a') as log:
        log.write(date() + ' ' + line + '\n')


def mp32rtp(ip, port):
    command = './mp32rtp -i ' + ip + ' -p ' + port
    command += ' < ' + config['audio_path']
    return command


def cvlc(ip, port):
    command = 'cvlc rtp://@' + ip + ':' + port
    return command


def get_file():
    if os.path.exists(sys.argv[1]):
        return sys.argv[1]
    else:
        sys.exit('file', sys.argv[1], 'not found')


def get_method():
    return sys.argv[2].upper()


def get_option(method):
    if method == 'REGISTER':
        try:
            return int(sys.argv[3])
        except:
            sys.exit('option must be a number')
    else:
        return sys.argv[3]


def get_arguments():
    xml_file = get_file()
    method = get_method()
    option = get_option(method)
    return xml_file, method, option

conf = {'account': ['username', 'passwd'],
        'uaserver': ['ip', 'puerto'],
        'rtpaudio': ['puerto'],
        'regproxy': ['ip', 'puerto'],
        'log': ['path'],
        'audio': ['path']}

if len(sys.argv) == 4:
    xml_file, method, option = get_arguments()
else:
    sys.exit('usage: python3 uaclient.py <fichero xml> <SIP method> <option>')

parser = make_parser()
xmlhandler = XMLHandler(conf)
parser.setContentHandler(xmlhandler)
parser.parse(open(xml_file))
config = xmlhandler.get_tags()

if not os.path.exists(config['log_path']):
    os.system('touch ' + config['log_path'])

proxy_address = (config['regproxy_ip'], int(config['regproxy_puerto']))
write_log('Starting client...')

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
    my_socket.connect(proxy_address)
    if method == 'REGISTER':
        send_register(my_socket, option)
        data = receive_message(my_socket)
        if '401 Unauthorized' in data:
            nonce = data.split('\r\n')[1].split('"')[-2]
            passwd = config['account_passwd']
            username = config['account_username']
            digest = digest_response(nonce, passwd, username)
            send_register_digest(my_socket, int(option), digest)
            data = receive_message(my_socket)
    elif method == 'INVITE':
        send_invite(my_socket, option)
        data = receive_message(my_socket)
        trying = 'SIP/2.0 100 Trying' in data
        ringing = 'SIP/2.0 180 Ringing' in data
        ok = 'SIP/2.0 200 OK' in data
        if trying and ringing and ok:
            send_ack(my_socket, option)
            ip = data.split('\r\n')[8].split()[-1]
            port = data.split('\r\n')[11].split()[1]
            command = mp32rtp(ip, port) + ' & ' + cvlc(ip, port)
            print('Ejecutando -- ', command)
            os.system(command)
    elif method == 'BYE':
        send_bye(my_socket, option)
        data = receive_message(my_socket)
    else:
        send_message(my_socket, method, option)
        data = receive_message(my_socket)

print("Socket terminado.")
write_log('Finishing client.')
