#!/bin/bash

# Install system packages required for rembg and OpenCV
yum update -y
yum install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    glib2-devel \
    libSM-devel \
    libXext-devel \
    libXrender-devel

echo "System packages installed for rembg support"