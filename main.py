import asyncio
import json
import os
import re
import subprocess
import urllib.parse
import edge_tts
from google import genai
import requests

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None
HISTORY_FILE = "history.json"

# हरेक सिनको लागि १००% मिल्ने भिजुअल लिंक फिक्स गरिएको मास्टर भल्ट
PERFECT_MYSTERIES = [
    {
        "topic": "The Mystery of D.B. Cooper",
        "scenes": [
            {
                "scene_number": 1,
                "hindi_speech": "1971 mein ek ajeeb aadmi ne hawa mein pura plane hijack kar liya.",
                "hinglish_caption": "1971 MEIN PLANE HIJACK HO GAYA",
                "search_query": "airplane flying dark storm clouds night",
                # १. प्लेन उडिरहेको दृश्य
                "exact_photo": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=1080&h=1920&fit=crop",
            },
            {
                "scene_number": 2,
                "hindi_speech": (
                    "Usne 20 lakh dollar cash liye aur parachute pehankar andhere"
                    " jungle mein kood gaya."
                ),
                "hinglish_caption": "20 LAKH DOLLAR LEKAR JUNGLE MEIN KOOD GAYA",
                "search_query": "dark misty pine forest night rain parachute",
                # २. रातिको डरलाग्दो कुहिरो भएको जंगल
                "exact_photo": "https://images.unsplash.com/photo-1511497584788-87676104235f?w=1080&h=1920&fit=crop",
            },
            {
                "scene_number": 3,
                "hindi_speech": (
                    "Hazaron FBI agents ne pura jungle chhan mara, par uska koi"
                    " saboot nahi mila."
                ),
                "hinglish_caption": "FBI KO AAJ TAK KOI SABOOT NAHI MILA",
                "search_query": "detectives flashlight searching dark woods",
                # ३. जंगलमा टर्च बालेर खोजिरहेको दृश्य
                "exact_photo": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1080&h=1920&fit=crop",
            },
            {
                "scene_number": 4,
                "hindi_speech": (
                    "50 saal beet chuke hain, par ye mystery aaj bhi unsolved"
                    " hai. Kahan gaya wo? Comment karein."
                ),
                "hinglish_caption": "KAHAN GAYA WO AADMI? COMMENT KAREIN",
                "search_query": "vintage classified case file detective desk",
                # ४. सीक्रेट केस फाइल र जासूसको टेबल
                "exact_photo": "https://images.unsplash.com/photo-1455390582262-044cdead277a?w=1080&h=1920&fit=crop",
            },
        ],
    }
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


# ३-तहको सुरक्षित भ्वाइस इन्जिन
async def generate_scene_voice(text, filename):
    attempts = [
        ("hi-IN-MadhurNeural", "-2Hz", "+10%"),
        ("hi-IN-MadhurNeural", "+0Hz", "+0%"),
        ("hi-IN-SwaraNeural", "+0Hz", "+0%"),
    ]
    for voice, pitch, rate in attempts:
        try:
            communicate = edge_tts.Communicate(
                text=text, voice=voice, pitch=pitch, rate=rate
            )
            await communicate.save(filename)
            if os.path.exists(filename) and os.path.getsize(filename) > 500:
                return
        except Exception as e:
            print(f"⚠️ Voice retry ({voice}): {e}", flush=True)
            await asyncio.sleep(1)
    raise RuntimeError("Voice generation failed")


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


# १ सेकेन्डमै ठ्याक्कै कथा अनुसार मिल्ने फोटो डाउनलोड गर्ने इन्जिन
def download_exact_scene_image(scene_data, filename):
    query = scene_data.get("search_query", "")
    exact_backup = scene_data.get("exact_photo", "")

    print(f"🎯 सिनको लागि १००% मिल्ने फोटो खोज्दैछ: '{query}'...", flush=True)

    # १. पहिले Lexica AI बाट खोज्ने
    try:
        encoded = urllib.parse.quote(query)
        lexica_url = f"https://lexica.art/api/v1/search?q={encoded}"
        res = requests.get(
            lexica_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                    " AppleWebKit/537.36"
                )
            },
            timeout=5,
        )
        if res.status_code == 200:
            images = res.json().get("images", [])
            if images:
                best_img = images[0].get("src") or images[0].get("srcSmall")
                img_res = requests.get(best_img, timeout=6)
                if img_res.status_code == 200 and len(img_res.content) > 5000:
                    with open(filename, "wb") as f:
                        f.write(img_res.content)
                    print(
                        f"✅ Lexica बाट हुबहु फोटो सुरक्षित भयो! ({len(img_res.content)} bytes)",
                        flush=True,
                    )
                    return
    except Exception as e:
        print(f"⚠️ Lexica retry: {e}", flush=True)

    # २. यदि Lexica ढिला भए सिधै त्यो सिनको लागि फिक्स गरिएको फोटो हाल्ने (१००% प्लेन/जंगल/फाइल नै आउँछ)
    print("🎯 सिनको लागि ग्यारेन्टी गरिएको फोटो हाल्दैछ...", flush=True)
    res = requests.get(exact_backup, timeout=8)
    with open(filename, "wb") as f:
        f.write(res.content)
    print("✅ ठ्याक्कै मिल्ने फोटो सुरक्षित भयो!", flush=True)


# २ सेकेन्डमै सिन रेन्डर गर्ने इन्जिन
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
    story_data = PERFECT_MYSTERIES[0]
    topic = story_data["topic"]
    save_history(topic)
    print(f"\n🔥 छानिएको रहस्य: {topic}", flush=True)

    scene_files = []
    total_dur = 0.0

    for idx, scene in enumerate(story_data["scenes"], 1):
        print(f"\n--- सिन {idx} तयार गर्दैछ ---", flush=True)
        aud_file = f"audio_{idx}.mp3"
        img_file = f"img_{idx}.jpg"
        vid_file = f"scene_{idx}.mp4"

        # १. आवाज निकाल्ने
        await generate_scene_voice(scene["hindi_speech"], aud_file)
        dur = get_audio_duration(aud_file)
        total_dur += dur

        # २. ठ्याक्कै त्यही सिनको फोटो ल्याउने
        download_exact_scene_image(scene, img_file)

        # ३. भिडियो जोड्ने
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
