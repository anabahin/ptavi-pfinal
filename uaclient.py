#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
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
      
if __name__ == '__main__':
  
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
  
  with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
    my_socket.connect(proxy_address)
    if method == 'REGISTER':
      pass
    elif method == 'INVITE':
      pass
    elif method == 'BYE':
      pass
    else:
      pass
    
  print('Socket terminado')
