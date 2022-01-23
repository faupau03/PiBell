# use buster as picamera is not available in bullseye
FROM arm32v7/python:3-buster 

WORKDIR /usr/src/app

COPY . .

CMD ["/usr/bin/uv4l -f -k --sched-fifo --mem-lock --driver dummy --enable-server --server-option=--enable-webrtc-audio=yes --server-option=--enable-webrtc-video=no --server-option=--webrtc-vad --server-option=--use-ssl=yes --server-option=--ssl-private-key-file=/usr/src/app/key.pem --server-option=--ssl-certificate-file=/usr/src/app/cert.pem" ]