FROM python:3
WORKDIR /usr/src/app
COPY . /usr/src/app
RUN pip3 install -r requirements.txt
ENTRYPOINT ["python3", "main.py"]