### 1. Solution/Architecture

#### Overview
The LiveKit Chatbot is a real-time, web-based application that supports text-based interaction with a Mock LLM, leveraging LiveKit Cloud for WebRTC connectivity. The system is designed to be lightweight, free to use, and extensible for future audio integration. It uses a client-server architecture with FastAPI for the backend, a web interface for the frontend, and LiveKit for real-time communication.

#### Architecture Components
1. **Frontend (Client)**:
   - **Purpose**: Provides a user interface for sending text messages and (partially) recording audio.
   - **Technologies**:
     - **HTML/Jinja2 Template (`index.html`)**: Renders the chat interface.
     - **CSS (`style.css`)**: Styles the interface with a responsive, modern design.
     - **JavaScript**: Handles WebSocket communication and audio recording (currently logs audio chunks).
   - **Functionality**:
     - Users type messages in a text input and send them via WebSocket.
     - Displays user and bot messages in a chat container.
     - Buttons for starting/stopping audio recording and clearing the chat.
     - Responsive design for mobile and desktop.

2. **Backend (Server)**:
   - **Purpose**: Manages WebSocket connections, LiveKit room interactions, and Mock LLM responses.
   - **Technologies**:
     - **FastAPI**: Serves the web interface, handles WebSocket endpoints, and mounts static files.
     - **LiveKit Python SDK**: Connects to LiveKit Cloud for real-time communication.
     - **Mock LLM**: A simple class that echoes user input (e.g., "Hello" → "Echo: Hello").
     - **python-dotenv**: Loads environment variables for LiveKit credentials.
   - **Functionality**:
     - **WebSocket Endpoint (`/ws`)**: Receives user messages, processes them with the Mock LLM, and sends responses back.
     - **LiveKit Room**: Connects to a "demo-room" for real-time data exchange, publishing responses to participants.
     - **Token Endpoint (`/token`)**: Generates JWTs for LiveKit room access.
     - **Logging**: Tracks connection events, messages, and errors for debugging.

3. **LiveKit Cloud**:
   - **Purpose**: Provides WebRTC infrastructure for real-time communication.
   - **Role**: Hosts the "demo-room" where the chatbot agent operates, using the free tier for cost-free operation.
   - **Credentials**: API Key, API Secret, and Host URL are stored in a `.env` file.

4. **Mock LLM**:
   - **Purpose**: Simulates an LLM by echoing user input, ensuring a free solution.
   - **Implementation**: A `MockLLM` class with an async `generate` method that prefixes "Echo: " to the input.

#### Data Flow
1. **User Interaction**:
   - User types a message in the web interface and clicks "Send".
   - The message is sent via WebSocket to the `/ws` endpoint.
2. **Backend Processing**:
   - The FastAPI server receives the message.
   - The `ChatbotAgent` processes it with the `MockLLM`, generating a response (e.g., "Echo: Hello").
   - The response is sent back to the client via WebSocket and published to the LiveKit room.
3. **Frontend Update**:
   - The client receives the response and appends it to the chat container as a bot message.
4. **Audio (Partial)**:
   - Audio recording starts/stops via buttons, logging chunks to the browser console (full processing requires additional LiveKit setup).

#### Architecture Diagram
```
[User] <--> [Browser: HTML/CSS/JS]
                     |
                     | (WebSocket: ws://localhost:8000/ws)
                     |
            [FastAPI Server: main.py]
               |        |
               |        | (MockLLM: Echoes input)
               |        |
               |    [ChatbotAgent]
               |        |
               |        | (LiveKit SDK)
               |        |
            [LiveKit Cloud: demo-room]
```

#### Key Features
- **Text Chat**: Real-time text input/output with a Mock LLM.
- **WebRTC Integration**: LiveKit room for scalable communication.
- **Responsive UI**: Clean, mobile-friendly interface.
- **Free**: Uses LiveKit Cloud free tier and Mock LLM.
- **Extensible**: Ready for audio integration or real LLM replacement.

#### Limitations
- **Audio**: Limited to logging audio chunks; full voice processing needs WebRTC audio streaming.
- **Mock LLM**: Basic echo functionality; lacks intelligent responses.
- **Scalability**: Free tier has usage limits; production requires monitoring.

---

### 2. Documentation

#### Project Name
LiveKit Voice Chatbot

#### Description
A web-based chatbot demo using LiveKit Cloud for real-time communication and a Mock LLM for text responses. The application supports text input/output and partial audio recording, designed to be free and extensible.

#### Folder Structure
```
Voice_Chatbot/
├── main.py                 # FastAPI application
├── .env                    # Environment variables (LiveKit credentials)
├── static/                 # Static files
│   └── style.css           # CSS styles
├── templates/              # HTML templates
│   └── index.html          # Main page
├── requirements.txt        # Python dependencies
└── venv/                   # Virtual environment
```

#### Prerequisites
1. **Python 3.10+**:
   - Verify: `python --version`.
   - Install from [python.org](https://www.python.org/downloads/) if needed.
2. **LiveKit Cloud Account** (Free Tier):
   - Sign up at [LiveKit Cloud](https://livekit.io/cloud).
   - Obtain **API Key**, **API Secret**, and **Host URL** from the dashboard.
3. **Web Browser**: Chrome, Firefox, or Edge for testing.

#### Setup Instructions
1. **Clone or Create Project Folder**:
   - Create a folder: `E:\Projects\Blackcoffer Pratice\Voice_Chatbot`.
   - Place the provided source files (below) in the correct structure.

2. **Set Up Virtual Environment**:
   - Open PowerShell and navigate to the project folder:
     ```powershell
     cd "E:\Projects\Blackcoffer Pratice\Voice_Chatbot"
     ```
   - Create and activate a virtual environment:
     ```powershell
     python -m venv venv
     .\venv\Scripts\activate
     ```

3. **Install Dependencies**:
   - Ensure `requirements.txt` is in the project root.
   - Install packages:
     ```powershell
     pip install -r requirements.txt
     ```

4. **Configure Environment Variables**:
   - Create a `.env` file in the project root:
     ```plaintext
     LIVEKIT_API_KEY=your_api_key
     LIVEKIT_API_SECRET=your_api_secret
     LIVEKIT_HOST=https://your-livekit-host.livekit.cloud
     ```
   - Replace placeholders with your LiveKit Cloud credentials.
   - Example:
     ```plaintext
     LIVEKIT_API_KEY=API123456789
     LIVEKIT_API_SECRET=secret123456789
     LIVEKIT_HOST=https://chatbot-aus4f2hf.livekit.cloud
     ```

5. **Verify Source Files**:
   - Ensure `main.py`, `static/style.css`, `templates/index.html`, and `requirements.txt` are correctly placed.
   - The server will create `templates/index.html` if missing, but it’s included below for completeness.

6. **Run the Server**:
   - Start the FastAPI server:
     ```powershell
     uvicorn main:app --host 0.0.0.0 --port 8000 --reload
     ```
   - Expected output:
     ```
     INFO:     Will watch for changes in these directories: ['E:\\Projects\\Blackcoffer Pratice\\Voice_Chatbot']
     INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
     INFO:     Started reloader process [...]
     INFO:     Started server process [...]
     INFO:     Waiting for application startup.
     INFO:     Application startup complete.
     ```

#### How to Use
1. **Access the Chatbot**:
   - Open a browser and navigate to `http://localhost:8000`.
   - The interface shows a chat container, text input, and buttons.

2. **Send Text Messages**:
   - Type a message (e.g., "Hello") in the input field.
   - Click "Send" or press Enter.
   - The chat container displays:
     - User message (e.g., "Hello") in a blue bubble.
     - Bot response (e.g., "Echo: Hello") in a gray bubble.

3. **Test Audio (Limited)**:
   - Click "Start Voice Chat" to begin recording (allow microphone access).
   - Speak, then click "Stop Voice Chat".
   - Check the browser console (F12 > Console) for logs like:
     ```
     Recording started
     Audio chunk recorded
     Recording stopped
     ```
   - Note: Audio is not fully processed in this demo.

4. **Clear Chat**:
   - Click "Clear Chat" to remove all messages from the chat container.

5. **Stop the Server**:
   - In PowerShell, press `Ctrl+C`.
   - Deactivate the virtual environment:
     ```powershell
     deactivate
     ```

### Final Verification
Your logs confirm the server is running and handling messages correctly:
- WebSocket connection established.
- Message "Hello" processed, with response "Echo: Hello".
- LiveKit room connection successful.

To test:
1. Access `http://localhost:8000`.
2. Send a message (e.g., "Test") and verify the response ("Echo: Test").
3. Test audio buttons and check console logs.
4. Ensure the UI matches the styled design from `style.css`.
