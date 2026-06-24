FROM python:3.10-slim

# Create a non-root user (Required by Hugging Face Spaces)
RUN useradd -m -u 1000 user

# Set working directory
WORKDIR /app

# Copy requirements file
COPY --chown=user backend/requirements.txt ./backend/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r backend/requirements.txt

# Copy the rest of the application
COPY --chown=user . /app

# Switch to the non-root user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Hugging Face routes traffic to port 7860 by default
EXPOSE 7860

# Change to backend directory and start the Gunicorn server
WORKDIR /app/backend
CMD ["gunicorn", "-k", "eventlet", "-w", "1", "-b", "0.0.0.0:7860", "app:app"]
