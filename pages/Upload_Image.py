import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO
import json
import ollama
from utilities.icon import page_icon


# Streamlit page configuration
st.set_page_config(
    page_title="Upload Image",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = "http://localhost:11434/api/generate"

def img_to_base64(image):
    """Convert an image to base64 format."""
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def get_allowed_model_names(models_info):
    """Returns the names of the allowed models."""
    allowed_models = {"bakllava:latest", "llava:latest"}
    model_names = {model["name"] for model in models_info["models"]}
    return tuple(allowed_models.intersection(model_names))

def handle_model_download(model_name):
    """Download the specified model."""
    try:
        ollama.pull(model_name)
        st.toast(f"Downloaded model: {model_name}", icon="✅")
        st.rerun()
    except Exception as e:
        st.error(f"Failed to download model: {model_name}. Error: {str(e)}", icon="😳")

def process_image(image, model, prompt):
    """Send the image and prompt to the API and get the response."""
    image_base64 = img_to_base64(image)
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    data = {"model": model, "prompt": prompt, "images": [image_base64]}
    try:
        response = requests.post(API_URL, json=data, headers=headers)
        response.raise_for_status()
        response_lines = response.text.split("\n")
        llava_response = ""
        for line in response_lines:
            if line.strip():
                try:
                    response_data = json.loads(line)
                    if "response" in response_data:
                        llava_response += response_data["response"]
                except json.JSONDecodeError:
                    continue
        return llava_response
    except requests.RequestException as e:
        st.error(f"Failed to get a response from {model}. Error: {str(e)}", icon="😳")
        return ""

def main():
    page_icon("📲")
    st.subheader("Upload Image", divider="red", anchor=False)

    models_info = ollama.list()
    available_models = get_allowed_model_names(models_info)
    missing_models = {"bakllava:latest", "llava:latest"} - set(available_models)

    col_1, col_2 = st.columns(2)
    
    with col_1:
        if not available_models:
            st.error("No allowed models are available.", icon="😳")
            model_to_download = st.selectbox("Select a model to download", ["bakllava:latest", "llava:latest"])
            if st.button(f"Download {model_to_download}"):
                handle_model_download(model_to_download)
        else:
            if missing_models:
                model_to_download = st.selectbox(":green[**📥 DOWNLOAD MODEL**]", list(missing_models))
                if st.button(f":green[Download **_{model_to_download}_**]"):
                    handle_model_download(model_to_download)

    if not available_models:
        return

    selected_model = col_2.selectbox("Pick a model available locally on your system ↓", available_models, key=1)

    if "chats" not in st.session_state:
        st.session_state.chats = []

    if "uploaded_file_state" not in st.session_state:
        st.session_state.uploaded_file_state = None

    uploaded_file = st.file_uploader("Upload an image for analysis", type=["png", "jpg", "jpeg"])

    col1, col2 = st.columns(2)

    with col2:
        container1 = st.container(height=500, border=True)
        with container1:
            if uploaded_file:
                st.session_state.uploaded_file_state = uploaded_file.getvalue()
                image = Image.open(BytesIO(st.session_state.uploaded_file_state))
                st.image(image, caption="Uploaded image")

    with col1:
        container2 = st.container(height=500, border=True)

        if uploaded_file:
            for message in st.session_state.chats:
                avatar = "🌋" if message["role"] == "assistant" else "🫠"
                with container2.chat_message(message["role"], avatar=avatar):
                    st.markdown(message["content"])

            if user_input := st.chat_input("Question about the image...", key="chat_input"):
                st.session_state.chats.append({"role": "user", "content": user_input})
                container2.chat_message("user", avatar="🫠").markdown(user_input)

                llava_response = process_image(image, selected_model, user_input)
                if llava_response:
                    st.markdown(llava_response)
                else:
                    st.error(f"No response received from {selected_model}.", icon="😳")

                st.session_state.chats.append({"role": "assistant", "content": llava_response})

if __name__ == "__main__":
    main()
