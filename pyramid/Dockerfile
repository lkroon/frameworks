FROM python:3.12-slim

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY wsgi.py .

EXPOSE 6543
CMD ["waitress-serve", "--listen=0.0.0.0:6543", "wsgi:application"]
