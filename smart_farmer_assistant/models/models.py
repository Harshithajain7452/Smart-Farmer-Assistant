"""
SQLAlchemy ORM models — mirrors database.sql one-to-one.

Every table uses InnoDB-compatible types so the same models work on MySQL
(production) and SQLite (local development / CI).
"""
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


# ---------------------------------------------------------------------------
# 1. Authentication & profile
# ---------------------------------------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="farmer", nullable=False)  # farmer | admin
    is_active_flag = db.Column("is_active", db.Boolean, default=True, nullable=False)
    reset_token = db.Column(db.String(120), nullable=True, index=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)

    profile = db.relationship(
        "Profile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    disease_predictions = db.relationship(
        "DiseasePrediction", back_populates="user", cascade="all, delete-orphan"
    )
    pest_predictions = db.relationship(
        "PestPrediction", back_populates="user", cascade="all, delete-orphan"
    )
    notifications = db.relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
    chats = db.relationship(
        "ChatbotHistory", back_populates="user", cascade="all, delete-orphan"
    )

    # -- password helpers (PBKDF2-SHA256 via Werkzeug) ----------------------
    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password, method="pbkdf2:sha256:600000")

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_active(self) -> bool:  # Flask-Login hook
        return bool(self.is_active_flag)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class Profile(db.Model):
    __tablename__ = "profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    state = db.Column(db.String(80))
    district = db.Column(db.String(80))
    village = db.Column(db.String(120))
    farm_size = db.Column(db.Float, default=0.0)         # acres
    soil_type = db.Column(db.String(60))
    crops_grown = db.Column(db.Text)                     # comma separated
    preferred_language = db.Column(db.String(5), default="en")
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    avatar = db.Column(db.String(255))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="profile")

    @property
    def crop_list(self):
        return [c.strip() for c in (self.crops_grown or "").split(",") if c.strip()]


# ---------------------------------------------------------------------------
# 2. AI prediction history
# ---------------------------------------------------------------------------
class DiseasePrediction(db.Model):
    __tablename__ = "disease_predictions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    crop = db.Column(db.String(80))
    disease_name = db.Column(db.String(160), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    is_healthy = db.Column(db.Boolean, default=False)
    causes = db.Column(db.Text)
    symptoms = db.Column(db.Text)
    treatment = db.Column(db.Text)
    prevention = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User", back_populates="disease_predictions")


class PestPrediction(db.Model):
    __tablename__ = "pest_predictions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    pest_name = db.Column(db.String(160), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    damage = db.Column(db.Text)
    prevention = db.Column(db.Text)
    treatment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User", back_populates="pest_predictions")


class CropRecommendation(db.Model):
    __tablename__ = "crop_recommendations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    soil_type = db.Column(db.String(60))
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    rainfall = db.Column(db.Float)
    ph = db.Column(db.Float)
    recommended_crop = db.Column(db.String(80))
    confidence = db.Column(db.Float)
    alternatives = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class FertilizerRecommendation(db.Model):
    __tablename__ = "fertilizer_recommendations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    crop = db.Column(db.String(80))
    soil_type = db.Column(db.String(60))
    nitrogen = db.Column(db.Float)
    phosphorus = db.Column(db.Float)
    potassium = db.Column(db.Float)
    fertilizer = db.Column(db.String(120))
    confidence = db.Column(db.Float)
    advice = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class YieldPrediction(db.Model):
    __tablename__ = "yield_predictions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    crop = db.Column(db.String(80))
    area = db.Column(db.Float)          # acres
    rainfall = db.Column(db.Float)      # mm
    temperature = db.Column(db.Float)   # °C
    fertilizer_used = db.Column(db.Float)  # kg/acre
    predicted_yield = db.Column(db.Float)  # tonnes
    yield_per_acre = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# 3. Knowledge / reference data (admin managed)
# ---------------------------------------------------------------------------
class MarketPrice(db.Model):
    __tablename__ = "market_prices"

    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.String(80), nullable=False, index=True)
    district = db.Column(db.String(80), nullable=False, index=True)
    market = db.Column(db.String(120))
    crop = db.Column(db.String(80), nullable=False, index=True)
    variety = db.Column(db.String(80))
    min_price = db.Column(db.Float, nullable=False)   # ₹ per quintal
    max_price = db.Column(db.Float, nullable=False)
    modal_price = db.Column(db.Float, nullable=False)
    price_date = db.Column(db.Date, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class GovernmentScheme(db.Model):
    __tablename__ = "government_schemes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    scheme_type = db.Column(db.String(20), default="central", index=True)  # central | state
    state = db.Column(db.String(80), index=True)   # NULL for central schemes
    description = db.Column(db.Text)
    eligibility = db.Column(db.Text)
    benefits = db.Column(db.Text)
    documents = db.Column(db.Text)
    application_process = db.Column(db.Text)
    website = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SoilInformation(db.Model):
    __tablename__ = "soil_information"

    id = db.Column(db.Integer, primary_key=True)
    soil_type = db.Column(db.String(60), unique=True, nullable=False)
    description = db.Column(db.Text)
    nutrients = db.Column(db.Text)
    advantages = db.Column(db.Text)
    limitations = db.Column(db.Text)
    suitable_crops = db.Column(db.Text)
    fertilizer_recommendation = db.Column(db.Text)
    irrigation_recommendation = db.Column(db.Text)
    regions = db.Column(db.Text)
    image = db.Column(db.String(255))


class CropCalendar(db.Model):
    __tablename__ = "crop_calendar"

    id = db.Column(db.Integer, primary_key=True)
    crop = db.Column(db.String(80), nullable=False, index=True)
    state = db.Column(db.String(80), nullable=False, index=True)
    season = db.Column(db.String(40))  # Kharif | Rabi | Zaid
    sowing_time = db.Column(db.String(120))
    planting_time = db.Column(db.String(120))
    irrigation_schedule = db.Column(db.Text)
    fertilizer_schedule = db.Column(db.Text)
    harvesting_time = db.Column(db.String(120))
    duration_days = db.Column(db.Integer)
    notes = db.Column(db.Text)


class WeatherLog(db.Model):
    __tablename__ = "weather_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    city = db.Column(db.String(120))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    wind_speed = db.Column(db.Float)
    pressure = db.Column(db.Float)
    rain_probability = db.Column(db.Float)
    condition = db.Column(db.String(120))
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


class ChatbotHistory(db.Model):
    __tablename__ = "chatbot_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    intent = db.Column(db.String(60))
    language = db.Column(db.String(5), default="en")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User", back_populates="chats")


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text)
    category = db.Column(db.String(40), default="general")  # weather | scheme | price | general
    severity = db.Column(db.String(20), default="info")     # info | warning | danger
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User", back_populates="notifications")
