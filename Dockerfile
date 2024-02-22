# Используйте базовый образ Python
FROM python:3.11

# Установите зависимости
COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-u", "app.py"]
