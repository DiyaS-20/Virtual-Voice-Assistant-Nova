from groq import Groq  # Importing the Groq library to use its API.
import json  # Import json at the module level
from dotenv import dotenv_values  # Importing dotenv_values to read environment variables from a .env file
import datetime  # datetime module for real-time date and time information.
import os  # For file path operations

# Load environment variables from the .env file
env_vars = dotenv_values("C:\\Users\\jordanj\\Desktop\\AI-Voice-Assistant\\.env")

# Retrieve specific environment variables for username, assistant name, and API key.
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")

# Initialize the Groq client using the provided API key.
client = Groq(api_key=GroqAPIKey)

# Chat log file path
CHAT_LOG_PATH = "C:\\Users\\jordanj\\Desktop\\AI-Voice-Assistant\\Data\\ChatLog.json"

# Define a system message that provides context to the AI chatbot about its role and behavior.
System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which also has real-time up-to-date information from the internet.
*** Do not tell time until I ask, do not talk too much, just answer the question.***
*** Reply in only English, even if the question is in Hindi, reply in English.***
*** Do not provide notes in the output, just answer the question and never mention your training data. ***
"""

SystemChatBot = [
    {"role": "system", "content": System}
]

# Function to safely load the chat log
def load_chat_log():
    """Safely load the chat log from JSON file, handling any potential errors."""
    # Ensure the Data directory exists
    os.makedirs(os.path.dirname(CHAT_LOG_PATH), exist_ok=True)
    
    try:
        # Check if file exists and has content
        if os.path.exists(CHAT_LOG_PATH) and os.path.getsize(CHAT_LOG_PATH) > 0:
            with open(CHAT_LOG_PATH, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    print("Invalid JSON in chat log file. Creating new chat log.")
                    reset_chat_log()
                    return []
        else:
            # File doesn't exist or is empty
            reset_chat_log()
            return []
    except Exception as e:
        print(f"Error loading chat log: {e}")
        reset_chat_log()
        return []

# Function to reset/initialize the chat log file
def reset_chat_log():
    """Create a new chat log file with an empty array."""
    try:
        with open(CHAT_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump([], f)
    except Exception as e:
        print(f"Error resetting chat log: {e}")

# Function to save messages to the chat log
def save_chat_log(messages):
    """Save the messages to the chat log file."""
    try:
        with open(CHAT_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=4)
    except Exception as e:
        print(f"Error saving chat log: {e}")

# Function to get real-time date and time information
def RealtimeInformation():
    current_date_time = datetime.datetime.now()  # Get the current date and time

    day = current_date_time.strftime("%A")       # Day of the week
    date = current_date_time.strftime("%d")       # Day of the month
    month = current_date_time.strftime("%B")      # Full month name
    year = current_date_time.strftime("%Y")       # Year
    hour = current_date_time.strftime("%H")       # Hour in 24-hour format
    minute = current_date_time.strftime("%M")     # Minute
    second = current_date_time.strftime("%S")     # Second

    # Format the information into a string
    data = "Please use this real-time information if needed,\n"
    data += f"Day: {day}\nDate: {date}\nMonth: {month}\nYear: {year}\n"
    data += f"Time: {hour} hours : {minute} minutes : {second} seconds.\n"
    return data

# Function to modify the chatbot's response for better formatting
def AnswerModifier(Answer):
    lines = Answer.split('\n')  # Split the response into lines
    non_empty_lines = [line for line in lines if line.strip()]  # Remove empty lines
    modified_answer = '\n'.join(non_empty_lines)  # Join non-empty lines
    return modified_answer

def Chatbot(Query):
    """
    This function sends the user's query to the chatbot and returns the AI's response.
    """
    try:
        # Load the existing chat log
        messages = load_chat_log()

        # Append the user's query to the messages list
        messages.append({"role": "user", "content": f"{Query}"})

        # Make a request to the Groq API for a response
        completion = client.chat.completions.create(
            model="llama3-70b-8192",  # Specify the AI model to use
            messages=SystemChatBot + [{'role': "system", 'content': RealtimeInformation()}] + messages,  # Include system prompt and chat history
            max_tokens=1024,       # Limit the maximum tokens in the response
            temperature=0.7,       # Adjust response randomness
            top_p=1,               # Use nucleus sampling
            stream=True,           # Enable streaming response
            stop=None              # Allow the model to determine when to stop
        )

        Answer = ""  # Initialize an empty string to store the AI's response

        # Process the streamed response chunks
        for chunk in completion:
            if chunk.choices[0].delta.content:  # Check if there's content in the current chunk
                Answer += chunk.choices[0].delta.content

        Answer = Answer.replace("</s>", "")  # Clean up any unwanted tokens

        # Append the chatbot's response to the messages list
        messages.append({"role": "assistant", "content": Answer})

        # Save the updated chat log
        save_chat_log(messages)

        # Return the formatted response
        return AnswerModifier(Answer)

    except Exception as e:
        print(f"Error in Chatbot function: {e}")
        
        # Reset the chat log and try again with a fresh start
        reset_chat_log()
        
        # For critical errors, return a fallback message instead of recursive call
        # to prevent potential infinite recursion
        if "Query" in locals() and Query:
            return "I'm sorry, I encountered an error. Please try again."
        else:
            return "An unexpected error occurred. Please try again later."

# Main program entry point
if __name__ == "__main__":
    # Initialize the chat log if needed
    if not os.path.exists(CHAT_LOG_PATH) or os.path.getsize(CHAT_LOG_PATH) == 0:
        reset_chat_log()
    
    while True:
        user_input = input("Enter Your Question: ")
        print(Chatbot(user_input))  # Call the chatbot function and print its response