FROM python:3.6

ADD web.py /server/
ADD tcp_server.py /server/
ADD settings.py /server/
ADD models.py /server/
ADD requirements.txt /server/
ADD web_handlers /server/web_handlers

WORKDIR /server/

ENV PYTHONPATH "${PYTONPATH}:/server"

RUN pip install -r requirements.txt