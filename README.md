# Sukoon — سکون

**Free sleep & calm studio.** Guided breathing, original sleep stories, synthesised sleep sounds, dhikr counter, prayer-aware wind-down planner, sleep diary — everything free, everything unlocked.

An original clean-room build from the daily-app-gap-build series. It fills the gaps in **Calm** (Premium $16.99/month or $79.99/year, Trustpilot 1.3/5 — billing complaints dominate, no Urdu, no Islamic content). Sukoon is **not affiliated** with Calm or Headspace.

## Why Sukoon exists

| | Calm Premium | Sukoon |
|---|---|---|
| Price | $79.99/year (2026) | **Free, forever** |
| Sleep Stories | 100+, mostly paywalled | 3 original + AI generator, free |
| Breathing patterns | 1 free (Relax) | 4 patterns, free |
| Sleep sounds | Paywalled library | 4 synthesised sounds, free |
| Urdu / Roman-Urdu | No | **EN + Roman-Urdu + Urdu** |
| Dhikr / Isha-aware wind-down | No | **Yes** |
| Billing traps | Trustpilot 1.3/5 | No billing at all |

Gap report: `../market-gaps/daily/2026-11-08-sukoon.md` (in the builder's workspace).

## Features

- **Guided breathing** — 4-7-8 (19 s/cycle), Box 4-4-4-4 (16 s), Coherent 5-5 (10 s, 6 breaths/min), 4-4-6 (14 s). Animated pacer, phase labels, session timer. Cycle math is server-verified.
- **Sleep stories** — 3 original stories written for Sukoon (EN, Roman-Urdu, Urdu script), read aloud by the device's own speech voices, plus a **Gemini AI story generator** that writes a new original story on a theme you pick (validated: 250–1500 words, 3+ paragraphs, calm ending, labelled AI-written).
- **Sleep sounds** — rain, brown noise, ocean waves, fan, **synthesised live in the browser** with the Web Audio API from published filter recipes. No audio files, no licences, no streaming.
- **Dhikr counter (Tasbih)** — SubhanAllah 33, Alhamdulillah 33, Allahu Akbar 34, La ilaha illallah 100, Astaghfirullah 100, Durood Sharif 100, with round tracking and daily totals (localStorage).
- **Wind-down planner** — enter your Isha time and bedtime; it builds tonight's schedule (dhikr → breathing → story → sounds) that ends exactly at bedtime. Prayer times are never fetched or guessed — you enter Isha yourself. Plus a **Gemini AI wind-down plan** from bedtime, wake time, stress level and tonight's worry.
- **Sleep diary** — log bedtime, wake time, quality 1–5; duration and 7-day average computed honestly. Data stays in your browser (localStorage); nothing is stored server-side.

## Honest limits

- Sukoon is a calm and sleep **aid**, not medical advice and not a treatment for insomnia or anxiety. Persistent poor sleep → see a clinician.
- Story narration uses voices installed on **your** device; Urdu voice support varies by phone/browser.
- Sleep sounds are synthesised filtered noise, not recordings of real rain or ocean.
- AI stories and plans need `GEMINI_API_KEY` in the environment; without it everything else works fully and the page says the AI is off.

## Run

```bash
# as a FastAPI route (lives at /sukoon in the clinic-demo app)
pip install fastapi uvicorn
uvicorn app.main:app --reload   # from the clinic-demo repo
```

Or mount the router from this package in any FastAPI app:

```python
from fastapi import FastAPI
from sukoon.routes import router as sukoon_router
app = FastAPI()
app.include_router(sukoon_router)
```

## Tests

```bash
python tests/verify.py   # exit 0 = all pass; no network, no key needed
```

Tests cover breathing cycle math (hand-computed), dhikr rounds, wind-down schedule math (no overlap, ends at bedtime, short-window shrink), sleep duration across midnight, 7-day averages, story validation and content checks, sound recipes, AI-output shape validators, and the HTTP routes via TestClient.

## License

MIT — original code and original stories, written for this project.
