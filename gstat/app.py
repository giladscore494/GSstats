# GSTAT Streamlit App – עם חסימה ב־100 בקשות
import streamlit as st
import requests
import json
import os
from datetime import datetime, timezone
import matplotlib.pyplot as plt
import re

st.set_page_config(page_title="GSTAT", layout="centered")

# ---------- CSS ----------
st.markdown("""
<style>
    body {background: linear-gradient(to right, #f4f6f9, #e2e8f0);font-family:'Segoe UI',sans-serif;margin:0;}
    .title {text-align:center;font-size:3em;font-weight:bold;color:#1a202c;margin-top:30px;margin-bottom:10px;}
    .box {background:white;padding:30px;border-radius:24px;box-shadow:0 8px 20px rgba(0,0,0,0.1);margin:30px auto;max-width:700px;}
    .footer {text-align:center;font-size:0.9em;color:#718096;margin-top:40px;padding-bottom:20px;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">GSTAT ⭐ נתוני כדורגל חכמים</div>', unsafe_allow_html=True)

# ---------- CONFIG ----------
API_KEY = st.secrets["api_key"]
REQUEST_LIMIT = 100
REQUESTS_FILE = "requests_today.json"
SEASON = "2023"
LEAGUE_ID = 39  # פרמייר ליג

# ---------- REQUEST COUNTER ----------
def load_requests():
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    data = {}
    if os.path.exists(REQUESTS_FILE):
        with open(REQUESTS_FILE, "r") as f:
            data = json.load(f)
    if today not in data:
        data[today] = 0
    return data, today

def add_api_call(cnt: int = 1):
    data, today = load_requests()
    data[today] += cnt
    with open(REQUESTS_FILE, "w") as f:
        json.dump(data, f)

def remaining_requests():
    data, today = load_requests()
    return REQUEST_LIMIT - data[today]

# ---------- API WRAPPER ----------
def raw_api(endpoint: str, params: dict):
    if remaining_requests() <= 0:
        st.error("🔒 הגעת למכסת הבקשות היומית (100). נסה מחר שוב.")
        st.stop()
    url = f"https://api-football-v1.p.rapidapi.com/v3/{endpoint}"
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    res = requests.get(url, headers=headers, params=params, timeout=10)
    res.raise_for_status()
    add_api_call()
    return res.json()

# ---------- SEARCH ----------
def search_player(name: str):
    js = raw_api("players", {"search": name, "season": SEASON, "league": LEAGUE_ID})
    return js.get("response", [])

# ---------- STATS ----------
def extract_stats(response):
    if not response:
        return None
    s = response[0]["statistics"][0]
    return {
        "team": s["team"]["name"],
        "position": s["games"]["position"],
        "appearances": s["games"]["appearences"],
        "goals": s["goals"]["total"],
        "rating": s["games"].get("rating", "—")
    }

# ---------- NORMALIZATION ----------
normalize = lambda n: re.sub(r"[^a-zA-Zא-ת\s]", "", n.strip()).title()

# ---------- UI ----------
name_in = st.text_input("הכנס שם שחקן (בעברית או באנגלית)")

if name_in:
    name = normalize(name_in)
    data = search_player(name)
    stats = extract_stats(data)

    if stats:
        st.markdown(f"""
        <div class='box'>
            <h3>🌟 {name}</h3>
            <p><strong>🏟️ קבוצה:</strong> {stats['team']}</p>
            <p><strong>🕴️ עמדה:</strong> {stats['position']}</p>
            <p><strong>🎯 הופעות:</strong> {stats['appearances']}</p>
            <p><strong>⚽ שערים:</strong> {stats['goals']}</p>
            <p><strong>⭐ דירוג:</strong> {stats['rating']}</p>
            <p style='color:#4a5568;'>API‑Football | עונת 2023</p>
        </div>
        """, unsafe_allow_html=True)

        if isinstance(stats["goals"], int):
            fig, ax = plt.subplots()
            ax.bar("2023", stats["goals"], color="seagreen")
            ax.set_ylim(0, max(stats["goals"], 10) + 2)
            ax.set_title("⚽ שערים בעונת 2023")
            st.pyplot(fig)
    else:
        st.warning("⚠️ שחקן לא נמצא במאגר לעונת 2023.")

# ---------- FOOTER ----------
st.markdown(f"""
<div class='footer'>
    בקשות שנותרו להיום: {remaining_requests()} / {REQUEST_LIMIT}<br>
    GSTAT משתמש אך ורק במידע חוקי מ־API‑Football
</div>
""", unsafe_allow_html=True)

