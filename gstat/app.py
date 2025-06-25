import streamlit as st
import requests
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="GSTAT", layout="centered")

# ---------- CSS ----------
css = """
<style>
    body {
        background: linear-gradient(to right, #f4f6f9, #e2e8f0);
        font-family: 'Segoe UI', sans-serif;
        margin: 0;
        padding: 0;
    }
    .title {
        text-align: center;
        font-size: 3em;
        font-weight: bold;
        color: #1a202c;
        margin-top: 30px;
        margin-bottom: 10px;
        letter-spacing: 1px;
    }
    .box {
        background-color: white;
        padding: 30px;
        border-radius: 24px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
        margin: 30px auto;
        max-width: 700px;
        transition: all 0.3s ease-in-out;
    }
    .box:hover {
        transform: scale(1.01);
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.15);
    }
    .footer {
        text-align: center;
        font-size: 0.9em;
        color: #718096;
        margin-top: 40px;
        padding-bottom: 20px;
    }
    .credit {
        font-size: 0.95em;
        color: #4a5568;
        margin-top: 20px;
    }
    a {
        color: #2b6cb0;
        text-decoration: none;
    }
    a:hover {
        text-decoration: underline;
    }
    ul {
        padding-left: 20px;
    }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

st.markdown('<div class="title">GSTAT ⭐ נתוני כדורגל חכמים</div>', unsafe_allow_html=True)

# ---------- CONFIG & LIMITING ----------
API_KEY = "0e57f2f38dmsh1962d384d4d8f07p1f24bbjsn56d0996a7b97"
REQUESTS_FILE = "requests_today.json"
REQUEST_LIMIT = 100

# Load or initialize daily request counter
def load_requests():
    today = datetime.today().strftime('%Y-%m-%d')
    if os.path.exists(REQUESTS_FILE):
        with open(REQUESTS_FILE, 'r') as f:
            data = json.load(f)
    else:
        data = {}
    if today not in data:
        data[today] = 0
    return data, today

def save_requests(data):
    with open(REQUESTS_FILE, 'w') as f:
        json.dump(data, f)

# ---------- API CALL ----------
def get_api_football_stats(player_name: str, season: str) -> dict:
    data, today = load_requests()
    if data[today] >= REQUEST_LIMIT:
        st.error("❌ חרגת מהמכסה היומית (100 בקשות). נסה שוב מחר.")
        return {}

    url = "https://api-football-v1.p.rapidapi.com/v3/players"
    querystring = {"search": player_name, "season": season}
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    try:
        res = requests.get(url, headers=headers, params=querystring, timeout=10)
        res.raise_for_status()
        data[today] += 1
        save_requests(data)
        stats = {}
        js = res.json()
        if js.get("response"):
            p = js["response"][0]
            stats["team"] = p["statistics"][0]["team"]["name"]
            stats["position"] = p["statistics"][0]["games"]["position"]
            stats["appearances"] = p["statistics"][0]["games"]["appearences"]
            stats["goals"] = p["statistics"][0]["goals"]["total"]
            stats["rating"] = p["statistics"][0]["games"].get("rating", "—")
        return stats
    except Exception as e:
        st.error("שגיאה בשליפת הנתונים מה-API")
        return {}

# ---------- GRAPH ----------
def plot_goals_bar(goals: int, season: str):
    fig, ax = plt.subplots()
    ax.bar([season], [goals], color='mediumseagreen')
    ax.set_title(f"⚽ שערים בעונת {season}")
    ax.set_ylim(0, max(goals, 10) + 2)
    st.pyplot(fig)

# ---------- UI ----------
name_input = st.text_input("הכנס שם של שחקן (באנגלית בלבד)")
season = st.selectbox("בחר עונה", ["2024", "2023"], index=0)

if name_input:
    player_name = name_input.strip()
    stats = get_api_football_stats(player_name, season)

    if stats:
        name_disp = player_name.title()
        team = stats.get("team", "—")
        pos = stats.get("position", "—")
        appearances = stats.get("appearances", "—")
        goals = stats.get("goals", "—")
        rating = stats.get("rating", "—")

        st.markdown(f"""
        <div class='box'>
            <h3>🌟 {name_disp}</h3>
            <p><strong>🏟️ קבוצה:</strong> {team}</p>
            <p><strong>🕴️ עמדה:</strong> {pos}</p>
            <p><strong>🎯 הופעות:</strong> {appearances}</p>
            <p><strong>⚽ שערים:</strong> {goals}</p>
            <p><strong>⭐ דירוג:</strong> {rating}</p>
            <p class='credit'>מקור: API-Football (RapidAPI) לעונת {season}</p>
        </div>
        """, unsafe_allow_html=True)

        if isinstance(goals, int):
            st.markdown("### 🔼 גרף שערים")
            plot_goals_bar(goals, season)

# ---------- FOOTER ----------
st.markdown(
    """
<div class="footer">
    GSTAT מציג מידע חוקי ממקורות API רשמיים בלבד. אין שימוש בנתונים מוגני זכויות יוצרים ללא הרשאה.
</div>
""",
    unsafe_allow_html=True,
)
