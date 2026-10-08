FROM node:22-bookworm-slim@sha256:c3de60bf2f9dd0ac6370e6117950ff62d6e339527e7472301c9c78a017978392 AS frontend-build
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
COPY scripts/verify_build.py ./scripts/verify_build.py
COPY tests/client.test.cjs ./tests/client.test.cjs

RUN python3 scripts/build.py \
    && test -s web/app.js \
    && test -s web/manifest.webmanifest \
    && test -s web/sw.js \
    && node --test tests/client.test.cjs \
    && python3 scripts/verify_build.py

FROM python:3.13-slim@sha256:bf44cdfcb76cd3b41e879bc058fc37ec5872002ccfde7fcb765e218cde0cd79c AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000
WORKDIR /app

COPY requirements.lock ./
# The official base bundles pip and build-time utilities; these are not needed to
# serve GrimeQuest. Remove them only AFTER resolving and checking app dependencies.
# The exact removal procedure passed a fail-closed Trivy rootfs audit.
RUN python -m pip install --root-user-action=ignore --no-cache-dir -r requirements.lock \
    && python -m pip check \
    && python -m pip uninstall --yes --root-user-action=ignore msgpack setuptools urllib3 \
    && python -m pip check \
    && rm -rf /usr/local/lib/python3.13/site-packages/pip \
              /usr/local/lib/python3.13/site-packages/pip-*.dist-info \
              /usr/local/bin/pip /usr/local/bin/pip3 /usr/local/bin/pip3.13 \
    && python -c "import fastapi, starlette, anyio, httpx, pydantic, PIL, uvicorn" \
    && useradd --system --uid 10001 --no-create-home appuser

COPY server ./server
COPY --from=frontend-build /src/web ./web
# Import the exact server module after both backend and static app are present.
# This sanity check makes no network or paid vision calls.
RUN python -c "from server.app import app; from server.config import Settings; assert app is not None and not Settings().ready"
COPY run.py ./

USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=8s CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','8000')+'/api/health', timeout=2).read()"
CMD ["python", "run.py", "--host", "0.0.0.0"]
