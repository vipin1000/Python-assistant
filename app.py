import streamlit as st
import requests
import json # Useful for debugging API responses

# --- Configuration ---
# It's highly recommended to use Streamlit Secrets for API keys!
# Create a file .streamlit/secrets.toml and add:
# HUGGINGFACE_API_KEY = "your_actual_hf_key_here"
# Then access it with st.secrets["HUGGINGFACE_API_KEY"]
# For simplicity in this example, we'll keep it here, but **replace it or use secrets**.
try:
    # Try loading from secrets first
    API_KEY = "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"
except (FileNotFoundError, KeyError):
    # Fallback if secrets aren't configured (replace with your key)
    API_KEY = "YOUR_HUGGINGFACE_API_KEY_HERE" # <--- REPLACE OR USE SECRETS

if API_KEY == "YOUR_HUGGINGFACE_API_KEY_HERE" or not API_KEY:
    st.error("⚠️ Please replace 'YOUR_HUGGINGFACE_API_KEY_HERE' with your actual Hugging Face API key or configure it via Streamlit Secrets (`.streamlit/secrets.toml`).")
    st.stop() # Stop execution if key is missing


HUGGINGFACE_API_URL ="https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"


# HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/deepseek-ai/DeepSeek-R1-Distill-Llama-8B"

# --- Hugging Face API Interaction Function ---
# This function remains largely the same as the Flask version
def get_chatbot_response(prompt: str) -> str:
    """
    Sends the prompt to the Hugging Face API and returns the chatbot's response.
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # The detailed instruction prompt for the LLM
    # Note: Some models work better with simpler prompts. You might experiment.
    # Mistral-Instruct usually uses [INST] ... [/INST] but the API handles basic input too.
    # Let's slightly adapt the prompt structure for potentially better results with Mistral.
    instruction_prompt = f"""[INST] You are a Python programming expert with great communication skills. You are highly skilled in Python development and software engineering, capable of explaining complex coding concepts clearly and concisely. When users ask you questions, you should:

1.  **Provide clear and concise answers**, offering simple and effective explanations, code examples.
2.  **Break down complex concepts** in an easy-to-understand manner, ensuring the user learns from the conversation.
3.  **Offer advice on best practices** in Python programming, including code optimization, readability, and efficient problem-solving.
4.  **Respond confidently and professionally**, with a helpful and friendly tone, keeping the conversation educational yet approachable.
5.  **Help debug and solve coding problems** when users share error messages or describe issues in their code.
6.  **Strictly only generate responses for Python-related problems.** If the user input is not related to Python, **output only the exact phrase**: "I can only generate responses for Python-related queries." Do not add any other text before or after this phrase in that case.

User question: "{prompt}"

Assistant's Python-focused response: [/INST]"""


    payload = {
        "inputs": instruction_prompt, # Using the structured prompt
        "parameters": {             # Common parameters for text generation
            "max_new_tokens": 512,  # Limit response length
            "temperature": 0.7,     # Control randomness (creativity vs factual)
            "top_p": 0.9,           # Nucleus sampling
            "do_sample": True,      # Enable sampling for more varied responses
            "return_full_text": False # Important: often need False to get only the completion
        },
        "options": {"use_cache": False} # Disable caching if needed
    }

    try:
        response = requests.post(HUGGINGFACE_API_URL, json=payload, headers=headers, timeout=60) # Added timeout
        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)

        response_data = response.json()
        # print(f"API Response DEBUG: {json.dumps(response_data, indent=2)}") # For debugging

        # Response structure can vary slightly. Often it's a list with one dict.
        if isinstance(response_data, list) and len(response_data) > 0:
            generated_text = response_data[0].get("generated_text", "").strip()
        # Sometimes it might be directly a dict (less common for this endpoint)
        elif isinstance(response_data, dict):
             generated_text = response_data.get("generated_text", "").strip()
        else:
            generated_text = "Error: Unexpected response format from API."

        # Check if the model correctly identified a non-Python query
        if generated_text == "I can only generate responses for Python-related queries.":
             return generated_text # Return the exact restricted phrase

        # Further cleanup might be needed depending on the model's specific output habits
        # Remove any potential repetition of the input prompt if return_full_text wasn't respected perfectly
        if prompt in generated_text:
             # This is a basic way, might need refinement
             pass # Often `return_full_text: False` handles this

        return generated_text

    except requests.exceptions.RequestException as e:
        st.error(f"Network error connecting to Hugging Face API: {e}")
        return "Error: Could not connect to the chatbot service."
    except Exception as e:
        st.error(f"An error occurred: {e}")
        # Try to get more detail from the response if it exists and failed status check
        try:
            error_detail = response.json()
            st.error(f"API Error Details: {json.dumps(error_detail, indent=2)}")
        except:
            st.error(f"Raw API Response Text: {response.text if 'response' in locals() else 'N/A'}")
        return f"Error processing request: {e}"


# --- Streamlit App UI ---

st.set_page_config(page_title="Python Expert Chatbot", layout="wide")
st.title("🐍 Python Expert Chatbot")
st.caption("Ask me anything about Python programming!")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display past messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input field
if user_input := st.chat_input("Your Python question:"):
    # Add user message to history and display it
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Get response from the chatbot
    with st.chat_message("assistant"):
        message_placeholder = st.empty() # Create a placeholder for the response
        with st.spinner("Thinking... 🤔"): # Show spinner while waiting
            chatbot_response = get_chatbot_response(user_input)
            message_placeholder.markdown(chatbot_response) # Display the response

    # Add chatbot response to history
    st.session_state.messages.append({"role": "assistant", "content": chatbot_response})

# Add a sidebar note about the model
st.sidebar.info(f"Using model: `{HUGGINGFACE_API_URL.split('/')[-1]}`")
st.sidebar.info("Remember to set your Hugging Face API Key using Streamlit Secrets for security.")
