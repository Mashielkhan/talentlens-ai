FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 OMP_NUM_THREADS=2 TOKENIZERS_PARALLELISM=false
WORKDIR /app
ARG INSTALL_DEV=false
COPY pyproject.toml ./
COPY app ./app
# Install the CPU distribution first; the default Linux PyPI torch wheel can
# otherwise pull GPU runtimes that this application does not use.
RUN --mount=type=cache,target=/root/.cache/pip pip install --timeout=120 'torch>=2.6,<3' --index-url https://download.pytorch.org/whl/cpu
RUN --mount=type=cache,target=/root/.cache/pip pip install --timeout=120 --upgrade 'setuptools>=84.1.0' && pip install --timeout=120 . && python -m spacy download en_core_web_sm
RUN --mount=type=cache,target=/root/.cache/pip if [ "$INSTALL_DEV" = "true" ]; then pip install --timeout=120 '.[dev]'; fi
COPY alembic ./alembic
COPY alembic.ini ./
COPY tests ./tests
COPY scripts ./scripts
RUN useradd --create-home --uid 10001 talentlens && mkdir -p /data/resumes /data/models && chown -R talentlens /data
USER talentlens
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
