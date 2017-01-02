#!/bin/bash
# Note that if you are using Mac/Windows then the volume mount of docker may not work.
docker run -ti -v /var/run/docker.sock:/var/run/docker.sock dockerinpractice/image-stepper ubuntu latest
