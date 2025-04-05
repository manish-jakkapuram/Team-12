import streamlit as st
import pandas as pd
import hashlib
import json
import os
import time
import random
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from src.helper import voice_input, llm_model_object, text_to_speech

# Initialize session state variables if they don't exist
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'points' not in st.session_state:
    st.session_state.points = 0
if 'badges' not in st.session_state:
    st.session_state.badges = []
if 'streak' not in st.session_state:
    st.session_state.streak = 0
if 'last_interaction' not in st.session_state:
    st.session_state.last_interaction = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Chat"
if 'mood_data' not in st.session_state:
    st.session_state.mood_data = []
if 'achievements' not in st.session_state:
    st.session_state.achievements = []
if 'theme' not in st.session_state:
    st.session_state.theme = "default"
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""
if 'input_method' not in st.session_state:
    st.session_state.input_method = "Text"

# File paths for data storage
USERS_DB = "data/users.json"
CHAT_HISTORY_DIR = "data/chat_history"
MOOD_DATA_DIR = "data/mood_data"
ACHIEVEMENT_DIR = "data/achievements"

# Create directories if they don't exist
os.makedirs(os.path.dirname(USERS_DB), exist_ok=True)
os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)
os.makedirs(MOOD_DATA_DIR, exist_ok=True)
os.makedirs(ACHIEVEMENT_DIR, exist_ok=True)

# Initialize users database if it doesn't exist
if not os.path.exists(USERS_DB):
    with open(USERS_DB, "w") as f:
        json.dump({}, f)

# Background images and themes
THEMES = {
    "default": {
        "primary_color": "#4CAF50",
        "background": "url('https://images.unsplash.com/photo-1557682250-33bd709cbe85?q=80&w=2000')",
        "card_bg": "rgba(255, 255, 255, 0.8)",
        "user_bubble": "#dcf8c6",
        "bot_bubble": "#f1f0f0",
        "accent_color": "#FF5722",
    },
    "space": {
        "primary_color": "#3F51B5",
        "background": "url('https://images.unsplash.com/photo-1534796636912-3b95b3ab5986?q=80&w=2000')",
        "card_bg": "rgba(0, 0, 20, 0.7)",
        "user_bubble": "#4CAF50",
        "bot_bubble": "#7986CB",
        "accent_color": "#FF9800",
    },
    "ocean": {
        "primary_color": "#039BE5",
        "background": "url('https://images.unsplash.com/photo-1518837695005-2083093ee35b?q=80&w=2000')",
        "card_bg": "rgba(255, 255, 255, 0.7)",
        "user_bubble": "#80DEEA",
        "bot_bubble": "#B3E5FC",
        "accent_color": "#FF5722",
    },
    "forest": {
        "primary_color": "#388E3C",
        "background": "url('https://images.unsplash.com/photo-1448375240586-882707db888b?q=80&w=2000')",
        "card_bg": "rgba(255, 255, 255, 0.8)",
        "user_bubble": "#C5E1A5",
        "bot_bubble": "#DCEDC8",
        "accent_color": "#FF9800",
    },
    "sunset": {
        "primary_color": "#E64A19",
        "background": "url('https://images.unsplash.com/photo-1530508777238-14544088c3ed?q=80&w=2000')",
        "card_bg": "rgba(255, 255, 255, 0.7)",
        "user_bubble": "#FFCCBC",
        "bot_bubble": "#FFECB3",
        "accent_color": "#673AB7",
    }
}

# Sentiment analysis helper function (simplified)
def analyze_sentiment(text):
    positive_words = ["happy", "good", "great", "awesome", "excellent", "love", "like", "thanks", "thank", "please", "help", "nice", "wonderful", "fantastic", "amazing", "joy", "glad", "positive"]
    negative_words = ["sad", "bad", "terrible", "awful", "hate", "dislike", "angry", "mad", "upset", "unhappy", "disappointed", "negative", "worse", "worst", "horrible"]
    
    positive_count = sum(1 for word in positive_words if word in text.lower())
    negative_count = sum(1 for word in negative_words if word in text.lower())
    
    score = positive_count - negative_count
    
    if score > 2:
        return "very_positive", 5
    elif score > 0:
        return "positive", 4
    elif score == 0:
        return "neutral", 3
    elif score > -3:
        return "negative", 2
    else:
        return "very_negative", 1

# Helper functions for user management
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def save_user(username, password):
    with open(USERS_DB, "r") as f:
        users = json.load(f)
    
    users[username] = {
        "password_hash": hash_password(password),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "points": 0,
        "badges": [],
        "streak": 0,
        "last_interaction": None,
        "theme": "default",
        "achievements": []
    }
    
    with open(USERS_DB, "w") as f:
        json.dump(users, f)

def authenticate(username, password):
    with open(USERS_DB, "r") as f:
        users = json.load(f)
    
    if username in users and users[username]["password_hash"] == hash_password(password):
        st.session_state.points = users[username].get("points", 0)
        st.session_state.badges = users[username].get("badges", [])
        st.session_state.streak = users[username].get("streak", 0)
        st.session_state.last_interaction = users[username].get("last_interaction")
        st.session_state.theme = users[username].get("theme", "default")
        st.session_state.achievements = users[username].get("achievements", [])
        return True
    return False

def update_user_data():
    with open(USERS_DB, "r") as f:
        users = json.load(f)
    
    if st.session_state.username in users:
        users[st.session_state.username]["points"] = st.session_state.points
        users[st.session_state.username]["badges"] = st.session_state.badges
        users[st.session_state.username]["streak"] = st.session_state.streak
        users[st.session_state.username]["last_interaction"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        users[st.session_state.username]["theme"] = st.session_state.theme
        users[st.session_state.username]["achievements"] = st.session_state.achievements
        
        with open(USERS_DB, "w") as f:
            json.dump(users, f)

# Chat history management
def save_chat_history():
    if st.session_state.username:
        history_file = f"{CHAT_HISTORY_DIR}/{st.session_state.username}_history.json"
        with open(history_file, "w") as f:
            json.dump(st.session_state.chat_history, f)

def load_chat_history():
    if st.session_state.username:
        history_file = f"{CHAT_HISTORY_DIR}/{st.session_state.username}_history.json"
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                st.session_state.chat_history = json.load(f)
        else:
            st.session_state.chat_history = []

# Mood data management
def save_mood_data(sentiment, score):
    if st.session_state.username:
        mood_file = f"{MOOD_DATA_DIR}/{st.session_state.username}_mood.json"
        
        if os.path.exists(mood_file):
            with open(mood_file, "r") as f:
                mood_data = json.load(f)
        else:
            mood_data = []
        
        mood_data.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sentiment": sentiment,
            "score": score
        })
        
        with open(mood_file, "w") as f:
            json.dump(mood_data, f)
        
        st.session_state.mood_data = mood_data

def load_mood_data():
    if st.session_state.username:
        mood_file = f"{MOOD_DATA_DIR}/{st.session_state.username}_mood.json"
        if os.path.exists(mood_file):
            with open(mood_file, "r") as f:
                st.session_state.mood_data = json.load(f)
        else:
            st.session_state.mood_data = []

# Achievement management
def add_achievement(title, description, points, icon="🏆"):
    if st.session_state.username:
        achievement_exists = any(a["title"] == title for a in st.session_state.achievements)
        
        if not achievement_exists:
            achievement = {
                "title": title,
                "description": description,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "points": points,
                "icon": icon
            }
            
            st.session_state.achievements.append(achievement)
            st.session_state.points += points
            
            achievement_file = f"{ACHIEVEMENT_DIR}/{st.session_state.username}_achievements.json"
            with open(achievement_file, "w") as f:
                json.dump(st.session_state.achievements, f)
            
            st.balloons()
            st.success(f"🎉 New Achievement Unlocked: {title} (+{points} points)")
            
            return True
    
    return False

def load_achievements():
    if st.session_state.username:
        achievement_file = f"{ACHIEVEMENT_DIR}/{st.session_state.username}_achievements.json"
        if os.path.exists(achievement_file):
            with open(achievement_file, "r") as f:
                st.session_state.achievements = json.load(f)
        else:
            st.session_state.achievements = []

# Gamification functions
def award_points(message, response):
    points = 5  # Base points for interaction
    
    if len(message) > 20:
        points += 3
    
    sentiment, score = analyze_sentiment(message)
    save_mood_data(sentiment, score)
    
    if sentiment in ["positive", "very_positive"]:
        points += 2
    
    today = datetime.now().strftime("%Y-%m-%d")
    if st.session_state.last_interaction is None:
        st.session_state.streak = 1
    elif today not in st.session_state.last_interaction:
        last_date = datetime.strptime(st.session_state.last_interaction.split(" ")[0], "%Y-%m-%d")
        today_date = datetime.strptime(today, "%Y-%m-%d")
        
        if (today_date - last_date).days == 1:
            st.session_state.streak += 1
            
            if st.session_state.streak in [3, 7, 14, 30]:
                st.balloons()
                st.success(f"🔥 Amazing! You've reached a {st.session_state.streak}-day streak!")
                
        elif (today_date - last_date).days > 1:
            st.session_state.streak = 1
        
        if st.session_state.streak % 5 == 0:
            points += 10
            st.success(f"🔥 {st.session_state.streak} day streak! +10 bonus points!")
    
    check_for_achievements(message)
    
    st.session_state.points += points
    return points

def check_for_achievements(message=None):
    if st.session_state.points >= 100 and not any(a["title"] == "Beginner Communicator" for a in st.session_state.achievements):
        add_achievement("Beginner Communicator", "Earn 100 points through conversations", 20, "🥉")
    
    if st.session_state.points >= 500 and not any(a["title"] == "Intermediate Communicator" for a in st.session_state.achievements):
        add_achievement("Intermediate Communicator", "Earn 500 points through conversations", 50, "🥈")
    
    if st.session_state.points >= 1000 and not any(a["title"] == "Advanced Communicator" for a in st.session_state.achievements):
        add_achievement("Advanced Communicator", "Earn 1000 points through conversations", 100, "🥇")
    
    if st.session_state.streak >= 3 and not any(a["title"] == "3-Day Streak" for a in st.session_state.achievements):
        add_achievement("3-Day Streak", "Chat with the bot for 3 consecutive days", 15, "🔥")
    
    if st.session_state.streak >= 7 and not any(a["title"] == "Weekly Streak" for a in st.session_state.achievements):
        add_achievement("Weekly Streak", "Chat with the bot for 7 consecutive days", 30, "🌟")
    
    if st.session_state.streak >= 30 and not any(a["title"] == "Monthly Dedication" for a in st.session_state.achievements):
        add_achievement("Monthly Dedication", "Chat with the bot for 30 consecutive days", 100, "🏅")
    
    if len(st.session_state.chat_history) >= 10 and not any(a["title"] == "Conversation Starter" for a in st.session_state.achievements):
        add_achievement("Conversation Starter", "Have 10 exchanges with the bot", 15, "🗣️")
    
    if len(st.session_state.chat_history) >= 50 and not any(a["title"] == "Regular Chatter" for a in st.session_state.achievements):
        add_achievement("Regular Chatter", "Have 50 exchanges with the bot", 30, "💬")
    
    if len(st.session_state.chat_history) >= 100 and not any(a["title"] == "Chatting Expert" for a in st.session_state.achievements):
        add_achievement("Chatting Expert", "Have 100 exchanges with the bot", 50, "👑")
    
    if message:
        if any(word in message.lower() for word in ["thank you", "thanks", "appreciate"]) and not any(a["title"] == "Gratitude Expert" for a in st.session_state.achievements):
            add_achievement("Gratitude Expert", "Express thanks to the bot", 10, "🙏")
        
        if len(message) > 100 and not any(a["title"] == "Deep Thinker" for a in st.session_state.achievements):
            add_achievement("Deep Thinker", "Send a detailed, thoughtful message", 20, "🧠")
        
        creative_words = ["imagine", "create", "story", "idea", "draw", "invent", "design", "art"]
        if any(word in message.lower() for word in creative_words) and not any(a["title"] == "Creative Mind" for a in st.session_state.achievements):
            add_achievement("Creative Mind", "Engage in creative conversation", 15, "🎨")
        
        if "?" in message and not any(a["title"] == "Curious Learner" for a in st.session_state.achievements):
            add_achievement("Curious Learner", "Ask meaningful questions", 15, "❓")
        
        emoji_list = ["😊", "😄", "🙂", "👍", "❤️", "😁", "🎉", "👋", "😃"]
        if any(emoji in message for emoji in emoji_list) and not any(a["title"] == "Emoji Expert" for a in st.session_state.achievements):
            add_achievement("Emoji Expert", "Express yourself with emojis", 10, "😎")

def load_all_user_data():
    load_chat_history()
    load_mood_data()
    load_achievements()

# UI Components
def set_background():
    theme = THEMES[st.session_state.theme]
    st.markdown(f"""
    <style>
    .stApp {{
        background: {theme["background"]};
        background-size: cover;
        background-attachment: fixed;
    }}
    .card {{
        background-color: {theme["card_bg"]};
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
    }}
    .stButton button {{
        background-color: {theme["primary_color"]} !important;
        color: white !important;
        border-radius: 20px !important;
        border: none !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
        transition: all 0.3s ease !important;
    }}
    .stButton button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3) !important;
    }}
    .chat-message {{
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 10px;
        display: flex;
        flex-direction: column;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        animation: fadeIn 0.5s;
    }}
    .user-message {{
        background-color: {theme["user_bubble"]};
        margin-left: 50px;
        border-top-right-radius: 5px;
    }}
    .bot-message {{
        background-color: {theme["bot_bubble"]};
        margin-right: 50px;
        border-top-left-radius: 5px;
    }}
    .message-timestamp {{
        font-size: 0.8rem;
        color: #888;
        align-self: flex-end;
    }}
    .sidebar .stButton button {{
        width: 100%;
        margin-bottom: 10px;
    }}
    .achievement {{
        background: linear-gradient(135deg, {theme["primary_color"]}22, {theme["accent_color"]}22);
        border-left: 5px solid {theme["primary_color"]};
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: transform 0.3s ease;
    }}
    .achievement:hover {{
        transform: translateY(-5px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }}
    .badge-item {{
        display: inline-block;
        margin: 5px;
        padding: 8px 15px;
        background-color: {theme["primary_color"]};
        color: white;
        border-radius: 20px;
        font-size: 0.9rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }}
    .badge-item:hover {{
        transform: scale(1.05);
    }}
    .stats-box {{
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 12px;
        padding: 15px;
        margin: 5px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid {theme["primary_color"]};
        transition: all 0.3s ease;
    }}
    .stats-box:hover {{
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }}
    .page-title {{
        color: {theme["primary_color"]};
        margin-bottom: 20px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        font-size: 2.2rem;
        font-weight: bold;
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 24px;
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        white-space: pre-wrap;
        background-color: white;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        transition: all 0.3s ease;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {theme["primary_color"]} !important;
        color: white !important;
        transform: translateY(-3px);
    }}
    .stProgress > div > div > div > div {{
        background-color: {theme["primary_color"]};
    }}
    .points-animation {{
        position: fixed;
        color: {theme["accent_color"]};
        font-weight: bold;
        z-index: 9999;
        animation: floatUp 2s forwards;
    }}
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes floatUp {{
        0% {{ opacity: 0; transform: translateY(20px); }}
        10% {{ opacity: 1; }}
        80% {{ opacity: 1; }}
        100% {{ opacity: 0; transform: translateY(-50px); }}
    }}
    .login-form-container {{
        transition: all 0.5s ease;
        transform: scale(1);
    }}
    .login-form-container:hover {{
        transform: scale(1.02);
    }}
    .input-container {{
        position: relative;
        margin-bottom: 20px;
    }}
    .input-container input {{
        width: 100%;
        padding: 12px 15px;
        border: 2px solid #ddd;
        border-radius: 10px;
        font-size: 16px;
        transition: all 0.3s;
    }}
    .input-container input:focus {{
        border-color: {theme["primary_color"]};
        box-shadow: 0 0 8px {theme["primary_color"]}80;
    }}
    .input-container label {{
        position: absolute;
        top: -10px;
        left: 10px;
        background-color: white;
        padding: 0 5px;
        font-size: 12px;
        color: #555;
    }}
    .chat-input {{
        border-radius: 30px !important;
        padding: 12px 20px !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1) !important;
        border: 2px solid transparent !important;
        transition: all 0.3s ease !important;
    }}
    .chat-input:focus {{
        border-color: {theme["primary_color"]} !important;
        box-shadow: 0 2px 15px rgba(0,0,0,0.15) !important;
    }}
    .theme-selector {{
        border-radius: 8px;
        overflow: hidden;
        transition: all 0.3s ease;
    }}
    .theme-selector:hover {{
        transform: translateY(-3px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }}
    .level-indicator {{
        background: linear-gradient(90deg, {theme["primary_color"]}, {theme["accent_color"]});
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin-top: 5px;
    }}
    .settings-option {{
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 10px;
        background-color: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }}
    .settings-option:hover {{
        transform: translateY(-3px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }}
    </style>
    """, unsafe_allow_html=True)

def render_login_page():
    st.markdown("""
    <div class="card" style="text-align: center; padding: 30px;">
        <h1 style="font-size: 2.5rem; color: #4CAF50; margin-bottom: 10px;">🤖 Empathetic Response Chat Bot</h1>
        <p style="font-size: 1.2rem; margin-bottom: 30px;">Your friendly AI chat companion</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("""
        <div class="card" style="height: 100%;">
            <h2 style="color: #4CAF50; text-align: center; margin-bottom: 20px;">Why Kids Love KiddiChat</h2>
            <div style="display: flex; flex-wrap: wrap; justify-content: space-between;">
                <div style="flex: 0 0 48%; margin-bottom: 20px; padding: 15px; background-color: rgba(76, 175, 80, 0.1); border-radius: 10px;">
                    <h3 style="color: #4CAF50;">🏆 Earn Rewards</h3>
                    <p>Get points and cool badges for positive conversations and daily chats!</p>
                </div>
                <div style="flex: 0 0 48%; margin-bottom: 20px; padding: 15px; background-color: rgba(33, 150, 243, 0.1); border-radius: 10px;">
                    <h3 style="color: #2196F3;">📊 Track Progress</h3>
                    <p>See how your communication skills improve over time with fun charts!</p>
                </div>
                <div style="flex: 0 0 48%; padding: 15px; background-color: rgba(255, 152, 0, 0.1); border-radius: 10px;">
                    <h3 style="color: #FF9800;">🎨 Customize</h3>
                    <p>Choose cool themes and make KiddiChat look exactly how you want!</p>
                </div>
                <div style="flex: 0 0 48%; padding: 15px; background-color: rgba(156, 39, 176, 0.1); border-radius: 10px;">
                    <h3 style="color: #9C27B0;">🧠 Learn & Grow</h3>
                    <p>Have fun conversations that help you learn new things every day!</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="card" style="text-align: center;">
            <div style="background-image: url('https://images.unsplash.com/photo-1516627145497-ae6968895b40?q=80&w=1924'); background-size: cover; height: 200px; border-radius: 10px; margin-bottom: 20px;"></div>
            <h3 style="margin-bottom: 15px;">What Our Young Users Say</h3>
            <div style="display: flex; justify-content: space-around; flex-wrap: wrap;">
                <div style="flex: 0 0 30%; background-color: rgba(255,255,255,0.7); padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                    <p>"I love getting badges for talking to KiddiChat! It's so fun!" - Emma, 9</p>
                    <div>⭐⭐⭐⭐⭐</div>
                </div>
                <div style="flex: 0 0 30%; background-color: rgba(255,255,255,0.7); padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                    <p>"KiddiChat helps me practice writing and learn new things!" - Liam, 10</p>
                    <div>⭐⭐⭐⭐⭐</div>
                </div>
                <div style="flex: 0 0 30%; background-color: rgba(255,255,255,0.7); padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                    <p>"The space theme is my favorite! I chat every day to keep my streak." - Noah, 8</p>
                    <div>⭐⭐⭐⭐⭐</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        with st.container():
            st.markdown("""
            <div class="login-form-container" style="background-color: white; padding: 30px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                <h2 style="text-align: center; color: #4CAF50; margin-bottom: 30px;">Welcome Back!</h2>
            """, unsafe_allow_html=True)
            
            with st.form("login_form"):
                username = st.text_input("Username", key="login_username")
                password = st.text_input("Password", type="password", key="login_password")
                submit_button = st.form_submit_button("Login")
                
                if submit_button:
                    if authenticate(username, password):
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        load_all_user_data()
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
            
            st.markdown("""
                <div style="text-align: center; margin-top: 20px;">
                    <p>Don't have an account? <a href="#" onclick="document.getElementById('signup-tab').click()">Sign up</a></p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with st.container():
            st.markdown("""
            <div class="login-form-container" style="background-color: white; padding: 30px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); margin-top: 20px;">
                <h2 style="text-align: center; color: #4CAF50; margin-bottom: 30px;">Create Account</h2>
            """, unsafe_allow_html=True)
            
            with st.form("signup_form"):
                new_username = st.text_input("Choose a username", key="signup_username")
                new_password = st.text_input("Create a password", type="password", key="signup_password")
                confirm_password = st.text_input("Confirm password", type="password", key="signup_confirm_password")
                signup_button = st.form_submit_button("Sign Up")
                
                if signup_button:
                    if new_password == confirm_password:
                        with open(USERS_DB, "r") as f:
                            users = json.load(f)
                        
                        if new_username in users:
                            st.error("Username already exists")
                        else:
                            save_user(new_username, new_password)
                            st.success("Account created successfully! Please log in.")
                    else:
                        st.error("Passwords do not match")
            
            st.markdown("""
                <div style="text-align: center; margin-top: 20px;">
                    <p>Already have an account? <a href="#" onclick="document.getElementById('login-tab').click()">Log in</a></p>
                </div>
            </div>
            """, unsafe_allow_html=True)

def process_user_input(user_input):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input,
        "timestamp": timestamp
    })
    
    # Generate response using the LLM model
    bot_response = llm_model_object(user_input)
    
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": bot_response,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    # Convert response to speech
    text_to_speech(bot_response)
    
    # Award points for the interaction
    points = award_points(user_input, bot_response)
    
    # Save data
    save_chat_history()
    update_user_data()
    
    # Clear input and rerun
    st.session_state.user_input = ""
    st.rerun()

def render_chat_page():
    st.markdown(f'<h1 class="page-title">💬 Chat with KiddiChat</h1>', unsafe_allow_html=True)
    
    # Add input method selection
    input_method = st.radio("Choose input method:", 
                           ("Text", "Voice"), 
                           horizontal=True,
                           key="input_method_radio")
    
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <div><strong>You:</strong> {message["content"]}</div>
                    <div class="message-timestamp">{message["timestamp"]}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message bot-message">
                    <div><strong>KiddiChat:</strong> {message["content"]}</div>
                    <div class="message-timestamp">{message["timestamp"]}</div>
                </div>
                """, unsafe_allow_html=True)
    
    if input_method == "Text":
        col1, col2 = st.columns([5, 1])
        
        with col1:
            user_input = st.text_input(
                "Type your message...", 
                value=st.session_state.user_input,
                key="chat_input",
                label_visibility="collapsed"
            )
        
        with col2:
            if st.button("Send", use_container_width=True):
                if user_input.strip():
                    process_user_input(user_input)
            
            if st.button("🎤", use_container_width=True, help="Switch to voice input"):
                st.session_state.input_method = "Voice"
                st.rerun()
    
    else:  # Voice input method
        if st.button("Start Recording", key="voice_record", use_container_width=True):
            with st.spinner("Listening..."):
                voice_text = voice_input()
                if voice_text:
                    st.session_state.user_input = voice_text
                    process_user_input(voice_text)
                else:
                    st.warning("Sorry, I didn't hear anything. Please try again.")
        
        if st.button("✏️", use_container_width=True, help="Switch to text input"):
            st.session_state.input_method = "Text"
            st.rerun()

def render_stats_page():
    st.markdown(f'<h1 class="page-title">📊 Your Stats & Progress</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="stats-box">
            <h3>Points</h3>
            <h2 style="color: {THEMES[st.session_state.theme]['primary_color']};">{st.session_state.points}</h2>
            <div class="level-indicator">Level {st.session_state.points // 100 + 1}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stats-box">
            <h3>Current Streak</h3>
            <h2 style="color: {THEMES[st.session_state.theme]['primary_color']};">{st.session_state.streak} days</h2>
            <div style="margin-top: 10px;">
                🔥 {'🔥' * min(st.session_state.streak, 5)}{' +' + str(st.session_state.streak - 5) if st.session_state.streak > 5 else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stats-box">
            <h3>Messages Sent</h3>
            <h2 style="color: {THEMES[st.session_state.theme]['primary_color']};">{len([m for m in st.session_state.chat_history if m['role'] == 'user'])}</h2>
            <div style="margin-top: 10px;">
                🗣️ {len(st.session_state.chat_history)} total exchanges
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="card">
        <h2 style="margin-bottom: 20px;">😊 Your Mood Over Time</h2>
    """, unsafe_allow_html=True)
    
    if st.session_state.mood_data:
        mood_df = pd.DataFrame(st.session_state.mood_data)
        mood_df['timestamp'] = pd.to_datetime(mood_df['timestamp'])
        mood_df = mood_df.sort_values('timestamp')
        
        fig = px.line(
            mood_df, 
            x='timestamp', 
            y='score',
            color_discrete_sequence=[THEMES[st.session_state.theme]['primary_color']],
            labels={'score': 'Mood Score', 'timestamp': 'Date'},
            title=""
        )
        
        fig.update_layout(
            hovermode="x unified",
            xaxis_title="",
            yaxis_title="Mood Score",
            yaxis=dict(range=[0, 6], tickvals=[1, 2, 3, 4, 5], ticktext=["😢", "🙁", "😐", "🙂", "😊"]),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=0, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No mood data available yet. Start chatting to track your mood!")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="card">
        <h2 style="margin-bottom: 20px;">🏆 Your Achievements</h2>
    """, unsafe_allow_html=True)
    
    if st.session_state.achievements:
        cols = st.columns(3)
        for i, achievement in enumerate(st.session_state.achievements):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="achievement">
                    <div style="font-size: 2rem; text-align: center;">{achievement['icon']}</div>
                    <h3 style="margin-top: 5px; text-align: center;">{achievement['title']}</h3>
                    <p style="text-align: center; font-size: 0.9rem;">{achievement['description']}</p>
                    <div style="text-align: center; font-weight: bold; color: {THEMES[st.session_state.theme]['primary_color']}">
                        +{achievement['points']} points
                    </div>
                    <div style="text-align: center; font-size: 0.8rem; color: #666;">
                        Earned on {achievement['date'].split()[0]}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No achievements yet. Keep chatting to unlock your first badge!")
    
    st.markdown("</div>", unsafe_allow_html=True)

def render_history_page():
    st.markdown(f'<h1 class="page-title">📜 Chat History</h1>', unsafe_allow_html=True)
    
    if not st.session_state.chat_history:
        st.info("No chat history yet. Start chatting to see your history here!")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        date_filter = st.date_input("Filter by date", value=None)
    with col2:
        search_term = st.text_input("Search messages")
    
    for i, message in enumerate(st.session_state.chat_history):
        message_date = datetime.strptime(message["timestamp"], "%Y-%m-%d %H:%M:%S").date()
        if date_filter and message_date != date_filter:
            continue
        if search_term and search_term.lower() not in message["content"].lower():
            continue
        
        with st.expander(f"{message['timestamp']} - {message['role'].capitalize()}"):
            if message["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <div><strong>You:</strong> {message["content"]}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message bot-message">
                    <div><strong>KiddiChat:</strong> {message["content"]}</div>
                </div>
                """, unsafe_allow_html=True)
            
            if st.button(f"Delete this message", key=f"delete_{i}"):
                del st.session_state.chat_history[i]
                save_chat_history()
                st.rerun()
    
    if st.button("Clear All History", type="primary"):
        st.session_state.chat_history = []
        save_chat_history()
        st.rerun()

def render_settings_page():
    st.markdown(f'<h1 class="page-title">⚙️ Settings</h1>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown("""
        <div class="card">
            <h2 style="margin-bottom: 20px;">🎨 Choose Your Theme</h2>
            <div style="display: flex; flex-wrap: wrap; gap: 15px; justify-content: center;">
        """, unsafe_allow_html=True)
        
        cols = st.columns(5)
        theme_names = list(THEMES.keys())
        
        for i, theme in enumerate(theme_names):
            with cols[i]:
                if st.button(theme.capitalize(), key=f"theme_{theme}"):
                    st.session_state.theme = theme
                    update_user_data()
                    st.rerun()
                
                st.markdown(f"""
                <div class="theme-selector" style="background: {THEMES[theme]['background']}; background-size: cover; height: 100px; border-radius: 8px; margin-top: 10px; border: {'3px solid ' + THEMES[theme]['primary_color'] if st.session_state.theme == theme else '1px solid #ddd'};">
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("</div></div>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown("""
        <div class="card">
            <h2 style="margin-bottom: 20px;">🔒 Account Settings</h2>
        """, unsafe_allow_html=True)
        
        with st.form("change_password_form"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("Change Password"):
                with open(USERS_DB, "r") as f:
                    users = json.load(f)
                
                if users[st.session_state.username]["password_hash"] == hash_password(current_password):
                    if new_password == confirm_password:
                        users[st.session_state.username]["password_hash"] = hash_password(new_password)
                        with open(USERS_DB, "w") as f:
                            json.dump(users, f)
                        st.success("Password changed successfully!")
                    else:
                        st.error("New passwords don't match")
                else:
                    st.error("Current password is incorrect")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown("""
        <div class="card">
            <h2 style="margin-bottom: 20px;">📤 Export Your Data</h2>
            <p>Download a copy of your chat history and personal data.</p>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Export Chat History"):
                if st.session_state.chat_history:
                    df = pd.DataFrame(st.session_state.chat_history)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"{st.session_state.username}_chat_history.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No chat history to export")
        
        with col2:
            if st.button("Export Mood Data"):
                if st.session_state.mood_data:
                    df = pd.DataFrame(st.session_state.mood_data)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"{st.session_state.username}_mood_data.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No mood data to export")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    if st.button("Logout", type="primary"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.chat_history = []
        st.rerun()

# Main app function
def main():
    set_background()
    
    if not st.session_state.logged_in:
        render_login_page()
    else:
        with st.sidebar:
            st.markdown(f"""
            <div style="text-align: center; margin-bottom: 30px;">
                <h2 style="color: {THEMES[st.session_state.theme]['primary_color']};">Hi, {st.session_state.username}!</h2>
                <div class="level-indicator">Level {st.session_state.points // 100 + 1}</div>
                <div style="margin-top: 15px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span>Points:</span>
                        <span><strong>{st.session_state.points}</strong></span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span>Streak:</span>
                        <span><strong>{st.session_state.streak} days</strong></span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>Badges:</span>
                        <span><strong>{len(st.session_state.badges)}</strong></span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("💬 Chat", use_container_width=True):
                st.session_state.current_page = "Chat"
                st.rerun()
            
            if st.button("📜 History", use_container_width=True):
                st.session_state.current_page = "History"
                st.rerun()
            
            if st.button("📊 Stats", use_container_width=True):
                st.session_state.current_page = "Stats"
                st.rerun()
            
            if st.button("⚙️ Settings", use_container_width=True):
                st.session_state.current_page = "Settings"
                st.rerun()
            
            st.markdown("---")
            
            if st.session_state.achievements:
                st.markdown("### Recent Achievements")
                for achievement in st.session_state.achievements[-3:][::-1]:
                    st.markdown(f"""
                    <div style="background-color: rgba(255,255,255,0.7); padding: 10px; border-radius: 10px; margin-bottom: 10px;">
                        <div style="font-size: 1.5rem; text-align: center;">{achievement['icon']}</div>
                        <div style="text-align: center; font-weight: bold;">{achievement['title']}</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        if st.session_state.current_page == "Chat":
            render_chat_page()
        elif st.session_state.current_page == "History":
            render_history_page()
        elif st.session_state.current_page == "Stats":
            render_stats_page()
        elif st.session_state.current_page == "Settings":
            render_settings_page()

if __name__ == "__main__":
    main()