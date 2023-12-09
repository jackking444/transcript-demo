# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
from queue import Queue
from threading import Thread

import grpc
import yandex.cloud.ai.stt.v3.stt_pb2 as stt_pb2
import yandex.cloud.ai.stt.v3.stt_service_pb2_grpc as stt_service_pb2_grpc
from google.cloud import speech
from google.cloud.speech_v1 import types
from output import Output

#from google.cloud.speech import  enums
IAM_token = 'IAM_token'
cred = grpc.ssl_channel_credentials()
channel = grpc.secure_channel('stt.api.cloud.yandex.net:443', cred)
stub = stt_service_pb2_grpc.RecognizerStub(channel)
LINEAR16 = types.RecognitionConfig.AudioEncoding.LINEAR16
MULAW = types.RecognitionConfig.AudioEncoding.MULAW

_GOOGLE_SPEECH_CREDS_FILENAME = '/root/google_speech_creds.json'
_DONE = object()


class Transcriber:

    def __init__(self, language, codec, sample_rate):
        self._streaming_config = types.StreamingRecognitionConfig(
            config=types.RecognitionConfig(
                encoding=codec,
                sample_rate_hertz=sample_rate,
                language_code=language,
            ),
        )
        #self._client = speech.SpeechClient.from_service_account_file(
            #filename=_GOOGLE_SPEECH_CREDS_FILENAME,
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
        stt_pb2.StreamingRequest(chunk=stt_pb2.AudioChunk(data=data))
        it = stub.RecognizeStreaming(gen(data), metadata=(('authorization', f'Bearer {IAM_token}'),))
        # Обработайте ответы сервера и выведите результат в консоль.
        try:
            for r in it:
                event_type, alternatives = r.WhichOneof('Event'), None
                if event_type == 'partial' and len(r.partial.alternatives) > 0:
                    alternatives = [a.text for a in r.partial.alternatives]
                if event_type == 'final':
                    alternatives = [a.text for a in r.final.alternatives]
                if event_type == 'final_refinement':
                    alternatives = [a.text for a in r.final_refinement.normalized_text.alternatives]
                print(f'type={event_type}, alternatives={alternatives}')
                output += '{}\n'.format(alternatives)
        except grpc._channel._Rendezvous as err:
            print(f'Error code {err._state.code}, message: {err._state.details}')
            raise err
        logging.debug('final output: %s', output)
        return output
def gen(data):
    # Задайте настройки распознавания.
    recognize_options = stt_pb2.StreamingOptions(
        recognition_model=stt_pb2.RecognitionModelOptions(
            audio_format=stt_pb2.AudioFormatOptions(
                raw_audio=stt_pb2.RawAudio(
                    audio_encoding=stt_pb2.RawAudio.LINEAR16_PCM,
                    sample_rate_hertz=48000,
                    audio_channel_count=1
                )
            ),
            text_normalization=stt_pb2.TextNormalizationOptions(
                text_normalization=stt_pb2.TextNormalizationOptions.TEXT_NORMALIZATION_ENABLED,
                profanity_filter=False,
                literature_text=False
            ),
            language_restriction=stt_pb2.LanguageRestrictionOptions(
                restriction_type=stt_pb2.LanguageRestrictionOptions.WHITELIST,
                language_code=['en-US']
            ),
            audio_processing_type=stt_pb2.RecognitionModelOptions.REAL_TIME
        )
    )
    # Отправьте сообщение с настройками распознавания.
    yield stt_pb2.StreamingRequest(session_options=recognize_options)
    # Прочитайте аудиофайл и отправьте его содержимое порциями.
    yield stt_pb2.StreamingRequest(chunk=stt_pb2.AudioChunk(data=data))
