# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django web application for managing **rail wear inspections and maintenance** on a São Paulo metro line. All domain terminology and UI text is in **Portuguese (pt-BR)**. The system tracks inspection measurements (desgaste = wear), rail replacements (trocas de trilho), and generates Excel reports.

## Commands

```bash
# Development server
python manage.py runserver

# Apply database migrations
python manage.py migrate

# Create and apply a new migration after model changes
python manage.py makemigrations
python manage.py migrate

# Collect static files (production)
python manage.py collectstatic --noinput

# Load initial data
python manage.py carregar_inspecoes_iniciais
python manage.py importar_referencia_linear

# Production build script (installs deps, migrates, collectstatic)
./build.sh
```

There are no automated tests in this project.

## Architecture

Single Django app (`desgaste/`) with a `config/` package for settings and routing.

### Domain Model Hierarchy

```
Linha → Estacao → PontoOperacional → Trilho → Inspecao → MedicaoDesgaste
```

- **Trilho**: A physical rail, identified by `via` (1 or 2) and `trilho` (A/B/C/D). Validation enforces Via 1 maps to trilhos A/B and Via 2 to C/D.
- **TrocaTrilho**: Rail replacement records (standalone model, not linked to Trilho). Auto-calculates rail size from MT marker values using regex extraction.
- **InspecaoTrecho**: Section-level inspections with multiple `OcorrenciaInspecaoTrecho` child records, managed via Django inline formsets.
- **ReferenciaLinearPKMT**: Reference table mapping linear locations (PK/MT markers) used throughout inspection and replacement records.

### Key Files

| File | Responsibility |
|------|---------------|
| `desgaste/models.py` | All domain models (~685 lines), business validation in `clean()` |
| `desgaste/views.py` | All view functions (~607 lines) including the hardcoded `ESTACOES_MAPA` |
| `desgaste/forms.py` | All forms and inline formsets (~20KB) |
| `desgaste/relatorios.py` | Excel report generation via openpyxl |
| `desgaste/urls.py` | 15 URL routes for the app |
| `config/settings.py` | Django config; SQLite in dev, PostgreSQL via `DATABASE_URL` env var |

### URL Structure

Routes in `desgaste/urls.py` cover: inspection listing/creation/editing, rail replacement listing/creation/editing/map view, Excel export, inspection history, and a JSON API (`api_itens_inspecao`) for dynamic item loading.

### Station Map

`ESTACOES_MAPA` in `views.py` is a hardcoded list of 18 stations with MT range boundaries. It drives the visual rail replacement map (`mapa_trocas_trilho`). Update this list if the station data changes.

## Key Patterns

- **Business validation**: In `Model.clean()` methods, not in views. Parity rules for MT numbers and via/trilho pairing are enforced here.
- **Inline formsets**: Used in `nova_inspecao` and `editar_inspecao` views for handling multiple occurrences per inspection in a single POST.
- **Excel generation**: `relatorios.py` uses openpyxl directly with manual cell styling — no abstraction layer.
- **Static reference data**: `TextChoices` classes (`ViaChoices`, `TrilhoChoices`, `CriticidadeChoices`) in models define allowed field values.
- **Media files**: Inspection and replacement photos are uploaded to `/media/` and served from there in development.

## Environment

- Python 3.12.3, Django 5.2.7
- Locale: `pt-BR`, timezone: `America/Sao_Paulo`
- Dev database: `db.sqlite3` (SQLite)
- Prod database: set `DATABASE_URL` environment variable (PostgreSQL via psycopg3)
- `SECRET_KEY` and `ALLOWED_HOSTS` should be set via environment variables in production
