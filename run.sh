#!/bin/bash
# Note that if you are using Mac/Windows then the volume mount of docker may not work.
docker run -ti -v $(which docker):/usr/local/bin/docker dockerinpractice/image-stepper ubuntu latest
