import streamlit as st
import pandas as pd
import requests
import json
from io import StringIO
from docx import Document
import base64
from utilities.icon import page_icon


def process_text(text, model, prompt):
    """Send the text and prompt to the API and get the response."""
    API_URL = "http://localhost:11434/api/generate"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    data = {"model": model, "prompt": prompt, "text": text}
    try:
        response = requests.post(API_URL, json=data, headers=headers)
        response.raise_for_status()
        # Log or print the response text for debugging
        st.write("Raw response text:", response.text)
        response_data = response.json()
        return response_data.get("response", "")
    except requests.RequestException as e:
        st.error(f"Failed to get a response from {model}. Error: {str(e)}", icon="😳")
        return ""
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse response from {model}. Error: {str(e)}", icon="😳")
        return ""

def get_allowed_model_names(models_info):
    """Returns the names of the allowed models."""
    allowed_models = {"llama3.1:latest", "codegemma:latest"}
    model_names = {model["name"] for model in models_info["models"]}
    return tuple(allowed_models.intersection(model_names))

def read_docx(file):
    """Read content from a .docx file."""
    doc = Document(file)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

def main():
    page_icon("📜")
    st.subheader("Upload File", divider="red", anchor=False)

    # Set up session state for model selection and chat
    if "chats" not in st.session_state:
        st.session_state.chats = []

    if "selected_model" not in st.session_state:
        st.session_state.selected_model = None

    # Placeholder for models_info (this should be fetched or defined based on your application)
    models_info = {
        "models": [
            {"name": "llama3.1:latest"},
            {"name": "codegemma:latest"},
            {"name": "other:version"}
        ]
    }

    # Fetch and display allowed models
    allowed_models = get_allowed_model_names(models_info)

    # Model selection
    selected_model = st.selectbox("Select a model", options=allowed_models)
    st.session_state.selected_model = selected_model

    # File uploader
    uploaded_file = st.file_uploader("Upload a file (CSV, DOCX, or Text)", type=["csv", "txt", "docx"])

    if uploaded_file is not None:
        if uploaded_file.type == "text/csv":
            df = pd.read_csv(uploaded_file)
            st.write("CSV File Content:")
            st.write(df)
            file_text = df.to_csv(index=False)
        elif uploaded_file.type == "text/plain":
            file_text = uploaded_file.read().decode("utf-8")
            st.write("Text File Content:")
            st.write(file_text)
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            file_text = read_docx(uploaded_file)
            st.write("Word Document Content:")
            st.write(file_text)
        else:
            st.error("Unsupported file type.")
            return

        for message in st.session_state.chats:
            avatar = "🌋" if message["role"] == "assistant" else "🫠"
            st.markdown(f"**{message['role']}**: {message['content']}")

        # Create placeholders for the question and answer
        question_placeholder = st.empty()
        answer_placeholder = st.empty()

        # Question input box
        with question_placeholder.form(key="question_form"):
            user_input = st.text_area("Question about the file content...", key="file_chat_input", height=100)
            submit_button = st.form_submit_button(label="Submit")

            if submit_button and user_input:
                st.session_state.chats.append({"role": "user", "content": user_input})
                st.markdown(f"**user**: {user_input}")

                file_response = process_text(file_text, selected_model, user_input)
                if file_response:
                    answer_placeholder.markdown(file_response)
                else:
                    answer_placeholder.error(f"No response received from {selected_model}.", icon="😳")

                st.session_state.chats.append({"role": "assistant", "content": file_response})

if __name__ == "__main__":
    main()
