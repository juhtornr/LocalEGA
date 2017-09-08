#!/bin/bash
cd docker/images
make
cd ..
docker-compose up -d .

