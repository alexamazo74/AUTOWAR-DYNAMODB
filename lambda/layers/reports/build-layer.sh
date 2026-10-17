#!/bin/bash
# Build Lambda Layer for Reports with Linux-compatible dependencies

# Clean previous build
rm -rf python
mkdir -p python

# Install dependencies using Docker with Amazon Linux 2 image
docker run --rm \
  -v "$PWD":/var/task \
  public.ecr.aws/lambda/python:3.11 \
  pip install -t /var/task/python openpyxl python-docx matplotlib --no-cache-dir

echo "Layer built successfully in python/"
