FROM ubuntu:focal-20200916

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -y update && \
    apt-get -y install tzdata dbus-x11 libcanberra-gtk-module libcanberra-gtk3-module pulseaudio wget curl gnupg && \
    apt-get clean
