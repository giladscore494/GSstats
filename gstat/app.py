# GSTAT - גרסה עם חסימה ב־90+ בקשות
import streamlit as st
import requests
import re
import matplotlib.pyplot as plt

st.set_page_config(page_title="GSTAT", layout="centered")

st.markdown("""
<style>
    body {background: linear-gradient(to right, #f0f4f8, #d9e2ec);}
    .title {text-align:center;font-size:2.6em;font-weight:bold;margin-top:20px;color:#1a202c;}
    .box {background:white;padding:25px;border-radius:16px;box-shadow:0 4px 14px rgba(0,0,0,0.1);margin-top:30px;}
    .footer {text-align:center;margin-top:50px;color:#555;font-size:0.9em;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">GSTAT ⭐ נתוני כדורגל חכמים</div>', unsafe_allow_html=True)

API_KEY = st.secrets["api_key"]
API_HOST = "api-football-v1.p.rapidapi.com"
LEAGUE_ID = 39  # Premier League
SEASON = "2023"

HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": API_HOST
}

def normalize_name(name):
    return re.sub(r"[^a-zA-Zא-ת\s]", "", name.strip()).title()

def fetch_player(name):
    url = "https://api-football-v1.p.rapidapi.com/v3/players"
    params = {"search": name, "season": SEASON, "league": LEAGUE_ID}
    res = requests.get(url, headers=HEADERS, params=params)
    remaining = res.headers.get("x-ratelimit-requests-remaining")
    try:
        remaining = int(remaining)
    except:
        remaining = 0
    return res.json(), remaining

def extract_stats(js):
    if js.get("response"):
        p = js["response"][0]
        info = p["player"]
        stats = p["statistics"][0]
        return {
            "name": info["name"],
            "team": stats["team"]["name"],
            "position": stats["games"]["position"],
            "appearances": stats["games"]["appearences"],
            "goals": stats["goals"]["total"],
            "rating": stats["games"].get("rating", "—")
        }
    return None

# ---------- UI ----------
name = st.text_input("הכנס שם שחקן (בעברית או באנגלית)")

if name:
    name = normalize_name(name)
    data, remain = fetch_player(name)

    if remain <= 10:
        st.error(f"❌ הגבלת בקשות יומית כמעט הושגה ({100 - remain}/100). החיפוש חסום זמנית.")
    else:
        stats = extract_stats(data)
        if not stats:
            st.warning(f"שחקן לא נמצא במאגר לעונת {SEASON}.")
        else:
            st.markdown(f"""
            <div class="box">
                <h4>🌟 {stats['name']}</h4>
                <p><b>קבוצה:</b> {stats['team']}</p>
                <p><b>עמדה:</b> {stats['position']}</p>
                <p><b>הופעות:</b> {stats['appearances']}</p>
                <p><b>שערים:</b> {stats['goals']}</p>
                <p><b>דירוג:</b> {stats['rating']}</p>
                <p style="color:gray;font-size:0.85em;">מקור: API-Football | עונה {SEASON}</p>
            </div>
            """, unsafe_allow_html=True)

            if isinstance(stats["goals"], int):
                fig, ax = plt.subplots()
                ax.bar(SEASON, stats["goals"], color="seagreen")
                ax.set_ylim(0, max(10, stats["goals"] + 2))
                ax.set_title("⚽ שערים בעונה")
                st.pyplot(fig)

    st.markdown(f"<div class='footer'>בקשות שנותרו להיום: {remain} / 100</div>", unsafe_allow_html=True)
