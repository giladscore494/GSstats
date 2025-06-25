import streamlit as st
import requests
import json
import os
from datetime import datetime, timezone
import matplotlib.pyplot as plt
import re

# --- הגדרות בסיסיות ---
st.set_page_config(page_title="GSTAT", layout="centered")
API_KEY = st.secrets["api_key"]
REQUEST_LIMIT = 100
REQUESTS_FILE = "requests_today.json"
SEASON = "2023"

# --- עיצוב ---
st.markdown("""
<style>
    body {background: linear-gradient(to right, #f4f6f9, #e2e8f0);font-family:'Segoe UI',sans-serif;}
    .title {text-align:center;font-size:2.8em;font-weight:bold;margin:20px;}
    .box {background:white;padding:24px;border-radius:20px;box-shadow:0 6px 16px rgba(0,0,0,0.08);}
    .footer {text-align:center;font-size:0.9em;color:#718096;margin-top:40px;}
</style>
""", unsafe_allow_html=True)
st.markdown('<div class="title">GSTAT ⭐ נתוני כדורגל חכמים</div>', unsafe_allow_html=True)

# --- ניהול בקשות ---
def load_requests():
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    if os.path.exists(REQUESTS_FILE):
        with open(REQUESTS_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {}
    if today not in data:
        data[today] = 0
    return data, today

def add_request():
    data, today = load_requests()
    data[today] += 1
    with open(REQUESTS_FILE, "w") as f:
        json.dump(data, f)

def remaining_requests():
    data, today = load_requests()
    return REQUEST_LIMIT - data[today]

# --- שליחת בקשת API אחת בלבד ---
def raw_api(endpoint, params):
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    url = f"https://api-football-v1.p.rapidapi.com/v3/{endpoint}"
    response = requests.get(url, headers=headers, params=params)
    add_request()
    return response.json()

# --- חיפוש שחקן ---
def search_player(name):
    result = raw_api("players", {"search": name, "season": SEASON})
    for r in result.get("response", []):
        pname = r["player"]["name"].lower()
        if name.lower() in pname or pname in name.lower():
            return r["player"]["id"]
    return None

# --- סטטיסטיקות ---
def get_stats(pid):
    result = raw_api("players", {"id": pid, "season": SEASON})
    if result.get("response"):
        s = result["response"][0]["statistics"][0]
        return {
            "team": s["team"]["name"],
            "position": s["games"]["position"],
            "appearances": s["games"]["appearences"],
            "goals": s["goals"]["total"],
            "rating": s["games"].get("rating", "—")
        }
    return None

# --- ממשק משתמש ---
name = st.text_input("הכנס שם שחקן (בעברית או באנגלית)")
if name:
    pid = search_player(name)
    if not pid:
        st.error("⚠️ שחקן לא נמצא במאגר לעונת 2023.")
    else:
        stats = get_stats(pid)
        if not stats:
            st.warning("לא נמצאו סטטיסטיקות לשחקן.")
        else:
            st.markdown(f"""
            <div class='box'>
                <h4>🌟 {name.title()}</h4>
                <p><strong>🏟️ קבוצה:</strong> {stats['team']}</p>
                <p><strong>🕴️ עמדה:</strong> {stats['position']}</p>
                <p><strong>🎯 הופעות:</strong> {stats['appearances']}</p>
                <p><strong>⚽ שערים:</strong> {stats['goals']}</p>
                <p><strong>⭐ דירוג:</strong> {stats['rating']}</p>
            </div>
            """, unsafe_allow_html=True)

            fig, ax = plt.subplots()
            ax.bar(SEASON, stats["goals"], color="seagreen")
            ax.set_title(f"שערים בעונת {SEASON}")
            st.pyplot(fig)

# --- תחתית ---
st.markdown(f"<div class='footer'>בקשות שנותרו להיום: {remaining_requests()} / {REQUEST_LIMIT}</div>", unsafe_allow_html=True)
