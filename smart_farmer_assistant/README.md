# 🌾 Smart Farmer Assistant

An AI-powered agricultural assistance platform for Indian farmers — crop disease
and pest detection, live weather, mandi prices, nearby markets, government
schemes, soil intelligence, an agronomy chatbot, a crop calendar and three ML
advisory models, in nine Indian languages, with a full admin panel.

Built with **Flask + MySQL + scikit-learn + TensorFlow/Keras + Bootstrap 5 +
Chart.js**, and deployable to Render, Railway, AWS or Docker.

---

## Table of contents

1. [Feature overview](#feature-overview)
2. [Tech stack](#tech-stack)
3. [Screens and routes](#screens-and-routes)
4. [Quick start](#quick-start)
5. [Configuration](#configuration)
6. [Database](#database)
7. [Machine learning](#machine-learning)
8. [Project structure](#project-structure)
9. [REST API](#rest-api)
10. [Security](#security)
11. [Internationalisation](#internationalisation)
12. [Deployment](#deployment)
13. [Troubleshooting](#troubleshooting)
14. [Roadmap](#roadmap)

---

## Feature overview

| # | Module | What it does |
|---|--------|--------------|
| 1 | **Authentication** | Register, login, logout, forgot/reset password. Passwords hashed with Werkzeug PBKDF2. Session protection via Flask-Login. Profile captures name, email, phone, state, district, farm size, preferred language and crops grown. |
| 2 | **Smart dashboard** | Weather summary card, disease-scan shortcut, mandi price movers, scheme highlights, crop calendar strip, notification feed, activity statistics, Chart.js visualisations, collapsible sidebar and quick actions. |
| 3 | **Crop disease detection** | Upload a leaf photo → CNN classifies it across 15 PlantVillage classes with a confidence score, then shows causes, symptoms, treatment and prevention. Every scan is stored in history. |
| 4 | **Pest detection** | Upload a pest photo → CNN identifies the pest and returns damage profile, prevention and treatment (chemical + biological). |
| 5 | **Live weather forecast** | Temperature, feels-like, humidity, wind speed and direction, pressure, visibility, cloud cover, rain probability, sunrise and sunset. Current conditions, 24-hour hourly strip and a 7-day outlook with icons and Chart.js trend lines. |
| 6 | **Nearby market finder** | Browser geolocation → Leaflet/OpenStreetMap map with APMC mandi markers, distance in km, contact number and one-tap directions. |
| 7 | **Crop market prices** | Filter by state, district and crop → min, max and modal price per quintal with the last-updated date and a 30-day trend chart. Live data from the data.gov.in mandi API when a key is configured. |
| 8 | **Government schemes** | Central and state schemes with description, eligibility, benefits, required documents, application process and the official website. Filterable by state. |
| 9 | **Soil information** | Eight Indian soil types with nutrients, advantages, limitations, suitable crops, and fertiliser and irrigation recommendations. |
| 10 | **Farmer AI chatbot** | Intent-driven agronomy assistant with per-user chat history. The service layer is Gemini-ready — set `GEMINI_API_KEY` to switch backends without touching routes. |
| 11 | **Crop calendar** | Pick a state and crop → sowing window, planting time, irrigation schedule, fertiliser schedule, harvesting window and crop duration. |
| 12 | **Crop recommendation** | Random Forest classifier over soil type, temperature, humidity, rainfall and pH → best crop plus three ranked alternatives. |
| 13 | **Fertilizer recommendation** | Random Forest classifier over crop, soil type and N-P-K soil-test values → fertiliser plus a specific dose and application advice. |
| 14 | **Yield prediction** | Gradient Boosting regressor over crop, area, rainfall, temperature and fertiliser use → tonnes per acre and total expected tonnage. |
| 15 | **Notifications** | Weather warnings (heavy rain, heat wave, high wind), new-scheme alerts and price-change alerts, with read/unread state and full history. |
| 16 | **Multilingual UI** | English, हिन्दी, मराठी, বাংলা, ગુજરાતી, ਪੰਜਾਬੀ, தமிழ், తెలుగు, ಕನ್ನಡ — switchable from the navbar, persisted per user. |
| 17 | **Admin panel** | Manage users (activate/deactivate/delete), schemes, soil records, crop calendar and market prices; browse disease and pest scan records; chatbot intent analytics; platform statistics and model status. |

Plus: **dark mode toggle**, fully responsive mobile-first layout, skeleton
loaders, smooth transitions, and a REST API for every prediction endpoint.

---

## Tech stack

**Frontend** — HTML5, CSS3 (custom properties, container-aware layout),
Bootstrap 5.3, vanilla JavaScript (ES modules), Chart.js 4, Leaflet 1.9,
Bootstrap Icons.

**Backend** — Python 3.12, Flask 3.1 (application-factory + blueprints),
Flask-Login, Flask-WTF (CSRF), Flask-SQLAlchemy 3.1, Gunicorn.

**Database** — MySQL 8 (InnoDB, utf8mb4) via PyMySQL, with an automatic SQLite
fallback for zero-setup local development.

**Machine learning** — scikit-learn 1.9 (Random Forest ×2, Gradient Boosting),
TensorFlow/Keras (MobileNetV2 and EfficientNetB0 transfer learning),
NumPy, pandas, joblib.

**External APIs** — OpenWeatherMap (current + forecast), data.gov.in mandi
prices, browser Geolocation API, OpenStreetMap tiles via Leaflet.

---

## Screens and routes

| Route | Blueprint | Description |
|-------|-----------|-------------|
| `/` | main | Landing page with hero, feature grid and CTA |
| `/auth/register`, `/auth/login`, `/auth/logout` | auth | Account lifecycle |
| `/auth/forgot-password`, `/auth/reset-password/<token>` | auth | Token-based reset |
| `/dashboard/` | dashboard | Smart dashboard |
| `/dashboard/profile` | dashboard | Farmer profile editor |
| `/dashboard/notifications` | dashboard | Alert centre |
| `/dashboard/history` | dashboard | All past predictions |
| `/disease-detection` | detection | Leaf disease scanner |
| `/pest-detection` | detection | Pest scanner |
| `/weather` | weather | Forecast dashboard |
| `/market-prices` | market | Mandi price explorer |
| `/nearby-markets` | market | Nearby market map |
| `/schemes` | knowledge | Government schemes |
| `/soil` | knowledge | Soil information |
| `/calendar` | knowledge | Crop calendar |
| `/crop-recommendation` | advisor | Crop recommendation |
| `/fertilizer-recommendation` | advisor | Fertilizer recommendation |
| `/yield-prediction` | advisor | Yield prediction |
| `/chatbot` | chatbot | AI assistant |
| `/admin/` and `/admin/*` | admin | Admin panel (role-gated) |
| `/api/v1/*` | api | JSON REST endpoints |
| `/healthz` | main | Health check for load balancers |

---

## Quick start

### 1. Clone and install

```bash
git clone <your-repo-url> smart_farmer_assistant
cd smart_farmer_assistant

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY.
# Leave DATABASE_URL blank to use the SQLite fallback for a first run.
```

### 3. Train the models

```bash
python ml/train_all.py
```

This generates the tabular datasets into `datasets/` and writes three artefacts
into `trained_models/`. It takes under a minute. The app still runs without this
step — the ML service falls back to documented agronomic rules — but you should
train before deploying.

### 4. Run

```bash
python app.py
```

Open **http://localhost:5000**.

Demo admin account (created automatically on first boot):

```
email:    admin@smartfarmer.in
password: Admin@1234
```

Change this password immediately in any real deployment.

---

## Configuration

Every setting is read from environment variables in `config/config.py`, with
development, production and testing configurations.

| Variable | Required | Purpose |
|----------|----------|---------|
| `SECRET_KEY` | **yes** in production | Session signing and CSRF tokens |
| `FLASK_ENV` | no | `development` (default) or `production` |
| `DATABASE_URL` | no | Full SQLAlchemy URL. Blank → SQLite `smart_farmer.db` |
| `MYSQL_HOST` / `MYSQL_PORT` / `MYSQL_USER` / `MYSQL_PASSWORD` / `MYSQL_DB` | no | Used to compose the URL when `DATABASE_URL` is unset |
| `OPENWEATHER_API_KEY` | no | Live weather. Without it, a clearly labelled sample forecast is served |
| `DATA_GOV_API_KEY` | no | Live mandi prices from data.gov.in |
| `GOOGLE_MAPS_API_KEY` | no | Only if you switch the map provider from Leaflet |
| `GEMINI_API_KEY` | no | Switches the chatbot to the Gemini backend |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | no | Seeded admin credentials |

**Graceful degradation is deliberate.** Every external API has a documented
offline fallback, so the platform demonstrates end-to-end without a single API
key — and the UI always labels sample data as sample data.

---

## Database

### MySQL (recommended)

```bash
mysql -u root -p < database.sql

# then in .env
DATABASE_URL=mysql+pymysql://root:yourpassword@localhost:3306/smart_farmer
```

### SQLite (zero setup)

Leave `DATABASE_URL` unset. The app creates `smart_farmer.db` in the project
root and seeds it on first boot.

### Schema

Fourteen tables with proper foreign keys and cascade rules:

```
users ──1:1──> profiles
  │
  ├──1:N──> disease_predictions        (ON DELETE CASCADE)
  ├──1:N──> pest_predictions           (ON DELETE CASCADE)
  ├──1:N──> crop_recommendations       (ON DELETE CASCADE)
  ├──1:N──> fertilizer_recommendations (ON DELETE CASCADE)
  ├──1:N──> yield_predictions          (ON DELETE CASCADE)
  ├──1:N──> chatbot_history            (ON DELETE CASCADE)
  ├──1:N──> notifications              (ON DELETE CASCADE)
  └──1:N──> weather_logs               (ON DELETE SET NULL)

reference tables: market_prices, government_schemes,
                  soil_information, crop_calendar
```

`utils/seed_data.py` populates soil information, government schemes, the crop
calendar and 30 days of mandi price history on first boot.

Schema changes are tracked in `migrations/` — see `migrations/README.md`.

---

## Machine learning

### Tabular models — train in seconds, included in the repo

| Model | Algorithm | Features | Artefact |
|-------|-----------|----------|----------|
| Crop recommendation | RandomForestClassifier (320 trees) | soil type, temperature, humidity, rainfall, pH | `trained_models/crop_recommendation.pkl` |
| Fertilizer recommendation | RandomForestClassifier (300 trees) | crop, soil type, N, P, K | `trained_models/fertilizer_recommendation.pkl` |
| Yield prediction | GradientBoostingRegressor (420 stages) | crop, area, rainfall, temperature, fertiliser | `trained_models/yield_prediction.pkl` |

```bash
python ml/train_all.py                    # all three
python ml/train_crop_recommendation.py    # or individually
python ml/train_fertilizer.py
python ml/train_yield.py
```

Each script prints hold-out accuracy, cross-validated accuracy (or R², MAE and
RMSE for the regressor) and feature importances.

**About the bundled data.** `ml/generate_datasets.py` produces reproducible
synthetic datasets that encode real agronomic relationships (ICAR temperature
and rainfall envelopes, soil-suitability, pH tolerance, Soil Health Card nutrient
deficit rules, diminishing fertiliser response). This makes the project train
end-to-end with no downloads. The fertiliser and yield models score well on it;
the crop classifier scores lower because several Rabi crops share almost
identical climate envelopes by design — that overlap is agronomically honest.

**To train on real data**, drop these CSVs into `datasets/` using the same
column names and re-run the scripts:

| File | Source |
|------|--------|
| `crop_recommendation.csv` | Kaggle — `atharvaingle/crop-recommendation-dataset` |
| `fertilizer_recommendation.csv` | Kaggle — `gdabhishek/fertilizer-prediction` |
| `crop_yield.csv` | data.gov.in — district-wise crop production statistics |

### CNN models — bring your own images

| Model | Backbone | Dataset |
|-------|----------|---------|
| Disease detection | MobileNetV2 transfer learning + fine-tuning | PlantVillage (`abdallahalidev/plantvillage-dataset`) |
| Pest detection | EfficientNetB0 transfer learning + fine-tuning | IP102 or `gauravduttakiit/agricultural-pests-image-dataset` |

```bash
pip install tensorflow-cpu==2.18.0

kaggle datasets download -d abdallahalidev/plantvillage-dataset
unzip plantvillage-dataset.zip -d datasets/plantvillage
python ml/train_disease_cnn.py --epochs 12

kaggle datasets download -d gauravduttakiit/agricultural-pests-image-dataset
unzip agricultural-pests-image-dataset.zip -d datasets/pests
python ml/train_pest_cnn.py --epochs 15
```

Class folder names must match the keys in `services/knowledge_base.py`
(`DISEASE_DB`, `PEST_DB`) so predictions map to the agronomy guidance.

**TensorFlow is optional by design.** It is commented out in
`requirements.txt` so the app fits a free 512 MB Render dyno. Without it,
`services/ml_service.py` uses a deterministic image-fingerprint heuristic and
labels the result `source: "heuristic"` so the UI can flag it. Every other
module is unaffected.

---

## Project structure

```
smart_farmer_assistant/
├── app.py                       # Application factory, blueprints, error handlers
├── extensions.py                # db, login_manager, csrf singletons
├── requirements.txt
├── database.sql                 # Full MySQL DDL + seed data
├── README.md
├── DEPLOYMENT.md
├── Dockerfile / docker-compose.yml
├── Procfile / render.yaml / runtime.txt
├── .env.example
│
├── config/
│   └── config.py                # Development / Production / Testing configs
│
├── models/
│   └── models.py                # 14 SQLAlchemy models with FKs and cascades
│
├── routes/                      # One blueprint per domain
│   ├── main.py                  # Landing, language switch, health check
│   ├── auth.py                  # Register, login, logout, password reset
│   ├── dashboard.py             # Dashboard, profile, notifications, history
│   ├── detection.py             # Disease + pest scanners, upload serving
│   ├── weather.py               # Forecast dashboard
│   ├── market.py                # Mandi prices, nearby markets
│   ├── knowledge.py             # Schemes, soil, crop calendar
│   ├── advisor.py               # Crop, fertilizer, yield advisors
│   ├── chatbot.py               # Chat UI + JSON endpoint
│   ├── admin.py                 # Admin panel (role-gated)
│   └── api.py                   # REST API
│
├── services/                    # Business logic, isolated from HTTP
│   ├── ml_service.py            # Model loading, caching, prediction, fallbacks
│   ├── weather_service.py       # OpenWeatherMap client + alert builder
│   ├── market_service.py        # data.gov.in client + trend computation
│   ├── geo_service.py           # Haversine distance, APMC market directory
│   ├── chatbot_service.py       # Intent engine, Gemini-ready
│   ├── notification_service.py  # Alert generation and delivery
│   └── knowledge_base.py        # States, districts, crops, disease + pest DB
│
├── utils/
│   ├── decorators.py            # @admin_required, @profile_required
│   ├── validators.py            # Input sanitisation, secure upload handling
│   ├── i18n.py                  # Translation loader and `t()` helper
│   ├── db_utils.py              # Pagination and query helpers
│   ├── seed_data.py             # First-boot reference data
│   └── build_locales.py         # Regenerates static/locales/*.json
│
├── ml/                          # Training scripts (not imported at runtime)
│   ├── generate_datasets.py
│   ├── train_crop_recommendation.py
│   ├── train_fertilizer.py
│   ├── train_yield.py
│   ├── train_disease_cnn.py
│   ├── train_pest_cnn.py
│   └── train_all.py
│
├── templates/
│   ├── base.html                # Public shell
│   ├── app.html                 # Authenticated shell (sidebar + navbar)
│   ├── index.html               # Landing page
│   ├── partials/                # logo, head, flash, language menu
│   ├── auth/                    # login, register, forgot, reset
│   ├── dashboard/               # home, profile, notifications, history
│   ├── modules/                 # 12 feature pages
│   ├── admin/                   # 8 admin pages
│   └── errors/                  # 403 / 404 / 413 / 500
│
├── static/
│   ├── css/style.css            # Design system, dark mode, components
│   ├── js/                      # theme, app, chatbot, maps
│   ├── img/                     # Logo and favicon (inline SVG)
│   └── locales/                 # 9 translation JSON files
│
├── datasets/                    # Generated + downloaded training data
├── trained_models/              # .pkl and .h5 artefacts
├── uploads/                     # User-uploaded scan images
└── migrations/                  # Schema change tracking
```

---

## REST API

All endpoints return JSON. Prediction endpoints require an authenticated
session; `/api/health` is public.

| Method | Endpoint | Body / query | Returns |
|--------|----------|--------------|---------|
| `GET` | `/healthz` | — | `{"status": "ok"}` |
| `GET` | `/api/v1/meta` | — | States, districts, crops, soil types, seasons |
| `GET` | `/api/v1/districts/<state>` | — | Districts of a state |
| `GET` | `/api/v1/weather?city=Pune` | or `lat` + `lon` | Full weather bundle |
| `GET` | `/api/v1/prices?state=&district=&crop=` | — | Latest mandi price rows |
| `GET` | `/api/v1/prices/trend?crop=&state=` | — | 30-day trend series for charts |
| `GET` | `/api/v1/markets/nearby?lat=&lon=&radius=` | — | Nearby APMC markets with distance |
| `GET` | `/api/v1/schemes?state=&type=` | — | Filtered scheme list |
| `GET` | `/api/v1/notifications` | — | Current user's alerts |
| `POST` | `/api/v1/predict/crop` | `soil_type, temperature, humidity, rainfall, ph` | Crop + confidence + alternatives |
| `POST` | `/api/v1/predict/fertilizer` | `crop, soil_type, nitrogen, phosphorus, potassium` | Fertilizer + advice |
| `POST` | `/api/v1/predict/yield` | `crop, area, rainfall, temperature, fertilizer` | Yield per acre + total |
| `POST` | `/api/chat` | `{"message": "..."}` | Reply + detected intent |
| `POST` | `/api/chat/clear` | — | Clears the caller's chat history |

```bash
curl -X POST http://localhost:5000/api/v1/predict/crop \
     -H "Content-Type: application/json" \
     -d '{"soil_type":"Alluvial","temperature":29,"humidity":85,"rainfall":220,"ph":6.2}'
```

---

## Security

| Control | Implementation |
|---------|----------------|
| Password hashing | Werkzeug PBKDF2-SHA256 with per-user salt. Plaintext is never stored or logged. |
| Session protection | Flask-Login with `session_protection="strong"`, HttpOnly and SameSite=Lax cookies, `SESSION_COOKIE_SECURE` in production. |
| CSRF protection | Flask-WTF `CSRFProtect` applied globally; every form carries a `csrf_token`. The JSON API blueprints are explicitly exempted and session-guarded instead. |
| SQL injection | SQLAlchemy ORM with parameter binding throughout — no string-concatenated SQL anywhere in the codebase. |
| Input validation | `utils/validators.py` sanitises and type-coerces every user input; numeric ranges are clamped before reaching a model. |
| Secure uploads | Extension allow-list (png/jpg/jpeg/webp), `secure_filename()`, UUID renaming, 5 MB cap via `MAX_CONTENT_LENGTH`, Pillow re-encode to strip embedded payloads, files served through a controlled route rather than a static directory. |
| Authorisation | `@login_required` on all member routes, `@admin_required` on the entire admin blueprint. |
| Security headers | `X-Content-Type-Options`, `X-Frame-Options: DENY`, `Referrer-Policy`, and a Content-Security-Policy set in an `after_request` hook. |
| Error handling | Custom 403/404/413/500 pages; tracebacks go to rotating log files, never to the browser. |

---

## Internationalisation

Nine languages ship in `static/locales/`:

`en` English · `hi` हिन्दी · `mr` मराठी · `bn` বাংলা · `gu` ગુજરાતી ·
`pa` ਪੰਜਾਬੀ · `ta` தமிழ் · `te` తెలుగు · `kn` ಕನ್ನಡ

The active language comes from the user's profile, falling back to the session,
then to `en`. Switch it from the navbar globe menu; the choice persists to the
profile for logged-in users.

To add a language: add the ISO code and native label to `LANGUAGES` in
`utils/i18n.py`, add the strings to `utils/build_locales.py`, then run
`python utils/build_locales.py`. Templates use `{{ t('key') }}`; JavaScript
reads the same JSON from `/static/locales/<lang>.json`.

---

## Deployment

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for step-by-step guides covering Render,
Railway, AWS Elastic Beanstalk, AWS EC2 with Nginx, Docker and PythonAnywhere,
plus a production hardening checklist.

Quick version:

```bash
# Docker (app + MySQL together)
docker compose up --build

# Render — push the repo, then "New > Blueprint" (render.yaml is included)

# Any PaaS with a Procfile
gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 2 --threads 4
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Can't connect to MySQL server` | Confirm MySQL is running and `DATABASE_URL` is correct. Clear `DATABASE_URL` to fall back to SQLite. |
| `ModuleNotFoundError: MySQLdb` | Use the `mysql+pymysql://` scheme, not `mysql://`. |
| Weather shows "sample data" | Set `OPENWEATHER_API_KEY` in `.env`. New keys take a few minutes to activate. |
| Predictions say `source: rule_based` | Run `python ml/train_all.py` to create the `.pkl` artefacts. |
| Disease result says `source: heuristic` | Install TensorFlow and train the CNN — see [Machine learning](#machine-learning). |
| Geolocation does not work | Browsers only expose it over HTTPS or on `localhost`. |
| `413 Request Entity Too Large` | The upload exceeds 5 MB. Raise `MAX_CONTENT_LENGTH` in `config/config.py`. |
| Indic text renders as boxes | Ensure the database is `utf8mb4` and the Noto Sans font is loading. |

---

## Roadmap

- Gemini-backed conversational chatbot with retrieval over the scheme corpus
- SMS and WhatsApp alerts for weather and price triggers
- Offline-first PWA with a service worker for low-connectivity villages
- Voice input and text-to-speech in all nine languages
- Satellite NDVI crop-health monitoring
- Farmer-to-buyer marketplace with escrow

---

## Data sources and credits

- Weather — [OpenWeatherMap](https://openweathermap.org/api)
- Mandi prices — [data.gov.in Agmarknet resource](https://data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi)
- Maps and tiles — [OpenStreetMap](https://www.openstreetmap.org/copyright) via [Leaflet](https://leafletjs.com)
- Disease imagery — [PlantVillage dataset](https://www.kaggle.com/datasets/abdallahalidev/plantvillage-dataset)
- Pest imagery — [Agricultural Pests Image Dataset](https://www.kaggle.com/datasets/gauravduttakiit/agricultural-pests-image-dataset)
- Scheme details — [PM-KISAN](https://pmkisan.gov.in), [PMFBY](https://pmfby.gov.in), [Soil Health Card](https://soilhealth.dac.gov.in), [PMKSY](https://pmksy.gov.in)
- UI — [Bootstrap 5](https://getbootstrap.com), [Bootstrap Icons](https://icons.getbootstrap.com), [Chart.js](https://www.chartjs.org)

Scheme details and agronomic guidance are provided for information only. Always
confirm eligibility and dosage with your local Krishi Vigyan Kendra or the
official scheme portal before acting.

## License

MIT — free to use, modify and deploy.
