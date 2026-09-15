# Logisim для macOS и Windows

**[English](README.md) | Русский**

[![Проверка сборок](https://github.com/Mastn1kth/logisim-macos/actions/workflows/build.yml/badge.svg)](https://github.com/Mastn1kth/logisim-macos/actions/workflows/build.yml)
[![Последний релиз](https://img.shields.io/github/v/release/Mastn1kth/logisim-macos?display_name=tag)](https://github.com/Mastn1kth/logisim-macos/releases/latest)
[![Лицензия GPL-3.0](https://img.shields.io/badge/license-GPL--3.0-blue.svg)](https://github.com/logisim-evolution/logisim-evolution/blob/v5.0.0/LICENSE.md)

Я собрал этот репозиторий для учёбы и лабораторных работ, чтобы Logisim можно
было скачать и запустить без отдельной установки Java.

В основе лежит официальный **Logisim-evolution 5.0.0**, но приложение на macOS
называется короче — **Logisim**. Русский язык уже встроен. Исходный симулятор
создан не мной: моя часть — упаковка, автоматическая проверка и удобные файлы для
скачивания.

## Скачать

Все файлы находятся на странице
**[Releases](https://github.com/Mastn1kth/logisim-macos/releases/latest)**.

| Устройство | Что скачать | Java |
| --- | --- | --- |
| Mac с M1, M2, M3, M4 или M5 | `Logisim-5.0.0-macOS-Apple-Silicon.zip` | Уже внутри |
| Старый Mac с Intel | `Logisim-5.0.0-macOS-Intel.zip` | Уже внутри |
| Обычный Windows Intel/AMD | `logisim-evolution-5.0.0-amd64.msi` | Уже внутри |
| Windows Intel/AMD без установки | `logisim-evolution-5.0.0-windows-amd64.zip` | Уже внутри |
| Windows ARM | `logisim-evolution-5.0.0-aarch64.msi` | Уже внутри |
| Windows ARM без установки | `logisim-evolution-5.0.0-windows-aarch64.zip` | Уже внутри |

Большинству пользователей Windows нужен файл **`amd64.msi`**. Он подходит и
для процессоров Intel, и для AMD.

## Что внутри

- Logisim-evolution 5.0.0;
- встроенная Java — устанавливать её отдельно не нужно;
- русский интерфейс и переключатель языка;
- логические элементы, память, регистры, TTL и временные диаграммы;
- FPGA, VHDL и дополнительные библиотеки Evolution;
- поддержка учебных файлов `.circ`.

Язык меняется через **Logisim → Настройки → Международные → Язык**.

## Установка на macOS

1. Узнай процессор: меню Apple → **Об этом Mac**.
2. Скачай ZIP для Apple Silicon или Intel.
3. Распакуй архив и перенеси `Logisim.app` в **Программы**.
4. При первом запуске нажми по приложению с зажатым `Control`, выбери
   **Открыть** и подтверди запуск.

Сборки локально подписываются и проверяются через `codesign`, но не
нотарифицированы платным сертификатом Apple. Если macOS блокирует программу,
открой **Системные настройки → Конфиденциальность и безопасность → Всё равно
открыть**.

## Установка на Windows

Для обычной установки скачай `amd64.msi`. Если на учебном компьютере нельзя
устанавливать программы, скачай portable ZIP, распакуй его и запусти приложение
из полученной папки.

Windows-файлы не изменяются: это официальные пакеты Logisim-evolution,
проверенные по опубликованным SHA-256.

## Совместимость лабораторных

Evolution открывает большинство схем старого Logisim 2.7.1, но абсолютная
обратная совместимость не гарантируется. Храни исходную лабораторную отдельно и
сохраняй рабочую копию под новым именем. Если преподаватель проверяет работу в
2.7.1, не используй новые компоненты Evolution.

## Проверка сборок

GitHub Actions отдельно собирает, подписывает, распаковывает и запускает
приложение на macOS Intel и Apple Silicon. Дополнительно проверяются JAR, ZIP,
права запуска, архитектура нативных файлов, версия и контрольные суммы загрузок.

```sh
python scripts/build-modern-logisim.py --arch all
python scripts/download-windows-packages.py
```

## О проекте

Это независимый проект упаковки, а не официальный сайт Logisim-evolution. Сам
симулятор разрабатывается командой
[logisim-evolution](https://github.com/logisim-evolution/logisim-evolution) и
распространяется по GPL-3.0.

Упаковку и этот репозиторий поддерживает
[@Mastn1kth](https://github.com/Mastn1kth). Спасибо Carl Burch за оригинальный
Logisim и всем участникам Logisim-evolution.
