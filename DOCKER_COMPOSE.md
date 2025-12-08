# 🎯 Что такое Docker Compose?

> Docker Compose — это инструмент для определения и запуска многоконтейнерных Docker-приложений. Вместо запуска множества команд docker run, вы описываете всё в одном YAML-файле.

Проблема без Compose:

```shell
# Создать сеть
docker network create app-network

# Запустить БД
docker run -d --name database --network app-network \
  -e POSTGRES_PASSWORD=dbpass -e POSTGRES_DB=appdb postgres:15

# Собрать и запустить backend
cd backend && docker build -t mybackend .
docker run -d --name backend --network app-network mybackend

# Собрать и запустить frontend
cd ../frontend && docker build -t myfrontend .
docker run -d --name frontend --network app-network -p 8080:80 myfrontend
```

С Docker Compose:
```shell
docker-compose up
```

### 📝 Структура docker-compose.yml
Создайте файл docker-compose.yml в корне вашего проекта (app-network/docker-compose.yml):
```yaml
version: '3.8'  # Версия формата Compose

services:  # Определение контейнеров
  database:  # Имя сервиса (= имя контейнера в сети)
    image: postgres:15  # Образ для использования
    container_name: database  # Опционально: явное имя контейнера
    environment:  # Переменные окружения
      POSTGRES_PASSWORD: dbpass
      POSTGRES_DB: appdb
      POSTGRES_USER: postgres
    volumes:  # Постоянное хранилище
      - db_data:/var/lib/postgresql/data
    networks:  # Подключение к сетям
      - app-network
    restart: unless-stopped  # Политика перезапуска
    healthcheck:  # Проверка здоровья
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:  # Сборка из Dockerfile
      context: ./backend  # Путь к папке с Dockerfile
      dockerfile: Dockerfile  # Имя Dockerfile (можно опустить)
    container_name: backend
    depends_on:  # Зависимости запуска
      - database
    environment:
      DATABASE_HOST: database  # Используем имя сервиса
      DATABASE_NAME: appdb
      DATABASE_USER: postgres
      DATABASE_PASSWORD: dbpass
    networks:
      - app-network
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
    container_name: frontend
    depends_on:
      - backend
    ports:  # Проброс портов
      - "8080:80"  # host:container
    networks:
      - app-network
    restart: unless-stopped

networks:  # Определение сетей
  app-network:
    driver: bridge  # Тип сети

volumes:  # Определение named volumes
  db_data:  # Для сохранения данных БД
```

### 🔗 Связывание сервисов
В Docker Compose сервисы автоматически могут обращаться друг к другу по имени сервиса.


Как это работает:
- Автоматический DNS - Compose создает сеть и настраивает DNS
- Имя сервиса = hostname - database, backend, frontend
- depends_on - контролирует порядок запуска (но не ждет готовности!)


Пример связи:
В backend обращаемся к БД:
```python
conn = psycopg2.connect(
    host="database",  # Имя сервиса из docker-compose.yml!
    database="appdb",
    user="postgres",
    password="dbpass"
)
```

В nginx обращаемся к backend:
```shell
location /api/ {
    proxy_pass http://backend:8000/;  # Имя сервиса!
}
```

### 🔐 Переменные окружения и .env файл

Способ 1: Прямо в docker-compose.yml
```shell
services:
  backend:
    environment:
      DATABASE_PASSWORD: dbpass
      API_KEY: secret123
```

Способ 2: Из .env файла (РЕКОМЕНДУЕТСЯ)
Создайте файл .env рядом с docker-compose.yml:
```shell
# .env
POSTGRES_PASSWORD=mysecretpassword
POSTGRES_DB=appdb
POSTGRES_USER=postgres
BACKEND_PORT=8000
FRONTEND_PORT=8080
```


Используйте в docker-compose.yml:
```yaml
version: '3.8'

services:
  database:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}  # Из .env
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
    
  backend:
    build: ./backend
    environment:
      DATABASE_PASSWORD: ${POSTGRES_PASSWORD}
    
  frontend:
    build: ./frontend
    ports:
      - "${FRONTEND_PORT}:80"  # Динамический порт
```

Способ 3: Загрузка всех переменных из файла
```shell
services:
  backend:
    build: ./backend
    env_file:
      - ./backend/.env  # Отдельный файл для backend
```



## 🎬 Полный пример для вашего приложения

```yaml
version: '3.8'

services:
  # База данных PostgreSQL
  database:
    image: postgres:15-alpine
    container_name: app_database
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-dbpass}
      POSTGRES_DB: ${POSTGRES_DB:-appdb}
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Backend на FastAPI
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: app_backend
    depends_on:
      database:
        condition: service_healthy  # Ждем, пока БД будет готова
    environment:
      DATABASE_HOST: database
      DATABASE_NAME: ${POSTGRES_DB:-appdb}
      DATABASE_USER: ${POSTGRES_USER:-postgres}
      DATABASE_PASSWORD: ${POSTGRES_PASSWORD:-dbpass}
    networks:
      - app-network
    restart: unless-stopped
    # Для разработки: автоматическая перезагрузка при изменении кода
    volumes:
      - ./backend:/app
    # Можно раскомментировать для отладки:
    # ports:
    #   - "8000:8000"

  # Frontend на Nginx
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: app_frontend
    depends_on:
      - backend
    ports:
      - "${FRONTEND_PORT:-8080}:80"
    networks:
      - app-network
    restart: unless-stopped

networks:
  app-network:
    driver: bridge
    name: app-network

volumes:
  postgres_data:
    name: app_postgres_data
```

Создайте app-network/.env:
```shell
# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=supersecret123
POSTGRES_DB=appdb

# Ports
FRONTEND_PORT=8080
```

## 🚀 Основные команды Docker Compose

```shell
# Запустить все сервисы (создаст контейнеры, сети, volumes)
docker-compose up

# Запустить в фоне (detached mode)
docker-compose up -d

# Пересобрать образы перед запуском
docker-compose up --build

# Остановить все сервисы (контейнеры остаются)
docker-compose stop

# Запустить остановленные сервисы
docker-compose start

# Перезапустить сервисы
docker-compose restart

# Остановить и удалить контейнеры, сети
docker-compose down

# Остановить и удалить контейнеры, сети, volumes
docker-compose down -v

# Посмотреть логи всех сервисов
docker-compose logs

# Логи конкретного сервиса
docker-compose logs backend

# Логи в реальном времени
docker-compose logs -f

# Посмотреть запущенные сервисы
docker-compose ps

# Выполнить команду в сервисе
docker-compose exec backend bash

# Собрать образы без запуска
docker-compose build

# Пересобрать конкретный сервис
docker-compose build backend

# Проверить конфигурацию
docker-compose config

# Масштабирование сервисов (создать несколько экземпляров)
docker-compose up --scale backend=3
```


### 🎯 Продвинутые возможности

1. Множественные Compose файлы
```shell
# Базовая конфигурация
docker-compose.yml

# Для разработки
docker-compose.override.yml  # Применяется автоматически!

# Для продакшена
docker-compose.prod.yml
```

Запуск с определенным файлом:
```shell
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up
```


2. Healthcheck и зависимости
```yaml
services:
  backend:
    depends_on:
      database:
        condition: service_healthy  # Ждем ready-состояния
      
  database:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 5s
      timeout: 3s
      retries: 5
```


3. Разные типы volumes
```yaml
services:
  app:
    volumes:
      # Named volume (управляется Docker)
      - app_data:/data
      
      # Bind mount (папка хоста)
      - ./local_folder:/container/path
      
      # Анонимный volume
      - /container/path
      
      # Read-only
      - ./config:/etc/config:ro

volumes:
  app_data:  # Named volume нужно объявить
```

4. Переменные и подстановки
```yaml
services:
  app:
    image: nginx:${NGINX_VERSION:-latest}  # Значение по умолчанию
    ports:
      - "${PORT:-8080}:80"
```

5. Расширение конфигураций (Extension Fields)
```yaml
# Общие настройки для переиспользования
x-common-variables: &common
  restart: unless-stopped
  networks:
    - app-network

services:
  backend:
    <<: *common  # Вставка общих настроек
    build: ./backend
    
  frontend:
    <<: *common
    build: ./frontend
```

### 📊 Структура проекта для видео
```shell
app-network/
├── docker-compose.yml       # Главный файл
├── .env                     # Переменные окружения (не коммитим)
├── .env.example             # Шаблон .env для других разработчиков
├── .gitignore
├── backend/
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt     # (если нужно)
└── frontend/
    ├── Dockerfile
    ├── index.html
    └── nginx.conf
```


Пример .env.example:
```shell
# Copy this file to .env and fill with your values
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changeme
POSTGRES_DB=appdb
FRONTEND_PORT=8080
```


