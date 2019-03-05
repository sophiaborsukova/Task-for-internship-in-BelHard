import socket 
import threading 
import multiprocessing
import logging
from logging.handlers import RotatingFileHandler
from logging import StreamHandler
import argparse
import sys
import os
import signal
import signal
import platform
import base64
import json
import subprocess
from logging.config import dictConfig
from datetime import datetime
from functools import wraps
from datetime import datetime

from flask import Flask, redirect, jsonify, abort, request, make_response, __version__ as flask_version
from flask_httpauth import HTTPBasicAuth
from gevent import __version__ as wsgi_version
from gevent.pywsgi import WSGIServer 

app = Flask(__name__)
auth = HTTPBasicAuth()


#задаю максимальный размер передаваемых данных и размер одного файла лога
max_content_length = 1024*3


#задаю параметры логов
logging.basicConfig(filename='logging.log', filemode = 'w', level=logging.INFO)
logger = logging.getLogger('my_logger')

formatter = logging.Formatter(fmt = '%(levelname)-8s| %(message)s')

handler = RotatingFileHandler('logging.log', maxBytes=max_content_length, backupCount=5)
handler.setFormatter(formatter)

stream_handler = StreamHandler()
stream_handler.setFormatter(formatter)

logger.addHandler(handler)
logger.addHandler(stream_handler)


#переопределение ошибок
@app.errorhandler(400)
def incorrect_url(error):
    return make_response(jsonify({'error': 'The requested URL was incorrect.'}), 400)

@app.errorhandler(401)
def lack_valid(error):
    return make_response(jsonify({'error': 'The request has not been applied because it lacks valid authentication credentials for the target resource.'}), 401)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'The requested URL was not found on the server.'}), 404)

@app.errorhandler(405)
def method_not_allowed(error):
    return make_response(jsonify({'error': 'The method is not allowed for the requested URL.'}), 405)

@app.errorhandler(406)
def method_not_acceptable(error):
    return make_response(jsonify({'error': 'The method is not acceptable for the requested URL.'}), 406)

@app.errorhandler(415)
def unsupported_media_type(error):
    return make_response(jsonify({'error': 'Your request have unsupported media type .'}), 415)

@app.errorhandler(500)
def internal_server_error(error):
    print(error)
    return make_response(jsonify({'error': 'The server encountered an internal error and was unable to complete your request.'}), 500)


#авторизация
@auth.get_password
def get_password(username):
    if username == 'serv':
        return '4_task'

#взяла у Влада
def limit_content_length():
    ''' Декоратор для ограничения размера передаваемых клиентом данных. '''
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if request.content_length > max_content_length:                
                return make_response(jsonify({'error': 'Maximum data transfer size exceeded, allowed only until {: .2f} kB.'.format(max_content_length/1024)}), 413)
            elif request.content_length == 0:
                return make_response(jsonify({'error': 'The request body contains no data.'}), 400)
            elif request.json == None:
                return make_response(jsonify({'error': 'The request body contains an unsupported data type. Only json is supported'}), 415)
            return f(*args, **kwargs)
        return wrapper
    return decorator



@app.route('/')
@auth.login_required
def hello():
    '''при запуске через браузер или с помощи утилиты curl для начала требует авторизации, а затем показывает некоторое сообщение'''
    return make_response(jsonify({'text': 'Hello, I am server. I was created for my internship. Now you only can post me messages with the help of special file named wclient.py'}))


@app.route('/accept', methods=['POST'])
@auth.login_required
@limit_content_length()
def accept():
    '''Метод, который принимает данные от клиентов и отдает им ответ'''
    data = request.json
    mess = data.get('message')
    mess = ans_to_cl(request.remote_addr, 'Получено сообщение: '+ mess)
    logger.info(mess)
    mess = ans_to_cl(request.remote_addr, 'Отправлено сообщение: good')
    logger.info(mess)
    return make_response(jsonify({'answer': 'good'}))
    
def ans_serv(mess):
    '''Определенный формат логов'''
    return datetime.now().strftime('[%Y-%m-%d %H:%M:%S]')+' '+ mess

def ans_to_cl(ip, mess):
    '''Определенный формат логов'''
    return ip+' - - '+ datetime.now().strftime('[%Y-%m-%d %H:%M:%S]')+' '+ mess


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

def run(host, port, wsgi = False, https_mode = False):
    
    if port == 0: # Если был введён порт 0, то автовыбор любого доступного порта
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind((host, 0))
            port = sock.getsockname()[1]
            sock.close()
        except socket.gaierror:
            sock.close()
            return
        except OSError:
            sock.close()
            return

    mess = ans_serv('установлен максимальный размер принимаемых данных: {:.2f} Кб'.format(max_content_length/1024))
    logger.info(mess)

    if wsgi:
        global http_server
        if https_mode: #WSGIServer https
            http_server = WSGIServer((host, port), app, keyfile='key.pem', certfile='cert.pem',log=logger, error_log=logger)
            logger.info(ans_serv('WSGI сервер запущен на https://' + host + ':' + str(port)))
        else: #WSGIServer http
            http_server = WSGIServer((host, port), app, log=logger, error_log= logger)
            logger.info(ans_serv('WSGI сервер запущен на http://' + host + ':' + str(port)))
        http_server.serve_forever()
    else:
        if https_mode: #Flask https
            app.run(host=host, port=port, ssl_context=('cert.pem', 'key.pem'), threaded=True, debug=False)
            logger.info(ans_serv('Flask запущен на https://' + host + ':' + str(port)))
        else: #Flask http
            app.run(host=host, port=port, threaded=True, debug=False)
            logger.info(ans_serv('Flask запущен на http://' + host + ':' + str(port)))

def main():
    host = '127.0.0.1'
    port = 5000 

    if len(sys.argv) > 1:
        if sys.argv[1] == '-s': # запуск в режиме https
            if len(sys.argv) > 2:
                if sys.argv[2] == '-d': # запуск тестового Flask сервера
                    if len(sys.argv) > 3:
                        if sys.argv[3].find('localaddr') != -1 and sys.argv[3].find(':') != -1: # localaddr:port
                            host = get_address_on_local_network()
                            port = int(sys.argv[3][sys.argv[3].find(':') + 1:])
                            run(host, port, https_mode=True)
                        elif sys.argv[3].count('.') == 3 and sys.argv[3].count(':') == 1: # host:port                        
                            host = sys.argv[3][:sys.argv[3].find(':')]
                            port = int(sys.argv[3][sys.argv[3].find(':') + 1:])
                            run(host, port, https_mode=True)                
                    else:
                        run(host, port, https_mode=True)

                elif sys.argv[2].count('.') == 3 and sys.argv[2].count(':') == 1: # запуск WSGI сервера на host:port              
                    host = sys.argv[2][:sys.argv[2].find(':')]
                    port = int(sys.argv[2][sys.argv[2].find(':') + 1:])
                    run(host, port, wsgi=True, https_mode=True)               
            else: 
                host = get_address_on_local_network()
                run(host, port, wsgi=True, https_mode=True)

        elif sys.argv[1] == '-d': # запуск тестового Flask сервера
            if len(sys.argv) > 2:
                if sys.argv[2].find('localaddr') != -1 and sys.argv[2].find(':') != -1: # localaddr:port
                    host = get_address_on_local_network()
                    port = int(sys.argv[2][sys.argv[2].find(':') + 1:])
                    run(host, port)
                elif sys.argv[2].count('.') == 3 and sys.argv[2].count(':') == 1: # host:port
                    host = sys.argv[2][:sys.argv[2].find(':')]
                    port = int(sys.argv[2][sys.argv[2].find(':') + 1:])
                    run(host, port)                
            else:
                run(host, port)

        elif sys.argv[1].count('.') == 3 and sys.argv[1].count(':') == 1: # запуск WSGI сервера на host:port
            host = sys.argv[1][:sys.argv[1].find(':')]
            port = int(sys.argv[1][sys.argv[1].find(':') + 1:])
            run(host, port, wsgi=True)
    else: # запуск WSGI сервера с автоопределением адреса машины в локальной сети и портом 5000
        host = get_address_on_local_network()
        run(host, port, wsgi=True)
    run(host, port)

def on_stop(*args):
    logger.info(ans_serv('сервер остановлен'))
    sys.exit(0)

if __name__ == '__main__':
    # При нажатии комбинаций Ctrl+Z, Ctrl+C либо закрытии терминала будет вызываться функция on_stop() 
     # (Работает только на linux системах!)
    if platform.system() == 'Linux':
        for sig in (signal.SIGTSTP, signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, on_stop)
    main()