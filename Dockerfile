FROM python:3

RUN useradd -ms /bin/bash bindila
WORKDIR /home/bindila

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

ADD bindila .

USER bindila
CMD ["python3", "-m", "bindila"]
