FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y nginx && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN rm /etc/nginx/sites-enabled/default && \
    cp nginx.conf /etc/nginx/sites-available/nextmovie && \
    ln -s /etc/nginx/sites-available/nextmovie /etc/nginx/sites-enabled/ && \
    mkdir -p /etc/nginx/ssl && \
    cp ssl/certificate.crt /etc/nginx/ssl/ && \
    cp ssl/private.key /etc/nginx/ssl/

EXPOSE 80 443

CMD service nginx start && uvicorn app:app --host 0.0.0.0 --port 8000