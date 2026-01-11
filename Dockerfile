FROM python:3.11-slim


# Installer pandoc
RUN apt-get update \
    && apt-get install -y --no-install-recommends pandoc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 61337

CMD ["python", "init_db.py"]
CMD ["python", "import_Adrela.py"]
CMD ["python", "app.py"]
