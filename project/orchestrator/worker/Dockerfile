# Dockerfile for the worker container

FROM python

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /worker
COPY . .

EXPOSE 8001

RUN pip install -r requirements.txt
CMD ["sh", "-c", "python worker.py"]
