"""Quick Gemini connection test. Never prints your key.

Run from the backend/ folder:   python tools/test_gemini.py   (or add model names to test)
"""
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
KEY = os.getenv("GEMINI_API_KEY", "").strip()
MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest").strip() or "gemini-flash-latest"
BASE = "https://generativelanguage.googleapis.com/v1beta"
H = {"x-goog-api-key": KEY}


def show(label, started, r=None, err=None):
    secs = time.monotonic() - started
    if err:
        print(f"[FAIL] {label}: {err.__class__.__name__} after {secs:.1f}s")
    else:
        msg = ""
        if r.status_code != 200:
            try:
                msg = " - " + r.json().get("error", {}).get("message", "")[:200]
            except ValueError:
                msg = " - " + r.text[:200]
        print(f"[{'OK' if r.status_code == 200 else 'FAIL'}] {label}: HTTP {r.status_code} in {secs:.1f}s{msg}")
    return secs


if not KEY:
    sys.exit("[FAIL] No GEMINI_API_KEY in backend/.env")
print(f"Key found ({len(KEY)} characters, starts with {KEY[:3]}...). Model: {MODEL}\n")

# 1. Can we reach Google at all, and which models does this key see?
t = time.monotonic()
try:
    r = httpx.get(f"{BASE}/models", headers=H, params={"pageSize": 200}, timeout=30)
    show("1. Reach Google + list models", t, r)
    if r.status_code == 200:
        names = [m["name"].split("/")[-1] for m in r.json().get("models", [])
                 if "generateContent" in m.get("supportedGenerationMethods", [])]
        flash = [n for n in names if "flash" in n]
        print("   Flash models this key can use:", ", ".join(flash[:12]) or "(none)")
except httpx.HTTPError as e:
    show("1. Reach Google + list models", t, err=e)


def ask(label, model, extra=None):
    body = {"contents": [{"role": "user", "parts": [{"text": "Reply with just the word: hello"}]}],
            "generationConfig": {"maxOutputTokens": 50, **(extra or {})}}
    t = time.monotonic()
    try:
        r = httpx.post(f"{BASE}/models/{model}:generateContent", headers=H, json=body, timeout=30)
        show(label, t, r)
        if r.status_code == 200:
            try:
                print("   Reply:", r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()[:60])
            except (KeyError, IndexError):
                print("   (reply had no text)")
    except httpx.HTTPError as e:
        show(label, t, err=e)


# 2. Tiny question to several models (or the ones you name: python tools/test_gemini.py gemini-2.5-flash)
models = sys.argv[1:] or [MODEL, "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3.1-flash-lite"]
seen = []
for m in models:
    if m not in seen:
        seen.append(m)
        ask(f"2. Tiny question to {m}", m)
print("\nPick the fastest [OK] model and put it in backend/.env as GEMINI_MODEL=<name>, then restart.")
print("Copy everything above (it doesn't include your key) and send it to Claude.")
