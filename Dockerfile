FROM python:3.12-alpine

WORKDIR /backend

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY backend/app/ ./app/
COPY backend/alembic/ ./alembic/
COPY backend/alembic.ini ./

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
