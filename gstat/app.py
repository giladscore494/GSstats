# GSTAT Streamlit App – Cloud‑only version
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
SEASON_CANDIDATES = ["2024", "2023", "2022", "2021"]
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ---------- REQUEST COUNTER ----------
def load_requests():
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    data = {}
    if os.path.exists(REQUESTS_FILE):
        with open(REQUESTS_FILE, "r") as f:
            data =
