import streamlit as st
from openai import OpenAI
from PIL import Image
import io
import base64
import json

# Function to load and save gallery data
def load_gallery_data(filename='gallery_data.json'):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_gallery_data(data, filename='gallery_data.json'):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

# Function to convert images and display them
def image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

def display_base64_image(image_b64):
    image_bytes = base64.b64decode(image_b64)
    image_bytes_io = io.BytesIO(image_bytes)
    st.image(image_bytes_io, width=150)

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["apiKey"])

def get_bot_response():
    messages_for_api = []
    for m in st.session_state.messages:
        if m['role'] == 'user' and 'is_photo' in m and m['is_photo']:
            image_base64 = image_to_base64(m['content'])
            image_url = "data:image/jpeg;base64," + image_base64
            messages_for_api.append({
                "role": "user",
                "content": [{"type": "image_url", "image_url": {"url": image_url}}]
            })
        else:
            messages_for_api.append({
                "role": m['role'],
                "content": [{"type": "text", "text": m['content']}]
            })

    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=messages_for_api,
        max_tokens=300,
    )

    bot_reply = ""
    if response.choices:
        bot_reply = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        with st.chat_message(st.session_state['messages'][-1]['role']):
            st.markdown(st.session_state['messages'][-1]['content'])
    return bot_reply

if 'messages' not in st.session_state:
    st.session_state['messages'] = []

# Sidebar navigation
app_mode = st.sidebar.selectbox('Choose the app mode', ['Munchkin Bot', 'Gallery'])

if app_mode == 'Munchkin Bot':
    st.title("Munchkin Bot")
    camera_container = st.empty()

    if 'photo_captured' not in st.session_state or not st.session_state['photo_captured']:
        with camera_container:
            photo = st.camera_input("Take a photo")
            if photo is not None:
                st.session_state['photo_captured'] = True
                pil_image = Image.open(photo)
                st.session_state['messages'].append({'role': 'user', 'content': pil_image, 'is_photo': True})
                wildlife_message = "You are a wildlife expert. Identify the organism in this picture. Tell me the name of the organism. The species. The Scientific name. Two fun facts about this organism that are not known to many."
                st.session_state['messages'].append({'role': 'user', 'content': wildlife_message})
                bot_reply = get_bot_response()
                # Associate the bot's reply with the image message for gallery display
                st.session_state['messages'][0]['description'] = bot_reply
                camera_container.empty()

    if 'photo_captured' in st.session_state and st.session_state['photo_captured']:
        for message in st.session_state['messages']:
            if 'is_photo' in message and message['is_photo']:
                with st.chat_message(message['role']):
                    st.image(message['content'], use_column_width=True)
            else:
                with st.chat_message(message['role']):
                    st.write(message['content'])

        user_input = st.chat_input("Type your message...", key="chat_input")
        if user_input:
            st.session_state['messages'].append({'role': 'user', 'content': user_input})
            with st.chat_message(st.session_state['messages'][-1]['role']):
                st.markdown(st.session_state['messages'][-1]['content'])
            get_bot_response()

elif app_mode == 'Gallery':
    st.title("Gallery")
    gallery_data = load_gallery_data()

    for message in st.session_state['messages']:
        if 'is_photo' in message and message['is_photo']:
            image_b64 = image_to_base64(message['content'])
            if not any(entry['image'] == image_b64 for entry in gallery_data):
                gallery_data.append({'image': image_b64, 'description': message['description']})

    save_gallery_data(gallery_data)

    for entry in gallery_data:
        cols = st.columns([1, 3], gap="small")
        with cols[0]:
            display_base64_image(entry['image'])
        with cols[1]:
            st.write(entry['description'])
        st.markdown("---")
