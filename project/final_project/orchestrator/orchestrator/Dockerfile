FROM python

# This keeps Python from buffering stdin/stdout
ENV PYTHONUNBUFFERED 1
# This prevents Python from writing out pyc files
ENV PYTHONDONTWRITEBYTECODE 1

ADD . /orchestrator
WORKDIR /orchestrator

EXPOSE 8000

RUN pip install -r requirements.txt
