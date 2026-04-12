chore: очистка проекта, настройка email, DEBUG=False

- Удалено 58 мусорных файлов из корня (BUG_*.md, test_*.py, *_IMPLEMENTATION.md и т.д.)
- DEBUG по умолчанию False, включается через env-переменную
- ALLOWED_HOSTS читается из env-переменной
- Email настроен на adm1npioner@yandex.com
- Обновлены fallback-значения email в settings.py