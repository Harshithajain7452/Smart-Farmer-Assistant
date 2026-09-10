-- =====================================================================
--  Smart Farmer Assistant — MySQL 8.0 schema
--  ------------------------------------------------------------------
--  Mirrors models/models.py exactly (SQLAlchemy ORM is the source of
--  truth at runtime; this file is the canonical DDL for MySQL setups,
--  DBA review and CI provisioning).
--
--  Usage:
--      mysql -u root -p < database.sql
--
--  Engine  : InnoDB (transactional + foreign keys)
--  Charset : utf8mb4 / utf8mb4_unicode_ci (full Indic script support for
--            Hindi, Bengali, Tamil, Telugu, Kannada, Marathi, Gujarati,
--            Punjabi content)
-- =====================================================================

DROP DATABASE IF EXISTS smart_farmer;
CREATE DATABASE smart_farmer
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
USE smart_farmer;

SET FOREIGN_KEY_CHECKS = 1;

-- ---------------------------------------------------------------------
-- 1. users — authentication + role
-- ---------------------------------------------------------------------
CREATE TABLE users (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    name                VARCHAR(120)  NOT NULL,
    email               VARCHAR(160)  NOT NULL,
    phone               VARCHAR(20)   NULL,
    password_hash       VARCHAR(255)  NOT NULL,          -- werkzeug pbkdf2:sha256
    role                VARCHAR(20)   NOT NULL DEFAULT 'farmer',   -- farmer | admin
    is_active           BOOLEAN       NOT NULL DEFAULT TRUE,
    reset_token         VARCHAR(120)  NULL,
    reset_token_expiry  DATETIME      NULL,
    created_at          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login          DATETIME      NULL,
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT uq_users_phone UNIQUE (phone),
    INDEX ix_users_email (email),
    INDEX ix_users_reset_token (reset_token),
    INDEX ix_users_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 2. profiles — farmer profile, 1:1 with users
-- ---------------------------------------------------------------------
CREATE TABLE profiles (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    user_id             INT           NOT NULL,
    state               VARCHAR(80)   NULL,
    district            VARCHAR(80)   NULL,
    village             VARCHAR(120)  NULL,
    farm_size           FLOAT         DEFAULT 0,          -- acres
    soil_type           VARCHAR(60)   NULL,
    crops_grown         TEXT          NULL,               -- comma separated
    preferred_language  VARCHAR(5)    DEFAULT 'en',
    latitude            FLOAT         NULL,
    longitude           FLOAT         NULL,
    avatar              VARCHAR(255)  NULL,
    updated_at          DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_profiles_user UNIQUE (user_id),
    CONSTRAINT fk_profiles_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX ix_profiles_state (state),
    INDEX ix_profiles_district (district)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 3. disease_predictions — CNN leaf-disease history
-- ---------------------------------------------------------------------
CREATE TABLE disease_predictions (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT           NOT NULL,
    image_path    VARCHAR(255)  NOT NULL,
    crop          VARCHAR(80)   NULL,
    disease_name  VARCHAR(160)  NOT NULL,
    confidence    FLOAT         NOT NULL,
    is_healthy    BOOLEAN       DEFAULT FALSE,
    causes        TEXT          NULL,
    symptoms      TEXT          NULL,
    treatment     TEXT          NULL,
    prevention    TEXT          NULL,
    created_at    DATETIME      DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_disease_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX ix_disease_created (created_at),
    INDEX ix_disease_user_created (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 4. pest_predictions — CNN pest history
-- ---------------------------------------------------------------------
CREATE TABLE pest_predictions (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT           NOT NULL,
    image_path  VARCHAR(255)  NOT NULL,
    pest_name   VARCHAR(160)  NOT NULL,
    confidence  FLOAT         NOT NULL,
    damage      TEXT          NULL,
    prevention  TEXT          NULL,
    treatment   TEXT          NULL,
    created_at  DATETIME      DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pest_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX ix_pest_created (created_at),
    INDEX ix_pest_user_created (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 5. crop_recommendations — Random Forest output log
-- ---------------------------------------------------------------------
CREATE TABLE crop_recommendations (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    user_id           INT          NOT NULL,
    soil_type         VARCHAR(60)  NULL,
    temperature       FLOAT        NULL,
    humidity          FLOAT        NULL,
    rainfall          FLOAT        NULL,
    ph                FLOAT        NULL,
    recommended_crop  VARCHAR(80)  NULL,
    confidence        FLOAT        NULL,
    alternatives      TEXT         NULL,               -- JSON array as text
    created_at        DATETIME     DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_croprec_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX ix_croprec_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 6. fertilizer_recommendations
-- ---------------------------------------------------------------------
CREATE TABLE fertilizer_recommendations (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT           NOT NULL,
    crop         VARCHAR(80)   NULL,
    soil_type    VARCHAR(60)   NULL,
    nitrogen     FLOAT         NULL,
    phosphorus   FLOAT         NULL,
    potassium    FLOAT         NULL,
    fertilizer   VARCHAR(120)  NULL,
    confidence   FLOAT         NULL,
    advice       TEXT          NULL,
    created_at   DATETIME      DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_fertrec_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX ix_fertrec_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 7. yield_predictions
-- ---------------------------------------------------------------------
CREATE TABLE yield_predictions (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    user_id          INT          NOT NULL,
    crop             VARCHAR(80)  NULL,
    area             FLOAT        NULL,       -- acres
    rainfall         FLOAT        NULL,       -- mm
    temperature      FLOAT        NULL,       -- deg C
    fertilizer_used  FLOAT        NULL,       -- kg/acre
    predicted_yield  FLOAT        NULL,       -- tonnes (total)
    yield_per_acre   FLOAT        NULL,       -- tonnes/acre
    created_at       DATETIME     DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_yield_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX ix_yield_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 8. market_prices — APMC mandi rates (₹ per quintal)
-- ---------------------------------------------------------------------
CREATE TABLE market_prices (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    state        VARCHAR(80)   NOT NULL,
    district     VARCHAR(80)   NOT NULL,
    market       VARCHAR(120)  NULL,
    crop         VARCHAR(80)   NOT NULL,
    variety      VARCHAR(80)   NULL,
    min_price    FLOAT         NOT NULL,
    max_price    FLOAT         NOT NULL,
    modal_price  FLOAT         NOT NULL,
    price_date   DATE          NOT NULL,
    created_at   DATETIME      DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_prices_state (state),
    INDEX ix_prices_district (district),
    INDEX ix_prices_crop (crop),
    INDEX ix_prices_date (price_date),
    INDEX ix_prices_lookup (state, district, crop, price_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 9. government_schemes
-- ---------------------------------------------------------------------
CREATE TABLE government_schemes (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    name                VARCHAR(200)  NOT NULL,
    scheme_type         VARCHAR(20)   DEFAULT 'central',   -- central | state
    state               VARCHAR(80)   NULL,                -- NULL for central
    description         TEXT          NULL,
    eligibility         TEXT          NULL,
    benefits            TEXT          NULL,
    documents           TEXT          NULL,
    application_process TEXT          NULL,
    website             VARCHAR(255)  NULL,
    is_active           BOOLEAN       DEFAULT TRUE,
    created_at          DATETIME      DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_schemes_type (scheme_type),
    INDEX ix_schemes_state (state)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 10. soil_information
-- ---------------------------------------------------------------------
CREATE TABLE soil_information (
    id                        INT AUTO_INCREMENT PRIMARY KEY,
    soil_type                 VARCHAR(60)   NOT NULL,
    description               TEXT          NULL,
    nutrients                 TEXT          NULL,
    advantages                TEXT          NULL,
    limitations               TEXT          NULL,
    suitable_crops            TEXT          NULL,
    fertilizer_recommendation TEXT          NULL,
    irrigation_recommendation TEXT          NULL,
    regions                   TEXT          NULL,
    image                     VARCHAR(255)  NULL,
    CONSTRAINT uq_soil_type UNIQUE (soil_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 11. crop_calendar — state + crop sowing/harvest schedule
-- ---------------------------------------------------------------------
CREATE TABLE crop_calendar (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    crop                 VARCHAR(80)   NOT NULL,
    state                VARCHAR(80)   NOT NULL,
    season               VARCHAR(40)   NULL,            -- Kharif | Rabi | Zaid
    sowing_time          VARCHAR(120)  NULL,
    planting_time        VARCHAR(120)  NULL,
    irrigation_schedule  TEXT          NULL,
    fertilizer_schedule  TEXT          NULL,
    harvesting_time      VARCHAR(120)  NULL,
    duration_days        INT           NULL,
    notes                TEXT          NULL,
    INDEX ix_calendar_crop (crop),
    INDEX ix_calendar_state (state),
    INDEX ix_calendar_lookup (state, crop, season)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 12. weather_logs — OpenWeatherMap snapshots (user_id nullable)
-- ---------------------------------------------------------------------
CREATE TABLE weather_logs (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    user_id           INT           NULL,
    city              VARCHAR(120)  NULL,
    latitude          FLOAT         NULL,
    longitude         FLOAT         NULL,
    temperature       FLOAT         NULL,
    humidity          FLOAT         NULL,
    wind_speed        FLOAT         NULL,
    pressure          FLOAT         NULL,
    rain_probability  FLOAT         NULL,
    `condition`       VARCHAR(120)  NULL,
    recorded_at       DATETIME      DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_weather_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX ix_weather_recorded (recorded_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 13. chatbot_history
-- ---------------------------------------------------------------------
CREATE TABLE chatbot_history (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT          NOT NULL,
    message     TEXT         NOT NULL,
    response    TEXT         NOT NULL,
    intent      VARCHAR(60)  NULL,
    language    VARCHAR(5)   DEFAULT 'en',
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_chat_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX ix_chat_created (created_at),
    INDEX ix_chat_intent (intent)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 14. notifications
-- ---------------------------------------------------------------------
CREATE TABLE notifications (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT           NOT NULL,
    title       VARCHAR(200)  NOT NULL,
    body        TEXT          NULL,
    category    VARCHAR(40)   DEFAULT 'general',   -- weather | scheme | price | general
    severity    VARCHAR(20)   DEFAULT 'info',      -- info | warning | danger
    is_read     BOOLEAN       DEFAULT FALSE,
    created_at  DATETIME      DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_notif_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX ix_notif_read (is_read),
    INDEX ix_notif_created (created_at),
    INDEX ix_notif_user_read (user_id, is_read)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
--  SEED DATA
--  The application also seeds these tables automatically on first boot
--  (utils/seed_data.py). The inserts below let you provision a database
--  without running Python, e.g. in CI or a managed MySQL instance.
-- =====================================================================

-- Demo admin — password is Admin@1234 (werkzeug pbkdf2:sha256 hash).
-- Change it immediately in production.
INSERT INTO users (name, email, phone, password_hash, role, is_active) VALUES
('Platform Admin', 'admin@smartfarmer.in', '9000000001',
 'scrypt:32768:8:1$PLACEHOLDER$replace-by-running-python-seed', 'admin', TRUE);

-- Soil information -----------------------------------------------------
INSERT INTO soil_information
    (soil_type, description, nutrients, advantages, limitations, suitable_crops,
     fertilizer_recommendation, irrigation_recommendation, regions)
VALUES
('Alluvial',
 'Deposited by the Indus, Ganga and Brahmaputra river systems; the most fertile and most widely cultivated soil in India, covering roughly 40% of the land area.',
 'Rich in potash and lime; moderate nitrogen; often low in phosphorus and organic matter.',
 'High fertility, excellent water retention, easy to till, supports two to three crops a year.',
 'Nitrogen and phosphorus deficient in older (bangar) tracts; prone to waterlogging in low-lying areas.',
 'Rice, Wheat, Sugarcane, Maize, Pulses, Oilseeds, Banana',
 'Apply 120:60:40 NPK kg/ha for cereals. Add 5 t/ha farmyard manure before sowing to correct organic carbon.',
 'Irrigate every 10-12 days for wheat, keep 5 cm standing water for transplanted rice.',
 'Punjab, Haryana, Uttar Pradesh, Bihar, West Bengal, Assam'),
('Black',
 'Also called regur or black cotton soil; formed from Deccan lava. Swells when wet, cracks deeply when dry — a natural self-ploughing behaviour.',
 'High in calcium carbonate, magnesium, potash and lime; low in nitrogen, phosphorus and organic matter.',
 'Outstanding moisture retention, ideal for rain-fed cotton, high clay content holds nutrients well.',
 'Sticky and hard to work when wet, develops wide cracks in summer, poor drainage.',
 'Cotton, Soybean, Chickpea, Sugarcane, Sorghum, Sunflower',
 'Apply 100:50:50 NPK kg/ha. Gypsum at 250 kg/ha improves structure on sodic patches.',
 'Fewer but heavier irrigations; avoid irrigating when the soil is saturated to prevent puddling.',
 'Maharashtra, Madhya Pradesh, Gujarat, Telangana, Karnataka'),
('Red',
 'Formed from weathered crystalline and metamorphic rock; the red colour comes from iron oxide diffusion.',
 'Low in nitrogen, phosphorus, humus and lime; fair potash content.',
 'Well drained, easy to plough, responds strongly to irrigation and fertiliser.',
 'Low fertility and moisture-holding capacity; acidic in high-rainfall pockets.',
 'Groundnut, Millets, Pulses, Cotton, Tobacco, Potato',
 'Apply 80:40:40 NPK kg/ha along with 10 t/ha compost. Lime at 2 t/ha where pH is below 5.5.',
 'Frequent light irrigations; drip irrigation gives the best water-use efficiency.',
 'Tamil Nadu, Karnataka, Andhra Pradesh, Odisha, Chhattisgarh'),
('Laterite',
 'Formed by intense leaching in high-rainfall tropical regions; hardens irreversibly on exposure to air.',
 'Rich in iron and aluminium oxides; very poor in nitrogen, phosphate, potash, lime and organic matter.',
 'Excellent drainage, ideal for plantation crops, blocks cut from it are used as building material.',
 'Highly acidic, severely leached, low fertility without heavy amendment.',
 'Tea, Coffee, Cashew, Rubber, Coconut, Tapioca, Millets',
 'Heavy organic manuring at 15 t/ha plus 100:50:100 NPK kg/ha. Lime at 3 t/ha to raise pH.',
 'Frequent irrigation is essential; mulch heavily to reduce evaporation loss.',
 'Kerala, Karnataka coast, Maharashtra Konkan, Odisha, Assam'),
('Loamy',
 'A balanced mixture of sand, silt and clay — widely considered the ideal agricultural soil.',
 'Well balanced NPK with good organic matter and active microbial life.',
 'Ideal drainage plus retention, easy to work in every season, suits nearly all crops.',
 'Needs regular organic replenishment to stay in balance; can compact under heavy machinery.',
 'Wheat, Maize, Vegetables, Sugarcane, Pulses, Tomato, Onion',
 'Apply 100:50:50 NPK kg/ha with 8 t/ha farmyard manure. Follow the Soil Health Card dose.',
 'Irrigate at 50% depletion of available soil moisture, roughly every 8-10 days.',
 'Uttar Pradesh, Punjab, Haryana, parts of Maharashtra and Karnataka'),
('Sandy',
 'Coarse-textured soil with large particles and very wide pore spaces.',
 'Very low in nutrients and organic carbon; nutrients leach away quickly.',
 'Warms up early in the season, never waterlogs, very easy to cultivate.',
 'Extremely poor water and nutrient retention; needs frequent irrigation and split fertiliser doses.',
 'Groundnut, Millets, Watermelon, Potato, Carrot, Castor',
 'Split nitrogen into 3-4 doses. Apply 15 t/ha organic manure to build water-holding capacity.',
 'Short, frequent irrigations. Drip or sprinkler systems are strongly recommended.',
 'Rajasthan, Gujarat, parts of Haryana and coastal Andhra Pradesh'),
('Clay',
 'Fine-textured soil with more than 40% clay particles; very slow infiltration.',
 'High in potassium and calcium; nitrogen availability limited by poor aeration.',
 'Superb nutrient and water retention, excellent for puddled rice.',
 'Poor aeration and drainage, hard to till, cracks on drying, prone to waterlogging.',
 'Rice, Jute, Sugarcane, Wheat (with drainage), Vegetables on raised beds',
 'Apply 120:60:60 NPK kg/ha. Gypsum plus organic matter improves structure and infiltration.',
 'Long-interval, heavy irrigations. Provide surface drainage during the monsoon.',
 'West Bengal, Bihar, coastal Odisha, Kerala backwaters'),
('Desert',
 'Arid, sandy to sandy-loam soil with high soluble-salt content and very low rainfall.',
 'Very low nitrogen and organic matter; high phosphate and calcium carbonate.',
 'Highly productive when irrigated — the Indira Gandhi canal command is proof.',
 'Salinity, wind erosion, extreme moisture stress.',
 'Bajra (Pearl millet), Guar, Mustard, Barley, Date palm, Moth bean',
 'Apply 60:40:20 NPK kg/ha with heavy organic matter. Use gypsum on saline-sodic patches.',
 'Drip irrigation is essential. Shelterbelts and mulching cut evaporation losses sharply.',
 'Rajasthan, north Gujarat, southern Haryana and Punjab');

-- Government schemes (a representative subset; the Python seeder loads more)
INSERT INTO government_schemes
    (name, scheme_type, state, description, eligibility, benefits, documents,
     application_process, website, is_active)
VALUES
('PM-KISAN Samman Nidhi', 'central', NULL,
 'Income support of ₹6,000 per year paid in three equal instalments directly into the bank accounts of eligible landholding farmer families.',
 'All landholding farmer families. Institutional landholders, income-tax payers and serving or retired government employees above Group D are excluded.',
 '₹6,000 per year in three instalments of ₹2,000, credited by direct benefit transfer.',
 'Aadhaar card, land ownership records, bank passbook, mobile number',
 'Register at pmkisan.gov.in or through the nearest Common Service Centre; verification is done by the village revenue officer.',
 'https://pmkisan.gov.in', TRUE),
('Pradhan Mantri Fasal Bima Yojana (PMFBY)', 'central', NULL,
 'Comprehensive crop insurance against non-preventable natural risks from pre-sowing to post-harvest.',
 'All farmers growing notified crops in notified areas, including sharecroppers and tenant farmers.',
 'Farmer premium capped at 2% for Kharif, 1.5% for Rabi and 5% for commercial or horticultural crops; the balance is subsidised.',
 'Aadhaar card, land records or tenancy agreement, sowing certificate, bank passbook',
 'Apply through your bank, a Common Service Centre or the PMFBY portal before the notified cut-off date for the season.',
 'https://pmfby.gov.in', TRUE),
('Kisan Credit Card (KCC)', 'central', NULL,
 'Short-term institutional credit for crop production, post-harvest expenses and allied activities at a concessional interest rate.',
 'All farmers including tenant farmers, oral lessees, sharecroppers, and self-help or joint-liability groups.',
 'Credit up to ₹3 lakh at 7% interest, reduced to 4% effective with the prompt-repayment incentive. Includes accident insurance cover.',
 'Application form, identity and address proof, land documents, passport photographs',
 'Apply at any commercial bank, regional rural bank or cooperative bank branch, or online via the PM-KISAN portal KCC link.',
 'https://www.myscheme.gov.in/schemes/kcc', TRUE),
('Soil Health Card Scheme', 'central', NULL,
 'Provides every farmer with a soil health card carrying crop-wise nutrient recommendations based on laboratory soil testing.',
 'All farmers holding agricultural land.',
 'Free soil testing for 12 parameters and a customised fertiliser recommendation issued once every two years.',
 'Land records, Aadhaar card',
 'Submit a soil sample at the nearest soil-testing laboratory or through the village agriculture officer.',
 'https://soilhealth.dac.gov.in', TRUE),
('Pradhan Mantri Krishi Sinchayee Yojana (PMKSY)', 'central', NULL,
 'Expands irrigation coverage ("Har Khet Ko Pani") and improves water-use efficiency through micro-irrigation ("Per Drop More Crop").',
 'All categories of farmers; small and marginal farmers receive a higher subsidy share.',
 '55% subsidy for small and marginal farmers and 45% for other farmers on drip and sprinkler systems.',
 'Land records, Aadhaar card, bank passbook, quotation from a registered supplier',
 'Apply through the state horticulture or agriculture department, or on the PMKSY state portal.',
 'https://pmksy.gov.in', TRUE),
('Rythu Bandhu', 'state', 'Telangana',
 'Investment support scheme paying land-owning farmers a per-acre grant every season to cover input costs.',
 'All land-owning farmers in Telangana with a valid pattadar passbook.',
 '₹5,000 per acre per season (₹10,000 per acre per year) credited directly to the bank account.',
 'Pattadar passbook, Aadhaar card, bank passbook',
 'Automatic enrolment through the land-records database; verify your details at the local mandal revenue office.',
 'https://rythubandhu.telangana.gov.in', TRUE),
('Mukhyamantri Krishi Ashirwad Yojana', 'state', 'Jharkhand',
 'Grant-in-aid to small and marginal farmers to meet crop input costs at the start of the Kharif season.',
 'Small and marginal farmers holding up to 5 acres of cultivable land in Jharkhand.',
 '₹5,000 per acre per year, up to a maximum of 5 acres.',
 'Land records, Aadhaar card, bank passbook',
 'Apply through the block agriculture office or the state agriculture department portal.',
 'https://jrfry.jharkhand.gov.in', TRUE),
('Bhavantar Bhugtan Yojana', 'state', 'Madhya Pradesh',
 'Price-deficiency payment scheme that pays farmers the gap between the minimum support price and the modal mandi sale price.',
 'Registered farmers of Madhya Pradesh selling notified crops in a notified mandi.',
 'Direct transfer of the difference between MSP and the average modal price for the notified period.',
 'Registration slip, mandi sale receipt, Aadhaar card, bank passbook',
 'Register on the e-Uparjan portal before the notified date, then sell at a notified mandi.',
 'https://mpeuparjan.nic.in', TRUE);

-- =====================================================================
--  Useful reporting views (optional but handy for the admin panel)
-- =====================================================================
CREATE OR REPLACE VIEW v_user_activity AS
SELECT u.id, u.name, u.email, u.created_at, u.last_login,
       (SELECT COUNT(*) FROM disease_predictions d WHERE d.user_id = u.id) AS disease_scans,
       (SELECT COUNT(*) FROM pest_predictions p    WHERE p.user_id = u.id) AS pest_scans,
       (SELECT COUNT(*) FROM chatbot_history c     WHERE c.user_id = u.id) AS chat_messages
FROM users u;

CREATE OR REPLACE VIEW v_latest_prices AS
SELECT state, district, market, crop, min_price, max_price, modal_price, price_date
FROM market_prices mp
WHERE price_date = (SELECT MAX(price_date) FROM market_prices m2
                    WHERE m2.state = mp.state AND m2.district = mp.district
                      AND m2.crop = mp.crop);

-- =====================================================================
--  Application database user (adjust host and password for your setup)
-- =====================================================================
-- CREATE USER 'sfa_app'@'%' IDENTIFIED BY 'change-this-password';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON smart_farmer.* TO 'sfa_app'@'%';
-- FLUSH PRIVILEGES;
