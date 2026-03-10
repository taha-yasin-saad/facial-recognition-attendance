FROM python:3.11-slim

# install build tools needed for dlib and other packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       cmake \
       libglib2.0-0 \
       libsm6 \
       libxrender1 \
       libxext6 \
       libjpeg-dev \
       libopenblas-dev \
       liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
