FROM python:3.7-alpine

RUN adduser -D slip_app

WORKDIR /home/slip_app

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn

COPY flask_app flask_app
COPY db db
COPY slip slip
COPY migrations migrations
COPY slip_app.py config.py boot.sh ./
RUN chmod +x boot.sh
RUN dos2unix boot.sh

ENV FLASK_APP slip_app.py

RUN chown -R slip_app:slip_app ./
USER slip_app

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
