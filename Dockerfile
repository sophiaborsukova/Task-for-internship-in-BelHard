#Download base image ubuntu 18.04
FROM ubuntu:18.04

#for ubuntu
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get -y update 
RUN apt-get -y install tzdata python3 python3-dev python3-pip python3-tk python3-setuptools locales locales-all net-tools

#for host time zone
ENV TZ=Europe/Minsk
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN dpkg-reconfigure -f noninteractive tzdata

#for python3
RUN pip3 install --upgrade pip
RUN pip3 install decorator flask==1.0.2 flask-httpauth==3.2.4 gevent==1.3.7 requests

#Localization change
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

#cleaning
RUN apt-get clean
RUN apt-get autoclean
RUN apt-get autoremove

#ENTRYPOINT ["python3", "webserver.py"]  

