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