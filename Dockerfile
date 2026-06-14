FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the entire project
COPY . /app/

# Environment variables
ENV PYTHONUNBUFFERED=1

# Expose the dashboard port
EXPOSE 8000

# Start the dashboard server
CMD ["python", "mvp/dashboard_server.py"]
