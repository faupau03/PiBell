# use buster as picamera is not available in bullseye
FROM arm32v7/python:3-buster 

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./server.py" ]