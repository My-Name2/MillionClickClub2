import streamlit as st
import random
import time
import requests
import re

# Load Discord bot token and channel ID from Streamlit secrets
DISCORD_BOT_TOKEN = st.secrets["discord"]["bot_token"]
DISCORD_CHANNEL_ID = st.secrets["discord"]["channel_id"]

# Prohibited words and patterns
PROHIBITED_WORDS = ["badword1", "badword2", "offensivephrase"]
PROHIBITED_PATTERNS = [
    r"https?://[^\s]+",  # Matches URLs (http:// or https://)
    r"\.(jpg|png|gif|jpeg|bmp|webp)$"  # Matches image file extensions
]

# Function to validate a message
def validate_message(message):
    for word in PROHIBITED_WORDS:
        if word.lower() in message.lower():
            return False, f"Message contains prohibited word: {word}"

    for pattern in PROHIBITED_PATTERNS:
        if re.search(pattern, message):
            return False, "Message contains a prohibited URL or file type."

    if len(message) > 500:
        return False, "Message is too long. Keep it under 500 characters."

    return True, None

# Function to send a message to the Discord channel
def send_message_to_channel(message):
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
        raise Exception(f"Failed to send message: {response.status_code} - {response.text}")

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
        raise Exception(f"Failed to create invite: {response.status_code} - {response.text}")

# Function to log flagged messages to the moderation channel
def log_flagged_message(user, message):
    url = f"https://discord.com/api/v10/channels/{DISCORD_CHANNEL_ID}/messages"
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "content": f"🚨 **Flagged Message** 🚨\n**User:** {user}\n**Content:** {message}"
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"Failed to log message: {response.status_code} - {response.text}")

# Initialize click counter
if "click_count" not in st.session_state:
    st.session_state.click_count = 0

# Streamlit frontend
st.title("MillionClickClub")
st.write(
    "Click the button below for a **1 in 1,000,000** chance to join the exclusive Discord club. "
    "If you win, you'll get a one-time-use invite link valid for 30 seconds!"
)

st.write(f"Total clicks so far: **{st.session_state.click_count}**")

if st.button("Click to try your luck"):
    st.session_state.click_count += 1
    random_number = random.randint(1, 10)
    if random_number == 1:
        st.success("🎉 You won! Generating your invite...")
        time.sleep(2)
        try:
            invite_link = create_invite()
            st.write(f"[Click here to join the Discord!]({invite_link})")
        except Exception as e:
            st.error(f"Error generating invite: {e}")
    else:
        st.error(f"Not this time! Your number was {random_number}. Try again!")

st.write("Keep trying—maybe you'll hit the jackpot!")

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
                send_message_to_channel(user_message)
                st.success("Message sent to the server!")
            except Exception as e:
                st.error(f"Failed to send message: {e}")
        else:
            if user_name:
                log_flagged_message(user_name, user_message)
            st.error(error_message)
    else:
        st.error("Message cannot be empty!")
