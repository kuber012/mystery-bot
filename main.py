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
    You are an elite dark documentary creator for YouTube Shorts (duration 35-45 seconds).
    TASK:
    1. Check for real-life CURRENT TRENDING mysteries globally. If found, pick it.
    2. If no trending mystery, pick a chilling, real-life UNSOLVED HISTORICAL mystery from anywhere worldwide.
    3. FORBIDDEN TOPICS: {past_topics}
    4. Must be 100% REAL mystery. Fast-paced, punchy, and thrilling.
    
    FORMAT (Strict JSON only):
    {{
      "topic": "Name of the mystery",
      "is_trending": false,
      "scenes": [
        {{
          "scene_number": 1,
          "hindi_speech": "रोमाञ्चक हिन्दी भाषा",
          "hinglish_caption": "SHORT HINGLISH CAPITAL TEXT",
          "english_visual_prompt": "Cinematic 35mm photograph, dark moody lighting, archival footage, 8k"
        }}
      ]
    }}
    Create strictly 4 short scenes. Total words around 60-75 words.
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


def download_ai_image(prompt, filename):
    print(f"🎨 Flux AI बाट ३५एमएम तस्बिर बन्दैछ: {prompt[:40]}...")
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&model=flux&nologo=true"
    res = requests.get(url, timeout=50)
    with open(filename, "wb") as f:
        f.write(res.content)


def build_scene_video(img_path, audio_path, caption_text, duration, out_path):
    # अक्षरहरू सफा बनाउने
    caption_escaped = (
        caption_text.replace("'", "")
        .replace(":", "")
        .replace('"', "")
        .replace("\\", "")
    )

    # बोल्ड फन्ट फाइल छ कि छैन चेक गर्ने
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font_param = f":fontfile='{font_path}'" if os.path.exists(font_path) else ""

    # 'bold=1' हटाएर मोटो बोर्डर (borderw=6) हालिएको छ जसले गर्दा एरर कहिल्यै आउँदैन
    filter_complex = (
        f"[0:v]zoompan=z='min(zoom+0.0012,1.15)':d={int(duration*30)}:s=1080x1920:fps=30,"
        f"eq=contrast=1.35:brightness=-0.05:saturation=0.65,"
        f"colorbalance=bs=0.15:bm=0.1:rs=-0.05,"
        f"vignette=PI/4,"
        f"drawtext=text='{caption_escaped}'{font_param}:fontcolor=yellow:fontsize=54:"
        f"bordercolor=black:borderw=6:x=(w-text_w)/2:y=h-420[v]"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
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
        "-t",
        str(duration),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        out_path,
    ]
    subprocess.run(cmd, check=True)


async def main():
    print("🚀 नयाँ रहस्य कथा खोज्दैछ...")
    data = generate_mystery_story()
    topic = data["topic"]
    save_history(topic)
    print(f"\n🔥 छानिएको नयाँ विषय: {topic}")

    scene_files = []
    for idx, scene in enumerate(data["scenes"], 1):
        print(f"\n--- सिन {idx} तयार गर्दैछ ---")
        aud_file = f"audio_{idx}.mp3"
        img_file = f"img_{idx}.jpg"
        vid_file = f"scene_{idx}.mp4"

        await generate_scene_voice(scene["hindi_speech"], aud_file)
        dur = get_audio_duration(aud_file)

        download_ai_image(scene["english_visual_prompt"], img_file)

        build_scene_video(
            img_file, aud_file, scene["hinglish_caption"], dur, vid_file
        )
        scene_files.append(vid_file)

    with open("list.txt", "w") as f:
        for v in scene_files:
            f.write(f"file '{v}'\n")

    print("\n🎬 सबै सिनहरू र ब्याकग्राउन्ड सस्पेन्स साउन्ड जोड्दैछ...")

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
        "aevalsrc=0.12*sin(2*PI*55*t)+0.06*sin(2*PI*110*t):s=44100",
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
        "final_mystery_short.mp4",
    ]
    subprocess.run(cmd_final, check=True)

    print("\n🎉 १००% कम्प्लिट भयो! भिडियो फाइल: final_mystery_short.mp4")


if __name__ == "__main__":
    asyncio.run(main())
