# Use Python 3.9 (or whichever version your project needs)
FROM python:3.9

# Set working directory inside container


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