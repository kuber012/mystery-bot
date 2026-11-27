import asyncio
import json
import os
import re
import edge_tts
from google import genai

# १. GitHub Secret बाट API Key लिने
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

HISTORY_FILE = "history.json"


# पहिले बनिसकेका पुराना विषयहरू लोड गर्ने
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


# नयाँ विषय मेमोरीमा सेभ गर्ने
def save_history(topic):
    history = load_history()
    if topic not in history:
        history.append(topic)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)


# AI बाट ट्रेन्डिङ / पुराना भयानक रहस्य खोज्ने
def generate_mystery_story():
    past_topics = load_history()
    print("🧠 पुरानो इतिहास चेक गर्दैछ... पहिले बनेका विषयहरू:", past_topics)

    prompt = f"""
    You are an elite dark documentary creator for YouTube Shorts (duration 35-45 seconds).
    
    TASK:
    1. Check for real-life CURRENT TRENDING mysteries globally. If found, pick it.
    2. If no trending mystery, pick a chilling, real-life UNSOLVED HISTORICAL mystery from anywhere worldwide.
    3. FORBIDDEN TOPICS (Do NOT repeat): {past_topics}
    4. Must be 100% REAL mystery.
    
    FORMAT:
    Return strictly a valid JSON object without any extra text:
    {{
      "topic": "Name of the mystery",
      "is_trending": true or false,
      "scenes": [
        {{
          "scene_number": 1,
          "hindi_speech": "शुद्ध र डरलाग्दो हिन्दी भाषा (बोल्नको लागि)",
          "hinglish_caption": "ENGLISH LETTERS MA HINGLISH CAPITAL TEXT (SUBTITLE)",
          "english_visual_prompt": "Cinematic 35mm photograph, archival footage, dark moody thriller atmosphere, 8k"
        }}
      ]
    }}
    Total scenes must be exactly 4 to 5 short scenes (around 70-90 words total).
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=prompt
    )

    text = response.text.strip()
    # JSON निकाल्ने
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    return json.loads(text)


# Edge-TTS बाट डरलाग्दो आवाज निकाल्ने
async def generate_voice(full_text, filename):
    communicate = edge_tts.Communicate(
        text=full_text, voice="hi-IN-MadhurNeural", pitch="-6Hz", rate="-5%"
    )
    await communicate.save(filename)


async def main():
    print("🚀 बोटले विश्वव्यापी रहस्य खोज्दैछ...")
    data = generate_mystery_story()
    topic = data["topic"]
    save_history(topic)

    print(f"\n🔥 छानिएको नयाँ विषय: {topic}")
    print(
        f"के यो ट्रेन्डिङ हो?: {'हो (Trending)' if data.get('is_trending') else 'होइन (पुराना खतरनाक रहस्य)'}"
    )

    # पूर्ण हिन्दी स्क्रिप्ट बनाउने
    full_hindi_speech = " ".join([s["hindi_speech"] for s in data["scenes"]])

    # स्क्रिप्टलाई फाइलमा सेभ गर्ने ताकि पढ्न सकियोस्
    with open("story_details.txt", "w", encoding="utf-8") as f:
        f.write(f"विषय: {topic}\n\n")
        for s in data["scenes"]:
            f.write(f"--- सिन {s['scene_number']} ---\n")
            f.write(f"आवाज (Hindi): {s['hindi_speech']}\n")
            f.write(f"क्याप्सन (Hinglish): {s['hinglish_caption']}\n")
            f.write(f"दृश्य प्रोम्प्ट (English): {s['english_visual_prompt']}\n\n")

    print("🎙️ पूरा कथाको आवाज बनाउँदैछ...")
    await generate_voice(full_hindi_speech, "full_story_voice.mp3")
    print("✅ सबै तयार भयो!")


if __name__ == "__main__":
    asyncio.run(main())
