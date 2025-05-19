import os
import asyncio
import logging
from fastapi import FastAPI, WebSocket, Request, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from livekit import rtc
from livekit.api import AccessToken, VideoGrants
from dotenv import load_dotenv
import uvicorn
from starlette.websockets import WebSocketState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(dotenv_path="application/.env")

app = FastAPI()

app.mount("/static", StaticFiles(directory="variables/static"), name="static")
templates = Jinja2Templates(directory="templates")

LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
LIVEKIT_HOST = os.getenv("LIVEKIT_HOST")

class MockLLM:
    async def generate(self, prompt):
        logger.info(f"Generating response for prompt: {prompt}")
        return f"Echo: {prompt}"

class ChatbotAgent:
    def __init__(self):
        self.llm = MockLLM()
        self.room = None
        self.participant = None
    
    async def connect(self, room_name, identity):
        self.room = rtc.Room()
        
        if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
            raise ValueError("LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be set in environment variables")
        
        token = AccessToken(api_key=LIVEKIT_API_KEY, api_secret=LIVEKIT_API_SECRET) \
            .with_identity(identity) \
            .with_name(identity) \
            .with_grants(VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True
            )) \
            .to_jwt()
        
        await self.room.connect(LIVEKIT_HOST, token)
        logger.info(f"Connected to room {room_name} as {identity}")
        
        self.room.on("participant_connected", self.on_participant_connected)
        self.room.on("participant_disconnected", self.on_participant_disconnected)
        self.room.on("data_received", self.on_data_received)
        
        return self.room
    
    async def disconnect(self):
        if self.room:
            await self.room.disconnect()
            self.room = None
            logger.info("Disconnected from LiveKit room")
    
    def on_participant_connected(self, participant):
        logger.info(f"Participant connected: {participant.identity}")
    
    def on_participant_disconnected(self, participant):
        logger.info(f"Participant disconnected: {participant.identity}")
    
    def on_data_received(self, data, participant, kind):
        try:
            message = data.decode('utf-8')
            logger.info(f"Received message from {participant.identity}: {message}")
            
            async def process_message():
                response = await self.llm.generate(message)
                await self.room.local_participant.publish_data(
                    payload=response.encode('utf-8'), reliable=True
                )
            
            asyncio.create_task(process_message())
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def send_message(self, message):
        if self.room and self.room.local_participant:
            logger.info(f"Sending message: {message}")
            await self.room.local_participant.publish_data(
                payload=message.encode('utf-8'), reliable=True
            )
            return True
        logger.warning("Cannot send message: Room or participant not initialized")
        return False

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    agent = ChatbotAgent()
    room_name = "demo-room"
    
    try:
        await agent.connect(room_name, "chatbot-agent")
        
        while True:
            message = await websocket.receive_text()
            logger.info(f"Received WebSocket message: {message}")
            response = await agent.llm.generate(message)
            await websocket.send_text(response)
            await agent.send_message(response)
            
    except WebSocketDisconnect as e:
        logger.info(f"WebSocket disconnected: code={e.code}, reason={e.reason}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await agent.disconnect()
        if websocket.client_state == WebSocketState.CONNECTED:
            logger.info("Closing WebSocket connection")
            await websocket.close(code=1000, reason="Normal closure")
        else:
            logger.info("WebSocket already closed")

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    os.makedirs("templates", exist_ok=True)
    
    if not os.path.exists("templates/index.html"):
        with open("templates/index.html", "w") as f:
            f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voice Chatbot</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <h1>LiveKit Voice Chatbot</h1>
    
    <div class="chat-container" id="chat-container"></div>
    
    <div class="input-area">
        <input type="text" id="message-input" placeholder="Type your message here..." />
        <button id="send-btn">Send</button>
    </div>
    
    <div class="controls">
        <button id="start-voice-btn">Start Voice Chat</button>
        <button id="stop-voice-btn" disabled>Stop Voice Chat</button>
        <button id="clear-btn">Clear Chat</button>
    </div>

    <script>
        const chatContainer = document.getElementById('chat-container');
        const messageInput = document.getElementById('message-input');
        const sendBtn = document.getElementById('send-btn');
        const startVoiceBtn = document.getElementById('start-voice-btn');
        const stopVoiceBtn = document.getElementById('stop-voice-btn');
        const clearBtn = document.getElementById('clear-btn');
        
        let socket;
        let reconnectAttempts = 0;
        const maxReconnectAttempts = 5;
        let reconnectTimeout = null;
        
        function initWebSocket() {
            if (reconnectTimeout) clearTimeout(reconnectTimeout);
            socket = new WebSocket(`ws://${window.location.host}/ws`);
            
            socket.onopen = () => {
                console.log('WebSocket connection established');
                addMessage('System', 'Connected to server');
                reconnectAttempts = 0;
            };
            
            socket.onmessage = (event) => {
                console.log('Received message:', event.data);
                addMessage('Bot', event.data);
            };
            
            socket.onclose = (event) => {
                console.log(`WebSocket closed: code=${event.code}, reason=${event.reason}`);
                addMessage('System', `Disconnected (code: ${event.code}${event.reason ? ', ' + event.reason : ''})`);
                
                if (reconnectAttempts < maxReconnectAttempts) {
                    reconnectAttempts++;
                    const delay = Math.min(3000 * Math.pow(2, reconnectAttempts), 10000);
                    console.log(`Reconnecting in ${delay}ms (${reconnectAttempts}/${maxReconnectAttempts})...`);
                    reconnectTimeout = setTimeout(initWebSocket, delay);
                } else {
                    addMessage('System', 'Max reconnect attempts reached. Please refresh the page.');
                }
            };
            
            socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                addMessage('System', 'Connection error occurred');
            };
        }
        
        function addMessage(sender, text) {
            const messageElement = document.createElement('div');
            messageElement.classList.add('message');
            messageElement.classList.add(sender.toLowerCase() === 'bot' ? 'bot' : 'user');
            
            messageElement.innerHTML = `<strong>${sender}:</strong> ${text}`;
            chatContainer.appendChild(messageElement);
            
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        function sendMessage() {
            const message = messageInput.value.trim();
            
            if (message && socket && socket.readyState === WebSocket.OPEN) {
                console.log('Sending message:', message);
                socket.send(message);
                addMessage('You', message);
                messageInput.value = '';
                messageInput.focus();
            } else {
                addMessage('System', 'Cannot send message: Not connected');
            }
        }
        
        async function initLiveKitVoice() {
            try {
                const response = await fetch(`/token?identity=user-${Date.now()}`);
                const data = await response.json();
                
                addMessage('System', 'Voice chat initialized (placeholder)');
                startVoiceBtn.disabled = true;
                stopVoiceBtn.disabled = false;
            } catch (error) {
                console.error('Error initializing voice chat:', error);
                addMessage('System', 'Failed to initialize voice chat');
            }
        }
        
        sendBtn.addEventListener('click', sendMessage);
        
        messageInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                sendMessage();
            }
        });
        
        startVoiceBtn.addEventListener('click', initLiveKitVoice);
        
        stopVoiceBtn.addEventListener('click', () => {
            addMessage('System', 'Voice chat stopped (placeholder)');
            startVoiceBtn.disabled = false;
            stopVoiceBtn.disabled = true;
        });
        
        clearBtn.addEventListener('click', () => {
            chatContainer.innerHTML = '';
        });
        
        window.addEventListener('load', initWebSocket);
        
        window.addEventListener('beforeunload', () => {
            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.close(1000, 'Page unloading');
            }
        });
    </script>
</body>
</html>""")
    
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/token")
async def get_token(identity: str, room: str = "demo-room"):
    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        raise ValueError("LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be set in environment variables")
        
    token = AccessToken(api_key=LIVEKIT_API_KEY, api_secret=LIVEKIT_API_SECRET) \
        .with_identity(identity) \
        .with_name(identity) \
        .with_grants(VideoGrants(
            room_join=True,
            room=room,
            can_publish=True,
            can_subscribe=True
        )) \
        .to_jwt()
    return {"token": token}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)