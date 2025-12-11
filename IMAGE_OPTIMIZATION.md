# 🚀 ОПТИМИЗАЦИЯ DOCKER ОБРАЗОВ

### 📌 Зачем оптимизировать образы?

1. **Скорость развертывания** - меньший образ быстрее скачивается и запускается
2. Экономия ресурсов - меньше места на диске, в registry, меньше трафика
3. Безопасность - меньше кода = меньше потенциальных уязвимостей


Пример из реальной жизни:
- Неоптимизированный Node.js образ: 1.2 GB
- Оптимизированный: 150 MB
- Разница: в 8 раз меньше!


## 📁 1. .DOCKERIGNORE - ИСКЛЮЧАЕМ ЛИШНЕЕ
### Что такое .dockerignore?
> Это файл, который указывает Docker, **какие файлы и папки не нужно копировать в build context при сборке образа.**


Когда вы запускаете docker build, Docker сначала копирует весь контекст (обычно текущую директорию) в Docker daemon. Если там есть:
- огромная папка node_modules/ (300+ MB)
- папка .git/ (может быть гигабайты)
- логи, кеши, временные файлы

...всё это передаётся Docker daemon, даже если не используется! Это замедляет сборку.


📝 Что нужно исключать?
Создайте файл .dockerignore в корне проекта:
```
# ===== VCS (системы контроля версий) =====
.git
.gitignore
.gitattributes

# ===== Зависимости (устанавливаются внутри образа) =====
node_modules/
npm-debug.log
venv/
env/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# ===== IDE и редакторы =====
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# ===== Логи и временные файлы =====
*.log
logs/
tmp/
temp/
*.tmp

# ===== Тесты (если не нужны в образе) =====
tests/
test/
*.test.js
*.spec.js
__tests__/
coverage/
.pytest_cache/

# ===== Документация =====
README.md
CHANGELOG.md
docs/
*.md

# ===== CI/CD конфиги =====
.github/
.gitlab-ci.yml
.travis.yml
Jenkinsfile

# ===== Docker файлы =====
Dockerfile*
docker-compose*.yml
.dockerignore

# ===== Build артефакты =====
dist/
build/
target/
*.o
*.so

# ===== Переменные окружения и секреты =====
.env
.env.local
*.pem
*.key
secrets/
```


## ⚡ 2. ПОРЯДОК КОМАНД В DOCKERFILE (КЕШИРОВАНИЕ)

🧩 Как работает кеширование слоёв?
Docker строит образы по слоям. Каждая команда в Dockerfile = новый слой.
Ключевое правило:
> Docker использует кеш для слоя, если:
> 1. Команда не изменилась
> 2. Предыдущие слои не изменились
> 3. Файлы, которые копируются, не изменились


### 🎓 Золотое правило порядка
```Dockerfile
FROM базовый_образ

# 1. Системные зависимости (меняются редко)
RUN apt-get update && apt-get install -y curl

# 2. Зависимости приложения (меняются редко)
COPY requirements.txt .
RUN pip install -r requirements.txt

# 3. Конфигурационные файлы (меняются редко)
COPY config.yaml .

# 4. Исходный код (меняется часто)
COPY src/ ./src/

# 5. CMD/ENTRYPOINT (метаданные, не создают большой слой)
CMD ["python", "app.py"]
```

Принцип: От редко изменяемого к часто изменяемому

🔥 Практический тест для видео
Создайте файл requirements.txt в app-network/backend/:
```txt
fastapi==0.104.1
uvicorn==0.24.0
psycopg2-binary==2.9.9
```

Оптимизированный Dockerfile:
```python
FROM python:3.11-slim

WORKDIR /app

# Копируем только requirements
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY app.py .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Демонстрация для видео:
```shell
# Первая сборка
time docker build -t backend:v1 .
# Займет ~30-60 секунд

# Измените app.py (добавьте комментарий)
echo "# Updated" >> app.py

# Вторая сборка
time docker build -t backend:v2 .
# Займет ~2-3 секунды (зависимости из кеша!)
```


## 🎭 3. MULTI-STAGE BUILDS - МАГИЯ ОПТИМИЗАЦИИ

🤔 В чём проблема?
Для сборки приложения часто нужны инструменты:
- Компиляторы (gcc, g++)
- Build tools (npm, webpack, maven)
- Dev зависимости
Но для запуска они не нужны!
Результат: Образ раздувается инструментами сборки.


### 💡 Решение: Multi-stage Builds
Идея: разделить сборку на несколько этапов (stages):
- Stage 1 (builder) - собираем приложение со всеми инструментами
- Stage 2 (final) - копируем только результат в чистый минимальный образ
📐 Структура Multi-stage Dockerfile
```shell
# ==========================================
# Стадия 1: СБОРКА
# ==========================================
FROM образ_для_сборки AS builder
# ... устанавливаем инструменты
# ... компилируем/собираем
# ... результат в /app/build

# ==========================================
# Стадия 2: PRODUCTION
# ==========================================
FROM минимальный_образ
# Копируем ТОЛЬКО результат из builder
COPY --from=builder /app/build /app
CMD ["./app"]
```

🎯 Пример 1: Go приложение
Без multi-stage:
```Dockerfile
FROM golang:1.21
WORKDIR /app
COPY . .
RUN go build -o myapp
CMD ["./myapp"]
```
Размер: ~900 MB ❌ (включает весь Go toolchain)


С multi-stage:
```Dockerfile
# ==========================================
# Стадия 1: Сборка
# ==========================================
FROM golang:1.21 AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o myapp .

# ==========================================
# Стадия 2: Production
# ==========================================
FROM alpine:3.18

# Добавляем сертификаты для HTTPS
RUN apk --no-cache add ca-certificates

WORKDIR /root/

# Копируем ТОЛЬКО бинарник из builder
COPY --from=builder /app/myapp .

CMD ["./myapp"]
```

Размер: ~15 MB ✅ (в 60 раз меньше!)


#### Пример 2: Python с компилируемыми зависимостями
Оптимизируем ваш Python app:
```Dockerfile
# ==========================================
# Стадия 1: Сборка с компиляцией зависимостей
# ==========================================
FROM python:3.11 AS builder

WORKDIR /app

# Устанавливаем build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements
COPY requirements.txt .

# Устанавливаем зависимости в отдельную папку
RUN pip install --user --no-cache-dir -r requirements.txt

# ==========================================
# Стадия 2: Production (slim)
# ==========================================
FROM python:3.11-slim

WORKDIR /app

# Копируем установленные пакеты из builder
COPY --from=builder /root/.local /root/.local

# Добавляем локальные пакеты в PATH
ENV PATH=/root/.local/bin:$PATH

# Копируем только код приложения
COPY app.py .

# Создаём non-root пользователя для безопасности
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

CMD ["python", "app.py"]
```

Преимущества:
- Финальный образ не содержит gcc, g++ и build tools
- Меньше размер
- Меньше поверхность атаки (безопаснее)


🔍 Продвинутая техника: именованные stages
```Dockerfile
# Stage для зависимостей
FROM python:3.11 AS dependencies
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Stage для тестов
FROM dependencies AS test
COPY tests/ ./tests/
RUN pytest

# Stage для production
FROM python:3.11-slim AS production
COPY --from=dependencies /root/.local /root/.local
COPY app.py .
CMD ["python", "app.py"]
```

Сборка конкретного stage:
```shell
# Сборка и запуск тестов
docker build --target test -t myapp:test .

# Сборка только production
docker build --target production -t myapp:prod .
```


# 🎬 ПРАКТИЧЕСКАЯ ДЕМОНСТРАЦИЯ ДЛЯ ВИДЕО

Сценарий 1: Показать влияние .dockerignore
```shell
# 1. Создайте тестовую папку с "мусором"
mkdir test-dockerignore && cd test-dockerignore
mkdir node_modules .git logs
dd if=/dev/zero of=node_modules/big.bin bs=1M count=100  # 100MB файл

# 2. Простой Dockerfile
cat > Dockerfile << 'EOF'
FROM alpine
COPY . /app
EOF

# 3. Сборка БЕЗ .dockerignore
time docker build -t test:no-ignore .
# Sending build context: 100+ MB

# 4. Создаём .dockerignore
cat > .dockerignore << 'EOF'
node_modules/
.git/
logs/
EOF

# 5. Сборка С .dockerignore
time docker build -t test:with-ignore .
# Sending build context: 1-2 KB (в 100000 раз меньше!)
```

Сценарий 2: Кеширование слоёв
```shell
# Создайте проект
mkdir cache-demo && cd cache-demo

cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn==0.24.0
EOF

cat > app.py << 'EOF'
print("Hello from Docker v1")
EOF

# Плохой Dockerfile
cat > Dockerfile.bad << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
EOF

# Хороший Dockerfile
cat > Dockerfile.good << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
CMD ["python", "app.py"]
EOF

# Тест 1: Плохой вариант
echo "=== Тест BAD Dockerfile ==="
time docker build -f Dockerfile.bad -t bad:v1 .
# Первая сборка: ~30 секунд

# Меняем код
sed -i 's/v1/v2/' app.py

time docker build -f Dockerfile.bad -t bad:v2 .
# Вторая сборка: ~30 секунд (кеш не работает!)

# Тест 2: Хороший вариант
echo "=== Тест GOOD Dockerfile ==="
sed -i 's/v2/v1/' app.py
time docker build -f Dockerfile.good -t good:v1 .
# Первая сборка: ~30 секунд

# Меняем код
sed -i 's/v1/v2/' app.py

time docker build -f Dockerfile.good -t good:v2 .
# Вторая сборка: ~2 секунды (кеш работает!)
```

Сценарий 3: Multi-stage Build
```shell
# Go приложение для демонстрации
mkdir multistage-demo && cd multistage-demo

cat > main.go << 'EOF'
package main
import "fmt"

func main() {
    fmt.Println("Hello from optimized Docker!")
}
EOF

# Без multi-stage
cat > Dockerfile.single << 'EOF'
FROM golang:1.21
WORKDIR /app
COPY main.go .
RUN go build -o app main.go
CMD ["./app"]
EOF

# С multi-stage
cat > Dockerfile.multi << 'EOF'
FROM golang:1.21 AS builder
WORKDIR /app
COPY main.go .
RUN CGO_ENABLED=0 go build -o app main.go

FROM alpine:3.18
COPY --from=builder /app/app /app
CMD ["/app"]
EOF

# Сборка и сравнение
docker build -f Dockerfile.single -t go-single .
docker build -f Dockerfile.multi -t go-multi .

# Сравнение размеров
docker images | grep "go-"
# go-single    ~900 MB
# go-multi     ~15 MB (в 60 раз меньше!)
```

🎓 ЧЕКЛИСТ ОПТИМИЗАЦИИ (для завершения видео)
✅ Базовый уровень:
[ ] Используйте официальные образы
[ ] Выбирайте slim/alpine варианты
[ ] Создайте .dockerignore
[ ] Правильный порядок COPY (зависимости → код)
✅ Средний уровень:
[ ] Объединяйте RUN команды
[ ] Используйте --no-cache-dir для pip/npm
[ ] Очищайте пакетные кеши в том же слое
[ ] Добавьте HEALTHCHECK
✅ Продвинутый уровень:
[ ] Multi-stage builds
[ ] Non-root пользователь (USER)
[ ] Используйте .dockerignore максимально
[ ] ARG для параметризации образов
[ ] Используйте конкретные версии зависимостей


📚 ДОПОЛНИТЕЛЬНЫЕ BEST PRACTICES

1. Очистка в том же RUN слое

❌ Плохо:
```shell
RUN apt-get update
RUN apt-get install -y curl
RUN rm -rf /var/lib/apt/lists/*  # Бесполезно! Кеш уже в предыдущем слое
```

✅ Хорошо:
```shell
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*  # Очистка в том же слое
```

2. Используйте конкретные версии
❌ Плохо:
```shell
FROM python:3
RUN pip install flask
```

✅ Хорошо:
```shell
FROM python:3.11.6-slim
RUN pip install flask==3.0.0
```

3. Избегайте RUN apt-get upgrade
```shell
# ❌ НЕ делайте так:
RUN apt-get upgrade -y

# ✅ Вместо этого обновите базовый образ:
FROM python:3.11.6-slim  # <- более новая версия
```