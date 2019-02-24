#!/usr/bin/python3
# -*- coding: utf-8 -*- 

import socket 
import threading 
import multiprocessing
import logging
import argparse
import sys
import os
import signal
import platform


class ClientThread(threading.Thread): 
    ''' Предназначен для открытия нового потока для клиента и описывает его деятельность.
    1. ip- адрес клиента.
    2. port- порт.
    3. conn- объект сокета '''
    def __init__(self,ip,port,conn): 
        threading.Thread.__init__(self) 
        self.ip = ip 
        self.port = port 
        self.conn = conn
        print('New server socket thread started for ' + ip + ': ' + str(port))
 

    def run(self): 
        ''' Принимает информацию от клиента. Отправляет сообщение "все в порядке". 
        выводит в терминал  и пишет в лог информацию. '''
        while True : 
            data = self.conn.recv(1024).decode('utf-8') 
            d = {'ip': self.ip, 'port': self.port}            
            if data:
                mystr = "recieved: %s" % (data)
                logging.info(mystr, extra = d)
            else:
                break
            self.conn.send('ok'.encode('utf-8'))
            mystr = "send: ok"
            logging.info(mystr, extra = d)


def create_parser():
    ''' Для приема аргументов командной строки. Если их нет, значения стоят по умолчанию. '''
    parser = argparse.ArgumentParser()
    parser.add_argument('-host', default='0.0.0.0', type=str)
    parser.add_argument('-port', default=2005, type=int) 
    return parser


def main():
    # Принимаем аргументы командной строки
    parser = create_parser()
    namespace = parser.parse_args(sys.argv[1:])

    # Задаем хост и порт сервера
    TCP_IP = namespace.host
    TCP_PORT = namespace.port
    
    # Создаем сокет, представляющий собой указатель на объект соединения.
    # Этому сокету мы передаем два аргумента: первый аргумент говорит о том,
    # что это интернет-сокет, второй – что мы используем TCP-протокол.
    tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    tcpServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    tcpServer.bind((TCP_IP, TCP_PORT)) 

    threads = [] 

    # Для подсчета количества доступных ядер
    cpu_count = multiprocessing.cpu_count()

    with open('logging.log', 'w'):
        pass
 
    while True: 
        print('Multithreaded Python server : Waiting for connections from TCP clients...') 

        logging.basicConfig(level=logging.INFO,
                            format='%(levelname)s\t| %(asctime)s --%(ip)s:%(port)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            handlers=[logging.StreamHandler(),
                                logging.FileHandler('logging.log')])
        
        tcpServer.listen(cpu_count) 
        (conn, (ip, port)) = tcpServer.accept() 
        newthread = ClientThread(ip, port, conn) 
        newthread.daemon = True
        newthread.start() 
        threads.append(newthread) 


def on_stop(*args):
    os._exit(0)


if __name__ == '__main__':
     # При нажатии комбинаций Ctrl+Z, Ctrl+C либо закрытии терминала будет вызываться функция on_stop() 
     # (Работает только на linux системах!)
    if platform.system() == 'Linux':
        for sig in (signal.SIGTSTP, signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, on_stop)
    main()