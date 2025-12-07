# Gunakan image Python yang ringan
FROM python:3.9-slim

# Set working directory inside the container
WORKDIR /app

# Copy requirements file first to leverage Docker cache
COPY requirements.txt .

# Install dependencies including uvicorn
# Update pip to ensure we can install packages properly
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create a non-root user to run the app (Recommended for security)
RUN useradd -m -u 1000 user
USER user

# Set environment variables
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Expose port 7860 (Standar Hugging Face Spaces)
EXPOSE 7860

# Command to run the application
CMD ["uvicorn", "src.api_service:app", "--host", "0.0.0.0", "--port", "7860"]
