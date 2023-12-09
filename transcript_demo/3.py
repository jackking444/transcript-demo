#!/usr/bin/python3

"""Example demonstrating ARI channel origination. This will dial an
endpoint when a Stasis call arrives, and connect the call.

"""

#
# Copyright (c) 2013, Digium, Inc.
# Copyright (c) 2018, Matthias Urlichs
#
import asyncari
import anyio
import logging
from asyncari.state import ToplevelChannelState, HangupBridgeState, DTMFHandler, as_task
from asyncari.model import ChannelExit
from pprint import pprint

import os
ast_host = os.getenv("AST_HOST", 'localhost')
ast_port = int(os.getenv("AST_ARI_PORT", 8088))
ast_url = os.getenv("AST_URL", 'http://%s:%d/'%(ast_host,ast_port))
ast_username = os.getenv("AST_USER", 'jack')
ast_password = os.getenv("AST_PASS", '12345')
ast_app = os.getenv("AST_APP", 'hello')
ast_outgoing = os.getenv("AST_OUTGOING", 'SIP/1001')
ext_chan_media = ''

# This demonstrates incoming DTMF recognition on both legs of a call

class CallState(ToplevelChannelState, DTMFHandler):
    async def on_dtmf(self,evt):
        print("*DTMF*EXT*",evt.digit)

class CallerState(ToplevelChannelState, DTMFHandler):
    @as_task
    async def on_start(self):
        print("on_start in CallerState")
        print(self.client)
        async with HangupBridgeState.new(self.client) as br:
            await br.add(self.channel)
            await br.add(ext_chan_media)
            print(br)
            await br.dial(endpoint=ast_outgoing, State=CallState)
            await self.channel.wait_bridged()
            await self.channel.wait_not_bridged()
    async def on_dtmf(self,evt):
        print("*DTMF*INT*",evt.digit)

async def on_start(client):
    """Callback for StasisStart events.

    When an incoming channel starts, put it in the holding bridge and
    originate a channel to connect to it. When that channel answers, create a
    bridge and put both of them into it.

    :param incoming:
    :param event:
    """

    # Answer and put in the holding bridge
    async with client.on_channel_event('StasisStart') as listener:
        async for objs, event in listener:
            print("print event:")
            print(event)
            if not event['args']:
               print("noop for external media")
               global ext_chan_media
               ext_chan_media = objs['channel']
               print(objs['channel'])
               continue
            if event['args'][0] == 'dialed':
                continue
            print("start_____") 
            print(objs)
            incoming = objs['channel']
            print(incoming)
            cs = CallerState(incoming)
            await cs.start_task()

async def main():
    async with asyncari.connect(ast_url, ast_app, ast_username,ast_password) as client:
        client.taskgroup.start_soon(on_start, client)
        async for m in client:
            #print("** EVENT **", m)
            pprint(("** EVENT **", m, vars(m)))

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    try:
        anyio.run(main)
    except KeyboardInterrupt:
        pass

