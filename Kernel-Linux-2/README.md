# Ubuntu Monitoring & Network Administration

Web system for Ubuntu 22.04 monitoring and administration using Flask, SQLAlchemy, SQLite, Bootstrap 5, JavaScript and Chart.js.

## Quick Start

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py init-db
python wsgi.py
```

Open `http://127.0.0.1:5000` and sign in with:

- Admin: `admin / Admin@12345`
- Operator: `operator / Operator@12345`

## Docker

```bash
docker compose up --build
```

## Documentation

See [docs/architecture.md](docs/architecture.md) for architecture, diagrams, database design, deployment, sudo setup and testing.
