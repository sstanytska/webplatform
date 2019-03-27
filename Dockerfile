# Pulling default image from DockerHub
FROM python:latest
MAINTAINER Farkhod Sadykov

## Copy everything to image folder root
WORKDIR /app
COPY . /app

## Create kube folder insied root Copy KuberConfig to the docker images
RUN mkdir /root/.kube
COPY config /root/.kube/

## Set credentials for google cluster
ENV GOOGLE_APPLICATION_CREDENTIALS=/root/.kube/


## Install all requirements to the docker image
RUN python -m pip install -r requirements.txt

## Install gcloud in docker container
RUN curl -sSL https://sdk.cloud.google.com | bash

## Expose the port 5000
EXPOSE 5000

#WORKDIR /root/
## To run this docker image need commmand
# CMD ['python', '/app/app.py']
