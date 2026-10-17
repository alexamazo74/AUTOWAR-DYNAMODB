#!/bin/bash
# Build script for reports Lambda layer

# Create python directory structure
mkdir -p python

# Install dependencies
pip install -r requirements.txt -t python/

# Clean up unnecessary files
find python -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find python -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find python -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true

echo "Reports layer built successfully"
