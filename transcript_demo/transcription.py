# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import os
from queue import Queue
from threading import Thread

import grpc
import pydub
#from google.cloud import speech
#from google.cloud.speech import types, enums
import requests
import yandex.cloud.ai.stt.v3.stt_pb2 as stt_pb2
import yandex.cloud.ai.stt.v3.stt_service_pb2_grpc as stt_service_pb2_grpc
from output import Output

_DONE = object()
folder_id = "b1gjmpe4cbrluouipura"

class Transcriber:

    def __init__(self, language, codec, sample_rate):
        self._specification = stt_service_pb2.RecognitionSpec(
        language_code=os.getenv('language_code', 'ru-RU'),
        profanity_filter=os.getenv('profanity_filter', False),
        model=os.getenv('model', 'general'),
        partial_results=os.getenv('partial_results', True),
        audio_encoding=os.getenv('audio_encoding', 'LINEAR16_PCM'),
        sample_rate_hertz=os.getenv('sample_rate_hertz', 8000)
        )
        self._streaming_config = stt_service_pb2.RecognitionConfig(specification=self._specification, folder_id=folder_id)
        cred = grpc.ssl_channel_credentials()
        channel = grpc.secure_channel(os.getenv('secure_channel', 'stt.api.cloud.yandex.net:443'), cred)
        self._stub = stt_service_pb2_grpc.SttServiceStub(channel)
        #self._client = speech.SpeechClient.from_service_account_file(
        #    filename=_GOOGLE_SPEECH_CREDS_FILENAME,
        #)
        self._queue = Queue()
        self._thread = Thread(target=self._transcribe)
        self._output = Output()

    def start(self):
        self._thread.start()

    def stop(self):
        self._queue.put_nowait(_DONE)
        self._thread.join()

    def push(self, data):
        self._queue.put_nowait(data)

    def _transcribe(self):
        step = 64 * 1024
        transcribe_threshold = step
        buffer = b''
        while True:
            data = self._queue.get()
            try:
                if data == _DONE:
                    return
                buffer += data
                written = len(buffer)
                if written >= transcribe_threshold:
                    transcribed = self._do_transcription(buffer)
                    transcribe_threshold = written + step
                    self._output.write(transcribed)
            finally:
                self._queue.task_done()

    def _do_transcription(self, data):
        logging.debug('Sending %s to the speech API', len(data))
        #request = types.StreamingRecognizeRequest(audio_content=data)
        output = '\n'

        #responses = self._client.streaming_recognize(self._streaming_config, [request])
        responses = self._stub.stt_service_pb2.StreamingRecognitionRequest(audio_content=data)
        for response in responses:
            for result in response.results:
                if not result.is_final:
                    continue
            output += '{}\n'.format(result.alternatives[0].transcript)

        logging.debug('final output: %s', output)
        return output
