# Dockerfile dla aplikacji Python3 z pyftpdlib i requests
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Zainstaluj certyfikaty (opcjonalne) i odśwież pip
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir --upgrade pip

# Zainstaluj dodatkowe biblioteki
RUN pip install --no-cache-dir pyftpdlib requests

# Skopiuj aplikację do obrazu
COPY . /app

# Expose application ports and passive FTP range
EXPOSE 3000 3021 60000-65535

# Uruchom main.py z argumentem config_1.json
CMD ["python", "main.py", "config_1.json"]