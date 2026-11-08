"""Live Gemini check for Sukoon — uses the registered surrogate
credential (key never handled, never printed). Calls the real
sukoon.gemini functions once each and validates the outputs with
the engine validators. Run: python tests/live_check.py
"""
import os
import sys

sys.path.insert(0, "/opt/muse/skills/custom-connector-setup/bin")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dynamic_credentials import dynamic_credential_entry  # noqa: E402

entry = dynamic_credential_entry("custom.google-gemini")
os.environ["GEMINI_API_KEY"] = entry["surrogate"]

from sukoon import gemini  # noqa: E402

print("key_available:", gemini.key_available())

story, err = gemini.story_ai("sea", "en")
if err:
    print("STORY ERROR:", err)
    sys.exit(1)
print(f"STORY OK: {story['words']} words, ~{story['minutes']} min, theme={story['theme']}")
print("story first 120 chars:", story["story"][:120].replace("\n", " "))
assert story["words"] >= 250 and story["ai"] is True

plan, err = gemini.wind_down_ai("23:00", "06:30", 3, "kal ki presentation ki fikar", "en")
if err:
    print("PLAN ERROR:", err)
    sys.exit(1)
print(f"PLAN OK: {plan['words']} words, bedtime={plan['bedtime']}, stress={plan['stress']}/5")
print("plan first 120 chars:", plan["plan"][:120].replace("\n", " "))
assert plan["words"] >= 80 and plan["ai"] is True
print("LIVE CHECK PASSED")
