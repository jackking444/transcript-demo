#!/usr/bin/python3
# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import socket
import logging
import requests

#from . import ARI_URL, ARI_USERNAME, ARI_PASSWORD, APPLICATION
from transcription import Transcriber, MULAW
ARI_URL = 'http://192.168.0.110:8088'
ARI_USERNAME = ''
ARI_PASSWORD = ''
APPLICATION = 'hello'
#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig()

LISTEN_ADDRESS = '127.0.0.1'
LISTEN_PORT = 12222


def serve(transcriber):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((LISTEN_ADDRESS, LISTEN_PORT))
    while True:
        data, _ = sock.recvfrom(4096)
        payload = data[12:]
        transcriber.push(payload)


def create_external_media_channel():
    url = '/'.join([ARI_URL, 'ari', 'channels', 'externalMedia'])
    print("url:"+url)
    response = requests.post(
        url,
        auth=(ARI_USERNAME, ARI_PASSWORD),
        json={
            'app': APPLICATION,
            'external_host': '{}:{}'.format('127.0.0.1', LISTEN_PORT),
            'format': 'ulaw'
        }
    )
    #print("req"+requests.post)
    print(response.json())
    return response.json()['id']


def destroy_external_media_channel(channel_id):
    url = '/'.join([ARI_URL, 'ari', 'channels', channel_id])
    requests.delete(url, auth=(ARI_USERNAME, ARI_PASSWORD))


def main():
    print("start")
    transcriber = Transcriber(language='en-US', codec=MULAW, sample_rate=8000)
    transcriber.start()

    print("transcrib start")
    external_media_channel_id = create_external_media_channel()

    try:
         serve(transcriber)
         print("try")
    except KeyboardInterrupt:
        pass
    finally:
        destroy_external_media_channel(external_media_channel_id)
        transcriber.stop()

if __name__ == "__main__":
    main()
