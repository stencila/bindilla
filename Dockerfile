FROM python:3

RUN useradd -ms /bin/bash bindila
WORKDIR /home/bindila
USER bindila

ADD setup.py .
RUN pip3 install . --user

ADD bindila bindila

CMD ["python3", "-m", "bindila"]
