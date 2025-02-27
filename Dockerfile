FROM python:3.10-slim

WORKDIR /flask-app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .

WORKDIR /flask-app

RUN flask db init

RUN flask db migrate

RUN flask db upgrade

WORKDIR /flask-app

CMD ["python", "run.py"]