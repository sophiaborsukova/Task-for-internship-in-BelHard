#!/usr/bin/python3
# -*- coding: utf-8 -*-

import threading
import sys
import argparse
import socket
import os
import signal
import platform

#Задаем глобальную переменную для событий
events = []


class MyThread(threading.Thread):
    ''' Предназначен для инициализации потока и описывает его деятельность
    1. num_of_thread - номер потока
    2. num_of_i - номер итерации
    3. opened_file - открытый файл для записи '''
    def __init__(self, num_of_thread, num_of_i, socket):
        threading.Thread.__init__(self)
        self.num_of_thread=num_of_thread
        self.num_of_i =num_of_i 
        self.socket = socket


    def run(self):
        ''' Метод, определяющий деятельность потока (выводит в терминал и записывет в файл
        некую информацию, включая в себя номер потока и номер итерации). '''
        for i in range(self.num_of_i):
            events[self.num_of_thread].wait()
            events[self.num_of_thread].clear()
            message = 'Thread %s, iteration %s' % (self.num_of_thread, int(i*i+1))
            print(message)
            self.socket.send(message.encode('utf-8')) 
            data = self.socket.recv(1024).decode('utf-8') 

            if data != 'ok':
                break

            if self.num_of_thread + 1 < len(events):
                events[self.num_of_thread + 1].set()
            else:
                events[0].set()
        

def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-nt', default=5, type=int)
    parser.add_argument('-ni', default=10, type=int)
    parser.add_argument('-nhost', default='localhost', type=str)
    parser.add_argument('-port', default=2007, type=int) 
    return parser


def main():
    parser = create_parser()
    namespace = parser.parse_args(sys.argv[1:])

    num_of_thread = namespace.nt
    num_of_i = namespace.ni
    host = namespace.nhost
    port = namespace.port

    tcpClient = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    tcpClient.connect((host, port))

    # Для каждого потока создаем события
    i=0
    while i < num_of_thread:
        events.append(threading.Event())
        i+=1

    threads = []
    for j in range(num_of_thread):
        t = MyThread(j, num_of_i, tcpClient)
        threads.append(t)
        t.start()
    
    # Устанавливаю начальное событие
    events[0].set()

    for j in range(num_of_thread):
        threads[j].join()
    tcpClient.close()


def on_stop(*args):
    os._exit(0)


if __name__ == '__main__':
    # При нажатии комбинаций Ctrl+Z, Ctrl+C либо закрытии терминала будет вызываться функция on_stop() 
    # (Работает только на linux системах!)
    if platform.system() == 'Linux':
        for sig in (signal.SIGTSTP, signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, on_stop)
    main()
    print('exit to exit')
    ex = input()
    if ex == 'exit':
        pass