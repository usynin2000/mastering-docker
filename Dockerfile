FROM alpine:3.18

RUN echo "Hello from Docker!" > /hello.txt

CMD ["cat", "/hello.txt"]