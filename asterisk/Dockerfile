FROM debian:stretch

RUN echo "deb http://archive.debian.org/debian stretch main" > /etc/apt/sources.list
RUN apt-get -y update 
#RUN apt-get -y remove libcurl4 
RUN apt-get upgrade -y 
RUN apt-get install -y  build-essential openssl libxml2-dev libncurses5-dev uuid-dev sqlite3 libsqlite3-dev pkg-config libjansson-dev libssl-dev libedit-dev 
#curl smtp

ENV SRTP_VERSION 1.6.0
RUN cd /usr/local/src && curl -L -o srtp.tar.gz https://github.com/cisco/libsrtp/archive/v${SRTP_VERSION}.tar.gz \
    && tar xzf srtp.tar.gz
RUN cd /usr/local/src/libsrtp* \
    && ./configure CFLAGS=-fPIC \
    && make \
    && make install

ENV ASTERISK_VERSION 16.3.0
RUN cd /usr/local/src && curl -o asterisk.tar.gz http://downloads.asterisk.org/pub/telephony/asterisk/releases/asterisk-${ASTERISK_VERSION}.tar.gz \
    && tar xzf asterisk.tar.gz
RUN cd /usr/local/src/asterisk* \
    && ./configure --with-pjproject-bundled --with-jansson-bundled --with-crypto --with-ssl \
    && make \
    && make install \
    && make config