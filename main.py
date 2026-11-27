import asyncio
import json
import os
import random
import re
import subprocess
import urllib.parse
import edge_tts
from google import genai
import requests

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None
HISTORY_FILE = "history.json"

# गुगल जाम हुँदा तुरुन्तै काम गर्ने विश्वका टप सत्य रहस्यहरूको आपतकालीन भल्ट
BACKUP_MYSTERIES = [
    {
        "topic": "The Mystery of D.B. Cooper",
        "scenes": [
            {
                "hindi_speech": "१९७१ में एक रहस्यमयी आदमी ने बीच हवा में एक पूरा प्लेन हाईजैक कर लिया।",
                "hinglish_caption": "1971 MEIN PLANE HIJACK HO GAYA",
                "english_visual_prompt": (
                    "Vintage 1970s commercial airplane flying through dark"
                    " storm clouds at night, moody cinematic lighting, 35mm"
                    " photograph"
                ),
            },
            {
                "hindi_speech": (
                    "उसने २० लाख डॉलर कैश लिए और पैराशूट पहनकर ४ हजार मीटर की"
                    " ऊंचाई से रात के घने जंगलों में कूद गया।"
                ),
                "hinglish_caption": "20 LAKH DOLLAR LEKAR JUNGLE MEIN KOOD GAYA",
                "english_visual_prompt": (
                    "Dense dark rainy pine forest at night, mysterious silhouette"
                    " of parachutist vanishing into deep fog, 35mm"
                ),
            },
            {
                "hindi_speech": (
                    "हजारों एफबीआई एजेंटों ने जंगल का चप्पा-चप्पा छान मारा, पर"
                    " उसका कोई नामोनिशान नहीं मिला।"
                ),
                "hinglish_caption": "FBI KO AAJ TAK KOI SABOOT NAHI MILA",
                "english_visual_prompt": (
                    "1970s FBI detectives with vintage flashlights searching"
                    " muddy forest floor in heavy rain, eerie atmospheric"
                    " lighting"
                ),
            },
            {
                "hindi_speech": (
                    "५० साल बीत चुके हैं, पर डी.बी. कूपर का रहस्य आज भी दुनिया"
                    " की सबसे बड़ी अनसुलझी गुत्थी है।"
                ),
                "hinglish_caption": "KAHAN GAYA WO AADMI? COMMENT KAREIN",
                "english_visual_prompt": (
                    "Old vintage classified FBI case file on wooden detective"
                    " desk under dramatic yellow lamp light, 8k cinematic"
                ),
            },
        ],
    },
    {
        "topic": "The Ghost Ship Mary Celeste",
        "scenes": [
            {
                "hindi_speech": (
                    "१८७२ में अटलांटिक महासागर के बीच एक ऐसा जहाज मिला,"
                    " जिसने सबको हिला कर रख दिया।"
                ),
                "hinglish_caption": "SAMUNDAR KE BEECH MILA GHOST SHIP",
                "english_visual_prompt": (
                    "Creepy 1870s wooden merchant ship drifting alone in stormy"
                    " dark ocean waters, eerie sea mist, 35mm film"
                ),
            },
            {
                "hindi_speech": (
                    "जहाज पर सारा सामान, खाना और कीमती सामान सुरक्षित था, लेकिन"
                    " पूरा क्रू गायब था।"
                ),
                "hinglish_caption": "SABHI LOG ACHANAK GAYAB HO GAYE",
                "english_visual_prompt": (
                    "Empty ship deck at twilight, half-eaten breakfast table on"
                    " wooden cabin, spooky silence, cinematic mystery"
                ),
            },
            {
                "hindi_speech": (
                    "न कोई खून का कतरा, न कोई संघर्ष का निशान— मानो १० लोग"
                    " हवा में ही गायब हो गए।"
                ),
                "hinglish_caption": "HAWA MEIN BILA GAYE 10 LOG",
                "english_visual_prompt": (
                    "Eerie empty ship steering wheel moving slowly by itself in"
                    " cold sea breeze, dense ocean fog, dark cinema"
                ),
            },
            {
                "hindi_speech": (
                    "वैज्ञानिक आज तक यह नहीं समझ पाए कि आखिर मैरी सेलेस्ट के साथ"
                    " उस दिन क्या हुआ था।"
                ),
                "hinglish_caption": "KYA HUA THA US DIN? COMMENT KAREIN",
                "english_visual_prompt": (
                    "Deep dark ocean abyss at night, vast mysterious endless"
                    " waters, dramatic cinematic lighting, 8k"
                ),
            },
        ],
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


# गुगल AI बाट तुरुन्तै माग्ने, जाम भए भल्टबाट लिने (Never Hangs)
def get_mystery_story():
    past_topics = load_history()

    # १. पहिले Google AI बाट प्रयास गर्ने (८ सेकेन्ड मात्र पर्खिने)
    if client:
        prompt = f"""
        Elite YouTube Shorts thriller story (35s). 
        Check current trending mystery globally or pick real historical unsolved mystery. 
        Forbidden: {past_topics}. 
        Return strictly JSON:
        {{"topic":"Name", "scenes":[{{"scene_number":1, "hindi_speech":"...", "hinglish_caption":"...", "english_visual_prompt":"Cinematic 35mm..."}}]}}
        Strictly 4 short scenes.
        """
        for model in ["gemini-3.8-flash", "gemini-2.5-flash"]:
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
                    print("✅ Google AI ले नयाँ रहस्य तयार पार्यो!", flush=True)
                    return data
            except Exception as e:
                print(f"⚠️ Google AI ढिला भयो ({e}), अर्को प्रयास...", flush=True)
                break

    # २. यदि गुगल जाम भए आपतकालीन भल्टबाट तुरुन्तै लिने (० सेकेन्डमै)
    print("🛡️ भल्टबाट नयाँ रहस्यमयी कथा सुरक्षित गर्दैछ...", flush=True)
    available = [b for b in BACKUP_MYSTERIES if b["topic"] not in past_topics]
    return available[0] if available else BACKUP_MYSTERIES[0]


async def generate_scene_voice(text, filename):
    communicate = edge_tts.Communicate(
        text=text, voice="hi-IN-MadhurNeural", pitch="-3Hz", rate="+10%"
    )
    await communicate.save(filename)


def get_audio_duration(file_path):
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        file_path,
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return float(result.stdout.strip())


# १ सेकेन्डमै १००% डार्क सिनेम्याटिक फोटो सुरक्षित गर्ने
def download_ai_image(prompt, filename):
    print(
        f"🎨 ३५एमएम सिनेम्याटिक तस्बिर तयार गर्दैछ: {prompt[:30]}...",
        flush=True,
    )
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&model=flux&nologo=true"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }

    try:
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200 and len(res.content) > 10000:
            with open(filename, "wb") as f:
                f.write(res.content)
            print(
                f"✅ AI फोटो सुरक्षित भयो ({len(res.content)} bytes)", flush=True
            )
            return
    except:
        pass

    real_dark_photos = [
        "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1080&h=1920&fit=crop",
        "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1080&h=1920&fit=crop",
        "https://images.unsplash.com/photo-1509248961158-e54f6934749c?w=1080&h=1920&fit=crop",
        "https://images.unsplash.com/photo-1481833761820-0509d3217039?w=1080&h=1920&fit=crop",
    ]
    res = requests.get(random.choice(real_dark_photos), timeout=8)
    with open(filename, "wb") as f:
        f.write(res.content)
    print("✅ सिनेम्याटिक दृश्य सुरक्षित भयो!", flush=True)


# २ सेकेन्डमै सिन रेन्डर गर्ने लाइटवेट इन्जिन
def build_scene_video(img_path, audio_path, caption_text, duration, out_path):
    caption_escaped = (
        caption_text.replace("'", "")
        .replace(":", "")
        .replace('"', "")
        .replace("\\", "")
    )
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font_param = f":fontfile='{font_path}'" if os.path.exists(font_path) else ""

    filter_complex = (
        f"[0:v]scale=1160:2062:force_original_aspect_ratio=increase,"
        f"crop=1080:1920:'(in_w-1080)/2':'(in_h-1920)/2 + 4*t',"
        f"eq=contrast=1.3:brightness=-0.03:saturation=0.7,"
        f"colorbalance=bs=0.12:bm=0.08:rs=-0.04,"
        f"vignette=PI/4.5,"
        f"drawtext=text='{caption_escaped}'{font_param}:fontcolor=yellow:fontsize=54:"
        f"bordercolor=black:borderw=6:x=(w-text_w)/2:y=h-420[v]"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-t",
        str(duration),
        "-i",
        img_path,
        "-i",
        audio_path,
        "-filter_complex",
        filter_complex,
        "-map",
        "[v]",
        "-map",
        "1:a",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-shortest",
        out_path,
    ]
    subprocess.run(cmd, check=True)


async def main():
    data = get_mystery_story()
    topic = data["topic"]
    save_history(topic)
    print(f"\n🔥 छानिएको नयाँ विषय: {topic}", flush=True)

    scene_files = []
    total_dur = 0.0

    for idx, scene in enumerate(data["scenes"], 1):
        print(f"\n--- सिन {idx} तयार गर्दैछ ---", flush=True)
        aud_file = f"audio_{idx}.mp3"
        img_file = f"img_{idx}.jpg"
        vid_file = f"scene_{idx}.mp4"

        await generate_scene_voice(scene["hindi_speech"], aud_file)
        dur = get_audio_duration(aud_file)
        total_dur += dur

        download_ai_image(scene["english_visual_prompt"], img_file)

        build_scene_video(
            img_file, aud_file, scene["hinglish_caption"], dur, vid_file
        )
        scene_files.append(vid_file)

    with open("list.txt", "w") as f:
        for v in scene_files:
            f.write(f"file '{v}'\n")

    print(
        f"\n🎬 सबै सिनहरू जोड्दैछ ({total_dur:.1f}s)... डार्क BGM थप्दैछ...",
        flush=True,
    )

    cmd_final = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        "list.txt",
        "-f",
        "lavfi",
        "-i",
        f"aevalsrc=0.12*sin(2*PI*55*t)+0.06*sin(2*PI*110*t):s=44100:d={total_dur}",
        "-filter_complex",
        "[0:a][1:a]amix=inputs=2:duration=first:weights=3 0.25[a]",
        "-map",
        "0:v",
        "-map",
        "[a]",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-t",
        str(total_dur),
        "final_mystery_short.mp4",
    ]
    subprocess.run(cmd_final, check=True)

    print(
        "\n🎉 १००% सम्पन्न भयो! भिडियो फाइल: final_mystery_short.mp4", flush=True
    )


if __name__ == "__main__":
    asyncio.run(main())
