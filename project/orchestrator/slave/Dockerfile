FROM python:3.7-slim-stretch

# This keeps Python from buffering stdin/stdout
ENV PYTHONUNBUFFERED 1
# This prevents Python from writing out pyc files
ENV PYTHONDONTWRITEBYTECODE 1

ADD . /slave
WORKDIR /slave

EXPOSE 8001

RUN pip install -r requirements.txt
