# Инструкция для коммита

## Готовые файлы для коммита

Все изменения готовы к коммиту в Git.

## Команды для коммита

```bash
# Добавить все файлы
git add .

# Коммит с готовым сообщением
git commit -F COMMIT_MESSAGE.txt

# Или коммит с кратким сообщением
git commit -m "feat: complete database schema according to technical requirements"
```

## Что будет закоммичено

### Основные файлы проекта
- `manage.py` - Django management
- `requirements.txt` - зависимости
- `.env` - переменные окружения (добавить в .gitignore!)
- `db.sqlite3` - база данных SQLite (добавить в .gitignore!)

### Приложения
- `users/` - пользователи, роли, сессии
- `organizations/` - организации и города
- `services/` - услуги и элементы
- `bookings/` - бронирования
- `pioneer_backend/` - настройки проекта
- `api/` - API приложение

### Документация
- `README.md` - основная документация
- `API_DOCUMENTATION.md` - документация API
- `DATABASE_SCHEMA.md` - схема базы данных
- `TZ_CHECKLIST.md` - чек-лист выполнения ТЗ
- `CHANGELOG.md` - история изменений
- `SUMMARY.md` - сводка работ
- `COMMIT_MESSAGE.txt` - готовое сообщение для коммита

## ⚠️ Важно: Создать .gitignore

Перед коммитом создай файл `.gitignore`:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Django
*.log
db.sqlite3
db.sqlite3-journal
media/
staticfiles/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

## Команды после создания .gitignore

```bash
# Создать .gitignore
# (скопируй содержимое выше в файл .gitignore)

# Удалить из индекса файлы, которые не должны коммититься
git rm --cached .env
git rm --cached db.sqlite3
git rm -r --cached .vscode/

# Добавить все файлы
git add .

# Коммит
git commit -F COMMIT_MESSAGE.txt
```

## Проверка перед коммитом

```bash
# Проверить что будет закоммичено
git status

# Проверить изменения
git diff --cached

# Проверить что проект работает
python manage.py check
```

## После коммита

```bash
# Посмотреть историю
git log --oneline

# Посмотреть статистику коммита
git show --stat
```

## Пуш в удаленный репозиторий

```bash
# Добавить удаленный репозиторий (если еще не добавлен)
git remote add origin <URL>

# Запушить изменения
git push -u origin main
```
