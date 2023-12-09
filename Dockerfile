# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:2.7 as base
ARG DEBIAN_FRONTEND="noninteractive"
RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
         git mc
# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install --upgrade pip && \ 
python -m pip install -r requirements.txt

WORKDIR /app
RUN git clone https://github.com/yandex-cloud/cloudapi
RUN cd cloudapi && \
ls  && \
pwd && \
mkdir output && \
python -m grpc_tools.protoc -I . -I third_party/googleapis \
  --python_out=output \
  --grpc_python_out=output \
    google/api/http.proto \
    google/api/annotations.proto \
    yandex/cloud/api/operation.proto \
    google/rpc/status.proto \
    yandex/cloud/operation/operation.proto \
    yandex/cloud/ai/stt/v2/stt_service.proto && \
    ls  && \
    pwd && \
    ls  output 

RUN cp -R  /app/cloudapi/output /app/transcript_demo
COPY . /app
RUN python  python-client/setup.py install
RUN git clone https://github.com/asterisk/ari-py
RUN cd ari-py && python setup.py install 





# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
# RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
# USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
# RUN python setup.py install
RUN chmod 777 docker-entrypoint.sh
CMD ["/bin/sh"]
