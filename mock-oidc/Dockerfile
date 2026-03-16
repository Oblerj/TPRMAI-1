FROM python:3.12-alpine

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY main.py .

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:10090/health || exit 1

# Run as non-root user
RUN adduser -D -u 1000 oidc && chown -R oidc:oidc /app
USER oidc

EXPOSE 10090

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10090"]
