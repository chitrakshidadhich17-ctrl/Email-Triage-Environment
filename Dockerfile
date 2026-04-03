FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir pydantic openai pyyaml fastapi uvicorn

EXPOSE 7860

ENV PORT=7860

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]