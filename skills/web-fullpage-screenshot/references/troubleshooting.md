# Troubleshooting (web-fullpage-screenshot)

## Частые проблемы

### Пустой/неполный скрин

- Добавь `--waitUntil networkidle2` (по умолчанию уже так) или попробуй `--waitUntil domcontentloaded`.
- Для lazy-load контента добавь `--scroll`.
- Если сайт подгружает контент по событию/таймеру, иногда помогает увеличить `--timeoutMs`.

### Сайт показывает “bot detected” / Cloudflare / капчу

- Headless-браузер может блокироваться. Этот скилл не гарантирует обход защит.
- Иногда помогает использовать обычный (non-headless) браузер и экспортировать cookies, затем запускать с `--cookies`.

### Страница “за логином”

- Используй `--cookies /path/to/cookies.json`.
- Формат: JSON-массив cookies в формате Chrome/Puppeteer (например `[{\"name\":..., \"value\":..., \"domain\":..., \"path\":...}]`).
- Если у cookie нет поля `url`, скрипт подставит origin целевой страницы (работает для host-only cookies).

### Не найден Chrome/Chromium

- Установи Google Chrome или передай путь через `--chrome`.
- На macOS типовой путь: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`.

### Ошибка вида “Operation not permitted” / “remote debugging not ready”

- Скрипт использует локальный порт (Chrome DevTools Protocol). Некоторые sandbox-окружения запрещают слушать порты даже на `127.0.0.1`.
- В Codex попробуй выполнить команду вне sandbox (запрос на повышенные права / `require_escalated`).
