"""
Agronomic knowledge base.

Static reference data used by the disease/pest modules, dropdowns and the
chatbot. Kept in Python (not the DB) because it ships with the model classes
and must stay in sync with the CNN label order in ``trained_models/*_labels.json``.
"""

# ---------------------------------------------------------------------------
# Geography
# ---------------------------------------------------------------------------
STATES = [
    "Andhra Pradesh", "Assam", "Bihar", "Chhattisgarh", "Gujarat", "Haryana",
    "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
    "Maharashtra", "Odisha", "Punjab", "Rajasthan", "Tamil Nadu", "Telangana",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
]

DISTRICTS = {
    "Bihar": ["Patna", "Gaya", "Muzaffarpur", "Bhagalpur", "Aurangabad", "Darbhanga", "Purnia"],
    "Maharashtra": ["Pune", "Nashik", "Nagpur", "Aurangabad", "Solapur", "Kolhapur", "Latur"],
    "Karnataka": ["Bengaluru Rural", "Belagavi", "Mysuru", "Hubballi", "Kalaburagi", "Mandya"],
    "Punjab": ["Ludhiana", "Amritsar", "Patiala", "Bathinda", "Jalandhar", "Moga"],
    "Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi", "Meerut", "Agra", "Gorakhpur"],
    "Tamil Nadu": ["Coimbatore", "Madurai", "Thanjavur", "Salem", "Erode", "Tiruchirappalli"],
    "Telangana": ["Warangal", "Karimnagar", "Nizamabad", "Khammam", "Nalgonda"],
    "Andhra Pradesh": ["Guntur", "Krishna", "Kurnool", "Anantapur", "West Godavari"],
    "Gujarat": ["Rajkot", "Ahmedabad", "Junagadh", "Bhavnagar", "Surat", "Anand"],
    "Madhya Pradesh": ["Indore", "Bhopal", "Jabalpur", "Ujjain", "Sagar", "Hoshangabad"],
    "West Bengal": ["Bardhaman", "Hooghly", "Nadia", "Murshidabad", "Malda"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Kota", "Sri Ganganagar", "Alwar"],
    "Haryana": ["Karnal", "Hisar", "Sirsa", "Rohtak", "Ambala"],
    "Odisha": ["Cuttack", "Sambalpur", "Balasore", "Ganjam", "Bargarh"],
    "Kerala": ["Palakkad", "Thrissur", "Alappuzha", "Kottayam", "Wayanad"],
}

CROPS = [
    "Rice", "Wheat", "Maize", "Cotton", "Sugarcane", "Soybean", "Groundnut",
    "Mustard", "Chickpea", "Pigeon Pea", "Bajra", "Jowar", "Potato", "Onion",
    "Tomato", "Banana", "Mango", "Grapes", "Chilli", "Turmeric",
]

SOIL_TYPES = [
    "Alluvial", "Black", "Red", "Laterite", "Sandy", "Clayey", "Loamy", "Saline",
]

SEASONS = ["Kharif", "Rabi", "Zaid"]


# ---------------------------------------------------------------------------
# Crop diseases (PlantVillage class names -> agronomic guidance)
# ---------------------------------------------------------------------------
DISEASE_DB = {
    "Tomato___Late_blight": {
        "label": "Tomato — Late Blight",
        "crop": "Tomato",
        "healthy": False,
        "causes": "Caused by the oomycete Phytophthora infestans. Spreads rapidly in cool "
                  "(15–22 °C), humid weather with long leaf-wetness periods and dense canopies.",
        "symptoms": "Water-soaked greasy grey-green blotches on leaves that turn brown-black; "
                    "white fuzzy growth on leaf undersides in the morning; firm brown lesions "
                    "on fruit; rapid collapse of the plant.",
        "treatment": "Remove and destroy infected plants. Spray Mancozeb 75% WP @ 2 g/L or "
                     "Cymoxanil 8% + Mancozeb 64% @ 2 g/L; repeat at 7–10 day intervals. "
                     "Alternate chemistries to avoid resistance.",
        "prevention": "Use certified resistant varieties, 60 cm plant spacing for airflow, drip "
                      "irrigation instead of overhead, 3-year crop rotation with non-solanaceous "
                      "crops, and destroy volunteer plants and cull piles.",
    },
    "Tomato___Early_blight": {
        "label": "Tomato — Early Blight",
        "crop": "Tomato",
        "healthy": False,
        "causes": "Fungus Alternaria solani surviving on crop debris and infected seed; favoured "
                  "by warm humid weather and nitrogen-deficient plants.",
        "symptoms": "Dark brown spots with concentric target-like rings on older leaves, yellow "
                    "halo around lesions, progressive defoliation from the bottom upwards, "
                    "sunken dark lesions at the fruit stem end.",
        "treatment": "Spray Azoxystrobin 23% SC @ 1 ml/L or Chlorothalonil 75% WP @ 2 g/L at the "
                     "first symptom, two to three sprays 10 days apart. Remove affected leaves.",
        "prevention": "Mulch to stop soil splash, stake plants, maintain balanced NPK with "
                      "adequate potassium, rotate crops and use disease-free seed.",
    },
    "Potato___Late_blight": {
        "label": "Potato — Late Blight",
        "crop": "Potato",
        "healthy": False,
        "causes": "Phytophthora infestans carried by infected seed tubers; epidemics follow cool "
                  "cloudy days with more than 90% relative humidity.",
        "symptoms": "Dark water-soaked patches on leaf margins, white sporulation on the "
                    "underside, blackened stems, and reddish-brown granular rot inside tubers.",
        "treatment": "Apply Metalaxyl 8% + Mancozeb 64% @ 2.5 g/L immediately; follow with "
                     "contact fungicide Mancozeb @ 2 g/L every 7 days during humid spells.",
        "prevention": "Plant certified seed tubers, earth up ridges properly, avoid evening "
                      "irrigation, destroy haulms 10 days before harvest.",
    },
    "Potato___Early_blight": {
        "label": "Potato — Early Blight",
        "crop": "Potato",
        "healthy": False,
        "causes": "Alternaria solani on infected debris; aggravated by water stress and poor "
                  "soil fertility.",
        "symptoms": "Target-board concentric brown spots on lower leaves, leaf yellowing and "
                    "premature drop, shallow dark dry lesions on tubers.",
        "treatment": "Mancozeb 75% WP @ 2 g/L or Difenoconazole 25% EC @ 0.5 ml/L, two sprays "
                     "at a 10-day interval.",
        "prevention": "Balanced fertilisation, adequate irrigation, 2–3 year rotation with "
                      "cereals, and removal of infected debris after harvest.",
    },
    "Corn___Common_rust": {
        "label": "Maize — Common Rust",
        "crop": "Maize",
        "healthy": False,
        "causes": "Fungus Puccinia sorghi; urediniospores blow in over long distances and "
                  "germinate at 16–25 °C with heavy dew.",
        "symptoms": "Small cinnamon-brown powdery pustules scattered on both leaf surfaces that "
                    "later darken; severe infection dries out the leaf.",
        "treatment": "Spray Propiconazole 25% EC @ 1 ml/L or Tebuconazole @ 1 ml/L when 5–10% "
                     "leaf area is affected, repeat after 15 days if needed.",
        "prevention": "Grow resistant hybrids, avoid staggered sowing, destroy volunteer maize "
                      "and maintain field sanitation.",
    },
    "Corn___Northern_Leaf_Blight": {
        "label": "Maize — Northern Leaf Blight",
        "crop": "Maize",
        "healthy": False,
        "causes": "Exserohilum turcicum surviving on residue; favoured by moderate temperature "
                  "(18–27 °C) and prolonged leaf wetness.",
        "symptoms": "Long cigar-shaped grey-green to tan lesions running parallel to the veins, "
                    "starting on lower leaves and moving up.",
        "treatment": "Azoxystrobin 18.2% + Difenoconazole 11.4% SC @ 1 ml/L at early lesion "
                     "stage; two sprays 12–15 days apart.",
        "prevention": "Resistant hybrids, deep ploughing of residue, crop rotation with legumes "
                      "and avoiding excess nitrogen.",
    },
    "Rice___Bacterial_leaf_blight": {
        "label": "Rice — Bacterial Leaf Blight",
        "crop": "Rice",
        "healthy": False,
        "causes": "Bacterium Xanthomonas oryzae entering through wounds and hydathodes; spread "
                  "by irrigation water, storms and high nitrogen doses.",
        "symptoms": "Yellow-white wavy lesions from the leaf tip down the margins, milky bacterial "
                    "ooze in the morning, and wilting of seedlings (kresek).",
        "treatment": "Drain the field, stop nitrogen top-dressing, and spray Streptomycin "
                     "sulphate + Tetracycline @ 0.3 g/L combined with Copper oxychloride @ 2.5 g/L.",
        "prevention": "Use resistant varieties, treat seed with hot water at 52 °C for 30 min, "
                      "balanced nitrogen in splits, and clean field bunds.",
    },
    "Rice___Blast": {
        "label": "Rice — Blast",
        "crop": "Rice",
        "healthy": False,
        "causes": "Fungus Magnaporthe oryzae; night temperatures of 20–25 °C with long dew "
                  "periods and heavy nitrogen strongly favour epidemics.",
        "symptoms": "Spindle-shaped lesions with grey centres and brown margins on leaves; "
                    "blackened rotting node; whitish empty panicles when the neck is infected.",
        "treatment": "Spray Tricyclazole 75% WP @ 0.6 g/L at boot-leaf stage, repeat at heading. "
                     "Isoprothiolane 40% EC @ 1.5 ml/L is an effective alternative.",
        "prevention": "Avoid excess nitrogen, keep 2–3 cm standing water, use resistant varieties "
                      "and treat seed with Carbendazim @ 2 g/kg.",
    },
    "Wheat___Yellow_rust": {
        "label": "Wheat — Yellow (Stripe) Rust",
        "crop": "Wheat",
        "healthy": False,
        "causes": "Puccinia striiformis blowing down from the hills; cool (10–18 °C) moist "
                  "weather in north India triggers outbreaks.",
        "symptoms": "Bright yellow powdery pustules arranged in stripes between the veins; "
                    "yellow dust rubs off on clothes; shrivelled grain.",
        "treatment": "Spray Propiconazole 25% EC @ 1 ml/L as soon as stripes appear; a second "
                     "spray after 15 days protects the flag leaf.",
        "prevention": "Sow resistant varieties, avoid very early or late sowing, monitor fields "
                      "weekly from December, and destroy off-season volunteer wheat.",
    },
    "Grape___Black_rot": {
        "label": "Grape — Black Rot",
        "crop": "Grapes",
        "healthy": False,
        "causes": "Fungus Guignardia bidwellii overwintering in mummified berries and cane "
                  "lesions; rain splash spreads spores.",
        "symptoms": "Circular tan leaf spots with dark borders and black pycnidia; berries turn "
                    "brown, shrivel and become hard black mummies.",
        "treatment": "Spray Myclobutanil @ 0.4 ml/L or Mancozeb @ 2 g/L from bud break through "
                     "fruit set at 10-day intervals.",
        "prevention": "Remove mummified berries and prunings, open the canopy, and avoid "
                      "overhead irrigation.",
    },
    "Apple___Apple_scab": {
        "label": "Apple — Scab",
        "crop": "Apple",
        "healthy": False,
        "causes": "Venturia inaequalis overwintering in fallen leaves; ascospores released "
                  "during spring rains.",
        "symptoms": "Olive-green velvety spots on leaves turning black and corky; scabby cracked "
                    "lesions on fruit; early leaf fall.",
        "treatment": "Dodine 65% WP @ 0.75 g/L or Mancozeb @ 2 g/L at green tip, pink bud and "
                     "petal fall stages.",
        "prevention": "Rake and destroy fallen leaves, prune for airflow, plant scab-resistant "
                      "cultivars.",
    },
    "Cotton___Leaf_curl_virus": {
        "label": "Cotton — Leaf Curl Virus",
        "crop": "Cotton",
        "healthy": False,
        "causes": "Begomovirus transmitted by whitefly (Bemisia tabaci); dry hot weather with "
                  "high whitefly pressure drives spread.",
        "symptoms": "Upward or downward curling of leaves, thickened darkened veins, enations on "
                    "the underside, stunted plants with few bolls.",
        "treatment": "No cure once infected — rogue out severely infected plants and control the "
                     "whitefly vector with Diafenthiuron 50% WP @ 1 g/L or Flonicamid 50% WG @ "
                     "0.3 g/L.",
        "prevention": "Sow tolerant Bt hybrids, treat seed with Imidacloprid, install yellow "
                      "sticky traps at 10/acre, and remove alternate weed hosts.",
    },
    "Tomato___healthy": {
        "label": "Tomato — Healthy",
        "crop": "Tomato", "healthy": True,
        "causes": "—",
        "symptoms": "No disease symptoms detected. Leaf colour and structure look normal.",
        "treatment": "No treatment required.",
        "prevention": "Continue weekly scouting, balanced fertigation and clean cultivation.",
    },
    "Potato___healthy": {
        "label": "Potato — Healthy",
        "crop": "Potato", "healthy": True,
        "causes": "—",
        "symptoms": "Foliage appears healthy with uniform green colour.",
        "treatment": "No treatment required.",
        "prevention": "Maintain ridge moisture and monitor for late blight during cloudy weather.",
    },
    "Rice___healthy": {
        "label": "Rice — Healthy",
        "crop": "Rice", "healthy": True,
        "causes": "—",
        "symptoms": "No lesions or discolouration detected on the leaf.",
        "treatment": "No treatment required.",
        "prevention": "Keep balanced nitrogen and monitor after heavy dew.",
    },
}

DEFAULT_DISEASE_INFO = {
    "label": "Unidentified leaf condition",
    "crop": "Unknown",
    "healthy": False,
    "causes": "The model could not confidently match this image to a known class.",
    "symptoms": "Please upload a sharp, well-lit photo of a single affected leaf on a plain "
                "background.",
    "treatment": "Consult your nearest Krishi Vigyan Kendra (KVK) before applying chemicals.",
    "prevention": "Regular field scouting and clean cultivation remain the best defence.",
}


# ---------------------------------------------------------------------------
# Pests
# ---------------------------------------------------------------------------
PEST_DB = {
    "Fall_armyworm": {
        "label": "Fall Armyworm (Spodoptera frugiperda)",
        "damage": "Larvae feed inside the maize whorl leaving ragged holes and heavy moist "
                  "frass; severe attack destroys the growing point and cuts yield by 30–50%.",
        "prevention": "Deep summer ploughing, timely uniform sowing, intercropping with pulses, "
                      "pheromone traps at 5/acre, and conserving Trichogramma parasitoids.",
        "treatment": "Apply Emamectin benzoate 5% SG @ 0.4 g/L or Spinetoram 11.7% SC @ 0.5 ml/L "
                     "directed into the whorl in the evening; rotate molecules between sprays.",
    },
    "Aphids": {
        "label": "Aphids (Aphis spp.)",
        "damage": "Colonies suck sap from tender shoots causing curling and stunting; honeydew "
                  "leads to sooty mould and they transmit several plant viruses.",
        "prevention": "Encourage ladybird beetles and syrphid flies, avoid excess nitrogen, use "
                      "yellow sticky traps and remove weed hosts.",
        "treatment": "Spray Neem oil 1500 ppm @ 3 ml/L for light infestations; Thiamethoxam 25% "
                     "WG @ 0.2 g/L or Flonicamid 50% WG @ 0.3 g/L for heavy attack.",
    },
    "Whitefly": {
        "label": "Whitefly (Bemisia tabaci)",
        "damage": "Nymphs suck sap causing yellowing and vigour loss, and the adults transmit "
                  "leaf curl and yellow mosaic viruses in cotton, tomato and pulses.",
        "prevention": "Yellow sticky traps at 10/acre, avoid consecutive host crops, remove "
                      "parthenium and other weed hosts, and maintain field sanitation.",
        "treatment": "Diafenthiuron 50% WP @ 1 g/L or Pyriproxyfen 10% EC @ 1 ml/L; add a "
                     "sticker and spray the leaf underside thoroughly.",
    },
    "Stem_borer": {
        "label": "Stem Borer (Scirpophaga / Chilo spp.)",
        "damage": "Larvae bore into the stem producing dead-hearts in the vegetative stage and "
                  "white ears at panicle stage in rice and sugarcane.",
        "prevention": "Clip seedling tips before transplanting, release Trichogramma japonicum "
                      "cards at 50,000/ha, and destroy stubble after harvest.",
        "treatment": "Apply Cartap hydrochloride 4G @ 8 kg/acre in standing water, or spray "
                     "Chlorantraniliprole 18.5% SC @ 0.3 ml/L at dead-heart appearance.",
    },
    "Pink_bollworm": {
        "label": "Pink Bollworm (Pectinophora gossypiella)",
        "damage": "Larvae feed inside cotton bolls, causing rosetted flowers, stained lint and "
                  "premature boll opening with severe quality loss.",
        "prevention": "Follow a strict single-season crop window, avoid extended cotton, install "
                      "gossyplure pheromone traps at 8/acre and destroy stubble.",
        "treatment": "Spray Profenofos 50% EC @ 2 ml/L or Thiodicarb 75% WP @ 1 g/L at ETL "
                     "(8 moths/trap/night for 3 nights); collect and destroy rosette flowers.",
    },
    "Brown_planthopper": {
        "label": "Brown Planthopper (Nilaparvata lugens)",
        "damage": "Dense colonies at the base of rice tillers cause circular patches of drying "
                  "plants known as hopper burn, plus grassy stunt virus transmission.",
        "prevention": "Alternate wetting and drying, 30 cm alleys every 2 m, avoid excess "
                      "nitrogen and conserve spiders and mirid bugs.",
        "treatment": "Drain the field and spray Pymetrozine 50% WG @ 0.6 g/L or Dinotefuran 20% "
                     "SG @ 0.3 g/L directed at the plant base.",
    },
    "Thrips": {
        "label": "Thrips (Thrips tabaci / Scirtothrips dorsalis)",
        "damage": "Rasping and sucking causes silvery streaks, upward leaf curl in chilli "
                  "(murda complex) and scarred fruit in onion and grapes.",
        "prevention": "Blue sticky traps, border rows of maize as a barrier, adequate irrigation "
                      "since dry spells favour build-up.",
        "treatment": "Spirotetramat 15.31% OD @ 1 ml/L or Fipronil 5% SC @ 2 ml/L, alternated "
                     "with neem-based sprays.",
    },
    "Healthy": {
        "label": "No pest detected",
        "damage": "The image does not show a recognised pest species.",
        "prevention": "Continue weekly scouting and keep pheromone traps in place.",
        "treatment": "No pesticide application required at this stage.",
    },
}

DEFAULT_PEST_INFO = {
    "label": "Unidentified pest",
    "damage": "The model could not confidently identify this specimen.",
    "prevention": "Send a clear close-up photograph to your local KVK entomologist.",
    "treatment": "Avoid blind pesticide sprays; confirm the pest before treating.",
}


def get_disease_info(key: str) -> dict:
    info = dict(DISEASE_DB.get(key, DEFAULT_DISEASE_INFO))
    info.setdefault("label", key.replace("___", " — ").replace("_", " "))
    return info


def get_pest_info(key: str) -> dict:
    info = dict(PEST_DB.get(key, DEFAULT_PEST_INFO))
    info.setdefault("label", key.replace("_", " "))
    return info
