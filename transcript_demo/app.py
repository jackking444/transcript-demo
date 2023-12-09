#coding=utf8
import argparse

import fastapi
import grpc
import pydub
import yandex.cloud.ai.stt.v3.stt_pb2 as stt_pb2
import yandex.cloud.ai.stt.v3.stt_service_pb2_grpc as stt_service_pb2_grpc
from fastapi import File, UploadFile

CHUNK_SIZE = 4000
app = fastapi.FastAPI()

@app.post("/upload")
def upload(file: UploadFile = File(...)):
    try:
        contents = file.file.read()
        with open(file.filename, 'wb') as f:
            f.write(contents)
    except Exception:
        return {"message": "There was an error uploading the file"}
    finally:
        file.file.close()

    return {"message": f"Successfully uploaded {file.filename}"}

def gen(audio_file_name):
    with open(audio_file_name, 'rb') as f, open('sound_out.wav', 'wb') as fo:
        fo.write(pydub.AudioSegment(f).export(format = 'wav').read())
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
    with open('sound_out.wav', 'rb') as f:
        data = f.read(CHUNK_SIZE)
        while data != b'':
            yield stt_pb2.StreamingRequest(chunk=stt_pb2.AudioChunk(data=data))
            data = f.read(CHUNK_SIZE)

def run(iam_token, audio_file_name):
    # Установите соединение с сервером.
    cred = grpc.ssl_channel_credentials()
    channel = grpc.secure_channel('stt.api.cloud.yandex.net:443', cred)
    stub = stt_service_pb2_grpc.RecognizerStub(channel)

    # Отправьте данные для распознавания.
    it = stub.RecognizeStreaming(gen(audio_file_name), metadata=(
        ('authorization', f'Bearer {iam_token}'),
    ))

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
    except grpc._channel._Rendezvous as err:
        print(f'Error code {err._state.code}, message: {err._state.details}')
        raise err

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', required=True, help='IAM token')
    parser.add_argument('--path', required=True, help='audio file path')
    args = parser.parse_args()
    run(args.token, args.path)