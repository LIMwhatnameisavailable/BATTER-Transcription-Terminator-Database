FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY requirements-v03.txt ./requirements-v03.txt
RUN pip install --no-cache-dir -r requirements-v03.txt

# The API imports the backend package only.  Canonical release data stay on
# the host/release boundary and are not copied into the runtime image.
COPY backend ./backend

RUN useradd --create-home --uid 10001 bted \
    && chown -R bted:bted /app
USER bted

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
