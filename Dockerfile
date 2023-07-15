FROM python:3.11 as base

RUN apt update && apt-get -y install cmake


WORKDIR /app
COPY requirements.txt /app

RUN pip3 install -r requirements.txt --no-cache-dir

COPY . /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

