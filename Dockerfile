FROM python:3.7

RUN useradd -ms /bin/bash bindilla
WORKDIR /home/bindilla
USER bindilla

ADD setup.py .
RUN pip3 install . --user

ADD bindilla bindilla

EXPOSE 8888
CMD ["python3", "-m", "bindilla"]
