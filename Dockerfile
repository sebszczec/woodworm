FROM python:3.11-slim

WORKDIR /app

# Clone the repository
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 https://github.com/sebszczec/woodworm.git .

# Install Python dependencies
RUN pip install --no-cache-dir pyftpdlib>=1.7.0 requests>=2.28.0

# Default config file
ENV CONFIG_FILE=config.json

# Expose ports
# 3000 - TCP connections
EXPOSE 3000/tcp
# 3021 - FTP connection
EXPOSE 3021/tcp
# 60000-65535 - Passive FTP ports
EXPOSE 60000-65535/tcp

# Run main.py with config file argument
CMD ["sh", "-c", "python main.py ${CONFIG_FILE}"]
