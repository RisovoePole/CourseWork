FROM python:3.11-slim

WORKDIR /app

# системные зависимости (часто нужны для psycopg2, numpy и т.д.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# зависимости Python
COPY requirements.txt .

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

# код проекта
COPY . .

CMD ["python", "-u", "-m", "unittest", "discover", "-s", "tests", "-p", "test*.py"]