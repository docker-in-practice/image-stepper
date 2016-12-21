#!/bin/bash
x=1
for id in $(docker history -q "myimage:latest" | grep -vw missing | tac)
do
    docker tag "${id}" "myimage:latest_step_${x}"
    ((x++))
done
