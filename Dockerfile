FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python -m rag.ingestion.build_index
EXPOSE 8000 9000 9100 9200
CMD ["python", "scripts/run_local.py"]
