import streamlit as st
import requests
import json
import os
from datetime import datetime, timezone
import matplotlib.pyplot as plt
import re

st.set_page_config(page_title="GSTAT", layout="centered")

st.markdown("""
<style>
    body {background: linear-gradient(to right, #f4f6f9, #e2e8f0);font-family:'Segoe UI',sans-serif;margin:0;}
    .title {text-align:center;font-size:3em;font-weight:bold;color:#1a202c;margin-top:30px;margin-bottom:10px;letter-spacing:1px;}
    .box {background:white;padding:30px;border-radius:24px;box-shadow:0 8px 20px rgba(0,0,0,0.1);margin:30px auto;max-width:700px;transition:all .3s ease;}
    .box:hover {transform:scale(1.01);box-shadow:0 10px 24px rgba(0,0,0,0.15);}
    .footer {text-align:center;font-size:0.9em;color:#718096;margin-top:40px;padding-bottom:20px;}
    .credit {font-size:0.95em;color:#4a5568;margin-top:20px;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">GSTAT ⭐ נתוני כדורגל חכמים</div>', unsafe_allow_html=True)

# ---------- CONFIG ----------
API_KEY = st.secrets["api_key"]
REQUEST_LIMIT = 100
REQUESTS_FILE = "requests_today.json"
SEASON = "2023"

# ---------- REQUEST COUNTER ----------
def load_requests():
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    data = {}
    if os.path.exists(REQUESTS_FILE):
        with open(REQUESTS_FILE, "r") as f:
            data = json.load(f)
    if today not in data:
        data[today] = 0
        with open(REQUESTS_FILE, "w") as f:
            json.dump(data, f)
    return data, today

def add_api_call():
    data, today = load_requests()
    data[today] += 1
    with open(REQUESTS_FILE, "w") as f:
        json.dump(data, f)

def remaining_requests():
    data, today = load_requests()
    return REQUEST_LIMIT - data[today]

# ---------- API ----------
def raw_api(endpoint: str, params: dict):
    url = f"https://api-football-v1.p.rapidapi.com/v3/{endpoint}"
    headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
    res = requests.get(url, headers=headers, params=params, timeout=10)
    res.raise_for_status()
    add_api_call()
    return res.json()

@st.cache_data(show_spinner=False)
def get_suggestions(name: str):
    if len(name) < 2:
        return []
    js = raw_api("players", {"search": name, "season": SEASON})
    return [p["player"]["name"] for p in js.get("response", [])][:10]

@st.cache_data(show_spinner=False)
def get_player_id(name: str):
    name_lower = name.lower()
    js = raw_api("players", {"search": name, "season": SEASON})
    for p in js.get("response", []):
        full_name = p["player"]["name"].lower()
        if name_lower in full_name or full_name in name_lower:
            return p["player"]["id"]
    if js.get("response"):
        return js["response"][0]["player"]["id"]
    return None

@st.cache_data(show_spinner=False)
def get_stats(pid: int):
    js = raw_api("players", {"id": pid, "season": SEASON})
    if js.get("response"):
        s = js["response"][0]["statistics"][0]
        return {
            "team": s["team"]["name"],
            "position": s["games"]["position"],
            "appearances": s["games"]["appearences"],
            "goals": s["goals"]["total"],
            "rating": s["games"].get("rating", "—")
        }
    return {}

normalize = lambda n: re.sub(r"[^a-zA-Zא-ת\s]", "", n.strip()).title()

# ---------- UI ----------
name = st.text_input("הכנס שם של שחקן (בעברית או באנגלית)")
if name:
    suggestions = get_suggestions(name)
    pick = st.selectbox("בחר שחקן מהרשימה", suggestions or [name])
    name_norm = normalize(pick)

    pid = get_player_id(name_norm)
    if not pid:
        st.warning("⚠️ שחקן לא נמצא במאגר.")
    else:
        stats = get_stats(pid)
        if not stats:
            st.warning("לא נמצאו נתונים סטטיסטיים.")
        else:
            st.markdown(f"""
            <div class='box'>
                <h3>🌟 {name_norm}</h3>
                <p><strong>🏟️ קבוצה:</strong> {stats['team']}</p>
                <p><strong>🕴️ עמדה:</strong> {stats['position']}</p>
                <p><strong>🎯 הופעות:</strong> {stats['appearances']}</p>
                <p><strong>⚽ שערים:</strong> {stats['goals']}</p>
                <p><strong>⭐ דירוג:</strong> {stats['rating']}</p>
                <p class='credit'>API‑Football | עונה {SEASON}</p>
            </div>
            """, unsafe_allow_html=True)

            if isinstance(stats["goals"], int):
                fig, ax = plt.subplots()
                ax.bar(SEASON, stats["goals"], color="mediumseagreen")
                ax.set_ylim(0, max(stats["goals"], 10) + 2)
                ax.set_title(f"⚽ שערים בעונת {SEASON}")
                st.pyplot(fig)

# ---------- FOOTER ----------
st.markdown(f"""
<div class='footer'>
GSTAT מציג מידע חוקי ממקורות API רשמיים בלבד.<br>
בקשות שנותרו להיום: {remaining_requests()} / {REQUEST_LIMIT}
</div>
""", unsafe_allow_html=True)
