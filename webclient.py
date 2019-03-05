import time
import sys
import os
import subprocess
import curses
import requests
import base64
import threading
import argparse
import socket
import signal
import platform

#Задаем глобальную переменную для событий
events = []

class MyThread(threading.Thread):
    '''Предназначен для инициализации потока и описывает его деятельность
    1. num_of_thread - номер потока
    2. num_of_i - номер итерации
    3. host - адрес
    4. port - порт
    5. https - протокол да\нет'''
    def __init__(self, num_of_thread, num_of_i, host, port, https = False):
        threading.Thread.__init__(self)
        self.num_of_thread=num_of_thread
        self.num_of_i =num_of_i 
        self.host = host
        self.port = port
        self.https = https

    def run(self):
        '''Метод, определяющий деятельность потока'''

        if self.port == 0: # Если был введён порт 0, то автовыбор любого доступного порта
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind((self.host, 0))
                self.port = sock.getsockname()[1]
                sock.close()
            except socket.gaierror:
                sock.close()
                return
            except OSError:
                sock.close()
                return

        #для заглушки поставлю логин и пароль к серверу
        login = 'serv'
        password = '4_task'

        protocol = 'http'
        if self.https:
            protocol = 'https'

        #базовая авторизация
        auth = base64.b64encode((login + ':' + password).encode())
        headers = {'Authorization' : 'Basic ' + auth.decode()}

        addr = self.host + ':' + str(self.port)

        for i in range(self.num_of_i):
            events[self.num_of_thread].wait()
            events[self.num_of_thread].clear()
            mystr = 'Thread %s, iteration %s' % (self.num_of_thread, int(i*i+1))
            print(mystr)
            mess = {'message': mystr}

            response = requests.post(protocol + '://' + addr + '/accept', headers = headers,
                                     json = mess)

            data = response.json()
            ans = data.get('answer')
            print(ans)

            if self.num_of_thread+1 < len(events):
                events[self.num_of_thread+1].set()
            else:
                events[0].set()

def main():
    host = '127.0.0.1'
    port = '5000'
    
    num_of_thread = 5
    num_of_i = 10
    https = False

    if len(sys.argv) > 1:
        if sys.argv[1] == '-s': # запуск в режиме https
            if len(sys.argv) > 2:
                    if sys.argv[2].find('localaddr') != -1 and sys.argv[2].find(':') != -1: # localaddr:port
                            host = get_address_on_local_network()
                            port = int(sys.argv[2][sys.argv[2].find(':') + 1:])
                            https = True  
                    elif sys.argv[2].count('.') == 3 and sys.argv[2].count(':') == 1: # host:port                        
                            host = sys.argv[2][:sys.argv[2].find(':')]
                            port = int(sys.argv[2][sys.argv[2].find(':') + 1:])  
                            https = True  
            else:
                https = True    
        elif sys.argv[1].count('.') == 3 and sys.argv[1].count(':') == 1: # запуск на host:port
            host = sys.argv[1][:sys.argv[1].find(':')]
            port = int(sys.argv[1][sys.argv[1].find(':') + 1:])
        elif sys.argv[1].find('localaddr') != -1 and sys.argv[2].find(':') != -1: # localaddr:port
                host = get_address_on_local_network()
                port = int(sys.argv[2][sys.argv[2].find(':') + 1:])
    else: # запуск с автоопределением адреса машины в локальной сети и портом 5000
        host = get_address_on_local_network()

    for i in range(num_of_thread):
        events.append(threading.Event())

    threads = []
    for j in range(num_of_thread):
        t = MyThread(j, num_of_i, host, port, https)
        threads.append(t)
        t.start()
    
    #Устанавливаю начальное событие
    events[0].set()

    for j in range(num_of_thread):
        threads[j].join()

def get_address_on_local_network():
    ''' Определение адреса машины в локальной сети с помощью утилиты 'ifconfig' из пакета net-tools.
    1. возвращает строку с адресом или 127.0.0.1, если локальный адрес начинается не с 192.Х.Х.Х или 172.Х.Х.Х
    
    Проверено в Ubuntu 16.04 и 18.04. '''
    
    command_line = 'ifconfig'
    proc = subprocess.Popen(command_line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    out = out.decode()
    if out.find('not found') != -1:
        print("\n[E] 'ifconfig' не найден.")
        sys.exit(0)
    if out.find('inet 127.0.0.1') != -1:
        template = 'inet '
    elif out.find('inet addr:127.0.0.1') != -1:
        template = 'inet addr:'
    i = 0
    host_192xxx = None
    host_172xxx = None
    while host_192xxx == None or host_172xxx == None: 
        out = out[out.find(template) + len(template):]
        host = out[:out.find(' ')]
        out = out[out.find(' '):]
        if host.find('192.168') != -1:
            host_192xxx = host
        elif host.find('172.') != -1:
            host_172xxx = host
        i += 1
        if i >= 10:
            break
    if host_192xxx:
        return host_192xxx
    elif host_172xxx:
        return host_172xxx
    else:
        print("\n[E] Неподдерживаемый формат локального адреса, требуется корректировка исходного кода.\n")
        return '127.0.0.1'

def on_stop(*args):
    os._exit(0)

if __name__ == "__main__":
         # При нажатии комбинаций Ctrl+Z, Ctrl+C либо закрытии терминала будет вызываться функция on_stop() 
     # (Работает только на linux системах!)
    if platform.system() == 'Linux':
        for sig in (signal.SIGTSTP, signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, on_stop)
    main()