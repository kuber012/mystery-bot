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
if not api_key:
    raise ValueError("GEMINI_API_KEY भेटिएन!")

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
    prompt = f"""
    You are an elite dark documentary creator for YouTube Shorts (duration 30-40 seconds).
    TASK:
    1. Check for real-life CURRENT TRENDING mysteries globally. If found, pick it.
    2. If no trending mystery, pick a chilling, real-life UNSOLVED HISTORICAL mystery from anywhere worldwide.
    3. FORBIDDEN TOPICS: {past_topics}
    4. Must be 100% REAL mystery. Fast-paced, punchy, and thrilling.
    
    CRITICAL: For english_visual_prompt, do NOT use words like 'murder', 'blood', 'kill'. Use atmospheric words: 'isolated creepy house at night', 'dense dark spooky fog over pine trees', 'abandoned 1920s detective crime scene', '35mm photograph, eerie lighting'.
    
    FORMAT (Strict JSON only):
    {{
      "topic": "Name of the mystery",
      "is_trending": false,
      "scenes": [
        {{
          "scene_number": 1,
          "hindi_speech": "रोमाञ्चक हिन्दी भाषा",
          "hinglish_caption": "SHORT HINGLISH CAPITAL TEXT",
          "english_visual_prompt": "Cinematic 35mm photograph, eerie atmospheric lighting, dark mystery aesthetic, 8k"
        }}
      ]
    }}
    Create strictly 4 short scenes. Total words around 60 words.
    """
    for model_name in ["gemini-3.8-flash", "gemini-3.6-flash"]:
        try:
            res = client.models.generate_content(
                model=model_name, contents=prompt
            )
            if res and res.text:
                text = res.text.strip()
                match = re.search(r"\{.*\}", text, re.DOTALL)
                return json.loads(match.group(0)) if match else json.loads(text)
        except Exception as e:
            print(f"Retrying: {e}")
    raise RuntimeError("AI Story generate failed")


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


# १ सेकेन्डमै १००% डार्क सिनेम्याटिक फोटो ल्याउने इन्जिन
def download_ai_image(prompt, filename):
    print(
        f"🎨 ३५एमएम सिनेम्याटिक तस्बिर तयार गर्दैछ: {prompt[:35]}...",
        flush=True,
    )
    encoded = urllib.parse.quote(prompt)

    # १. Pollinations AI बाट प्रयास गर्ने (१० सेकेन्ड टाइमआउट)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&model=flux&nologo=true"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }

    try:
        res = requests.get(url, headers=headers, timeout=12)
        if res.status_code == 200 and len(res.content) > 10000:
            with open(filename, "wb") as f:
                f.write(res.content)
            print(
                f"✅ AI फोटो सुरक्षित भयो ({len(res.content)} bytes)", flush=True
            )
            return
    except:
        pass

    # २. तत्काल वास्तविक ४K डार्क मिस्ट्री फोटो हाल्ने (कालो बक्स कहिल्यै आउँदैन)
    print("⚡ द्रुत सिनेम्याटिक मिस्ट्री दृश्य सुरक्षित गर्दैछ...", flush=True)
    real_dark_photos = [
        "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1080&h=1920&fit=crop",
        "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1080&h=1920&fit=crop",
        "https://images.unsplash.com/photo-1509248961158-e54f6934749c?w=1080&h=1920&fit=crop",
        "https://images.unsplash.com/photo-1481833761820-0509d3217039?w=1080&h=1920&fit=crop",
        "https://images.unsplash.com/photo-1514539079130-25950c84af65?w=1080&h=1920&fit=crop",
    ]
    res = requests.get(random.choice(real_dark_photos), timeout=10)
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

    # CPU मा भार नपर्ने सुपर-फास्ट सिनेम्याटिक प्यान (Cinematic Motion)
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
    print("🚀 नयाँ रहस्य कथा खोज्दैछ...", flush=True)
    data = generate_mystery_story()
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
