"""
Nearby mandi finder.

Uses a curated dataset of APMC / regulated market coordinates and computes the
great-circle distance from the farmer's browser geolocation. The frontend
renders the results on a Leaflet (OpenStreetMap) map — no paid Maps key needed,
although GOOGLE_MAPS_API_KEY is honoured for directions links when set.
"""
import math

MARKETS = [
    {"name": "Patna Bazar Samiti (APMC)", "state": "Bihar", "district": "Patna",
     "lat": 25.6120, "lon": 85.1410, "phone": "+91 612 2234 567",
     "commodities": "Rice, Wheat, Maize, Potato, Onion"},
    {"name": "Aurangabad Krishi Bazar", "state": "Bihar", "district": "Aurangabad",
     "lat": 24.7524, "lon": 84.3742, "phone": "+91 6186 222 145",
     "commodities": "Paddy, Wheat, Pulses, Vegetables"},
    {"name": "Gaya Regulated Market", "state": "Bihar", "district": "Gaya",
     "lat": 24.7955, "lon": 85.0002, "phone": "+91 631 2221 908",
     "commodities": "Paddy, Gram, Mustard"},
    {"name": "Muzaffarpur Fruit & Veg Mandi", "state": "Bihar", "district": "Muzaffarpur",
     "lat": 26.1209, "lon": 85.3647, "phone": "+91 621 2245 331",
     "commodities": "Litchi, Mango, Vegetables"},
    {"name": "Varanasi Pahariya Mandi", "state": "Uttar Pradesh", "district": "Varanasi",
     "lat": 25.3421, "lon": 83.0198, "phone": "+91 542 2501 122",
     "commodities": "Wheat, Paddy, Vegetables"},
    {"name": "Lucknow Sitapur Road Mandi", "state": "Uttar Pradesh", "district": "Lucknow",
     "lat": 26.9124, "lon": 80.9200, "phone": "+91 522 2732 100",
     "commodities": "Wheat, Mustard, Potato"},
    {"name": "Kanpur Chakeri Grain Market", "state": "Uttar Pradesh", "district": "Kanpur",
     "lat": 26.4499, "lon": 80.3319, "phone": "+91 512 2401 908",
     "commodities": "Wheat, Gram, Pulses"},
    {"name": "Pune Market Yard (Gultekdi)", "state": "Maharashtra", "district": "Pune",
     "lat": 18.4966, "lon": 73.8720, "phone": "+91 20 2426 1000",
     "commodities": "Onion, Vegetables, Fruits, Pulses"},
    {"name": "Lasalgaon APMC (Onion)", "state": "Maharashtra", "district": "Nashik",
     "lat": 20.1436, "lon": 74.2385, "phone": "+91 2550 265 021",
     "commodities": "Onion, Grapes, Tomato"},
    {"name": "Nagpur Kalamna Market", "state": "Maharashtra", "district": "Nagpur",
     "lat": 21.1702, "lon": 79.1400, "phone": "+91 712 2680 344",
     "commodities": "Cotton, Soybean, Orange, Pulses"},
    {"name": "Ludhiana Grain Market", "state": "Punjab", "district": "Ludhiana",
     "lat": 30.9010, "lon": 75.8573, "phone": "+91 161 2402 555",
     "commodities": "Wheat, Paddy, Maize"},
    {"name": "Khanna Mandi (Asia's largest grain market)", "state": "Punjab",
     "district": "Ludhiana", "lat": 30.7046, "lon": 76.2220, "phone": "+91 1628 222 133",
     "commodities": "Wheat, Paddy"},
    {"name": "Yeshwanthpur APMC", "state": "Karnataka", "district": "Bengaluru Rural",
     "lat": 13.0230, "lon": 77.5500, "phone": "+91 80 2337 1288",
     "commodities": "Ragi, Maize, Vegetables, Copra"},
    {"name": "Hubballi APMC", "state": "Karnataka", "district": "Hubballi",
     "lat": 15.3647, "lon": 75.1240, "phone": "+91 836 2232 111",
     "commodities": "Cotton, Chilli, Groundnut"},
    {"name": "Guntur Mirchi Yard", "state": "Andhra Pradesh", "district": "Guntur",
     "lat": 16.3067, "lon": 80.4365, "phone": "+91 863 2233 445",
     "commodities": "Chilli, Cotton, Turmeric"},
    {"name": "Warangal Enumamula Market", "state": "Telangana", "district": "Warangal",
     "lat": 17.9784, "lon": 79.5941, "phone": "+91 870 2578 233",
     "commodities": "Cotton, Maize, Paddy, Chilli"},
    {"name": "Coimbatore Uzhavar Sandhai", "state": "Tamil Nadu", "district": "Coimbatore",
     "lat": 11.0168, "lon": 76.9558, "phone": "+91 422 2222 100",
     "commodities": "Vegetables, Banana, Coconut"},
    {"name": "Rajkot APMC", "state": "Gujarat", "district": "Rajkot",
     "lat": 22.3039, "lon": 70.8022, "phone": "+91 281 2440 222",
     "commodities": "Groundnut, Cotton, Cumin"},
    {"name": "Indore Chhawni Grain Mandi", "state": "Madhya Pradesh", "district": "Indore",
     "lat": 22.7196, "lon": 75.8577, "phone": "+91 731 2701 200",
     "commodities": "Soybean, Wheat, Gram"},
    {"name": "Burdwan Regulated Market", "state": "West Bengal", "district": "Bardhaman",
     "lat": 23.2324, "lon": 87.8615, "phone": "+91 342 2662 100",
     "commodities": "Paddy, Potato, Vegetables"},
]

EARTH_RADIUS_KM = 6371.0


def haversine(lat1, lon1, lat2, lon2) -> float:
    """Great-circle distance in kilometres."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return EARTH_RADIUS_KM * 2 * math.asin(math.sqrt(a))


def nearby_markets(lat: float, lon: float, radius_km: float = 250, limit: int = 10):
    """Markets within ``radius_km``, nearest first, with a directions link."""
    results = []
    for m in MARKETS:
        distance = haversine(lat, lon, m["lat"], m["lon"])
        if distance <= radius_km:
            item = dict(m)
            item["distance_km"] = round(distance, 1)
            item["directions"] = (
                f"https://www.google.com/maps/dir/?api=1&origin={lat},{lon}"
                f"&destination={m['lat']},{m['lon']}&travelmode=driving"
            )
            results.append(item)
    results.sort(key=lambda x: x["distance_km"])
    return results[:limit]
