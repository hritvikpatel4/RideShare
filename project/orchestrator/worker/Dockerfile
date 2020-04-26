FROM python

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /worker
COPY . /worker

EXPOSE 8001

RUN pip install -r requirements.txt
CMD ["sh", "-c", "sleep 10 && python master_slave.py"]