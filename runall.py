#!/usr/bin/python3
# -*- coding: utf-8 -*- 

import subprocess
import sys
import argparse
import os
import signal
import platform


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-host', default='0.0.0.0', type=str)
    parser.add_argument('-clhost', default='localhost', type=str)
    parser.add_argument('-port', default=2005, type=int)
    parser.add_argument('-cl', default=5, type=int)
    return parser


def main():
    parser = create_parser()
    namespace = parser.parse_args(sys.argv[1:])

    num_of_cl = namespace.cl
    clhost = namespace.clhost
    host = namespace.host
    port = namespace.port

    server = 'gnome-terminal -- python3 second.py -host %s -port %s' % (host, port)
    subprocess.call(server, shell=True)

    i = 0
    while i < num_of_cl:
        client = 'gnome-terminal -- python3 secondcl.py -nhost %s -port %s' % (clhost, port)
        subprocess.call(client, shell=True)
        i += 1


def on_stop(*args):
    os._exit(0)


if __name__ == '__main__':
    # При нажатии комбинаций Ctrl+Z, Ctrl+C либо закрытии терминала будет вызываться функция on_stop() 
    # (Работает только на linux системах!)
    if platform.system() == 'Linux':
        for sig in (signal.SIGTSTP, signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, on_stop)
    main()