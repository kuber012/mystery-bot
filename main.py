import asyncio
import edge_tts


async def generate_voice():
    # सस्पेन्स र डरलाग्दो बनाइएको हिन्दी आवाज
    text = "१९४५ में समुन्दर के ऊपर से ५ लड़ाकू विमान अचानक गायब हो गए। आज तक दुनिया का कोई भी वैज्ञानिक इनका पता नहीं लगा पाया।"

    print("🎙️ आवाज बन्दैछ...")
    communicate = edge_tts.Communicate(
        text=text, voice="hi-IN-MadhurNeural", pitch="-6Hz", rate="-5%"
    )
    await communicate.save("mystery_voice.mp3")
    print("✅ अडियो तयार भयो: mystery_voice.mp3")


if __name__ == "__main__":
    asyncio.run(generate_voice())
