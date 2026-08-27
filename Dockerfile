# Use lightweight Python 3.12 image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install dependencies first for Docker caching
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy the rest of the application
COPY . .

# Expose the Waitress port
EXPOSE 5000

# Set environment variables for Docker
ENV HOST=0.0.0.0
ENV PORT=5000

# Run the Waitress WSGI server
CMD ["python", "web_server.py"]
