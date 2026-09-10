"""
Idempotent database seeding.

Runs on every boot but only inserts rows that do not exist yet, so the app is
usable immediately after `flask run` (or a fresh Render deploy) without a
manual data import step.
"""
import random
from datetime import date, timedelta

from flask import current_app

from extensions import db
from models.models import (CropCalendar, GovernmentScheme, MarketPrice,
                           Profile, SoilInformation, User)

# ---------------------------------------------------------------------------
SOILS = [
    dict(soil_type="Alluvial",
         description="Deposited by the Himalayan river systems, alluvial soil covers the "
                     "Indo-Gangetic plains and is India's most productive soil. Texture "
                     "ranges from sandy loam to clay loam with a pH of 6.5–8.0.",
         nutrients="Rich in potash, phosphoric acid and lime; deficient in nitrogen and "
                   "organic matter.",
         advantages="High fertility, excellent water retention, easy to till, supports "
                    "intensive double cropping.",
         limitations="Low nitrogen and humus; newer khadar tracts flood during monsoon; "
                     "prone to nutrient mining under continuous rice–wheat rotation.",
         suitable_crops="Rice, Wheat, Sugarcane, Maize, Pulses, Oilseeds, Potato, Jute",
         fertilizer_recommendation="Apply 50 kg DAP + 20 kg MOP per acre basally with 45 kg "
                                   "urea in two splits. Add 2 t/acre FYM and include a green "
                                   "manure crop (dhaincha) once a year.",
         irrigation_recommendation="4–6 irrigations for wheat at CRI, tillering, jointing, "
                                   "flowering and grain filling. Use laser levelling and "
                                   "alternate wetting-and-drying in paddy to save water.",
         regions="Punjab, Haryana, Uttar Pradesh, Bihar, West Bengal, Assam"),
    dict(soil_type="Black",
         description="Also called regur or black cotton soil, formed from weathered Deccan "
                     "lava. Clay-rich, swells when wet and cracks deeply on drying, giving "
                     "self-ploughing behaviour. pH 7.5–8.5.",
         nutrients="High in calcium carbonate, magnesium, potash and lime; poor in nitrogen, "
                   "phosphorus and organic matter.",
         advantages="Outstanding moisture retention makes rain-fed cropping viable; ideal "
                    "for cotton and pulses.",
         limitations="Sticky and hard to work when wet, cracks widely when dry, poor "
                     "drainage and a risk of waterlogging.",
         suitable_crops="Cotton, Soybean, Sorghum, Pigeon Pea, Chickpea, Sunflower, Wheat",
         fertilizer_recommendation="Use 40 kg DAP + 25 kg MOP per acre; apply zinc sulphate "
                                   "10 kg/acre once every three years and gypsum 100 kg/acre "
                                   "for oilseeds.",
         irrigation_recommendation="Avoid over-irrigation. Broad bed and furrow layout with "
                                   "a protective irrigation at flowering and boll formation "
                                   "gives the best response.",
         regions="Maharashtra, Madhya Pradesh, Gujarat, Telangana, Karnataka"),
    dict(soil_type="Red",
         description="Formed by weathering of ancient crystalline and metamorphic rock. The "
                     "red colour comes from iron oxide. Light textured and porous with pH "
                     "5.5–6.8.",
         nutrients="Deficient in nitrogen, phosphorus, humus and lime; moderate potash.",
         advantages="Well drained and easy to plough; responds strongly to irrigation and "
                    "manuring.",
         limitations="Low fertility and water-holding capacity; erodes easily on slopes.",
         suitable_crops="Groundnut, Ragi, Millets, Pulses, Potato, Tobacco, Oilseeds",
         fertilizer_recommendation="Apply 4 t/acre FYM plus 45 kg urea, 50 kg SSP and 25 kg "
                                   "MOP per acre. Correct acidity with 2 q/acre lime when "
                                   "pH falls below 5.5.",
         irrigation_recommendation="Frequent light irrigations suit the low retention. Drip "
                                   "with mulching is highly effective for horticulture.",
         regions="Tamil Nadu, Karnataka, Andhra Pradesh, Odisha, Chhattisgarh"),
    dict(soil_type="Laterite",
         description="Formed under high rainfall with alternating wet and dry seasons through "
                     "intense leaching. Rich in iron and aluminium oxides, acidic with pH "
                     "5.0–6.0.",
         nutrients="Very low nitrogen, phosphorus, potash, calcium and organic matter; high "
                   "iron and aluminium.",
         advantages="Suits plantation crops; hardens into building material; good drainage.",
         limitations="Strongly acidic, low fertility, heavy leaching losses, needs constant "
                     "organic replenishment.",
         suitable_crops="Tea, Coffee, Rubber, Cashew, Coconut, Areca nut, Tapioca",
         fertilizer_recommendation="Apply lime 2–4 q/acre to correct acidity, 5 t/acre "
                                   "compost, plus split doses of NPK 10-26-26 at 50 kg/acre.",
         irrigation_recommendation="Mulch heavily and use drip irrigation; contour bunding "
                                   "prevents nutrient run-off on slopes.",
         regions="Kerala, Karnataka coast, Konkan, Odisha, Meghalaya"),
    dict(soil_type="Sandy",
         description="Coarse textured soil with over 70% sand, very high infiltration and low "
                     "capillary rise. Common in arid western India. pH 7.0–8.5.",
         nutrients="Very low in nitrogen, organic carbon and micronutrients.",
         advantages="Easy tillage, warms up quickly in spring, excellent aeration for root "
                    "and tuber crops.",
         limitations="Extremely poor water and nutrient retention; wind erosion and rapid "
                     "leaching of applied fertiliser.",
         suitable_crops="Bajra, Guar, Moth Bean, Watermelon, Groundnut, Castor, Cumin",
         fertilizer_recommendation="Split nitrogen into 3–4 doses to cut leaching, use "
                                   "vermicompost 2 t/acre and coated urea; foliar sprays "
                                   "give quicker response than soil application.",
         irrigation_recommendation="Short frequent irrigations or drip/sprinkler only. Add "
                                   "organic mulch and windbreak rows to reduce evaporation.",
         regions="Rajasthan, north Gujarat, southern Haryana, parts of Punjab"),
    dict(soil_type="Clayey",
         description="Fine textured soil with more than 40% clay. Sticky when wet, hard when "
                     "dry, with slow infiltration and high nutrient holding capacity.",
         nutrients="Good potash and calcium reserves; nitrogen availability limited by poor "
                   "aeration.",
         advantages="Excellent nutrient and water retention; ideal for puddled paddy.",
         limitations="Poor drainage and aeration, difficult tillage, cracks on drying, "
                     "waterlogging risk.",
         suitable_crops="Rice, Jute, Sugarcane, Banana, Cabbage, Cauliflower",
         fertilizer_recommendation="Apply 45 kg urea in three splits, 50 kg DAP basal and "
                                   "20 kg MOP per acre; incorporate 2 t/acre FYM to improve "
                                   "structure.",
         irrigation_recommendation="Maintain 3–5 cm standing water in paddy and provide "
                                   "surface drainage channels during heavy rain.",
         regions="West Bengal, coastal Andhra Pradesh, Kerala backwaters, Assam"),
    dict(soil_type="Loamy",
         description="A balanced mix of sand, silt and clay, widely considered the ideal "
                     "agricultural soil. Friable structure with pH 6.0–7.5.",
         nutrients="Well balanced N-P-K with good organic carbon when managed properly.",
         advantages="Ideal drainage plus retention, easy tillage, supports almost every crop.",
         limitations="Can lose structure under continuous tillage; needs regular organic "
                     "matter to stay productive.",
         suitable_crops="Wheat, Maize, Vegetables, Sugarcane, Cotton, Pulses, Fruits",
         fertilizer_recommendation="Follow soil-test based NPK; typically 40 kg urea, 50 kg "
                                   "DAP and 25 kg MOP per acre plus 2 t/acre compost.",
         irrigation_recommendation="Irrigate at 50% depletion of available soil moisture; "
                                   "drip irrigation raises water productivity by 40%.",
         regions="Widely distributed across the Deccan plateau and river valleys"),
    dict(soil_type="Saline",
         description="Soils with excess soluble salts (EC above 4 dS/m) or exchangeable "
                     "sodium, often called usar or reh land. Common in arid irrigated tracts.",
         nutrients="Nutrient uptake is blocked by osmotic stress despite adequate reserves; "
                   "zinc and iron deficiency common.",
         advantages="Reclaimable with gypsum and drainage; supports salt-tolerant varieties "
                    "and aquaculture on the fringe.",
         limitations="Poor germination, stunted growth, crusting, and severe yield loss "
                     "without reclamation.",
         suitable_crops="Barley, Salt-tolerant rice (CSR-36), Cotton, Mustard, Date palm",
         fertilizer_recommendation="Apply gypsum at 2–5 t/acre based on the gypsum "
                                   "requirement test, add 25% extra nitrogen, and use "
                                   "pressmud or green manure to build organic matter.",
         irrigation_recommendation="Use good-quality water with heavy leaching irrigations, "
                                   "install subsurface drainage, and irrigate frequently to "
                                   "keep salts below the root zone.",
         regions="Rajasthan, Haryana, Punjab, Gujarat coast, Uttar Pradesh usar belt"),
]

CENTRAL_SCHEMES = [
    dict(name="PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
         description="Central income-support scheme paying ₹6,000 per year to all landholding "
                     "farmer families in three equal instalments of ₹2,000, transferred "
                     "directly to the beneficiary's Aadhaar-linked bank account.",
         eligibility="All landholding farmer families with cultivable land in their name. "
                     "Institutional landholders, income-tax payers, serving or retired "
                     "government employees above Group D and professionals are excluded.",
         benefits="₹6,000 per year (₹2,000 every four months) via direct benefit transfer.",
         documents="Aadhaar card, land ownership records (khatauni/khasra), bank passbook, "
                   "mobile number, citizenship proof.",
         application_process="Register at pmkisan.gov.in under 'New Farmer Registration' or "
                             "through the nearest Common Service Centre / village revenue "
                             "officer. Complete e-KYC and land seeding to receive instalments.",
         website="https://pmkisan.gov.in"),
    dict(name="Pradhan Mantri Fasal Bima Yojana (PMFBY)",
         description="National crop insurance scheme covering yield losses from non-preventable "
                     "natural risks, from pre-sowing through post-harvest.",
         eligibility="All farmers growing notified crops in notified areas, including "
                     "sharecroppers and tenant farmers with valid land documents.",
         benefits="Premium capped at 2% of sum insured for Kharif, 1.5% for Rabi and 5% for "
                  "commercial or horticultural crops; the balance is subsidised by government.",
         documents="Aadhaar, bank passbook, land records or tenancy agreement, sowing "
                   "certificate, KCC details if loanee.",
         application_process="Apply through your bank or CSC before the cut-off date, or "
                             "self-register on pmfby.gov.in. Report crop loss within 72 hours "
                             "on the Crop Insurance app or the insurer's toll-free number.",
         website="https://pmfby.gov.in"),
    dict(name="Kisan Credit Card (KCC)",
         description="Short-term institutional credit for crop production, post-harvest "
                     "expenses, farm maintenance and allied activities such as dairy and "
                     "fisheries.",
         eligibility="Owner cultivators, tenant farmers, oral lessees, sharecroppers, and "
                     "self-help or joint liability groups engaged in agriculture.",
         benefits="Credit up to ₹3 lakh at 7% interest with a 3% prompt-repayment incentive, "
                  "giving an effective 4% rate; collateral-free up to ₹1.6 lakh; includes "
                  "personal accident insurance.",
         documents="Application form, identity and address proof, land documents, passport "
                   "photographs.",
         application_process="Apply at any commercial bank, RRB or cooperative bank branch, "
                             "or online through the PM-KISAN portal's KCC link. Sanction is "
                             "mandated within 14 days of a complete application.",
         website="https://www.myscheme.gov.in/schemes/kcc"),
    dict(name="Soil Health Card Scheme",
         description="Provides every farm holding with a soil health card carrying test "
                     "results for 12 parameters and crop-wise fertiliser recommendations, "
                     "reissued every three years.",
         eligibility="All farmers with agricultural land holdings.",
         benefits="Free soil testing and a customised nutrient plan that typically cuts "
                  "fertiliser spending by 8–10% while raising yield.",
         documents="Aadhaar, land record details, mobile number.",
         application_process="Contact your village agriculture officer or KVK to collect a "
                             "soil sample, or register on soilhealth.dac.gov.in. Cards are "
                             "delivered digitally and in print.",
         website="https://soilhealth.dac.gov.in"),
    dict(name="PM Krishi Sinchayee Yojana — Per Drop More Crop",
         description="Micro-irrigation mission promoting drip and sprinkler systems to raise "
                     "water-use efficiency and expand assured irrigation coverage.",
         eligibility="All categories of farmers; higher subsidy for small, marginal, SC/ST "
                     "and women farmers.",
         benefits="55% subsidy for small and marginal farmers and 45% for other farmers on "
                  "the cost of drip or sprinkler systems, with additional state top-ups.",
         documents="Aadhaar, land records, bank details, quotation from an empanelled "
                   "supplier, water source certificate.",
         application_process="Apply through the state horticulture or agriculture department "
                             "portal, get the site inspected, install through an empanelled "
                             "vendor, and receive subsidy by DBT after verification.",
         website="https://pmksy.gov.in"),
    dict(name="e-NAM (National Agriculture Market)",
         description="Pan-India electronic trading portal networking APMC mandis into a "
                     "unified national market for agricultural commodities.",
         eligibility="Farmers, farmer producer organisations and licensed traders registered "
                     "with a participating mandi.",
         benefits="Transparent online price discovery, wider buyer access, assaying "
                  "facilities and direct online payment to the farmer's account.",
         documents="Aadhaar, bank account details, mobile number, mandi registration.",
         application_process="Register free on enam.gov.in or the e-NAM mobile app, or "
                             "through the help desk at any integrated mandi.",
         website="https://www.enam.gov.in"),
    dict(name="Paramparagat Krishi Vikas Yojana (PKVY)",
         description="Cluster-based organic farming programme supporting input costs, "
                     "certification and marketing for chemical-free production.",
         eligibility="Farmer groups of at least 20 farmers covering 20 hectares in a cluster.",
         benefits="₹31,500 per hectare over three years, including ₹15,000 for organic "
                  "inputs, plus free participatory guarantee system certification.",
         documents="Aadhaar, land records, group formation resolution, bank account details.",
         application_process="Form a cluster with the help of the district agriculture "
                             "officer and apply through the state organic mission.",
         website="https://pgsindia-ncof.gov.in"),
    dict(name="Agriculture Infrastructure Fund (AIF)",
         description="₹1 lakh crore financing facility for post-harvest management "
                     "infrastructure — warehouses, cold chains, grading units and primary "
                     "processing centres.",
         eligibility="Farmers, FPOs, primary agricultural credit societies, self-help "
                     "groups, agri-entrepreneurs and startups.",
         benefits="3% annual interest subvention on loans up to ₹2 crore for seven years, "
                  "plus credit guarantee coverage under CGTMSE.",
         documents="Project report, land documents, KYC, entity registration, bank details.",
         application_process="Apply on agriinfra.dac.gov.in, select a lending bank, and "
                             "complete appraisal; the portal tracks sanction and subvention.",
         website="https://agriinfra.dac.gov.in"),
]

STATE_SCHEMES = [
    dict(name="Bihar Diesel Anudan Yojana", state="Bihar",
         description="Diesel subsidy for irrigating standing crops during deficient rainfall "
                     "in the Kharif season.",
         eligibility="Resident farmers of Bihar with registered farmer ID; owner cultivators "
                     "and tenant farmers both eligible up to 8 acres.",
         benefits="₹75 per litre subsidy amounting to roughly ₹750 per acre per irrigation, "
                  "for up to three irrigations.",
         documents="Farmer registration number, Aadhaar, diesel purchase receipt with the "
                   "registration number written on it, land or tenancy proof.",
         application_process="Apply on dbtagriculture.bihar.gov.in with the diesel receipt "
                             "within 30 days of purchase.",
         website="https://dbtagriculture.bihar.gov.in"),
    dict(name="Mukhyamantri Krishi Ashirwad Yojana", state="Bihar",
         description="State income support supplementing central transfers for small and "
                     "marginal farmers.",
         eligibility="Small and marginal farmers registered on the Bihar DBT agriculture "
                     "portal with verified land records.",
         benefits="Direct benefit transfer support per acre subject to state notification.",
         documents="Aadhaar, farmer registration ID, land records, bank passbook.",
         application_process="Register on the Bihar DBT agriculture portal and complete "
                             "block-level verification.",
         website="https://dbtagriculture.bihar.gov.in"),
    dict(name="Mahatma Jyotirao Phule Shetkari Karjmukti Yojana", state="Maharashtra",
         description="Crop-loan waiver and incentive scheme for regular repaying farmers in "
                     "Maharashtra.",
         eligibility="Farmers with outstanding short-term crop loans within the notified "
                     "cut-off dates, plus an incentive for those who repaid on time.",
         benefits="Loan waiver up to ₹2 lakh and an incentive of up to ₹50,000 for regular "
                  "repayers.",
         documents="Aadhaar, loan account details, bank passbook, land records.",
         application_process="Verification is done through the lending bank; farmers "
                             "authenticate at the bank or CSC using Aadhaar biometrics.",
         website="https://krishi.maharashtra.gov.in"),
    dict(name="Raitha Siri (Millet Incentive)", state="Karnataka",
         description="Incentive to promote cultivation of nutri-cereals and millets under "
                     "rain-fed conditions.",
         eligibility="Karnataka farmers cultivating notified millets with FRUITS ID "
                     "registration.",
         benefits="₹10,000 per hectare incentive transferred directly to the bank account.",
         documents="FRUITS ID, Aadhaar, RTC (pahani) land record, bank passbook.",
         application_process="Apply through the Raitha Samparka Kendra in your hobli during "
                             "the notified window.",
         website="https://raitamitra.karnataka.gov.in"),
    dict(name="Rythu Bharosa", state="Telangana",
         description="State investment support paid per acre per season to farmers for crop "
                     "inputs.",
         eligibility="Farmers with recorded agricultural landholdings in the Dharani portal.",
         benefits="Per-acre investment support each season, credited before the sowing "
                  "window.",
         documents="Aadhaar, Dharani land record, bank account details.",
         application_process="Automatic based on Dharani land records; grievances are "
                             "handled at the mandal agriculture office.",
         website="https://rythubandhu.telangana.gov.in"),
    dict(name="Pani Bachao Paisa Kamao", state="Punjab",
         description="Direct benefit transfer for electricity saved by farmers who reduce "
                     "groundwater pumping.",
         eligibility="Agricultural tubewell connection holders in pilot feeders.",
         benefits="₹4 per unit of electricity saved against the allotted quota, paid "
                  "directly to the farmer.",
         documents="Electricity connection details, Aadhaar, bank passbook.",
         application_process="Enrol through PSPCL at the feeder level; consumption is "
                             "metered and the incentive is credited monthly.",
         website="https://www.pspcl.in"),
    dict(name="Uzhavar Sandhai Farmer Market Support", state="Tamil Nadu",
         description="Farmer-to-consumer market network giving growers free selling space "
                     "and daily price boards without intermediaries.",
         eligibility="Farmers of Tamil Nadu producing vegetables, fruits and flowers, "
                     "verified by the local agriculture office.",
         benefits="Free stall allotment, weighing facility, transport support and daily "
                  "reference price display.",
         documents="Farmer ID card, Aadhaar, land record or cultivation certificate.",
         application_process="Register at the nearest Uzhavar Sandhai office to receive a "
                             "farmer identity card and stall allotment.",
         website="https://www.tn.gov.in/scheme/data_view/6822"),
]

CALENDAR_TEMPLATES = [
    dict(crop="Rice", season="Kharif", duration_days=135,
         sowing_time="Nursery: last week of May to mid-June",
         planting_time="Transplant 25–30 day old seedlings from late June to mid-July",
         irrigation_schedule="Keep 2–3 cm standing water from transplanting to panicle "
                             "initiation; practise alternate wetting and drying in between; "
                             "drain the field 10 days before harvest.",
         fertilizer_schedule="Basal: 50 kg DAP + 25 kg MOP per acre. Top dress 20 kg urea at "
                             "tillering (20–25 DAT) and 20 kg urea at panicle initiation "
                             "(45–50 DAT). Apply 10 kg/acre zinc sulphate if leaves show "
                             "bronzing.",
         harvesting_time="Mid-October to early November when 80% grains turn straw coloured",
         notes="Line transplanting at 20 × 15 cm and a weed-free first 40 days give the "
               "highest response."),
    dict(crop="Wheat", season="Rabi", duration_days=140,
         sowing_time="1 November to 25 November (timely sown)",
         planting_time="Seed rate 40 kg/acre at 20–22 cm row spacing, 5 cm depth",
         irrigation_schedule="Six irrigations at crown root initiation (21 DAS), tillering "
                             "(45 DAS), jointing (65 DAS), flowering (85 DAS), milk (105 DAS) "
                             "and dough stage (120 DAS). CRI irrigation is the most critical.",
         fertilizer_schedule="Basal: 50 kg DAP + 20 kg MOP per acre. Top dress 45 kg urea in "
                             "two equal splits at first and second irrigation.",
         harvesting_time="Late March to mid-April at 20% grain moisture",
         notes="Late sowing after 15 December reduces yield by roughly 1.5% per day."),
    dict(crop="Maize", season="Kharif", duration_days=100,
         sowing_time="Mid-June to first week of July with the onset of monsoon",
         planting_time="60 × 20 cm spacing, seed rate 8 kg/acre, ridge planting preferred",
         irrigation_schedule="Critical at knee-high, tasselling and grain-filling stages. "
                             "Ensure drainage — maize is very sensitive to waterlogging.",
         fertilizer_schedule="Basal: 50 kg DAP + 25 kg MOP. Top dress 30 kg urea at knee-high "
                             "and 30 kg at tasselling per acre.",
         harvesting_time="Late September to mid-October when the black layer forms at the "
                         "kernel base",
         notes="Scout weekly for fall armyworm from the 10th day after emergence."),
    dict(crop="Cotton", season="Kharif", duration_days=180,
         sowing_time="Mid-May (irrigated) to end June (rain-fed)",
         planting_time="Bt hybrids at 90 × 60 cm; refuge rows are mandatory",
         irrigation_schedule="Protective irrigation at squaring, flowering and boll "
                             "development. Drip with fertigation saves 40% water.",
         fertilizer_schedule="Basal: 50 kg DAP + 30 kg MOP. Urea 30 kg at squaring and 30 kg "
                             "at flowering per acre, plus 2 foliar sprays of 2% DAP.",
         harvesting_time="Picking from late November through February in 3–4 rounds",
         notes="Follow the crop window strictly and destroy stubble to break the pink "
               "bollworm cycle."),
    dict(crop="Sugarcane", season="Zaid", duration_days=330,
         sowing_time="Spring planting: February–March; Autumn: September–October",
         planting_time="Three-budded setts in furrows 90 cm apart, 35,000 setts/acre",
         irrigation_schedule="Irrigate every 7–10 days in summer and 15–20 days in winter; "
                             "tillering and grand growth are the critical phases.",
         fertilizer_schedule="112 kg urea, 50 kg DAP and 35 kg MOP per acre split at "
                             "planting, tillering and earthing up.",
         harvesting_time="December to March at peak sucrose content",
         notes="Trash mulching conserves moisture and suppresses weeds."),
    dict(crop="Soybean", season="Kharif", duration_days=100,
         sowing_time="Third week of June to first week of July after 100 mm rainfall",
         planting_time="45 × 5 cm spacing, seed rate 30 kg/acre with rhizobium treatment",
         irrigation_schedule="Mostly rain-fed; a protective irrigation at pod filling raises "
                             "yield significantly. Ensure drainage in black soils.",
         fertilizer_schedule="Basal only: 50 kg DAP + 20 kg MOP + 8 kg sulphur per acre. "
                             "Nitrogen beyond a 10 kg starter dose is not needed.",
         harvesting_time="Late September to mid-October when 95% pods turn brown",
         notes="Broad bed and furrow layout prevents waterlogging losses."),
    dict(crop="Mustard", season="Rabi", duration_days=125,
         sowing_time="Mid-October to first week of November",
         planting_time="30 × 10 cm spacing, seed rate 2 kg/acre at 2–3 cm depth",
         irrigation_schedule="Two irrigations — at pre-flowering (30 DAS) and siliqua "
                             "formation (65 DAS) — are sufficient.",
         fertilizer_schedule="Basal: 40 kg DAP + 15 kg MOP + 8 kg sulphur per acre. Top dress "
                             "25 kg urea at first irrigation.",
         harvesting_time="Mid-February to March when pods turn yellow-brown",
         notes="Sulphur application is essential for oil content; watch for aphids in "
               "January."),
    dict(crop="Chickpea", season="Rabi", duration_days=120,
         sowing_time="Late October to mid-November",
         planting_time="30 × 10 cm spacing, seed rate 30 kg/acre with rhizobium and PSB",
         irrigation_schedule="One irrigation at pre-flowering and one at pod development; "
                             "avoid excess water which causes vegetative growth.",
         fertilizer_schedule="Basal: 40 kg DAP + 8 kg sulphur per acre. Only a 10 kg starter "
                             "dose of urea is needed.",
         harvesting_time="March when leaves turn reddish-brown and pods rattle",
         notes="Install pheromone traps for pod borer at 5/acre from the flowering stage."),
]

CALENDAR_STATES = ["Bihar", "Uttar Pradesh", "Maharashtra", "Punjab", "Karnataka",
                   "Madhya Pradesh", "Tamil Nadu", "West Bengal"]

BASE_PRICES = {
    "Rice": 2183, "Wheat": 2275, "Maize": 2090, "Cotton": 7121, "Soybean": 4892,
    "Groundnut": 6377, "Mustard": 5650, "Chickpea": 5440, "Potato": 1250,
    "Onion": 1800, "Tomato": 1500, "Sugarcane": 340, "Turmeric": 8600, "Chilli": 12500,
}

PRICE_MARKETS = {
    "Bihar": [("Patna", "Patna Bazar Samiti"), ("Aurangabad", "Aurangabad Krishi Bazar"),
              ("Gaya", "Gaya Regulated Market")],
    "Maharashtra": [("Pune", "Pune Market Yard"), ("Nashik", "Lasalgaon APMC"),
                    ("Nagpur", "Kalamna Market")],
    "Punjab": [("Ludhiana", "Ludhiana Grain Market")],
    "Uttar Pradesh": [("Lucknow", "Sitapur Road Mandi"), ("Varanasi", "Pahariya Mandi")],
    "Karnataka": [("Hubballi", "Hubballi APMC")],
    "Telangana": [("Warangal", "Enumamula Market")],
}


# ---------------------------------------------------------------------------
def seed_all():
    """Seed every reference table plus the default admin account."""
    seed_admin()
    seed_soils()
    seed_schemes()
    seed_calendar()
    seed_prices()
    db.session.commit()


def seed_admin():
    email = current_app.config["ADMIN_EMAIL"]
    if User.query.filter_by(email=email).first():
        return
    admin = User(name="Platform Administrator", email=email, role="admin", phone="9000000000")
    admin.set_password(current_app.config["ADMIN_PASSWORD"])
    db.session.add(admin)
    db.session.flush()
    db.session.add(Profile(user_id=admin.id, state="Bihar", district="Patna",
                           preferred_language="en", farm_size=0))
    current_app.logger.info("Seeded admin account %s", email)


def seed_soils():
    if SoilInformation.query.count():
        return
    for row in SOILS:
        db.session.add(SoilInformation(**row))


def seed_schemes():
    if GovernmentScheme.query.count():
        return
    for row in CENTRAL_SCHEMES:
        db.session.add(GovernmentScheme(scheme_type="central", **row))
    for row in STATE_SCHEMES:
        db.session.add(GovernmentScheme(scheme_type="state", **row))


def seed_calendar():
    if CropCalendar.query.count():
        return
    for state in CALENDAR_STATES:
        for tpl in CALENDAR_TEMPLATES:
            db.session.add(CropCalendar(state=state, **tpl))


def seed_prices(days: int = 45):
    """Generate a realistic 45-day mandi price history for the trend charts."""
    if MarketPrice.query.count():
        return
    rng = random.Random(2026)
    today = date.today()
    for state, markets in PRICE_MARKETS.items():
        for district, market in markets:
            for crop, base in BASE_PRICES.items():
                level = base * rng.uniform(0.94, 1.06)
                for d in range(days, 0, -3):
                    day = today - timedelta(days=d)
                    level *= rng.uniform(0.985, 1.016)          # random walk
                    seasonal = 1 + 0.02 * ((d % 30) / 30 - 0.5)  # mild seasonality
                    modal = round(level * seasonal, 2)
                    db.session.add(MarketPrice(
                        state=state, district=district, market=market, crop=crop,
                        variety="Common",
                        min_price=round(modal * rng.uniform(0.88, 0.95), 2),
                        max_price=round(modal * rng.uniform(1.05, 1.14), 2),
                        modal_price=modal, price_date=day))
        db.session.flush()
