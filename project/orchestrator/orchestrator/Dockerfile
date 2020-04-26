FROM python

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /orchestrator
COPY . /orchestrator

EXPOSE 8000

RUN pip install -r requirements.txt
CMD ["sh", "-c", "sleep 15 && python orchestrator.py"]