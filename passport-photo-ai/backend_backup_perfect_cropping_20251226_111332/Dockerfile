FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libheif-dev \
    libheif-examples \
    wget \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set up the environment for the rembg model
# Create a directory for the model and tell rembg where to find it.
ENV U2NET_HOME=/app/models
RUN mkdir -p ${U2NET_HOME}
RUN wget -q https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx -O ${U2NET_HOME}/u2net.onnx

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --no-binary pyheif -r requirements.txt

# Copy the rest of the application code
COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
