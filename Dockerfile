FROM ubuntu
RUN apt-get update -y && apt-get install -y docker
ADD image_stepper /usr/local/bin/image_stepper
ENTRYPOINT ["/usr/local/bin/image_stepper"]
