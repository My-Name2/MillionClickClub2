import streamlit as st
import random
import time
import requests
import re

# Load Discord bot token and channel ID from Streamlit secrets
DISCORD_BOT_TOKEN = st.secrets["DISCORD_BOT_TOKEN"]
DISCORD_CHANNEL_ID = st.secrets["DISCORD_CHANNEL_ID"]

# Prohibited words and patterns
PROHIBITED_WORDS = ["badword1", "badword2", "offensivephrase"]
PROHIBITED_PATTERNS = [
    r"https?://[^\s]+",  # Matches URLs (http:// or https://)
    r"\.(jpg|png|gif|jpeg|bmp|webp)$"  # Matches image file extensions
]

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

# Initialize session state variables
if "click_count" not in st.session_state:
    st.session_state.click_count = 0
if "invite_generated" not in st.session_state:
    st.session_state.invite_generated = False
if "invite_link" not in st.session_state:
    st.session_state.invite_link = None

# Streamlit frontend
st.title("MillionClickClub")
st.write(
    "Click the button below for a **1 in 1,000,000** chance to join the exclusive Discord club. "
    "If you win, you'll get a one-time-use invite link valid for 30 seconds!"
)

# Calculate likelihood
st.write(f"Total clicks so far: **{st.session_state.click_count}**")
probability = 10000000 - ((999999 / 1000000) ** st.session_state.click_count)
st.write(f"📊 Your current likelihood of winning: **{probability * 100:.6f}%**")

# Generate invite button logic
if not st.session_state.invite_generated:
    if st.button("Click to try your luck"):
        st.session_state.click_count += 1
        user_number = random.randint(1, 1000000)
        winning_number = random.randint(1, 1000000)
        st.write(f"🎲 Your number: **{user_number}**")
        st.write(f"🏆 Winning number: **{winning_number}**")
        if user_number == winning_number:
            st.success("🎉 You won! Generating your invite...")
            time.sleep(2)
            try:
                invite_link = create_invite()
                st.session_state.invite_generated = True
                st.session_state.invite_link = invite_link
                st.write(f"[Click here to join the Discord!]({invite_link})")
            except Exception as e:
                st.error(f"Error generating invite: {e}")
        else:
            st.error("Not this time! Better luck next time!")

# Display invite link if generated
if st.session_state.invite_generated:
    st.write(f"[Your invite link (valid for 30 seconds)]({st.session_state.invite_link})")
    st.info("Refresh the page to try again.")

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
