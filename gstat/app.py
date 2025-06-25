import streamlit as st
import requests
import json
import os
from datetime import datetime, timezone
import matplotlib.pyplot as plt
import re
from bs4 import BeautifulSoup

st.set_page_config(page_title="GSTAT", layout="centered")

# ---------- CSS ----------
css = """
<style>
    body {background: linear-gradient(to right, #f4f6f9, #e2e8f0);font-family:'Segoe UI',sans-serif;margin:0;padding:0;}
    .title {text-align:center;font-size:3em;font-weight:bold;color:#1a202c;margin-top:30px;margin-bottom:10px;letter-spacing:1px;}
    .box {background:white;padding:30px;border-radius:24px;box-shadow:0 8px 20px rgba(0,0,0,0.1);margin:30px auto;max-width:700px;transition:all .3s ease-in-out;}
    .box:hover {transform:scale(1.01);box-shadow:0 10px 24px rgba(0,0,0,0.15);}
    .footer {text-align:center;font-size:0.9em;color:#718096;margin-top:40px;padding-bottom:20px;}
    .credit {font-size:0.95em;color:#4a5568;margin-top:20px;}
    a {color:#2b6cb0;text-decoration:none;}
    a:hover {text-decoration:underline;}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

st.markdown('<div class="title">GSTAT ⭐ נתוני כדורגל חכמים</div>', unsafe_allow_html=True)

# ---------- CONFIG ----------
API_KEY = st.secrets["api_key"]
REQUESTS_FILE = "requests_today.json"
REQUEST_LIMIT = 100
SEASON_CANDIDATES = ["2024", "2023", "2022", "2021"]
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ---------- REQUEST COUNTER ----------
def load_requests():
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    if os.path.exists(REQUESTS_FILE):
        with open(REQUESTS_FILE, 'r') as f:
            data = json.load(f)
    else:
        data = {}
    if today not in data:
        data[today] = 78
    return data, today

def save_requests(data):
    with open(REQUESTS_FILE, 'w') as f:
        json.dump(data, f)

def increment_counter():
    data, today = load_requests()
    data[today] += 1
    save_requests(data)
    return REQUEST_LIMIT - data[today]

def remaining_requests():
    data, today = load_requests()
    return REQUEST_LIMIT - data[today]

# ---------- HELPERS ----------
@st.cache_data(show_spinner=False)
def search_player_id(name: str):
    url = "https://api-football-v1.p.rapidapi.com/v3/players"
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    for season in SEASON_CANDIDATES:
        q = {"search": name, "season": season}
        r = requests.get(url, headers=headers, params=q, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("response"):
                return data["response"][0]["player"]["id"]
    return None

@st.cache_data(show_spinner=False)
def api_player_stats(player_id: int, season: str):
    url = "https://api-football-v1.p.rapidapi.com/v3/players"
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    q = {"id": player_id, "season": season}
    r = requests.get(url, headers=headers, params=q, timeout=10)
    r.raise_for_status()
    return r.json()

@st.cache_data(show_spinner=False)
def duckduckgo_english_name(query: str) -> str | None:
    ddg_url = f"https://html.duckduckgo.com/html/?q={query}+site:wikipedia.org+football"
    try:
        res = requests.get(ddg_url, headers=HEADERS, timeout=8)
        soup = BeautifulSoup(res.text, "html.parser")
        for a in soup.find_all("a", href=True):
            title = a.get_text(" ", strip=True)
            if "football" in title.lower():
                name = title.split("(")[0].strip()
                if len(name.split()) >= 2:
                    return name
    except Exception:
        pass
    return None

def normalize_name(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r'[^a-zA-Zא-ת\\s]', '', name)
    return name.title()

# ---------- CORE ----------
def get_player_stats(player_name: str):
    if remaining_requests() <= 0:
        st.error("❌ חרגת מהמכסה היומית (100 בקשות). נסה שוב מחר.")
        return None, None, {}

    player_id = search_player_id(player_name)
    increment_counter()
    if not player_id:
        return None, None, {}

    for season in SEASON_CANDIDATES:
        js = api_player_stats(player_id, season)
        increment_counter()
        if js.get("response"):
            p = js["response"][0]
            s = p["statistics"][0]
            return player_id, season, {
                "team": s["team"]["name"],
                "position": s["games"]["position"],
                "appearances": s["games"]["appearences"],
                "goals": s["goals"]["total"],
                "rating": s["games"].get("rating", "—")
            }
    return player_id, None, {}

# ---------- GRAPH ----------
def plot_goals(goals: int, season: str):
    fig, ax = plt.subplots()
    ax.bar(season, goals, color="mediumseagreen")
    ax.set_title(f"⚽ שערים בעונת {season}")
    ax.set_ylim(0, max(goals, 10) + 2)
    st.pyplot(fig)

# ---------- UI ----------
name_input = st.text_input("הכנס שם של שחקן (בעברית או באנגלית)")

if name_input:
    player_name = normalize_name(name_input)
    player_id, season_found, stats = get_player_stats(player_name)

    if not stats:
        alt_name = duckduckgo_english_name(player_name)
        if alt_name:
            player_id, season_found, stats = get_player_stats(alt_name)
            player_name = alt_name if stats else player_name

    if not stats:
        st.warning("לא נמצאו נתונים לשחקן.")
    else:
        st.markdown(f"""
        <div class='box'>
            <h3>🌟 {player_name}</h3>
            <p><strong>🏟️ קבוצה:</strong> {stats['team']}</p>
            <p><strong>🕴️ עמדה:</strong> {stats['position']}</p>
            <p><strong>🎯 הופעות:</strong> {stats['appearances']}</p>
            <p><strong>⚽ שערים:</strong> {stats['goals']}</p>
            <p><strong>⭐ דירוג:</strong> {stats['rating']}</p>
            <p class='credit'>מקור: API-Football (RapidAPI) לעונת {season_found}</p>
        </div>
        """, unsafe_allow_html=True)

        if isinstance(stats['goals'], int):
            st.markdown("### 🔼 גרף שערים")
            plot_goals(stats['goals'], season_found)

# ---------- FOOTER ----------
remaining = remaining_requests()
st.markdown(
    f"""
<div class='footer'>
    GSTAT מציג מידע חוקי ממקורות API רשמיים בלבד.<br>
    בקשות שנותרו להיום: {remaining} / {REQUEST_LIMIT}
</div>
""",
    unsafe_allow_html=True,
)
