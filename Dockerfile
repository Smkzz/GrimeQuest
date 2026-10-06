# Optional recipe, not built/scanned in this internal release. Pin a reviewed base
# digest and run a current vulnerability scan before external deployment.
FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements.lock ./
RUN python -m pip install --no-cache-dir -r requirements.lock \
    && useradd --system --uid 10001 --no-create-home appuser
COPY server ./server
COPY web ./web
COPY run.py ./
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2).read()"
CMD ["python", "run.py", "--host", "0.0.0.0", "--port", "8000"]
