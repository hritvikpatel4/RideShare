FROM python

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /users
COPY . .

EXPOSE 80

RUN pip install -r requirements.txt
CMD ["sh", "-c", "python CC_0125_0172_0242_1557_users.py"]
