"""Sukoon verification — breathing math, dhikr rounds, wind-down
schedule math, sleep duration/averages, story validation + content,
sound recipes, AI-output shape validators, routes.

Run: python tests/verify.py (or ~/workspace/.venv-fc/bin/python)
Exit code 0 = all pass. No network, no key needed (AI tests only
check the no-key error path and the shape validators, never a live
call). All date/time tests use fixed values so they are deterministic
whatever day the suite runs.
"""

import os
import sys

# Force the no-key path so AI-status tests are deterministic.
for _k in ("GEMINI_API_KEY", "GEMINI_APIkey"):
    os.environ.pop(_k, None)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sukoon import engine, gemini, stories  # noqa: E402

PASS = 0
FAIL = []


def check(name, cond, extra=""):
    global PASS
    if cond:
        PASS += 1
    else:
        FAIL.append(f"{name} {extra}")


# --- breathing: cycle seconds (hand-computed) ---
check("478 cycle 19s", engine.cycle_seconds("478") == 19)
check("box cycle 16s", engine.cycle_seconds("box") == 16)
check("coherent cycle 10s", engine.cycle_seconds("coherent") == 10)
check("446 cycle 14s", engine.cycle_seconds("446") == 14)
check("unknown pattern None", engine.cycle_seconds("nope") is None)
check("478 bpm 3.2", engine.breaths_per_minute("478") == 3.2)
check("coherent bpm 6.0", engine.breaths_per_minute("coherent") == 6.0)
check("box bpm 3.8", engine.breaths_per_minute("box") == 3.8)

sched, err = engine.breathing_schedule("478", 4)
check("478x4 ok", err is None and sched is not None, str(err))
check("478x4 total 76s", sched["total_seconds"] == 76, str(sched["total_seconds"]))
check("478x4 phases 12", len(sched["schedule"]) == 12)
check("478 first phase inhale 4", sched["schedule"][0] == {
    "cycle": 1, "phase": "inhale", "label": "Saans andar",
    "seconds": 4, "start": 0, "end": 4}, str(sched["schedule"][0]))
check("478 second phase hold 7", sched["schedule"][1]["phase"] == "hold"
      and sched["schedule"][1]["seconds"] == 7
      and sched["schedule"][1]["start"] == 4
      and sched["schedule"][1]["end"] == 11)
check("478 last end == total", sched["schedule"][-1]["end"] == 76)
check("478 phases contiguous",
      all(sched["schedule"][i]["end"] == sched["schedule"][i + 1]["start"]
          for i in range(len(sched["schedule"]) - 1)))
sched2, _ = engine.breathing_schedule("box", 2)
check("boxx2 total 32s", sched2["total_seconds"] == 32)
check("boxx2 phases 8", len(sched2["schedule"]) == 8)
_, err = engine.breathing_schedule("478", 0)
check("0 cycles rejected", err is not None)
_, err = engine.breathing_schedule("478", 21)
check("21 cycles rejected", err is not None)
_, err = engine.breathing_schedule("nope", 4)
check("bad pattern rejected", err is not None)

# --- dhikr ---
r, err = engine.dhikr_progress("subhanallah", 33)
check("33 = 1 round", err is None and r["rounds"] == 1 and r["remainder"] == 0
      and r["round_done"] is True, str(r))
r, _ = engine.dhikr_progress("subhanallah", 34)
check("34 = 1 round + 1", r["rounds"] == 1 and r["remainder"] == 1
      and r["round_done"] is False)
r, _ = engine.dhikr_progress("subhanallah", 66)
check("66 = 2 rounds", r["rounds"] == 2 and r["remainder"] == 0)
r, _ = engine.dhikr_progress("subhanallah", 0)
check("0 = 0 rounds", r["rounds"] == 0 and r["round_done"] is False)
r, _ = engine.dhikr_progress("allahu_akbar", 34)
check("akbar 34 = 1 round", r["rounds"] == 1 and r["target"] == 34)
r, _ = engine.dhikr_progress("la_ilaha", 100)
check("la ilaha 100 = 1 round", r["rounds"] == 1 and r["target"] == 100)
_, err = engine.dhikr_progress("nope", 5)
check("bad dhikr rejected", err is not None)
_, err = engine.dhikr_progress("subhanallah", -1)
check("negative count rejected", err is not None)
check("6 dhikr presets", len(engine.DHIKR_PRESETS) == 6)

# --- time parsing ---
check("parse 21:00", engine.parse_hhmm("21:00") == 1260)
check("parse 06:30", engine.parse_hhmm("06:30") == 390)
check("parse bad", engine.parse_hhmm("25:00") is None)
check("parse junk", engine.parse_hhmm("raat") is None)
check("hhmm wrap 1500", engine.minutes_to_hhmm(1500) == "01:00")
check("hhmm 1350", engine.minutes_to_hhmm(1350) == "22:30")

# --- wind-down ---
plan, err = engine.build_wind_down("21:00", "23:00")
check("wind 21-23 ok", err is None and plan is not None, str(err))
check("wind window 120", plan["window_minutes"] == 120)
blocks = plan["blocks"]
check("wind 4 blocks", len(blocks) == 4)
check("wind blocks sum 120", sum(b["minutes"] for b in blocks) == 120)
check("wind first dhikr 10", blocks[0] == {"block": "dhikr", "minutes": 10,
      "start": "21:00", "end": "21:10"}, str(blocks[0]))
check("wind sounds fill 85", blocks[3]["block"] == "sounds"
      and blocks[3]["minutes"] == 85 and blocks[3]["end"] == "23:00")
check("wind contiguous",
      all(blocks[i]["end"] == blocks[i + 1]["start"] for i in range(3)))
plan, _ = engine.build_wind_down("22:30", "01:00")
check("wind overnight 150", plan["window_minutes"] == 150
      and plan["blocks"][-1]["end"] == "01:00")
plan, _ = engine.build_wind_down("22:30", "23:00")
check("wind short 30", plan["window_minutes"] == 30
      and sum(b["minutes"] for b in plan["blocks"]) == 30
      and plan["blocks"][0]["minutes"] == 5  # short dhikr
      and plan["blocks"][3]["minutes"] == 12  # sounds remainder
      and plan["blocks"][-1]["end"] == "23:00")
plan, _ = engine.build_wind_down("22:45", "23:00")
check("wind 15 min", plan["window_minutes"] == 15
      and plan["blocks"][-1]["minutes"] >= 5
      and plan["blocks"][-1]["end"] == "23:00")
_, err = engine.build_wind_down("22:55", "23:00")
check("wind 5 min rejected", err is not None)
_, err = engine.build_wind_down("raat", "23:00")
check("wind bad time rejected", err is not None)

# --- sleep duration / average ---
d, err = engine.sleep_duration("23:00", "06:30")
check("sleep 23-06:30 = 450", err is None and d["minutes"] == 450
      and d["hours"] == 7.5 and d["label"] == "7 ghante 30 minute", str(d))
d, _ = engine.sleep_duration("22:00", "23:30")
check("sleep same evening 90", d["minutes"] == 90)
_, err = engine.sleep_duration("23:00", "23:00")
check("sleep 0 rejected", err is not None)
_, err = engine.sleep_duration("10:00", "12:00")
check("sleep 2h ok", err is None)
avg = engine.sleep_average([450, 420, 480])
check("avg 450", avg["average_minutes"] == 450 and avg["nights"] == 3)
check("avg empty None", engine.sleep_average([]) is None)
check("avg filters bad", engine.sleep_average([450, 9999, -5])["nights"] == 1)
check("word count", engine.word_count("one two three") == 3)
check("reading 200w = 1 min", engine.reading_minutes("w " * 200) == 1)

# --- stories ---
errs = stories.validate_stories()
check("stories valid", errs == [], str(errs))
check("3 stories", len(stories.STORIES) == 3)
check("story ids unique", len({s["id"] for s in stories.STORIES}) == 3)
meta = stories.story_meta()
check("meta 3", len(meta) == 3)
check("meta lantern minutes", meta[0]["minutes_en"] >= 2)
check("meta no full text", all("text" not in m for m in meta))
for s in stories.STORIES:
    check(f"{s['id']} en 300+", len(s["en"].split()) >= 300)
    check(f"{s['id']} mentions sleep",
          "sleep" in s["en"].lower())

# --- sounds ---
check("4 sound recipes", len(engine.SOUND_RECIPES) == 4)
for k, v in engine.SOUND_RECIPES.items():
    check(f"sound {k} has filter", v.get("filter") in ("bandpass", "lowpass")
          and isinstance(v.get("freq"), int) and 0 < v.get("gain", 0) <= 1)
check("timers include 30/60", 30 in engine.SLEEP_TIMERS and 60 in engine.SLEEP_TIMERS)

# --- AI validators ---
good_story = ("The river moved slowly under the moon. " * 30 + "\n\n" +
              "The old man sat by the water and listened to the night. " * 15 + "\n\n" +
              "And as the stars came out, his eyes closed, and he drifted into sleep.")
clean, err = engine.validate_ai_story(good_story)
check("ai story good passes", err is None and clean is not None, str(err))
_, err = engine.validate_ai_story("Too short.")
check("ai story short rejected", err is not None)
_, err = engine.validate_ai_story("One para only. " * 60)
check("ai story 1 para rejected", err is not None)
_, err = engine.validate_ai_story(good_story + " see http://x.example")
check("ai story link rejected", err is not None)
_, err = engine.validate_ai_story(good_story.replace("river", "Calm Premium"))
check("ai story brand rejected", err is not None)
clean, err = engine.validate_ai_plan("Step one: dim the lights and put the phone away. " * 9)
check("ai plan good passes", err is None, str(err))
_, err = engine.validate_ai_plan("Too short.")
check("ai plan short rejected", err is not None)
check("gemini no key", gemini.key_available() is False)
check("gemini themes", "river" in gemini.STORY_THEMES)
_, err = gemini.story_ai("nope", "en")
check("gemini bad theme", err is not None)

# --- routes via TestClient ---
try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sukoon.routes import router

    app = FastAPI()
    app.include_router(router)
    c = TestClient(app)
    r = c.get("/sukoon")
    check("route page 200", r.status_code == 200 and "Sukoon" in r.text)
    check("page says free", "Free forever" in r.text)
    check("page honest limits", "Honest limits" in r.text)
    check("page no Calm affiliation claim",
          "Not affiliated with Calm" in r.text)
    r = c.get("/sukoon/api/ai-status")
    check("route ai-status false", r.status_code == 200
          and r.json()["ai_available"] is False)
    r = c.get("/sukoon/api/stories")
    check("route stories 3", r.status_code == 200
          and len(r.json()["stories"]) == 3 and r.json()["valid"] is True)
    r = c.get("/sukoon/api/story/lantern?lang=en")
    check("route story lantern", r.status_code == 200
          and r.json()["ok"] is True and r.json()["words"] >= 300)
    r = c.get("/sukoon/api/story/lantern?lang=ur")
    check("route story urdu", r.status_code == 200
          and r.json()["ok"] is True and "دریا" in r.json()["text"])
    r = c.get("/sukoon/api/story/nope")
    check("route story bad id", r.status_code == 200
          and r.json()["ok"] is False)
    r = c.get("/sukoon/api/breathing?pattern=box&cycles=2")
    check("route breathing box", r.status_code == 200
          and r.json()["ok"] is True and r.json()["total_seconds"] == 32)
    r = c.get("/sukoon/api/breathing?pattern=nope&cycles=2")
    check("route breathing bad", r.status_code == 200
          and r.json()["ok"] is False)
    r = c.get("/sukoon/api/sounds")
    check("route sounds 4", r.status_code == 200
          and len(r.json()["sounds"]) == 4)
    r = c.post("/sukoon/api/dhikr", data={"key": "subhanallah", "count": 33})
    check("route dhikr 33", r.status_code == 200
          and r.json()["ok"] is True and r.json()["rounds"] == 1)
    r = c.post("/sukoon/api/wind-down",
               data={"isha": "21:00", "bedtime": "23:00"})
    check("route wind-down 120", r.status_code == 200
          and r.json()["ok"] is True and r.json()["window_minutes"] == 120)
    r = c.post("/sukoon/api/wind-down",
               data={"isha": "22:55", "bedtime": "23:00"})
    check("route wind-down short", r.status_code == 200
          and r.json()["ok"] is False)
    r = c.post("/sukoon/api/sleep", data={"bed": "23:00", "wake": "06:30"})
    check("route sleep 450", r.status_code == 200
          and r.json()["ok"] is True and r.json()["minutes"] == 450)
    r = c.post("/sukoon/api/sleep-average", data={"minutes": "450,420,480"})
    check("route sleep-avg 450", r.status_code == 200
          and r.json()["ok"] is True and r.json()["average_minutes"] == 450)
    r = c.post("/sukoon/api/story-ai", data={"theme": "river", "language": "en"})
    check("route story-ai no-key", r.status_code == 200
          and r.json()["ok"] is False)
    r = c.post("/sukoon/api/wind-down-ai",
               data={"bedtime": "23:00", "wake": "06:30", "stress": 3,
                     "worry": "", "language": "en"})
    check("route wind-down-ai no-key", r.status_code == 200
          and r.json()["ok"] is False)
except Exception as exc:  # noqa: BLE001 - surface as failures
    check("routes import/run", False, repr(exc))

print(f"PASS {PASS}  FAIL {len(FAIL)}")
for f in FAIL:
    print("FAIL:", f)
sys.exit(1 if FAIL else 0)
