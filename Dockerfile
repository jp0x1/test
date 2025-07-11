FROM python:3.11-slim

# Install system dependencies including MongoDB
RUN apt-get update && apt-get install -y \
    git \
    supervisor \
    varnish \
    wget \
    gnupg \
    curl \
    net-tools \
    procps \
    lsb-release \
    ca-certificates \
    && wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | gpg --dearmor | tee /usr/share/keyrings/mongodb-server-7.0.gpg > /dev/null \
    && echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/debian $(lsb_release -cs)/mongodb-org/7.0 main" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list \
    && apt-get update \
    && apt-get install -y mongodb-org \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Set environment variables
ENV MONGODB_URI=mongodb://localhost:27017/gitbad \
    Flag=L3AK{testing}

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories and users
RUN mkdir -p /var/log/supervisor /app/uploads /app/logs /data/db /var/log/mongodb \
    && groupadd -r mongodb || true \
    && useradd -r -g mongodb mongodb || true \
    && chown -R mongodb:mongodb /data/db \
    && chown -R mongodb:mongodb /var/log/mongodb \
    && chmod 755 /data/db

# Copy configuration files
COPY docker/supervisor/ /etc/supervisor/
COPY docker/varnish/default.vcl /etc/varnish/default.vcl

# Expose ports
EXPOSE 80

# Start supervisor (which will manage Flask, MongoDB, and Varnish)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
