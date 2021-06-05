FROM python:3.9-alpine
WORKDIR /usr/src/app
ADD requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
ADD . .
