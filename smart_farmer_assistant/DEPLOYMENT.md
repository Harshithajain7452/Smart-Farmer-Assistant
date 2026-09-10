# Deployment guide — Smart Farmer Assistant

Covers Render, Railway, Docker, AWS Elastic Beanstalk, AWS EC2 + Nginx and
PythonAnywhere, followed by a production hardening checklist.

The app is a standard WSGI application exposed through an application factory:

```
gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
```

Health check endpoint: `GET /healthz` → `{"status": "ok"}`

---

## Pre-flight checklist

Before deploying anywhere:

1. `SECRET_KEY` is a long random string, not the default.
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```
2. `FLASK_ENV=production` — this enables secure cookies and disables debug.
3. Change the seeded admin password (`admin@smartfarmer.in` / `Admin@1234`).
4. `DATABASE_URL` points at a managed MySQL instance, not SQLite.
5. Models are trained — `python ml/train_all.py` (or let the build command do it).
6. `.env` is in `.gitignore` and was never committed.

---

## 1. Render (recommended — free tier works)

A `render.yaml` blueprint is included, so the whole service is one click.

### Blueprint deploy

1. Push the repository to GitHub.
2. Render dashboard → **New → Blueprint** → select the repository.
3. Render reads `render.yaml` and creates the web service.
4. Fill in the `sync: false` secrets in the dashboard:
   `DATABASE_URL`, `OPENWEATHER_API_KEY`, `DATA_GOV_API_KEY`, `GEMINI_API_KEY`.
5. Deploy. First build takes 3-5 minutes (dependency install + model training).

### Manual deploy

| Field | Value |
|-------|-------|
| Environment | Python 3 |
| Region | Singapore (lowest latency for Indian users) |
| Build command | `pip install -r requirements.txt && python ml/train_all.py` |
| Start command | `gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120` |
| Health check path | `/healthz` |

### Database

Render does not offer managed MySQL. Use one of:

- **PlanetScale** (free tier) — `DATABASE_URL=mysql+pymysql://user:pass@host/db?ssl_ca=/etc/ssl/certs/ca-certificates.crt`
- **Railway MySQL** — copy the connection URL and change the scheme to `mysql+pymysql://`
- **Aiven for MySQL** (free tier)
- **Render PostgreSQL** — swap `PyMySQL` for `psycopg2-binary` and use `postgresql+psycopg2://`; the SQLAlchemy models work unchanged.

### Free-tier notes

- Free instances sleep after 15 minutes of inactivity; the first request then
  takes ~30 seconds. Ping `/healthz` every 10 minutes with a free uptime monitor
  to avoid this.
- The free dyno has 512 MB RAM — keep `tensorflow-cpu` commented out in
  `requirements.txt`. The three scikit-learn models fit comfortably.
- The filesystem is ephemeral. Uploaded scan images vanish on redeploy — move
  `uploads/` to S3 or Cloudinary for anything beyond a demo.

---

## 2. Railway

```bash
npm i -g @railway/cli
railway login
railway init
railway add --database mysql        # provisions MySQL and injects MYSQL_URL
railway up
```

Then in **Variables**:

```
FLASK_ENV=production
SECRET_KEY=<generated>
DATABASE_URL=mysql+pymysql://${{MySQL.MYSQLUSER}}:${{MySQL.MYSQLPASSWORD}}@${{MySQL.MYSQLHOST}}:${{MySQL.MYSQLPORT}}/${{MySQL.MYSQLDATABASE}}
OPENWEATHER_API_KEY=<key>
```

Railway auto-detects the `Procfile`. Set a custom start command only if you want
different worker counts.

Load the schema into the provisioned database:

```bash
railway run mysql -h $MYSQLHOST -P $MYSQLPORT -u $MYSQLUSER -p$MYSQLPASSWORD $MYSQLDATABASE < database.sql
```

---

## 3. Docker

### Single container

```bash
docker build -t smart-farmer .
docker run -d -p 5000:5000 --env-file .env --name sfa smart-farmer
docker logs -f sfa
```

### App + MySQL together

```bash
docker compose up --build -d
docker compose logs -f web
docker compose down          # add -v to also drop the database volume
```

`docker-compose.yml` mounts `database.sql` into the MySQL container's
init directory, so the schema and seed data load automatically on first start.
`uploads/` is bind-mounted so scan images survive container restarts.

### Push to a registry

```bash
docker tag smart-farmer ghcr.io/<user>/smart-farmer:1.0.0
docker push ghcr.io/<user>/smart-farmer:1.0.0
```

---

## 4. AWS Elastic Beanstalk

```bash
pip install awsebcli
eb init -p python-3.12 smart-farmer --region ap-south-1
eb create smart-farmer-prod --instance-type t3.small
```

Create `.ebextensions/01_flask.config`:

```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: "app:create_app()"
  aws:elasticbeanstalk:application:environment:
    FLASK_ENV: production
    PYTHONPATH: "/var/app/current:$PYTHONPATH"
  aws:elasticbeanstalk:environment:process:default:
    HealthCheckPath: /healthz

container_commands:
  01_train_models:
    command: "source /var/app/venv/*/bin/activate && python ml/train_all.py"
    leader_only: true
```

Set secrets without committing them:

```bash
eb setenv SECRET_KEY=<generated> \
          DATABASE_URL=mysql+pymysql://admin:pass@<rds-endpoint>:3306/smart_farmer \
          OPENWEATHER_API_KEY=<key>
eb deploy
eb open
```

**Database** — create an RDS MySQL 8.0 instance in the same VPC, allow inbound
3306 from the Beanstalk security group, then load `database.sql`:

```bash
mysql -h <rds-endpoint> -u admin -p < database.sql
```

**Uploads** — the instance filesystem is ephemeral behind autoscaling. Store
scan images in S3:

```bash
pip install boto3
# then point utils/validators.save_upload at your bucket
```

---

## 5. AWS EC2 + Nginx + Gunicorn + systemd

```bash
# On a fresh Ubuntu 24.04 instance
sudo apt update && sudo apt install -y python3-venv python3-pip nginx mysql-server git
git clone <repo> /opt/smart_farmer && cd /opt/smart_farmer
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python ml/train_all.py

sudo mysql < database.sql
cp .env.example .env && nano .env      # set SECRET_KEY, DATABASE_URL
```

`/etc/systemd/system/smartfarmer.service`:

```ini
[Unit]
Description=Smart Farmer Assistant
After=network.target mysql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/smart_farmer
EnvironmentFile=/opt/smart_farmer/.env
ExecStart=/opt/smart_farmer/.venv/bin/gunicorn "app:create_app()" \
          --bind unix:/opt/smart_farmer/sfa.sock --workers 3 --threads 4 --timeout 120 \
          --access-logfile /var/log/smartfarmer/access.log \
          --error-logfile /var/log/smartfarmer/error.log
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo mkdir -p /var/log/smartfarmer && sudo chown www-data:www-data /var/log/smartfarmer
sudo systemctl enable --now smartfarmer
sudo systemctl status smartfarmer
```

`/etc/nginx/sites-available/smartfarmer`:

```nginx
server {
    listen 80;
    server_name your-domain.in www.your-domain.in;

    client_max_body_size 6M;          # matches the 5 MB upload cap

    location /static/ {
        alias /opt/smart_farmer/static/;
        expires 30d;
        access_log off;
    }

    location / {
        proxy_pass http://unix:/opt/smart_farmer/sfa.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/smartfarmer /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Free HTTPS
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.in -d www.your-domain.in
```

The app already applies `ProxyFix`, so `X-Forwarded-Proto` is honoured and
secure cookies work correctly behind Nginx.

---

## 6. PythonAnywhere

1. Upload the project or `git clone` it in a Bash console.
2. Create a virtualenv and `pip install -r requirements.txt`.
3. **Web** tab → Add a new web app → Manual configuration → Python 3.12.
4. Edit the WSGI file:

```python
import os, sys
path = "/home/<username>/smart_farmer_assistant"
if path not in sys.path:
    sys.path.insert(0, path)

from dotenv import load_dotenv
load_dotenv(os.path.join(path, ".env"))

from app import create_app
application = create_app()
```

5. **Databases** tab → create a MySQL database, then set
   `DATABASE_URL=mysql+pymysql://<user>:<pass>@<user>.mysql.pythonanywhere-services.com/<user>$smart_farmer`
6. Static files mapping: URL `/static/` → directory
   `/home/<username>/smart_farmer_assistant/static`
7. Reload the web app.

Note: the free tier restricts outbound HTTP to a whitelist, so OpenWeatherMap
and data.gov.in calls fail — the app serves its labelled sample data instead.

---

## Production hardening checklist

**Application**

- [ ] `SECRET_KEY` from a secrets manager, rotated periodically
- [ ] `FLASK_ENV=production`, debug off
- [ ] Seeded admin password changed; consider deleting the demo account
- [ ] Rate limiting on `/login`, `/register` and the prediction API
      (`pip install Flask-Limiter`)
- [ ] `SESSION_COOKIE_SECURE=True` (automatic when `FLASK_ENV=production`)

**Database**

- [ ] Dedicated application user with only `SELECT, INSERT, UPDATE, DELETE`
- [ ] TLS enforced on the connection
- [ ] Automated daily backups
      (`mysqldump -u root -p smart_farmer | gzip > backup_$(date +%F).sql.gz`)
- [ ] Restore tested at least once
- [ ] `innodb_buffer_pool_size` tuned to ~70% of available RAM

**Infrastructure**

- [ ] HTTPS everywhere with auto-renewing certificates
- [ ] `uploads/` on S3 or another object store, not the instance disk
- [ ] Log rotation configured (`logs/` uses `RotatingFileHandler` already)
- [ ] Uptime monitor hitting `/healthz`
- [ ] Error tracking (`pip install sentry-sdk[flask]`)
- [ ] CDN in front of `/static/` for Indian edge caching

**Scaling**

- [ ] Gunicorn workers = `(2 × CPU cores) + 1`
- [ ] Cache weather and price responses in Redis (they change hourly at most)
- [ ] Move CNN inference to a separate service or a queue if you enable
      TensorFlow — image inference will otherwise block web workers
- [ ] Add a read replica once mandi price history grows past a few million rows

---

## Post-deploy smoke test

```bash
BASE=https://your-app.onrender.com

curl -fsS $BASE/healthz                                  # {"status":"ok"}
curl -fsS -o /dev/null -w "%{http_code}\n" $BASE/         # 200 landing
curl -fsS -o /dev/null -w "%{http_code}\n" $BASE/auth/login # 200 login
curl -fsS -o /dev/null -w "%{http_code}\n" $BASE/dashboard/ # 302 -> /auth/login
```

Then, in a browser:

1. Register a farmer account and confirm the profile fields save.
2. Upload a leaf image on the disease scanner and check the result and history.
3. Open the weather page and confirm live data (not the sample banner).
4. Filter mandi prices and confirm the trend chart renders.
5. Allow geolocation on the nearby-markets map and confirm markers appear.
6. Run all three advisors and confirm `source` is the model, not `rule_based`.
7. Switch the language to हिन्दी and confirm the navigation translates.
8. Toggle dark mode and reload — the choice should persist.
9. Log in as admin and confirm every admin page loads.
