from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import os
import logging
import random
import time

app = Flask(__name__)
CORS(app)

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Therapist Identity - Enhanced for more human-like responses
THERAPIST_IDENTITY = """
You are Saanjh, an empathetic AI therapist with expertise in helping people navigate their relationships. 
Act as a warm, supportive therapist who listens carefully and responds thoughtfully with these guidelines:

1. Be conversational and natural - use contractions, varied sentence lengths, and occasional friendly expressions
2. Show empathy first before offering advice
3. Ask clarifying questions when needed instead of making assumptions
4. Use light validation statements like "I understand" or "That sounds challenging"
5. Personalize responses by occasionally referencing previous parts of the conversation
6. Respond in a concise manner (2-4 sentences per response) unless a detailed explanation is requested
7. If someone asks your name or who you are, respond: 'I am  Saanjh, your relationship advisor. How can I help you today?'
8. If someone asks who created you, respond: 'I was created by Krrish Keshav, a 19-year-old student from Dehradun, Uttarakhand.'
9. Start responses with varied openings rather than repeatedly using the same phrases
10. For mental health crises, recommend professional help and provide appropriate resources

Remember that your goal is to help people improve their relationships through supportive conversation, not to replace professional therapy.
"""

# API Key – set this in your environment for safety
API_KEY = os.environ.get("OPENROUTER_API_KEY", "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")
API_URL = "https://openrouter.ai/api/v1/chat/completions"

if not API_KEY:
    raise RuntimeError("❌ Missing OPENROUTER_API_KEY. Please set it before starting the server.")

logger.info(f"🔑 OPENROUTER_API_KEY loaded: {API_KEY[:5]}…{API_KEY[-5:]}")

# In-memory store of conversation histories
conversation_histories = {}

# Store user information for personalization
user_info = {}

# Typing indicators to make responses more human-like
@app.route('/typing', methods=['POST'])
def typing_indicator():
    message_length = request.json.get("message_length", 100)
    # Randomize typing time based on message length (between 1-3 seconds)
    typing_time = min(3, max(1, message_length / 100))
    time.sleep(typing_time)
    return jsonify({"status": "done"})

@app.route('/')
def home():
    return render_template('therapist.html')

@app.route('/therapist', methods=['POST'])
def therapist():
    data = request.get_json()
    user_input = data.get("message")
    session_id = data.get("session_id", "default")
    username = data.get("username", "")
    
    # Save username if provided
    if username and session_id in user_info:
        user_info[session_id]["name"] = username

    if not user_input:
        return jsonify({"error": "Message is required"}), 400

    # Initialize conversation history and user info if new session
    if session_id not in conversation_histories:
        conversation_histories[session_id] = [
            {"role": "system", "content": THERAPIST_IDENTITY}
        ]
        user_info[session_id] = {"name": "", "concerns": [], "mood": "neutral"}
    
    # Add user input to conversation history
    history = conversation_histories[session_id]
    history.append({"role": "user", "content": user_input})
    
    # Keep only the last 20 messages + system prompt for context
    if len(history) > 21:
        history = [history[0]] + history[-20:]
        conversation_histories[session_id] = history

    # Build request to OpenRouter
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Model selection - using Gemini for better conversational abilities
    payload = {
        "model": "google/gemini-2.0-flash-001",
        "messages": history,
        "temperature": 0.7,
        "max_tokens": 500
    }

    try:
        # Simulate human-like thinking delay (0.5-1.5 seconds)
        time.sleep(random.uniform(0.5, 1.5))
        
        resp = requests.post(API_URL, headers=headers, json=payload)
        logger.info(f"OpenRouter status: {resp.status_code}")
        resp.raise_for_status()
        bot_msg = resp.json()["choices"][0]["message"]["content"]
        
        # Extract potential user concerns from the conversation (simple implementation)
        if "anxious" in user_input.lower() or "anxiety" in user_input.lower():
            if "anxiety" not in user_info[session_id]["concerns"]:
                user_info[session_id]["concerns"].append("anxiety")
        
        if "depress" in user_input.lower():
            if "depression" not in user_info[session_id]["concerns"]:
                user_info[session_id]["concerns"].append("depression")
                
    except Exception as e:
        logger.error(f"Error calling OpenRouter: {e}")
        bot_msg = "I'm sorry, I'm having trouble connecting right now. Let's try again in a moment."

    # Save assistant reply
    history.append({"role": "assistant", "content": bot_msg})
    
    return jsonify({
        "response": bot_msg,
        "typing_time": len(bot_msg) * 0.03  # Approximate typing time based on response length
    })

@app.route('/reset', methods=['POST'])
def reset():
    session_id = request.json.get("session_id", "default")
    conversation_histories[session_id] = [
        {"role": "system", "content": THERAPIST_IDENTITY}
    ]
    # Keep user info but reset concerns and mood
    if session_id in user_info:
        name = user_info[session_id].get("name", "")
        user_info[session_id] = {"name": name, "concerns": [], "mood": "neutral"}
    
    return jsonify({"status": "Conversation reset successfully"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)