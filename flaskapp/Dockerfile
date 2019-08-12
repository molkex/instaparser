FROM python:3.7-alpine
ENV APP /app
RUN mkdir $APP
WORKDIR $APP
COPY requirements.txt .
RUN apk --update add --virtual build-dependencies libffi-dev openssl-dev python-dev py-pip build-base \
  && pip install --upgrade pip \
  && pip install -r requirements.txt \
  && apk del build-dependencies


