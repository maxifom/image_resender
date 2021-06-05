FROM python:3.9-alpine
RUN apk --update add gcc linux-headers musl-dev
WORKDIR /usr/src/app
ADD requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
ADD . .

RUN python3 setup.py develop
ENTRYPOINT app
