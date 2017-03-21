
FROM debian

LABEL Description="mysql testing lab" version="0.12"

ARG version=5-5

ENV DEBIAN_FRONTEND noninteractive


RUN mkdir /data
RUN apt-get update && apt-get install -y mysql-client-${version} mysql-server-${version} sysstat tmux python3


