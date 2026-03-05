FROM node:22-alpine AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend ./
RUN npm run build

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FRONTEND_STATIC_DIR=/app/frontend-static

WORKDIR /app

RUN pip install --no-cache-dir uv

RUN uv pip install --system --no-cache-dir "fastapi>=0.118.0" "uvicorn[standard]>=0.37.0"

COPY backend /app/backend
COPY --from=frontend-builder /frontend/out /app/frontend-static

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--app-dir", "/app/backend", "--host", "0.0.0.0", "--port", "8000"]
