# Dockerfile for the orchestrator container

FROM python

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /orchestrator
COPY . .

EXPOSE 80

RUN pip install -r requirements.txt
CMD ["sh", "-c", "sleep 15 && python orchestrator.py"]
