#!/bin/bash
# Note that if you are using Mac/Windows then the volume mount of docker may not work.
docker run -ti -v $(which docker):/usr/local/bin/docker docker-in-practice/image_stepper
