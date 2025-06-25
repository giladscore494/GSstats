import streamlit as st
import requests
import matplotlib.pyplot as plt
import re

# ---------- CONFIG ----------
API_KEY   = st.secrets["api_key"]        # מוגדר ב-Streamlit Cloud
SEASON    = "2023"                       # עונה יחידה – פחות בזבוז
LEAGUE_ID = 39                           # פרמייר-ליג (אפשר לשנות)

# ---------- עיצוב בסיסי ----------
st.set_page_config(page_title="GSTAT", layout="centered")
st.markdown("""
<style>
 body{background:linear-gradient(to right,#f4f6f9,#e2e8f0);font-family:'Segoe UI',sans-serif;margin:0}
 .title{text-align:center;font-size:3em;font-weight:bold;margin:20px}
 .box{background:#fff;padding:24px;border-radius:20px;box-shadow:0 6px 16px rgba(0,0,0,.08)}
 .footer{text-align:center;font-size:.9em;color:#718096;margin-top:30px}
</style>""",unsafe_allow_html=True)
st.markdown("<div class='title'>GSTAT ⭐ נתוני כדורגל חכמים</div>",unsafe_allow_html=True)

# ---------- API helper ----------
def call_api(endpoint:str, params:dict):
    url = f"https://api-football-v1.p.rapidapi.com/v3/{endpoint}"
    headers = {"X-RapidAPI-Key":API_KEY,
               "X-RapidAPI-Host":"api-football-v1.p.rapidapi.com"}
    r = requests.get(url,headers=headers,params=params,timeout=10)
    r.raise_for_status()
    remaining = r.headers.get("x-ratelimit-requests-remaining", "?")
    return r.json(), remaining

# ---------- חיפוש שחקן ----------
def find_player_id(name:str):
    params = {"search":name,"season":SEASON,"league":LEAGUE_ID}
    js,_ = call_api("players",params)
    for p in js.get("response",[]):
        pname = p["player"]["name"].lower()
        if name.lower() in pname or pname in name.lower():
            return p["player"]["id"]
    if js.get("response"):
        return js["response"][0]["player"]["id"]
    return None

# ---------- סטטיסטיקות ----------
def fetch_stats(pid:int):
    js, remaining = call_api("players",{"id":pid,"season":SEASON})
    if not js.get("response"):
        return None, remaining
    s = js["response"][0]["statistics"][0]
    data = {
        "team":        s["team"]["name"],
        "position":    s["games"]["position"],
        "apps":        s["games"]["appearences"],
        "goals":       s["goals"]["total"],
        "rating":      s["games"].get("rating","—")
    }
    return data, remaining

# ---------- normalize ----------
clean = lambda n: re.sub(r"[^a-zA-Zא-ת\s]", "", n.strip()).title()

# ---------- UI ----------
name_input = st.text_input("הכנס שם שחקן (בעברית או באנגלית)")
if name_input:
    name = clean(name_input)
    pid = find_player_id(name)
    if not pid:
        st.warning("⚠️ שחקן לא נמצא בליגת הפרמייר-ליג לעונת 2023.")
    else:
        stats, remain = fetch_stats(pid)
        if not stats:
            st.warning("לא נמצאו נתונים סטטיסטיים.")
        else:
            st.markdown(f"""
            <div class='box'>
              <h4>🌟 {name}</h4>
              <p><b>🏟️ קבוצה:</b> {stats['team']}</p>
              <p><b>🕴️ עמדה:</b> {stats['position']}</p>
              <p><b>🎯 הופעות:</b> {stats['apps']}</p>
              <p><b>⚽ שערים:</b> {stats['goals']}</p>
              <p><b>⭐ דירוג:</b> {stats['rating']}</p>
              <p style='font-size:.85em;color:#4a5568'>מקור: API-Football | עונת {SEASON}</p>
            </div>
            """,unsafe_allow_html=True)

            # גרף שערים
            fig, ax = plt.subplots()
            ax.bar(SEASON, stats["goals"], color="seagreen")
            ax.set_title(f"שערים בעונת {SEASON}")
            ax.set_ylim(0, max(stats["goals"],10)+2)
            st.pyplot(fig)

            st.markdown(f"<div class='footer'>בקשות שנותרו להיום (ע"\
                        f"פ RapidAPI): {remain} / {REQUEST_LIMIT}</div>",
                        unsafe_allow_html=True)

