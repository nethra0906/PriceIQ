# Base image — Python 3.10 slim (lightweight)
FROM python:3.10-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements first (for caching — speeds up rebuilds)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project into container
COPY . .

# Run the full pipeline first, then launch dashboard
# We use a shell script to run multiple commands
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Expose Streamlit's default port
EXPOSE 8501

# Run entrypoint script
CMD ["./entrypoint.sh"]