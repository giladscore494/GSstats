import streamlit as st
import requests
import matplotlib.pyplot as plt
import re
from datetime import datetime, timezone

# ---------- CONFIG ----------
API_KEY       = st.secrets["api_key"]
REQUEST_LIMIT = 100                      # גבול היומי של RapidAPI
SEASON        = "2023"
LEAGUE_ID     = 39                       # פרמייר-ליג

# ---------- עיצוב ----------
st.set_page_config(page_title="GSTAT", layout="centered")
st.markdown("""
<style>
 body{background:linear-gradient(to right,#f4f6f9,#e2e8f0);font-family:'Segoe UI',sans-serif;}
 .title{text-align:center;font-size:3em;font-weight:bold;margin:20px}
 .box{background:#fff;padding:24px;border-radius:20px;box-shadow:0 6px 16px rgba(0,0,0,.08)}
 .footer{text-align:center;font-size:.9em;color:#718096;margin-top:30px}
</style>""", unsafe_allow_html=True)
st.markdown("<div class='title'>GSTAT ⭐ נתוני כדורגל חכמים</div>", unsafe_allow_html=True)

# ---------- API ----------
def call_api(endpoint:str, params:dict):
    url     = f"https://api-football-v1.p.rapidapi.com/v3/{endpoint}"
    headers = {"X-RapidAPI-Key":API_KEY,
               "X-RapidAPI-Host":"api-football-v1.p.rapidapi.com"}
    r = requests.get(url, headers=headers, params=params, timeout=10)
    r.raise_for_status()
    remain = r.headers.get("x-ratelimit-requests-remaining", "?")
    return r.json(), remain

def search_player_id(name:str):
    js,_ = call_api("players",
            {"search":name, "season":SEASON, "league":LEAGUE_ID})
    for p in js.get("response",[]):
        full = p["player"]["name"].lower()
        if name.lower() in full or full in name.lower():
            return p["player"]["id"]
    if js.get("response"):
        return js["response"][0]["player"]["id"]
    return None

def fetch_stats(pid:int):
    js, remain = call_api("players",
            {"id":pid, "season":SEASON})
    if not js.get("response"):
        return None, remain
    s = js["response"][0]["statistics"][0]
    return {
        "team":   s["team"]["name"],
        "pos":    s["games"]["position"],
        "apps":   s["games"]["appearences"],
        "goals":  s["goals"]["total"],
        "rating": s["games"].get("rating","—")
    }, remain

clean = lambda t: re.sub(r"[^a-zA-Zא-ת\s]", "", t.strip()).title()

# ---------- UI ----------
query = st.text_input("הכנס שם שחקן (בעברית או באנגלית)")
if query:
    pid = search_player_id(clean(query))
    if not pid:
        st.error("שחקן לא נמצא בפרמייר-ליג לעונת 2023.")
    else:
        data, remaining = fetch_stats(pid)
        if not data:
            st.warning("לא נמצאו נתונים סטטיסטיים.")
        else:
            st.markdown(f"""
            <div class='box'>
              <h4>🌟 {clean(query)}</h4>
              <p><b>🏟️ קבוצה:</b> {data['team']}</p>
              <p><b>🕴️ עמדה:</b> {data['pos']}</p>
              <p><b>🎯 הופעות:</b> {data['apps']}</p>
              <p><b>⚽ שערים:</b> {data['goals']}</p>
              <p><b>⭐ דירוג:</b> {data['rating']}</p>
              <p style='font-size:.85em;color:#4a5568'>
                 מקור: API-Football | עונת {SEASON}
              </p>
            </div>""", unsafe_allow_html=True)

            if isinstance(data["goals"], int):
                fig, ax = plt.subplots()
                ax.bar(SEASON, data["goals"], color="seagreen")
                ax.set_ylim(0, max(data["goals"],10)+2)
                ax.set_title(f"שערים בעונת {SEASON}")
                st.pyplot(fig)

            st.markdown(
              f"<div class='footer'>בקשות שנותרו להיום (ע\"פ RapidAPI): "
              f"{remaining} / {REQUEST_LIMIT}</div>",
              unsafe_allow_html=True)
