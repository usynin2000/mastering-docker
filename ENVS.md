# Переменные окружения и конфигурация

> Переменные окружения (Environment Variables) — это пары "ключ=значение", которые позволяют настраивать поведение приложения без изменения кода.


### 🔧 Способы передачи переменных окружения

1. Флаг -e или --env при запуске контейнера
Самый простой способ — передать переменную прямо в команде:

Пример с несколькими переменными:
```shell
docker run -d \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=secret123 \
  -e POSTGRES_DB=mydb \
  --name database \
  postgres:15
```

Проверка переменных внутри контейнера:
```shell
docker exec database env | grep POSTGRES
```

Вывод:
```shell
POSTGRES_USER=admin
POSTGRES_PASSWORD=secret123
POSTGRES_DB=mydb
```


Использование в приложении:
```python
# app.py
import psycopg2
import os

conn = psycopg2.connect(
    host=os.getenv('DATABASE_HOST', 'localhost'),
    database=os.getenv('POSTGRES_DB'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD')
)
```

2. Файл с переменными --env-file
Когда переменных много — удобнее хранить их в файле.
Создайте файл .env:


Когда переменных много — удобнее хранить их в файле.
Создайте файл .env:
```txt
# .env
POSTGRES_USER=admin
POSTGRES_PASSWORD=secret123
POSTGRES_DB=mydb
DATABASE_HOST=postgres
DATABASE_PORT=5432
LOG_LEVEL=debug
```

Запуск с --env-file:
```shell
docker run -d --env-file .env --name database postgres:15
```

✅ Преимущества:
- Удобно управлять конфигурацией
- Можно иметь разные файлы для разных окружений (.env.dev, .env.prod)
- Не захламляет команду запуска


⚠️ Важно:
```shell
# .gitignore
.env
.env.local
.env.*.local
```

Всегда добавляйте .env в .gitignore, чтобы секреты не попали в Git!
Создайте .env.example для других разработчиков:
```
# .env.example
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changeme
POSTGRES_DB=appdb
DATABASE_HOST=localhost
DATABASE_PORT=5432
LOG_LEVEL=info
```


3. Переменные в Dockerfile с помощью ENV
Устанавливают переменные внутри образа во время сборки.
```Dockerfile
FROM python:3.11-slim

# Переменные по умолчанию
ENV APP_HOME=/app \
    PYTHONUNBUFFERED=1 \
    LOG_LEVEL=info

WORKDIR $APP_HOME
COPY . .

CMD ["python", "app.py"]
```

Переопределение при запуске:
```shell
docker run -e LOG_LEVEL=debug myapp
```

Переменная LOG_LEVEL теперь будет debug, а не info.


4. Переменные в docker-compose.yml
Способ A: Прямо в файле
```yaml
version: '3.8'

services:
  backend:
    image: mybackend
    environment:
      DATABASE_HOST: postgres
      DATABASE_PORT: 5432
      LOG_LEVEL: info
```

Способ B: Из файла .env (рекомендуется!)
```yaml
version: '3.8'

services:
  database:
    image: postgres:15
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB:-defaultdb}  # Значение по умолчанию
  
  backend:
    build: ./backend
    env_file:
      - .env  # Загрузит все переменные из файла
    environment:
      DATABASE_HOST: database  # Можно комбинировать
```

Файл .env рядом с docker-compose.yml:
```
POSTGRES_USER=admin
POSTGRES_PASSWORD=supersecret
POSTGRES_DB=production_db
```

Docker Compose автоматически подставит переменные из .env.


### 🔐 Безопасность: Проблема с переменными окружения

⚠️ Переменные окружения НЕ безопасны для секретов!
Почему?
1. Видны в docker inspect:
```shell
docker inspect mycontainer | grep -A 10 Env
```
Покажет все переменные, включая пароли!

2. Логи могут показать переменные:
print(os.environ)  # Все переменные в логах!

3. Попадают в /proc/*/environ:
Любой процесс с правами может прочитать переменные другого процесса.

4. Сохраняются в образе (если используется ENV):
```shell
FROM alpine
ENV SECRET_PASSWORD=supersecret  # ❌ Останется в образе навсегда!
```

Даже если удалить образ — слой с секретом останется в истории!



## 🔒 Docker Secrets — правильный способ для продакшена

> Docker Secrets — это механизм безопасного хранения и передачи чувствительных данных в Docker Swarm и Kubernetes.

Ключевая идея:
- Секреты хранятся зашифрованными на диске
- Передаются контейнеру в памяти через tmpfs
- Доступны как файлы в /run/secrets/
- НЕ видны в логах, образах или docker inspect


#### Docker Secrets в Docker Swarm
⚠️ Важно: Docker Secrets работает только в Swarm mode.

Инициализация Swarm:
```shell
docker swarm init
```

Создание секрета:
```shell
# Из файла
echo "mysecretpassword123" | docker secret create db_password -

# Или из файла:
echo "supersecret" > db_password.txt
docker secret create db_password db_password.txt
rm db_password.txt  # Удаляем файл!
```

Просмотр секретов:
```shell
docker secret ls
```

ID                          NAME            CREATED          UPDATED
xk3f8j2h9d1s                db_password     10 seconds ago   10 seconds ago

❗ Невозможно прочитать содержимое секрета:
```shell
docker secret inspect db_password
```

Покажет только метаданные, но НЕ сам секрет!


### Использование секретов в docker-compose (Swarm mode)
```yaml
version: '3.8'

services:
  database:
    image: postgres:15
    secrets:
      - db_password  # Подключаем секрет
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password  # Postgres читает из файла

secrets:
  db_password:
    external: true  # Секрет уже создан через docker secret create
```


Деплой в Swarm:
```shell
docker stack deploy -c docker-compose.yml myapp
```

Как это работает:
1. Docker монтирует секрет как файл: /run/secrets/db_password
2. Postgres читает пароль из этого файла
3. Файл хранится только в памяти (tmpfs), не на диске!


Чтение секретов в приложении
```python
# app.py
import os

def get_secret(secret_name):
    """Читает секрет из Docker Secrets или из переменной окружения"""
    secret_path = f'/run/secrets/{secret_name}'
    
    # Если файл существует — читаем из секрета
    if os.path.exists(secret_path):
        with open(secret_path, 'r') as f:
            return f.read().strip()
    
    # Иначе берем из переменной окружения (для dev)
    return os.getenv(secret_name.upper())

DATABASE_PASSWORD = get_secret('db_password')
API_KEY = get_secret('api_key')
```


### Локальная разработка БЕЗ Swarm
Проблема: Docker Secrets требует Swarm, но для локальной разработки это избыточно.
Решение: Используйте bind mount для имитации секретов:
```yaml
version: '3.8'

services:
  app:
    image: myapp
    volumes:
      - ./secrets/db_password:/run/secrets/db_password:ro  # read-only
    environment:
      DATABASE_PASSWORD_FILE: /run/secrets/db_password
```

Создайте локальные секреты:
```shell
mkdir -p secrets
echo "devpassword" > secrets/db_password
chmod 600 secrets/db_password

# .gitignore
secrets/
```


### 📊 Лучшие практики (Best Practices)
✅ DO (Делай так):

1. Используй .env файлы для локальной 
```
   # .env для dev, .env.prod для production
```
2. Добавляй .env в .gitignore
```shell
   .env
   .env.local
   secrets/
```

3. Создавай .env.example для команды
```shell
   DATABASE_HOST=localhost
   DATABASE_PASSWORD=changeme
```

4. Используй Docker Secrets в production
```shell
   docker secret create db_password -
```

5. Валидируй обязательные переменные
```shell
   if not os.getenv('DATABASE_PASSWORD'):
       raise ValueError("DATABASE_PASSWORD is required!")
```

6. Используй значения по умолчанию
```shell
   LOG_LEVEL = os.getenv('LOG_LEVEL', 'info')
```

7. Логируй конфигурацию (БЕЗ секретов!)
```shell
   logger.info(f"Database host: {DATABASE_HOST}")
   # НЕ логируй пароли!
```

❌ DON'T (Не делай так):

1. НЕ храни секреты в Dockerfile
```shell
   ENV SECRET_KEY=hardcoded  # ❌ Останется в образе!
```

2. НЕ коммить .env в Git

3. НЕ логируй переменные окружения

4. НЕ используй переменные для секретов в production

5. НЕ храни секреты в volumes


# 🎓 Итоговая шпаргалка
```shell
# === ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ===

# 1. Передать при запуске
docker run -e KEY=value myapp

# 2. Из файла
docker run --env-file .env myapp

# 3. В Dockerfile
ENV LOG_LEVEL=info

# 4. В docker-compose.yml
environment:
  KEY: value

# 5. Из .env в Compose
environment:
  KEY: ${KEY}


# === DOCKER SECRETS ===

# Инициализация Swarm
docker swarm init

# Создание секрета
echo "secret" | docker secret create my_secret -

# Просмотр секретов
docker secret ls

# Удаление секрета
docker secret rm my_secret

# Использование в stack
docker stack deploy -c docker-compose.yml myapp


# === ПРОВЕРКА ===

# Посмотреть переменные в контейнере
docker exec mycontainer env

# Посмотреть секреты
docker exec mycontainer ls -la /run/secrets/
docker exec mycontainer cat /run/secrets/my_secret
```
