# Database migrations

The application creates every table automatically on first boot
(`db.create_all()` in `app.py`), and `database.sql` holds the canonical MySQL
DDL. This folder is where schema changes are tracked once the project is live
and `create_all()` is no longer safe to rely on.

## Recommended: Flask-Migrate (Alembic)

```bash
pip install Flask-Migrate
export FLASK_APP="app:create_app"

flask db init                       # once — scaffolds migrations/versions/
flask db migrate -m "add irrigation_logs table"
flask db upgrade                    # apply to the current database
flask db downgrade                  # roll back one revision
```

Wire it into the factory by adding two lines to `app.py`:

```python
from flask_migrate import Migrate
Migrate(app, db)
```

## Manual SQL migrations

If you prefer plain SQL, add numbered files here and apply them in order:

```
migrations/
  001_initial_schema.sql        -> same content as ../database.sql
  002_add_irrigation_logs.sql
  003_index_market_prices_date.sql
```

```bash
mysql -u root -p smart_farmer < migrations/002_add_irrigation_logs.sql
```

## Rules of thumb

1. Never edit a migration that has already run in production — write a new one.
2. Every migration must be reversible; include the `DROP`/`ALTER` rollback in a
   comment at the bottom of the file.
3. Take a backup before applying anything to production:
   `mysqldump -u root -p smart_farmer > backup_$(date +%F).sql`
4. Keep `database.sql` and `models/models.py` in sync with the latest migration.
