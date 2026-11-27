import asyncio
import json
import os
import re
import edge_tts
from google import genai

# १. GitHub Secret बाट API Key लिने
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY भेटिएन! कृपया Secret चेक गर्नुहोस्।")

client = genai.Client(api_key=api_key)
HISTORY_FILE = "history.json"


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save_history(topic):
    history = load_history()
    if topic not in history:
        history.append(topic)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)


def generate_mystery_story():
    past_topics = load_history()
    print("🧠 पुरानो इतिहास चेक गर्दैछ... पहिले बनेका विषयहरू:", past_topics)

    prompt = f"""
    You are an elite dark documentary creator for YouTube Shorts (duration 35-45 seconds).
    
    TASK:
    1. Check for real-life CURRENT TRENDING mysteries globally. If found, pick it.
    2. If no trending mystery, pick a chilling, real-life UNSOLVED HISTORICAL mystery from anywhere worldwide.
    3. FORBIDDEN TOPICS (Do NOT repeat): {past_topics}
    4. Must be 100% REAL mystery. Fast-paced and thrilling.
    
    FORMAT:
    Return strictly a JSON object:
    {{
      "topic": "Name of the mystery",
      "is_trending": true or false,
      "scenes": [
        {{
          "scene_number": 1,
          "hindi_speech": "शुद्ध र रोमाञ्चक हिन्दी भाषा (छिटो बोल्नको लागि)",
          "hinglish_caption": "ENGLISH LETTERS MA HINGLISH CAPITAL TEXT",
          "english_visual_prompt": "Cinematic 35mm photograph, dark moody thriller atmosphere, archival footage, 8k"
        }}
      ]
    }}
    Total scenes must be 4 to 5 short scenes (around 70-80 words total).
    """

    # यहाँ १००% काम गर्ने 'gemini-1.5-flash' मोडल राखिएको छ
    response = client.models.generate_content(
        model="gemini-1.5-flash", contents=prompt
    )

    text = response.text.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    return json.loads(text)


async def generate_voice(full_text, filename):
    # आवाजलाई हल्का छिटो (+10%) र गम्भीर (-3Hz) बनाइएको छ ताकि अल्छी नसुनियोस्
    communicate = edge_tts.Communicate(
        text=full_text, voice="hi-IN-MadhurNeural", pitch="-3Hz", rate="+10%"
    )
    await communicate.save(filename)


async def main():
    print("🚀 बोटले विश्वव्यापी रहस्य खोज्दैछ...")
    data = generate_mystery_story()
    topic = data["topic"]
    save_history(topic)

    print(f"\n🔥 छानिएको नयाँ विषय: {topic}")
    full_hindi_speech = " ".join([s["hindi_speech"] for s in data["scenes"]])

    with open("story_details.txt", "w", encoding="utf-8") as f:
        f.write(f"विषय: {topic}\n\n")
        for s in data["scenes"]:
            f.write(f"--- सिन {s['scene_number']} ---\n")
            f.write(f"आवाज (Hindi): {s['hindi_speech']}\n")
            f.write(f"क्याप्सन (Hinglish): {s['hinglish_caption']}\n")
            f.write(f"दृश्य प्रोम्प्ट (English): {s['english_visual_prompt']}\n\n")

    print("🎙️ छिटो र सस्पेन्स हिन्दी आवाज तयार गर्दैछ...")
    await generate_voice(full_hindi_speech, "full_story_voice.mp3")
    print("✅ सबै काम १००% सफल भयो!")


if __name__ == "__main__":
    asyncio.run(main())
