# Use official Python image
FROM python:3.12-slim

# Metadata labels for OCI/Docker registry
LABEL org.opencontainers.image.authors="Reky"
LABEL org.opencontainers.image.title="Mandiri Finance Telegram Bot"
LABEL org.opencontainers.image.description="A Telegram bot that parses Excel bank statements, auto-categorizes expenses, stores them in MySQL, and visualizes spending with charts."


# Set working directory inside the container
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Run the Telegram bot
CMD ["python", "run.py"]
