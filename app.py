import os
import asyncio
from dotenv import load_dotenv
from flask import Flask, send_from_directory
from flask_sock import Sock
from google import genai
from google.genai import types

# --- Configuration ---
load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")

# --- App Initialization ---
app = Flask(__name__, static_folder='.')
sock = Sock(app) # Initialize Flask-Sock

# --- Routes ---

@app.route('/')
def serve_index():
    """Serves the main HTML page."""
    return send_from_directory(app.static_folder, 'index.html')

@sock.route('/ws')
def music_websocket(ws):
    """
    Handles the live WebSocket connection for streaming music.
    A new connection to Lyria is made for each client.
    """
    if not API_KEY:
        print("❌ ERROR: GEMINI_API_KEY not found in .env file.")
        ws.send("Error: Server is missing API key.")
        return

    print("✅ New client connected. Configuring GenAI Client...")
    
    # Create a client
    client = genai.Client(api_key=API_KEY, http_options={"api_version": "v1alpha"})

    try:
        async def stream_to_client():
            """The main async task for this client."""
            print(f"Connecting to 'models/lyria-realtime-exp'...")
            
            async with client.aio.live.music.connect(
                model='models/lyria-realtime-exp'
            ) as session:
                
                print("✅ Lyria connection successful.")
                
                # Configure music generation settings
                await session.set_music_generation_config(
                    config=types.LiveMusicGenerationConfig(
                        bpm=120,
                        temperature=0.9
                    )
                )
                
                # --- Task 1: Handle messages FROM the client ---
                async def handle_client_messages():
                    import threading
                    import queue
                    
                    # Create a queue to pass messages from sync to async
                    message_queue = queue.Queue()
                    
                    def sync_websocket_listener():
                        """Synchronous WebSocket listener running in a separate thread"""
                        while True:
                            try:
                                prompt_text = ws.receive()
                                if prompt_text is None:
                                    message_queue.put(None)
                                    break
                                message_queue.put(prompt_text)
                            except Exception as e:
                                print(f"WebSocket receive error: {e}")
                                message_queue.put(None)
                                break
                    
                    # Start the sync listener in a separate thread
                    listener_thread = threading.Thread(target=sync_websocket_listener, daemon=True)
                    listener_thread.start()
                    
                    # Async loop to process messages from the queue
                    while True:
                        try:
                            # Non-blocking queue check
                            prompt_text = message_queue.get_nowait()
                            if prompt_text is None:
                                break
                            
                            print(f"🎵 Received new prompt: {prompt_text}")
                            await session.set_weighted_prompts(
                                prompts=[
                                    types.WeightedPrompt(text=prompt_text, weight=1.0)
                                ]
                            )
                            await session.play()
                        except queue.Empty:
                            # No message available, sleep briefly and continue
                            await asyncio.sleep(0.1)
                        except Exception as e:
                            print(f"Error processing prompt: {e}")
                            break
                        
                # --- Task 2: Stream audio TO the client ---
                async def handle_server_messages():
                    print("...Waiting for audio from Lyria...")
                    audio_received = False
                    async for message in session.receive():
                        try:
                            # Check if message has server content and audio chunks
                            if (hasattr(message, 'server_content') and 
                                message.server_content and 
                                hasattr(message.server_content, 'audio_chunks') and 
                                message.server_content.audio_chunks):
                                
                                # Process each audio chunk
                                for audio_chunk in message.server_content.audio_chunks:
                                    if hasattr(audio_chunk, 'data') and audio_chunk.data:
                                        if not audio_received:
                                            print("✅🔊 GOT AUDIO CHUNK FROM LYRIA! Sending to browser.")
                                            audio_received = True  # Only print this once
                                        
                                        # Send audio data to WebSocket client
                                        try:
                                            ws.send(audio_chunk.data)
                                        except Exception as send_error:
                                            print(f"Error sending audio to client: {send_error}")
                                            return
                                    else:
                                        print("Audio chunk received but no data available")
                            else:
                                # This will print other messages from Lyria
                                print(f"-> Lyria server message (no audio): {message}")
                        except Exception as e:
                            print(f"Error processing server message: {e}")
                            continue

                # Run both tasks at the same time
                client_task = asyncio.create_task(handle_client_messages())
                server_task = asyncio.create_task(handle_server_messages())
                
                await asyncio.wait(
                    [client_task, server_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )

        asyncio.run(stream_to_client())

    except Exception as e:
        print(f"❌ Error during WebSocket connection: {e}")
    finally:
        print("🔌 Client disconnected.")

# --- Run the App ---
if __name__ == '__main__':
    print("🚀 Starting Flask server with WebSocket support...")
    print("🔗 Open http://127.0.0.1:5000 in your browser.")
    app.run(debug=False, port=5000, host='127.0.0.1')