# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import sys
from functools import partial

import websocket

from .transcription import LINEAR16, Transcriber

logging.basicConfig(level=logging.DEBUG)


def on_message(transcriber, ws, message):
    transcriber.push(message)


def on_error(ws, error):
    logging.debug(error)


def on_close(ws):
    logging.debug('closing')


def main():
    transcriber = Transcriber(language='en-US', codec=LINEAR16, sample_rate=16000)
    transcriber.start()

    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(
        "ws://176.99.159.160:5039/ws",
        on_message=partial(on_message, transcriber),
        on_error=on_error,
        on_close=on_close,
        subprotocols=["stream-channel"],
        header=['Channel-ID: ' + sys.argv[1]],
    )

    try:
        ws.run_forever()
    finally:
        transcriber.stop()
