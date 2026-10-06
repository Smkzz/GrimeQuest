FROM node:22-bookworm-slim AS frontend-build
WORKDIR /src

# scripts/build.py creates the generated PWA shell and PNG icons.
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pil \
    && rm -rf /var/lib/apt/lists/*

COPY package.json package-lock.json tsconfig.json ./
RUN npm ci --ignore-scripts

COPY client ./client
COPY server/catalog.json ./server/catalog.json
COPY web ./web
COPY scripts/build.py ./scripts/build.py

RUN python3 scripts/build.py \
    && test -s web/app.js \
    && test -s web/manifest.webmanifest \
    && test -s web/sw.js

FROM python:3.13-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000
WORKDIR /app

COPY requirements.lock ./
RUN python -m pip install --no-cache-dir -r requirements.lock \
    && useradd --system --uid 10001 --no-create-home appuser

COPY server ./server
COPY --from=frontend-build /src/web ./web
COPY run.py ./

USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=8s CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','8000')+'/api/health', timeout=2).read()"
CMD ["python", "run.py", "--host", "0.0.0.0"]
