FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy the entire project
COPY . .

# Create a non-privileged user and adjust permissions
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Set environment variable to make sure output is not buffered
ENV PYTHONUNBUFFERED=1

# Run the Flask server using gunicorn for production
# We use run:app to run the complete Flask application factory
CMD ["sh", "-c", "gunicorn -w 4 --timeout 120 -b 0.0.0.0:${PORT:-5000} run:app"]
