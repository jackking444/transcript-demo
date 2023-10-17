# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import sys
import uuid
from contextlib import contextmanager
from functools import partial

import ari

from . import APPLICATION, ARI_PASSWORD, ARI_URL, ARI_USERNAME

# from ari.exceptions import ARINotFound


BRIDGE_ID = str(uuid.uuid4())

logging.basicConfig(level=logging.DEBUG)


@contextmanager
def application_bridge(client):
    logging.debug('Creating our bridge')
    bridge = client.bridges.createWithId(
        bridgeId=BRIDGE_ID,
        name=BRIDGE_ID,
        type='mixing',
    )
    try:
        yield bridge
    finally:
        try:
            logging.debug('Destroying our bridge')
            client.bridges.destroy(bridgeId=BRIDGE_ID)
        # except ARINotFound:
        except Exception:             
            pass


def on_stasis_start(objects, event, bridge):
    logging.debug('%s', event)
    objects['channel'].answer()
    channel_id = event['channel']['id']
    bridge.addChannel(channel=channel_id)


def main():
    logging.debug('Starting %s...', sys.argv[0])
    client = ari.connect(
        base_url=ARI_URL,
        username=ARI_USERNAME,
        password=ARI_PASSWORD,
    )

    with application_bridge(client) as bridge:
        client.on_channel_event('StasisStart', partial(on_stasis_start, bridge=bridge))
        client.run(apps=[APPLICATION])
