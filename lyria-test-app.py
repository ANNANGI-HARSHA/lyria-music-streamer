# lyria_rt_diagnose.py
import os, asyncio, wave, json, signal
from dotenv import load_dotenv  # <-- 1. IMPORT THIS
from google import genai
from google.genai import types

load_dotenv()  # <-- 2. ADD THIS TO LOAD THE .env FILE

# This line will now automatically find the key from your .env file
API_KEY = os.environ["GEMINI_API_KEY"] 

# v1alpha is required for Lyria RealTime per docs
client = genai.Client(api_key=API_KEY, http_options={"api_version": "v1alpha"})

DURATION_SEC = 12  # stream a bit longer to ensure chunks arrive

async def main():
    audio_chunks = []
    non_audio_msgs = 0

    async def receiver(session):
        nonlocal non_audio_msgs
        async for msg in session.receive():
            # Log raw message types for diagnosis
            kind = getattr(msg, "kind", None)
            if getattr(msg, "server_content", None) and msg.server_content.audio_chunks:
                for ch in msg.server_content.audio_chunks:
                    if ch.data:
                        audio_chunks.append(ch.data)
                    else:
                        print("Chunk missing PCM data:", ch)
            else:
                non_audio_msgs += 1
                # Print trimmed message so we can see what's happening
                try:
                    print("SERVER MSG (no-audio):", json.dumps(msg.model_dump(mode="json"))[:500], "...")
                except Exception:
                    print("SERVER MSG (no-audio):", msg)

    async with client.aio.live.music.connect(model="models/lyria-realtime-exp") as session:
        # Start receiver
        recv_task = asyncio.create_task(receiver(session))

        # 1) Prompt + config
        await session.set_weighted_prompts(prompts=[
            types.WeightedPrompt(
                text="Uplifting lo-fi house, warm pads, side-chained kick, 120 BPM",
                weight=1.0
            )
        ])

        # Optional: set BPM/temperature; defaults are okay, but explicit helps.
        await session.set_music_generation_config(
            config=types.LiveMusicGenerationConfig(
                bpm=120,
                temperature=0.9,
                # You can omit these; defaults are PCM16 stereo at ~48 kHz.
                # audio_format=types.AudioFormat.PCM16,
                # sample_rate_hz=48000,
            )
        )

        # 2) Play and let it stream
        await session.play()
        await asyncio.sleep(DURATION_SEC)

        # 3) Stop and allow final chunks to drain
        await session.stop()
        await asyncio.sleep(0.5)

        # Cancel receiver cleanly
        recv_task.cancel()
        try:
            await recv_task
        except asyncio.CancelledError:
            pass

    # Write the WAV only if we captured audio
    pcm = b"".join(audio_chunks)
    if pcm:
        with wave.open("lyria_realtime_test.wav", "wb") as f:
            f.setnchannels(2)
            f.setsampwidth(2)     # 16-bit
            f.setframerate(48000) # API streams ~48 kHz PCM
            f.writeframes(pcm)
        print(f"OK ✅  wrote lyria_realtime_test.wav ({len(pcm)//1024} KB), chunks={len(audio_chunks)}, non-audio msgs={non_audio_msgs}")
    else:
        print(f"⚠️  No audio received. chunks=0, non-audio msgs={non_audio_msgs} — see server messages above.")

if __name__ == "__main__":
    # Allow Ctrl+C to stop
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    asyncio.run(main())