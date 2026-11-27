import asyncio
import json
import os
import re
import edge_tts
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None
HISTORY_FILE = "history.json"

# गुगल जाम हुँदा प्रयोग हुने विश्वका सबैभन्दा खतरनाक र अनौठा सत्य रहस्यहरू
FALLBACK_MYSTERIES = [
    {
        "topic": "The Dyatlov Pass Incident",
        "script": (
            "1959 mein Russia ke barfile pahadon par 9 experienced trekkers ki"
            " aisi khaufnak maut hui, jiska jawab science ke paas aaj bhi nahi"
            " hai! Unka tent andar se chaku se kata hua mila, mano wo kisi aisi"
            " cheez se bhag rahe the jisne unhe dehshat mein daal diya tha."
            " Kadi thand mein unke shareer par kapde nahi the, aur kuch ki"
            " aankhein aur jeebh gayab thi! Na koi ladai ke nishan, na koi"
            " hathiyar. Aakhir un 9 logon ne us raat kya dekha tha? Kya wo koi"
            " secret military test tha, ya kuch aisa jise insaan nahi samajh"
            " sakte? Comment mein apni rai zaroor dein!"
        ),
        "editing_guide": (
            "CapCut Guide: 1. Snowy mountains / Tent footage 2. Creepy"
            " footprints in snow 3. 1950s Soviet investigation files 4. Dark"
            " blizzard ending"
        ),
    },
    {
        "topic": "The Disappearance of Flight 19",
        "script": (
            "1945 mein Bermuda Triangle ke upar se 5 American ladaku viman"
            " achanak hawa mein hi gayab ho gaye! Control room ko aakhiri"
            " sandesh aaya— 'Hamare compass ne kaam karna band kar diya hai,"
            " samundar ajeeb dikh raha hai!' Aur uske baad, sirf sannata."
            " Hairani ki baat to ye hai ki unhe dhoondhne gaya rescue plane bhi"
            " 20 minute baad gayab ho gaya! 5 viman aur 27 log, bina kisi"
            " malbe ya tel ke nishan ke, hawa mein hi bila gaye! Kya Bermuda"
            " Triangle mein waqai koi doosri duniya ka darwaza hai? Aapko kya"
            " lagta hai?"
        ),
        "editing_guide": (
            "CapCut Guide: 1. 1940s military planes flying 2. Radar screen"
            " spinning 3. Dark ocean storm 4. Bermuda triangle map"
        ),
    },
    {
        "topic": "The Mystery of Cicada 3301",
        "script": (
            "2012 mein internet par ek aisi tasveer aayi jisne duniya ke sabse"
            " bade hackers aur agencies ki neend uda di! Isme likha tha— 'Hum"
            " highly intelligent logon ki talash kar rahe hain.' Iske baad shuru"
            " hua itihas ka sabse complex puzzle! Duniya ke 5 deshon ke telephone"
            " booths par QR codes mile, deep web ke mysterious links khule."
            " Kuch hi log is aakhiri level tak pahunche, aur jo pahunche, wo"
            " hamesha ke liye gayab ho gaye! Ye organization kaun thi? CIA,"
            " Illuminati, ya koi secret society? Aaj tak kisi ko nahi pata!"
        ),
        "editing_guide": (
            "CapCut Guide: 1. Cicada moth logo / Dark computer screen 2. Hacker"
            " coding visual 3. Street telephone booth at night 4. Secret"
            " society symbol"
        ),
    },
    {
        "topic": "The Lost Colony of Roanoke",
        "script": (
            "1590 mein America ke ek island par basa pura ka pura gaon raaton"
            " raat gayab ho gaya! 115 log, jismein aurtein aur bachhe bhi the,"
            " bina kisi ladai ya khoon ke nishan ke, achanak gayab ho gaye!"
            " Pura gaon waisa ka waisa tha, khana table par rakha tha, bandookein"
            " deewar par latki thi. Wahan sirf ek ajeeb saboot mila— ped ki"
            " chhal par khuda hua ek akela shabd: CROATOAN! 400 saal se zyada"
            " guzar chuke hain, par koi nahi jaanta un 115 logon ko zameen nigal"
            " gayi ya aasmaan!"
        ),
        "editing_guide": (
            "CapCut Guide: 1. 1500s vintage village / forest 2. Empty abandoned"
            " wooden houses 3. Carved word CROATOAN on tree 4. Foggy spooky"
            " forest"
        ),
    },
]


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


# १. नयाँ ट्रेन्डिङ वा पुराना नसुल्झिएका रहस्य खोज्ने (Never Repeats)
def get_mystery_content():
    past_topics = load_history()
    print(f"🧠 पहिले बनिसकेका विषयहरू: {past_topics}", flush=True)

    if client:
        prompt = f"""
        You are an elite dark mystery investigator for YouTube Shorts (duration 35-45 seconds).
        
        TASK:
        1. Check if there are any CURRENT REAL-LIFE TRENDING mysteries, bizarre archaeological/deep-sea discoveries happening globally.
        2. If YES, pick that trending real mystery.
        3. If NO trending mystery, pick a legendary, terrifying, real-life UNSOLVED HISTORICAL mystery from anywhere worldwide.
        4. FORBIDDEN TOPICS (Do NOT repeat): {past_topics}
        5. Must be 100% REAL mystery. Fast-paced, goosebumps-inducing, and thrilling Hindi script.
        
        FORMAT (Strict JSON only):
        {{
          "topic": "Name of the mystery",
          "script": "Pura 35-45 second ka thrilling Hindi voiceover text bina kisi bracket ya emoji ke",
          "editing_guide": "CapCut ma halne 3-4 visual ideas"
        }}
        """
        for model in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]:
            try:
                print(
                    f"⚡ Google AI ({model}) बाट नयाँ रहस्य खोज्दैछ...",
                    flush=True,
                )
                res = client.models.generate_content(
                    model=model, contents=prompt
                )
                if res and res.text:
                    match = re.search(r"\{.*\}", res.text.strip(), re.DOTALL)
                    data = json.loads(match.group(0))
                    print(
                        f"✅ AI ले नयाँ विषय पत्ता लगायो: {data['topic']}",
                        flush=True,
                    )
                    return data
            except Exception as e:
                print(f"⚠️ {model} व्यस्त छ, अर्को प्रयास...", flush=True)

    # यदि गुगल ढिला भए आपतकालीन भल्टबाट नयाँ नदोहोरिएको रहस्य लिने
    print(
        "🛡️ भल्टबाट नदोहोरिएको नयाँ सत्य रहस्य लिँदैछ...", flush=True
    )
    for m in FALLBACK_MYSTERIES:
        if m["topic"] not in past_topics:
            return m
    return FALLBACK_MYSTERIES[0]


# २. Best of the Best स्टुडियो हिन्दी आवाज निकाल्ने
async def generate_best_voice(text, filename):
    print("🎙️ रौं ठाडो पार्ने स्टुडियो हिन्दी आवाज तयार गर्दैछ...", flush=True)
    # Pitch: -2Hz (गम्भीर बेस), Rate: +8% (छिटो, पन्ची र सस्पेन्स भरिएको गति)
    communicate = edge_tts.Communicate(
        text=text,
        voice="hi-IN-MadhurNeural",
        pitch="-2Hz",
        rate="+8%",
    )
    await communicate.save(filename)
    print("✅ आवाज १००% पर्फेक्ट बन्यो!", flush=True)


async def main():
    data = get_mystery_content()
    topic = data["topic"]
    save_history(topic)

    print(f"\n🔥 आजको विषय: {topic}", flush=True)

    # १. आवाज निकाल्ने
    audio_file = "mystery_voice.mp3"
    await generate_best_voice(data["script"], audio_file)

    # २. क्यापकटका लागि स्क्रिप्ट र गाइड सेभ गर्ने
    guide_file = "script_and_guide.txt"
    with open(guide_file, "w", encoding="utf-8") as f:
        f.write(f"=== {topic} ===\n\n")
        f.write(f"📝 हिन्दी भ्वाइस स्क्रिप्ट:\n{data['script']}\n\n")
        f.write(
            f"🎬 CapCut भिडियो एडिटिङ आइडिया:\n{data.get('editing_guide', '')}\n"
        )

    print("\n🎉 सबै काम सम्पन्न भयो!")
    print(f"📁 आवाज: {audio_file}")
    print(f"📄 स्क्रिप्ट र गाइड: {guide_file}")


if __name__ == "__main__":
    asyncio.run(main())
