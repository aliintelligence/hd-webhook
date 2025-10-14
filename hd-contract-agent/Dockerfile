# Dockerfile for HD Contract Agent
# Optional - use if you want to deploy with Docker instead of Render's native Python

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the agent in loop mode
CMD ["python", "outlook_agent.py", "--loop", "--interval", "300"]
