FROM python:3.11-alpine

WORKDIR /usr/src/app
RUN python3.11 -m venv venv
ENV PATH="/venv/bin:$PATH"
COPY ./src/bot ./src/bot
COPY requirements.txt requirements.txt
RUN python3.11 -m pip install -r requirements.txt
COPY run.py ./src

ENTRYPOINT python3.11 src/run.py 6287138389:AAEghG8Q3qPMbhzEVFs4lwVUhykLSDF_YSg
