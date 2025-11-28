### Что такое Dockerfile?

> Dockerfile — это текстовый файл с инструкциями, описывающими как собрать образ Docker.

🧩 Каждая инструкция в Dockerfile создаёт новый слой (layer) в образе.

Формат:
ИНСТРУКЦИЯ аргументы

Процесс сборки:
```shell
docker build -t myapp:1.0 .
```
Docker читает Dockerfile построчно → выполняет инструкции → создаёт образ.


🏗️ Основные инструкции Dockerfile
1. FROM — Базовый образ
Каждый Dockerfile обязан начинаться с FROM.
```Dockerfile
FROM ubuntu:22.04
```
Это означает: "начать с образа Ubuntu 22.04 как основы".

Примеры:
```Dockerfile
FROM python:3.11-slim       # Официальный Python (минималистичный)
FROM node:18-alpine         # Node.js на Alpine Linux (очень маленький)
FROM scratch                # Пустой образ (для статических бинарников)
```

> 💡 Совет: используй официальные образы и выбирай slim/alpine версии для уменьшения размера.

2. WORKDIR — Рабочая директория
Устанавливает текущую директорию внутри контейнера.
```Dockerfile
WORKDIR /app
```
Все последующие команды (RUN, COPY, CMD) будут выполняться относительно /app.

Без WORKDIR:
```Dockerfile
RUN cd /app && do something
COPY . /app
```
С WORKDIR:
```Dockerfile
WORKDIR /app
RUN do something
COPY . .
```
✅ Более читаемо и безопасно!

3. COPY vs ADD — Копирование файлов
COPY — простое копирование
```Dockerfile
COPY source destination
```

Примеры:
```Dockerfile
COPY app.py /app/           # Копирует app.py в /app/
COPY . /app                 # Копирует весь контекст сборки
COPY requirements.txt .     # Копирует в WORKDIR
```

ADD — копирование с дополнительными возможностями
```Dockerfile
ADD source destination
```

Отличия ADD:
1. Может скачивать файлы по URL:
```Dockerfile
ADD https://example.com/file.tar.gz /tmp/
```
2. Автоматически распаковывает tar/gzip архивы:
```Dockerfile
ADD archive.tar.gz /app/    # Автоматически распакует
```
> ⚠️ Best Practice: Используй COPY, если не нужны фичи ADD.


**Почему?**
- COPY более предсказуемый
- ADD может неожиданно распаковать архивы
- Явность лучше неявности


4. RUN — Выполнение команд при сборке
Выполняет команды во время сборки образа и создаёт новый слой.
```Dockerfile
RUN command
```

Примеры:
```Dockerfile
RUN apt-get update && apt-get install -y curl
RUN pip install -r requirements.txt
RUN npm install
RUN echo "Hello" > /tmp/hello.txt
```

**Shell form vs Exec form**

Shell form (запускается через /bin/sh -c):
```Dockerfile
RUN echo "Hello $USER"      # Переменные работают
```

Exec form (прямой вызов):
```Dockerfile
RUN ["apt-get", "install", "-y", "curl"]
```

Объединение команд RUN (важно!)
❌ Плохо — каждая команда = новый слой:
```Dockerfile
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get install -y wget
RUN rm -rf /var/lib/apt/lists/*
```
Результат: 4 слоя, кеш apt остаётся в промежуточных слоях

✅ Хорошо — одна команда = один слой:
```Dockerfile
RUN apt-get update && \
    apt-get install -y curl wget && \
    rm -rf /var/lib/apt/lists/*
```
Результат: 1 слой, очистка работает корректно


5. CMD vs ENTRYPOINT — Что запускается в контейнере
Обе инструкции задают команду, которая выполнится при запуске контейнера.

`CMD` — команда по умолчанию
```Dockerfile
CMD ["python", "app.py"]
```

CMD можно переопределить при запуске:
```shell
docker run myimage          # Запустит python app.py
docker run myimage ls -la   # Запустит ls -la вместо python
```

`ENTRYPOINT` — фиксированная точка входа
```Dockerfile
ENTRYPOINT ["python"]
```

ENTRYPOINT нельзя переопределить просто так:
```shell
docker run myimage app.py       # Запустит: python app.py
docker run myimage test.py      # Запустит: python test.py
```

##### Комбинирование ENTRYPOINT + CMD
Самый мощный паттерн:
```Dockerfile
ENTRYPOINT ["python"]
CMD ["app.py"]
```

Работает так:
- ENTRYPOINT — фиксированная часть команды
- CMD — аргументы по умолчанию, которые можно заменить

```shell
docker run myimage              # python app.py (по умолчанию)
docker run myimage test.py      # python test.py (заменили CMD)
```

##### Форматы записи
Exec form (рекомендуется):
```Dockerfile
CMD ["python", "app.py"]
```

Shell form:
```Dockerfile
CMD python app.py
```

⚠️ Shell form запускает /bin/sh -c, что может вызвать проблемы с сигналами (SIGTERM).

Практический пример
Если создаёшь утилиту-контейнер:
```Dockerfile
FROM alpine:3.18
ENTRYPOINT ["curl"]
CMD ["--help"]
```
Использование
```shell
docker build -t mycurl .                    # Собираем образ с самого начала 
docker run mycurl                           # curl --help
docker run mycurl https://example.com       # curl https://example.com
docker run mycurl -I https://google.com     # curl -I https://google.com
```


6. ENV — Переменные окружения

Устанавливает переменные окружения в образе.
```Dockerfile
ENV NODE_ENV=production
ENV PORT=8080
```

Многострочный синтаксис:
```Dockerfile
ENV NODE_ENV=production \
    PORT=8080 \
    LOG_LEVEL=info
```

Переменные доступны:
- В последующих инструкциях Dockerfile
- В запущенном контейнере

Использование:
```Dockerfile
FROM node:18
ENV APP_HOME=/app
WORKDIR $APP_HOME
COPY . .
CMD ["node", "server.js"]
```


7. ARG — Аргументы сборки
Переменные, доступные только во время сборки.
```Dockerfile
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim
```
Отличия ARG vs ENV:

Параметр	ARG	ENV
Доступен при сборке	✅	✅
Доступен в контейнере	❌	✅
Можно передать при сборке	✅	❌


Передача ARG при сборке:
```shell
docker build --build-arg PYTHON_VERSION=3.10 -t myapp .
```

Практический пример:
```Dockerfile
ARG VERSION=1.0.0
ENV APP_VERSION=${VERSION}

RUN echo "Building version ${VERSION}"
```

```shell
docker build --build-arg VERSION=2.0.0 -t myapp:2.0 .
```

8. EXPOSE — Документирование портов

Указывает, какой порт слушает приложение.
```dockerfile
EXPOSE 8080
```

> ⚠️ Важно: EXPOSE — это только документация!
Он не пробрасывает порт наружу. Для проброса используй -p:

```shell
docker run -p 8080:8080 myapp
```

Документация для других разработчиков
Используется при docker run -P (автоматический проброс всех EXPOSE портов)
```Dockerfile
FROM nginx:alpine
EXPOSE 80 443
```

9. USER — Смена пользователя

По умолчанию контейнеры запускаются от root.
⚠️ Это небезопасно в продакшене!

**Создание и использование non-root пользователя:**
```Dockerfile
FROM python:3.11-slim

# Создаём пользователя
RUN useradd -m -u 1000 appuser

# Устанавливаем права
WORKDIR /app
COPY --chown=appuser:appuser . .

# Переключаемся на appuser
USER appuser

CMD ["python", "app.py"]
```
✅ Теперь приложение не имеет root привилегий.



10. HEALTHCHECK — Проверка здоровья

Позволяет Docker проверять, работает ли приложение.
```Dockerfile
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1
```

Параметры:
- --interval — как часто проверять (по умолчанию 30s)
- --timeout — таймаут проверки (по умолчанию 30s)
- --retries — сколько раз повторить перед пометкой unhealthy (по умолчанию 3)


Пример с Python:
```Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY app.py .

HEALTHCHECK --interval=10s --timeout=3s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["python", "app.py"]
```


11. VOLUME — Точки монтирования
Объявляет, что определённая директория должна быть volume.
```Dockerfile
VOLUME /data
```

Для чего:
Документация (показывает, где ожидаются персистентные данные)
Автоматическое создание анонимного volume


Пример с базой данных:
```Dockerfile
FROM postgres:15
VOLUME /var/lib/postgresql/data
```

> ⚠️ На практике чаще используют именованные volume при запуске:
```shell
docker run -v mydata:/var/lib/postgresql/data postgres:15
```

12. LABEL — Метаданные

Добавляет метаданные к образу.
```Dockerfile
LABEL maintainer="dev@example.com"
LABEL version="1.0"
LABEL description="My awesome application"
```

Многострочный синтаксис:
```Dockerfile
LABEL org.opencontainers.image.authors="dev@example.com" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.description="Production app"
```

Просмотр labels:
```shell
docker inspect myimage | grep -A 10 Labels
```


### 🎯 Multi-stage Builds — Оптимизация размера

Проблема: Для сборки приложения часто нужны инструменты (компиляторы, npm, pip, gcc), которые занимают много места, но в финальном образе они не нужны для запуска приложения.

Решение: Разделить процесс на стадии:
1. Стадия сборки — устанавливаем все инструменты, компилируем, собираем.
2. Финальная стадия — копируем только результат сборки в минимальный образ

Как это работает?
```Dockerfile
# Стадия 1: даём ей имя "builder"
FROM node:18 AS builder
# ... собираем приложение ...

# Стадия 2: новый чистый образ
FROM nginx:alpine
# Копируем только результат из стадии "builder"
COPY --from=builder /app/build /usr/share/nginx/html
```

Ключевые преимущества:
- 📦 Значительно меньший размер образа (иногда в 10-50 раз!)
- 🔒 Безопаснее (нет инструментов сборки в production)
- ⚡ Быстрее разворачивается и скачивается


Пример 1: Go приложение
Без multi-stage (❌):
```Dockerfile
FROM golang:1.21
WORKDIR /app
COPY . .
RUN go build -o myapp
CMD ["./myapp"]
```
Размер: ~800MB (включает весь Go toolchain)


С multi-stage (✅):
```Dockerfile
# Стадия 1: Сборка
FROM golang:1.21 AS builder
WORKDIR /app
COPY . .
RUN go build -o myapp

# Стадия 2: Финальный образ
FROM alpine:3.18
WORKDIR /app
COPY --from=builder /app/myapp .
CMD ["./myapp"]
```

Размер: ~10MB (только бинарник!)


Пример 2: Python с компиляцией зависимостей
```Dockerfile
# Стадия сборки
FROM python:3.11 AS builder
WORKDIR /app
RUN pip install --user --no-cache-dir numpy pandas

# Финальная стадия
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY app.py .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "app.py"]
```


### 📋 .dockerignore — Исключение файлов
Аналог .gitignore для Docker.
Зачем?
Исключить ненужные файлы из build context → ускорить сборку → уменьшить размер.

Пример .dockerignore:

```.dockerignore
# Git
.git
.gitignore

# Dependencies
node_modules
venv
__pycache__
*.pyc

# IDE
.vscode
.idea
*.swp

# Logs
*.log
logs/

# Тесты
tests/
*.test.js

# Документация
README.md
docs/

# CI/CD
.github
.gitlab-ci.yml

# Временные файлы
tmp/
*.tmp
.DS_Store
```


#### ⚡ Кеширование слоёв — Оптимизация сборки

Docker кеширует каждый слой. Если слой не изменился → используется кеш.

❌ Плохой порядок:
```Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .                          # Копируем ВСЁ
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
```
Проблема: любое изменение кода → инвалидирует кеш → переустановка всех зависимостей.

✅ Правильный порядок:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .           # Сначала только зависимости
RUN pip install -r requirements.txt  # Кешируется!
COPY . .                          # Потом код
CMD ["python", "app.py"]
```

Выгода: изменения кода не инвалидируют слой с зависимостями!


🎓 Best Practices — Чек-лист
✅ Используй официальные базовые образы
✅ Выбирай slim/alpine версии
✅ Объединяй команды RUN для уменьшения слоёв
✅ Копируй зависимости перед кодом (кеширование)
✅ Используй .dockerignore
✅ Используй multi-stage builds для production
✅ Запускай от non-root пользователя (USER)
✅ Добавляй HEALTHCHECK для production сервисов
✅ Не храни секреты в образах
✅ Используй COPY вместо ADD (если не нужны фичи ADD)



### Практический пример 1: Flask приложение
Структура проекта:
flask_app/
├── Dockerfile
├── requirements.txt
├── app.py
└── .dockerignore


1. app.py — простое Flask приложение:
```python
from flask import Flask, jsonify
import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "message": "Hello from Flask in Docker!",
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

2. requirements.txt:
Flask==3.0.0
gunicorn==21.2.0


3. Dockerfile с multi-stage build:
```Dockerfile
# ============================================
# Стадия 1: Сборка и установка зависимостей
# ============================================
FROM python:3.11 AS builder

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем только requirements для кеширования
COPY requirements.txt .

# Устанавливаем зависимости в /install директорию
# --prefix=/install указывает куда устанавливать
RUN pip install --no-cache-dir --prefix=/install --no-warn-script-location \
    -r requirements.txt

# ============================================
# Стадия 2: Финальный минимальный образ
# ============================================
FROM python:3.11-slim

# Создаём non-root пользователя для безопасности
RUN useradd -m -u 1000 flaskuser

WORKDIR /app

# Копируем установленные пакеты из стадии builder
COPY --from=builder /install /usr/local

# Копируем код приложения
COPY --chown=flaskuser:flaskuser app.py .

# Переключаемся на non-root пользователя
USER flaskuser

# Документируем порт
EXPOSE 5000

# Healthcheck для проверки работоспособности
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# Запускаем через gunicorn для production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
```

Сборка и запуск:
```shell
# Сборка образа
docker build -t flask-app:multistage .

# Проверка размера
docker images flask-app:multistage

# Запуск контейнера
docker run -d -p 5000:5000 --name my-flask-app flask-app:multistage

# Проверка работы
curl http://localhost:5000
curl http://localhost:5000/health

# Проверка healthcheck
docker ps  # смотрим STATUS колонку, должно быть "healthy"
```


### 🌐 Практический пример 2: Статический сайт с Nginx
Создадим React-приложение (или просто статический HTML), соберём его и развернём на Nginx.
Структура проекта:
static_site/
├── Dockerfile
├── nginx.conf
└── src/
    ├── index.html
    ├── style.css
    └── app.js


1. src/index.html:
```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Docker Multi-stage Demo</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <h1>🐳 Docker Multi-stage Build</h1>
        <p>Этот сайт собран и развёрнут с использованием multi-stage Dockerfile</p>
        <div id="info"></div>
        <button onclick="loadData()">Загрузить данные</button>
    </div>
    <script src="app.js"></script>
</body>
</html>
```

2. src/style.css:
```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
}

.container {
    background: white;
    padding: 3rem;
    border-radius: 10px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    text-align: center;
    max-width: 600px;
}

h1 {
    color: #333;
    margin-bottom: 1rem;
}

button {
    margin-top: 1rem;
    padding: 10px 20px;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    font-size: 1rem;
}

button:hover {
    background: #764ba2;
}

#info {
    margin-top: 1rem;
    padding: 1rem;
    background: #f0f0f0;
    border-radius: 5px;
    display: none;
}
```

3. src/app.js:
```js
function loadData() {
    const info = document.getElementById('info');
    info.style.display = 'block';
    info.innerHTML = `
        <strong>Информация о сборке:</strong><br>
        Время загрузки: ${new Date().toLocaleString('ru-RU')}<br>
        User Agent: ${navigator.userAgent.substring(0, 50)}...
    `;
}
```

4. nginx.conf:
```conf
server {
    listen 80;
    server_name localhost;
    
    root /usr/share/nginx/html;
    index index.html;
    
    # Gzip сжатие
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    # Кеширование статических файлов
    location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # SPA fallback (если используешь React Router)
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Healthcheck endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

5. Dockerfile с multi-stage build:
```Dockerfile
# ============================================
# Стадия 1: Сборка статических файлов
# ============================================
FROM node:18-alpine AS builder

WORKDIR /build

# Если используешь Node.js проект (React, Vue и т.д.)
# COPY package*.json ./
# RUN npm ci --only=production

# Копируем исходники
COPY src/ ./src/

# Для примера просто копируем, но здесь мог быть npm run build
# или любой другой процесс сборки (Webpack, Vite, etc.)
RUN mkdir -p /build/dist && cp -r src/* /build/dist/

# ============================================
# Стадия 2: Production образ с Nginx
# ============================================
FROM nginx:alpine

# Копируем кастомную конфигурацию nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Копируем собранные файлы из стадии builder
COPY --from=builder /build/dist /usr/share/nginx/html

# Добавляем метаданные
LABEL maintainer="dev@example.com"
LABEL description="Static website with Nginx using multi-stage build"

# Документируем порт
EXPOSE 80

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

# Nginx запускается автоматически через базовый образ
# CMD ["nginx", "-g", "daemon off;"]
```

Сборка и запуск:
```shell
# Сборка образа
docker build -t static-site:multistage .

# Проверка размера (должно быть ~25-30MB)
docker images static-site:multistage

# Запуск контейнера
docker run -d -p 8080:80 --name my-static-site static-site:multistage

# Проверка в браузере
# Открой: http://localhost:8080

# Проверка healthcheck
curl http://localhost:8080/health
docker ps  # проверяем STATUS
```