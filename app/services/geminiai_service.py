import shelve
from dotenv import load_dotenv
import os
import time
import logging
import google.generativeai as genai
import pathlib
# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Configure the Gemini API client
genai.configure(api_key=GOOGLE_API_KEY)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def upload_and_get_file_reference(path):
    """
    Uploads a file to the Gemini API and returns a reference to it.
    This only needs to be done once per file.
    """
    logging.info(f"Uploading file: {path}")
    # The display name is what you'll see in the File API list
    # The file reference will be used in the prompt
    airbnb_file = genai.upload_file(path=path, display_name="Airbnb FAQ")
    logging.info(f"File uploaded successfully: {airbnb_file.uri}")
    return airbnb_file

def get_or_create_file_reference(path, db_name="file_reference_db"):
    """
    Checks if a file reference is already stored and returns it.
    If not, it uploads the file and stores the reference.
    """
    with shelve.open(db_name) as db:
        if "file_uri" in db:
            logging.info("Retrieving existing file reference.")
            # Recreate the file object from the stored URI
            return genai.get_file(name=db["file_uri"])
        else:
            logging.info("No existing file reference found. Uploading new file.")
            file_reference = upload_and_get_file_reference(path)
            db["file_uri"] = file_reference.name # Store the name/URI for future retrieval
            return file_reference

# Use context manager to ensure the shelf file is closed properly
def get_chat_history(wa_id):
    """Retrieves chat history for a given WhatsApp ID."""
    with shelve.open("threads_db_gemini") as threads_shelf:
        return threads_shelf.get(wa_id, None)

def store_chat_history(wa_id, history):
    """Stores the chat history."""
    with shelve.open("threads_db_gemini", writeback=True) as threads_shelf:
        threads_shelf[wa_id] = history

def generate_response(message_body, wa_id, name, airbnb_file_reference):
    """
    Generates a response using the Gemini model, chat history, and the uploaded file.
    """
    # Initialize the Gemini model
    model = genai.GenerativeModel(model_name='gemini-1.5-flash')

    # Retrieve or create chat history
    chat_history = get_chat_history(wa_id)

    # The initial prompt that sets the context for the assistant
    initial_prompt = f"""You're a helpful WhatsApp assistant named 'Sam Liew' working for MARQ International as Real Estate agent.
    You are friendly and professional. Introduce yourself at the start of the conversation.
    Use the knowledge in the attached document to best respond to guest queries.
    If you don't know the answer based on the document, say simply that you cannot help with the question and advise them to contact the host directly.
    You are having a conversation with {name}.
    """

    # Start a new chat session or continue an existing one
    if chat_history:
        logging.info(f"Resuming existing chat for {name} with wa_id {wa_id}")
        chat_session = model.start_chat(history=chat_history)
        prompt = message_body
    else:
        logging.info(f"Starting new chat for {name} with wa_id {wa_id}")
        # For a new chat, combine the initial prompt, the file, and the user's message
        chat_session = model.start_chat()
        prompt = [initial_prompt, airbnb_file_reference, message_body]
def generate_response(message_body, wa_id, name):
    """
    Generates a response using the Gemini model, chat history, and the uploaded file.
    """
    # Initialize the Gemini model
    model = genai.GenerativeModel(model_name='gemini-1.5-flash')

    # Retrieve or create chat history
    chat_history = get_chat_history(wa_id)

    # The initial prompt that sets the context for the assistant
    initial_prompt = f"""You're a helpful WhatsApp assistant named 'Sam Liew' working for MARQ International as Real Estate agent.
    You are friendly and professional. Introduce yourself at the start of the conversation.
    Use the knowledge in the attached document to best respond to guest queries.
    If you don't know the answer based on the document, say simply that you cannot help with the question and advise them to contact the host directly.
    You are having a conversation with {name}.
    """

    # Start a new chat session or continue an existing one
    if chat_history:
        logging.info(f"Resuming existing chat for {name} with wa_id {wa_id}")
        chat_session = model.start_chat(history=chat_history)
        prompt = message_body
    else:
        logging.info(f"Starting new chat for {name} with wa_id {wa_id}")
        # For a new chat, combine the initial prompt, the file, and the user's message
        chat_session = model.start_chat()
        prompt = [initial_prompt, message_body]
    # Send the message to the model
    response = chat_session.send_message(prompt)
    new_message = response.text
    logging.info(f"Generated message: {new_message}")

    # Store the updated chat history
    store_chat_history(wa_id, chat_session.history)
    return new_message