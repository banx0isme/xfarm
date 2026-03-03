---
name: web-fullpage-screenshot
description: Take full-page screenshots of web pages using a headless system Chrome (via Chrome DevTools Protocol), including dynamic pages, lazy-loaded content (auto-scroll), and authenticated sessions via cookies. Use when the user asks for a screenshot/скриншот/полный скрин веб-страницы, needs a pixel-accurate capture for review/debugging, or wants to archive a web page’s visual state.
---

# Web Fullpage Screenshot

## Quick start

## Что нужно, чтобы “полноценно” скриншотить сайт

- Доступ к сайту по сети (и чтобы сайт не блокировал headless-режим/ботов).
- Установленный браузер (по умолчанию используется системный Google Chrome).
- Node.js (у тебя уже есть). Скрипт работает без `npm install` и без внешних зависимостей.
- Окружение должно позволять открыть локальный порт `127.0.0.1:<port>` (используется Chrome DevTools Protocol). В некоторых sandbox-окружениях это запрещено — тогда команду нужно запускать “вне sandbox”.

## Сделать полный скриншот страницы

```bash
node /Users/pavel/ai_agent_farm/skills/web-fullpage-screenshot/scripts/screenshot.mjs \
  --url "https://example.com" \
  --out "/tmp/example.png" \
  --fullPage
```

## Для страниц с lazy-load / анимациями (скролл до низа)

```bash
node /Users/pavel/ai_agent_farm/skills/web-fullpage-screenshot/scripts/screenshot.mjs \
  --url "https://example.com" \
  --out "/tmp/example.png" \
  --fullPage \
  --scroll
```

## Авторизация через cookies (если страница “за логином”)

1) Экспортируй cookies в JSON (массив объектов cookies).
2) Запусти:

```bash
node /Users/pavel/ai_agent_farm/skills/web-fullpage-screenshot/scripts/screenshot.mjs \
  --url "https://example.com/private" \
  --cookies "/path/to/cookies.json" \
  --out "/tmp/private.png" \
  --fullPage
```

Подробности и типовые проблемы: `references/troubleshooting.md`.
