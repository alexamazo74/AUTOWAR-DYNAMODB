#!/bin/bash
# Build Lambda Layer for Reports with Linux-compatible dependencies.
#
# Instala TODAS las dependencias declaradas en requirements.txt (openpyxl,
# python-docx, matplotlib y Pillow) usando la imagen oficial de AWS Lambda para
# Python 3.11, de modo que los binarios nativos (Pillow, numpy, etc.) sean
# compatibles con manylinux2014_x86_64 / py3.11, el runtime de Lambda.
#
# Requiere Docker. La salida queda en python/ (que es lo que CDK empaqueta como
# layer). Los assets de marca en python/autowar_assets/ se preservan.
set -euo pipefail

cd "$(dirname "$0")"

# Preservar los assets de marca antes de limpiar python/.
ASSETS_SRC="python/autowar_assets"
ASSETS_BAK=""
if [ -d "$ASSETS_SRC" ]; then
  ASSETS_BAK="$(mktemp -d)"
  cp -R "$ASSETS_SRC/." "$ASSETS_BAK/"
fi

# Clean previous build
rm -rf python
mkdir -p python

# Install dependencies using the official AWS Lambda Python 3.11 image so native
# wheels match the Lambda runtime (manylinux2014_x86_64 / py3.11).
docker run --rm \
  --entrypoint /bin/sh \
  -v "$PWD":/var/task \
  public.ecr.aws/lambda/python:3.11 \
  -c "pip install -r /var/task/requirements.txt -t /var/task/python --no-cache-dir"

# Restaurar los assets de marca dentro del layer reconstruido.
if [ -n "$ASSETS_BAK" ]; then
  mkdir -p "$ASSETS_SRC"
  cp -R "$ASSETS_BAK/." "$ASSETS_SRC/"
  rm -rf "$ASSETS_BAK"
fi

echo "Layer built successfully in python/"
