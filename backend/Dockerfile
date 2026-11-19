# InChi Pilot Gateway — backend images (ARCHITECTURE.md §1, §8).
#
# One build context, two targets, both started by the root docker-compose.yml:
#   django    Django + DRF application layer under gunicorn (port 8000)
#   matching  FastAPI AI matching engine (backend/ai_matching/) under uvicorn (port 8001)
#
# The engine runs as its own Compose service. That runtime arrangement is
# reversible and still pending confirmation (D-15 / ARCHITECTURE.md §6.3).
# No embedding library or model is installed: D-11 is still TBD.

ARG PYTHON_IMAGE=python:3.12.16-slim-bookworm

# ---------------------------------------------------------------- base
FROM ${PYTHON_IMAGE} AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN groupadd --system --gid 1001 inchi \
    && useradd --system --uid 1001 --gid inchi --home-dir /app --shell /usr/sbin/nologin inchi

WORKDIR /app

# ---------------------------------------------------------------- matching engine
FROM base AS matching

COPY ai_matching/requirements.txt /tmp/ai_matching-requirements.txt
RUN pip install -r /tmp/ai_matching-requirements.txt

COPY --chown=inchi:inchi ai_matching/ /app/ai_matching/

USER inchi
EXPOSE 8001

HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=5 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8001/health', timeout=4).status == 200 else 1)"]

CMD ["uvicorn", "ai_matching.main:app", "--host", "0.0.0.0", "--port", "8001", "--no-server-header"]

# ---------------------------------------------------------------- django
FROM base AS django

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY --chown=inchi:inchi . /app/
# /app itself must be writable by the runtime user: gunicorn (>=24) creates its
# control socket directory there.
RUN chmod 0755 /app/docker-entrypoint.sh \
    && mkdir -p /app/staticfiles \
    && chown inchi:inchi /app /app/staticfiles

USER inchi
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=5 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/', timeout=4).status == 200 else 1)"]

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["sh", "-c", "exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-3} --timeout ${GUNICORN_TIMEOUT:-60} --access-logfile - --error-logfile -"]
