"""
Farmer assistant chatbot.

Two interchangeable backends behind one ``generate_reply()`` contract:

* ``RuleBasedEngine`` — intent classification over an agronomy knowledge base.
  Works offline, zero cost, deterministic; this is the default.
* ``GeminiEngine``    — activated automatically when ``GEMINI_API_KEY`` is set.
  Uses the same system prompt and returns the same payload shape, so no route
  or template change is needed to upgrade.
"""
import re

import requests
from flask import current_app

SYSTEM_PROMPT = (
    "You are Kisan Mitra, an agricultural extension assistant for Indian farmers. "
    "Answer briefly and practically, use metric units, quote doses per acre, mention "
    "government schemes where relevant, and always advise confirming chemical doses "
    "with the local Krishi Vigyan Kendra."
)

INTENTS = {
    "greeting": {
        "patterns": [r"\b(hi|hello|hey|namaste|namaskar|pranam)\b"],
        "reply": "Namaste! I am Kisan Mitra, your farming assistant. Ask me about crops, "
                 "fertilizers, irrigation, pests, diseases, organic farming or government "
                 "schemes.",
    },
    "crop_cultivation": {
        "patterns": [r"\b(sow|sowing|cultivat|grow|plant|variety|seed rate|spacing)\b"],
        "reply": "Sowing guidance: choose a certified variety suited to your season "
                 "(Kharif — paddy, maize, cotton; Rabi — wheat, gram, mustard). Treat seed "
                 "with a fungicide such as Carbendazim @ 2 g/kg, keep 20–22 cm row spacing "
                 "for wheat and 30 × 15 cm for transplanted paddy, and sow at 2–3 cm depth "
                 "into moist soil. Open the Crop Calendar module for the exact window in "
                 "your state.",
    },
    "fertilizer": {
        "patterns": [r"\b(fertilizer|fertiliser|urea|dap|npk|nutrient|nitrogen|potash|manure)\b"],
        "reply": "Always base doses on a soil test. A general cereal schedule is 50 kg DAP + "
                 "20 kg MOP per acre as basal, and 45 kg urea split between sowing and "
                 "active tillering. Add 2 t/acre of well-decomposed FYM or vermicompost "
                 "every season to build organic carbon. The Fertilizer Recommendation "
                 "module gives an ML-based suggestion from your N-P-K values.",
    },
    "irrigation": {
        "patterns": [r"\b(irrigat|water|drip|sprinkler|moisture|drought)\b"],
        "reply": "Irrigate at critical stages rather than on a fixed calendar — crown root "
                 "initiation and grain filling in wheat, tillering and panicle initiation in "
                 "paddy. Drip irrigation saves 40–50% water and pairs well with fertigation; "
                 "subsidies are available under PMKSY 'Per Drop More Crop'. Mulching reduces "
                 "evaporation losses substantially.",
    },
    "disease": {
        "patterns": [r"\b(disease|blight|rust|blast|wilt|rot|spot|fungus|mildew|virus)\b"],
        "reply": "Upload a clear leaf photo in the Disease Detection module for an AI "
                 "diagnosis with treatment steps. General rule: remove infected plant parts, "
                 "improve airflow and drainage, and use a protective fungicide such as "
                 "Mancozeb @ 2 g/L, switching to a systemic product only when symptoms are "
                 "spreading.",
    },
    "pest": {
        "patterns": [r"\b(pest|insect|worm|borer|aphid|whitefly|thrips|caterpillar|larva)\b"],
        "reply": "Follow IPM: install pheromone traps (5/acre), conserve natural enemies, and "
                 "spray only after the economic threshold is crossed. Neem oil 1500 ppm @ "
                 "3 ml/L handles early infestations; rotate chemical groups to prevent "
                 "resistance. Use the Pest Detection module to identify the species first.",
    },
    "organic": {
        "patterns": [r"\b(organic|natural farming|jeevamrut|vermicompost|bio.?fertilizer|zbnf)\b"],
        "reply": "For organic production use Jeevamrut (10 kg cow dung + 10 L urine + 2 kg "
                 "jaggery + 2 kg pulse flour in 200 L water) every 15 days, apply "
                 "vermicompost at 2 t/acre, use Trichoderma viride @ 5 g/kg for seed "
                 "treatment, and rotate with legumes. Certification support is available "
                 "under the Paramparagat Krishi Vikas Yojana (PKVY).",
    },
    "scheme": {
        "patterns": [r"\b(scheme|subsidy|yojana|loan|kcc|pm.?kisan|insurance|fasal bima)\b"],
        "reply": "Key schemes: PM-KISAN pays ₹6,000/year in three instalments; PMFBY provides "
                 "crop insurance at 2% premium for Kharif and 1.5% for Rabi; the Kisan Credit "
                 "Card offers loans up to ₹3 lakh at 4% effective interest with prompt "
                 "repayment; and the Soil Health Card scheme gives free nutrient testing. "
                 "See the Government Schemes module for eligibility and documents.",
    },
    "weather": {
        "patterns": [r"\b(weather|rain|forecast|temperature|humidity|monsoon|storm)\b"],
        "reply": "Open the Weather module for the live 7-day forecast for your location. "
                 "Avoid spraying when rain is expected within 6 hours, and postpone urea "
                 "top-dressing before heavy rain to prevent leaching losses.",
    },
    "price": {
        "patterns": [r"\b(price|rate|mandi|market|sell|msp|bhav)\b"],
        "reply": "Check the Market Price module for the minimum, maximum and modal rates in "
                 "your district, plus a 30-day trend chart. Compare with the eNAM portal "
                 "before selling, and prefer grading and storage when the trend is rising.",
    },
    "soil": {
        "patterns": [r"\b(soil|ph|alkaline|acidic|saline|black soil|red soil|alluvial)\b"],
        "reply": "Test your soil every two to three years through the Soil Health Card scheme. "
                 "Acidic soils (pH < 6) benefit from 2 q/acre of agricultural lime; alkaline "
                 "soils improve with gypsum plus green manuring. The Soil Information module "
                 "lists suitable crops and fertiliser plans for every major Indian soil type.",
    },
}

FALLBACK = (
    "I could not match that to a topic I know well yet. Try asking about crop cultivation, "
    "fertilizers, irrigation, diseases, pests, organic farming, weather, market prices or "
    "government schemes — or open the relevant module from the sidebar."
)

QUICK_PROMPTS = [
    "How do I control late blight in tomato?",
    "Best fertilizer dose for wheat per acre",
    "Am I eligible for PM-KISAN?",
    "When should I sow paddy in Bihar?",
    "How to start organic farming?",
]


def detect_intent(message: str) -> str:
    text = (message or "").lower()
    for intent, spec in INTENTS.items():
        for pattern in spec["patterns"]:
            if re.search(pattern, text):
                return intent
    return "unknown"


def _gemini_reply(message: str, history=None):
    """Call Gemini when a key is configured; returns None on any failure."""
    key = current_app.config.get("GEMINI_API_KEY")
    if not key:
        return None
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           f"gemini-1.5-flash:generateContent?key={key}")
    contents = []
    for turn in (history or [])[-6:]:
        contents.append({"role": "user", "parts": [{"text": turn["message"]}]})
        contents.append({"role": "model", "parts": [{"text": turn["response"]}]})
    contents.append({"role": "user", "parts": [{"text": message}]})
    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 500},
    }
    try:
        res = requests.post(url, json=payload, timeout=15)
        res.raise_for_status()
        data = res.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as exc:  # network, quota, schema drift
        current_app.logger.warning("Gemini fallback to rule engine: %s", exc)
        return None


def generate_reply(message: str, history=None) -> dict:
    """Return ``{reply, intent, engine}`` for the given farmer question."""
    intent = detect_intent(message)
    llm = _gemini_reply(message, history)
    if llm:
        return {"reply": llm, "intent": intent, "engine": "gemini"}
    reply = INTENTS[intent]["reply"] if intent in INTENTS else FALLBACK
    return {"reply": reply, "intent": intent, "engine": "rule_based"}
