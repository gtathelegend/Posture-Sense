# Use Python 3.12 slim image for production deployment
FROM python:3.12-slim

# Set working directory inside container
WORKDIR /app


# Install OS dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Run your app (replace with correct file)
EXPOSE 8080

CMD ["python", "app.py"]