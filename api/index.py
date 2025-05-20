from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import calendar
from datetime import datetime
import re

from cachetools import TTLCache

app = Flask(__name__)

GEMEINDEN = {
    "Bisamberg": "31201",
    "Enzersfeld": "31202",
    "Ernstbrunn": "31203",
    "Großmugl": "31204",
    "Großrußbach": "31205",
    "Hagenbrunn": "31206",
    "Harmannsdorf": "31207",
    "Hausleiten": "31208",
    "Leobendorf": "31216",
    "Niederhollabrunn": "31234",
    "Rußbach": "31224",
    "Sierndorf": "31226",
}

WASTE_TYPE_ENUM = {
    "Bio": "bio",
    "Restmüll": "restmuell",
    "Gelber Sack": "gelber_sack",
    "Altpapier": "altpapier",
}

BASE_URL = "https://korneuburg.umweltverbaende.at/"

# TTL cache: max 100 entries, expire after 600 seconds (10 minutes)
cache = TTLCache(maxsize=100, ttl=600)


def parse_date_to_iso(date_str, year_hint=None):
    try:
        day, month = map(int, date_str.strip(".").split("."))
        now = datetime.now()
        year = year_hint if year_hint else now.year
        if month < now.month - 6:
            year += 1
        dt = datetime(year, month, day)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None


def normalize_type(raw_type):
    for label, enum_val in WASTE_TYPE_ENUM.items():
        if raw_type.startswith(label):
            return enum_val
    return raw_type.lower().replace(" ", "_")


def extract_lay_1_content(html):
    soup = BeautifulSoup(html, "html.parser")
    lay_div = soup.find("div", id="lay_1")
    if not lay_div:
        return None, "No div with id 'lay_1' found on the page."

    gemeinde_tag = lay_div.select_one("div[style*='padding-left'] > div > b")
    gemeinde_name = gemeinde_tag.get_text(strip=True) if gemeinde_tag else None

    result = []
    now = datetime.now()
    for entry in lay_div.select('div[style*="padding:5px"]'):
        text = entry.get_text(strip=True, separator=" ")
        parts = text.split(" ", 1)
        if len(parts) != 2:
            continue
        date_raw, rest = parts
        iso_date = parse_date_to_iso(date_raw, now.year)
        if not iso_date:
            continue

        if "," in rest:
            waste_type_raw, area_sub_raw = map(str.strip, rest.split(",", 1))
            area_list = [
                a.strip() for a in re.split(r",|\n|\bund\b", area_sub_raw) if a.strip()
            ]
            if not area_list:
                area_list = None
        else:
            waste_type_raw = rest.strip()
            area_list = None

        waste_type_norm = normalize_type(waste_type_raw)

        entry_data = {"date": iso_date, "type": waste_type_norm, "area": area_list}
        result.append(entry_data)

    return {"gemeinde": gemeinde_name, "data": result}, None


def get_gemeinde_data_cached(gemeinde_name):
    if gemeinde_name in cache:
        return cache[gemeinde_name], None

    if gemeinde_name not in GEMEINDEN:
        return None, f"Invalid gemeinde: '{gemeinde_name}'"

    gem_nr = GEMEINDEN[gemeinde_name]
    session = requests.Session()
    domain = urlparse(BASE_URL).netloc
    expires_dt = datetime.strptime("2030-12-31T12:00:00Z", "%Y-%m-%dT%H:%M:%SZ")
    expires_unix = calendar.timegm(expires_dt.utctimetuple())
    session.cookies.set("gemeindenummer", gem_nr, domain=domain, expires=expires_unix)

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    }

    url = f"{BASE_URL}?gem_nr={gem_nr}"
    response = session.get(url, headers=headers)

    if response.status_code != 200:
        return None, f"Failed to fetch page: {response.status_code}"

    content, error = extract_lay_1_content(response.text)
    if error:
        return None, error

    cache[gemeinde_name] = content
    return content, None


@app.route("/api/gemeinde", methods=["GET"])
def gemeinde_handler():
    gemeinde_name = request.args.get("name")
    if not gemeinde_name:
        return jsonify({"error": "Missing 'name' parameter"}), 400

    data, error = get_gemeinde_data_cached(gemeinde_name)
    if error:
        return jsonify({"error": error}), 400

    return jsonify(data)


@app.route("/api/gemeinden", methods=["GET"])
def list_gemeinden():
    return jsonify(sorted(GEMEINDEN.keys()))
