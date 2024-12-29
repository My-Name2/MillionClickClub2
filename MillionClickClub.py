import streamlit as st
import random
import time
import requests
import re
from datetime import datetime, timedelta

# Load Discord bot token and channel ID from Streamlit secrets
DISCORD_BOT_TOKEN = st.secrets["DISCORD_BOT_TOKEN"]
DISCORD_CHANNEL_ID = st.secrets["DISCORD_CHANNEL_ID"]

# Prohibited words and patterns
PROHIBITED_WORDS = ["badword1", "badword2", "offensivephrase"]
PROHIBITED_PATTERNS = [
    r"https?://[^\s]+",  # Matches URLs (http:// or https://)
    r"\.(jpg|png|gif|jpeg|bmp|webp)$"  # Matches image file extensions
]

# Initialize session state variables
if "click_count" not in st.session_state:
    st.session_state.click_count = 0
if "points" not in st.session_state:
    st.session_state.points = 0
if "auto_clickers" not in st.session_state:
    st.session_state.auto_clickers = 0
if "click_multiplier" not in st.session_state:
    st.session_state.click_multiplier = 1
if "cooldown_until" not in st.session_state:
    st.session_state.cooldown_until = None
if "shop_message" not in st.session_state:
    st.session_state.shop_message = ""

# Function to validate a message
def validate_message(message):
    if len(message) > 100:  # Check message length
        return False, "Message is too long. Keep it under 100 characters."

    for word in PROHIBITED_WORDS:
        if word.lower() in message.lower():
            return False, f"Message contains prohibited word: {word}"

    for pattern in PROHIBITED_PATTERNS:
        if re.search(pattern, message):
            return False, "Message contains a prohibited URL or file type."

    return True, None

# Function to send a message to the Discord channel
def send_message_to_channel(message, username=""):
    if username.strip():
        message = f"{message} - {username}"
    
    url = f"https://discord.com/api/v10/channels/{DISCORD_CHANNEL_ID}/messages"
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "content": message
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()
    elif response.status_code == 403:
        raise Exception("Missing Permissions: Ensure the bot has the 'Send Messages' permission.")
    else:
        error = response.json()
        raise Exception(f"Failed to send message: {response.status_code} - {error.get('message', 'Unknown error')}")

# Function to create a one-time-use invite link
def create_invite():
    url = f"https://discord.com/api/v10/channels/{DISCORD_CHANNEL_ID}/invites"
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {"max_age": 30, "max_uses": 1}

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        invite_data = response.json()
        return f"https://discord.gg/{invite_data['code']}"
    elif response.status_code == 403:
        raise Exception("Missing Permissions: Ensure the bot has the 'Create Instant Invite' permission.")
    else:
        error = response.json()
        raise Exception(f"Failed to create invite: {response.status_code} - {error.get('message', 'Unknown error')}")

# Function to handle random events
def random_event():
    event_roll = random.randint(1, 100)
    if event_roll <= 5:  # 5% chance for a random event
        cooldown_time = random.randint(5, 15)  # Cooldown for 5 to 15 seconds
        st.session_state.cooldown_until = datetime.now() + timedelta(seconds=cooldown_time)
        return f"A random event occurred! Clicking is disabled for {cooldown_time} seconds."
    return None

# Shop logic
def shop():
    st.write("### Shop")
    st.write(f"**Points:** {st.session_state.points}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Buy Auto-Clicker (Cost: 100 points)"):
            if st.session_state.points >= 100:
                st.session_state.auto_clickers += 1
                st.session_state.points -= 100
                st.session_state.shop_message = "Bought an Auto-Clicker!"
            else:
                st.session_state.shop_message = "Not enough points for an Auto-Clicker."
    with col2:
        if st.button("Buy Click Multiplier (Cost: 200 points)"):
            if st.session_state.points >= 200:
                st.session_state.click_multiplier += 1
                st.session_state.points -= 200
                st.session_state.shop_message = "Bought a Click Multiplier!"
            else:
                st.session_state.shop_message = "Not enough points for a Click Multiplier."

    st.info(st.session_state.shop_message)

# Handle auto-clicking
def handle_auto_clicking():
    st.session_state.points += st.session_state.auto_clickers * st.session_state.click_multiplier

# Streamlit frontend
st.title("MillionClickClub")
st.write(
    "Click the button below for a **1 in 1,000,000** chance to join the exclusive Discord club. "
    "If you win, you'll get a one-time-use invite link valid for 30 seconds!"
)

# Calculate likelihood
st.write(f"Total clicks so far: **{st.session_state.click_count}**")
probability = 1 - ((999999 / 1000000) ** st.session_state.click_count)
st.write(f"📊 Your current likelihood of winning: **{probability * 100:.6f}%**")

# Check for cooldown
if st.session_state.cooldown_until and datetime.now() < st.session_state.cooldown_until:
    st.warning(f"Clicking disabled until {st.session_state.cooldown_until.strftime('%H:%M:%S')}.")
else:
    if st.session_state.cooldown_until:
        st.session_state.cooldown_until = None  # Reset cooldown

    if st.button("Click to try your luck"):
        random_event_message = random_event()
        if random_event_message:
            st.warning(random_event_message)
        else:
            st.session_state.click_count += 1
            st.session_state.points += st.session_state.click_multiplier
            user_number = random.randint(1, 1000000)
            winning_number = random.randint(1, 1000000)
            st.write(f"🎲 Your number: **{user_number}**")
            st.write(f"🏆 Winning number: **{winning_number}**")
            if user_number == winning_number:
                st.success("🎉 You won! Generating your invite...")
                time.sleep(2)
                try:
                    invite_link = create_invite()
                    st.write(f"[Click here to join the Discord!]({invite_link})")
                except Exception as e:
                    st.error(f"Error generating invite: {e}")
            else:
                st.error("Not this time! Better luck next time!")

# Display shop
shop()

# Handle auto-clickers
handle_auto_clicking()

# User Message Input
st.write("---")
st.write("### Send a Message to the Server")
user_name = st.text_input("Your Username (Optional):", "")
user_message = st.text_input("Enter your message:")
if st.button("Send Message"):
    if user_message.strip():
        is_valid, error_message = validate_message(user_message)
        if is_valid:
            try:
                send_message_to_channel(user_message, username=user_name)
                st.success("Message sent to the server!")
            except Exception as e:
                st.error(f"Failed to send message: {e}")
        else:
            st.error(error_message)
    else:
        st.error("Message cannot be empty!")
