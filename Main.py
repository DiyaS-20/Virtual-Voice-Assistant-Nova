from Frontend.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextToScreen,
    TempDirectoryPath,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus
)
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Model import FirstLayerDMM
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import Chatbot
from Backend.TextToSpeech import TextToSpeech
from dotenv import dotenv_values
from asyncio import run
from time import sleep
import subprocess
import threading
import json
import os

# Ensure the Data directory exists
data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data")
os.makedirs(data_dir, exist_ok=True)

# Path to the chat log file
chatlog_path = os.path.join(data_dir, "ChatLog.json")

# Make sure the ChatLog.json file exists and contains valid JSON
if not os.path.exists(chatlog_path) or os.path.getsize(chatlog_path) == 0:
    with open(chatlog_path, "w", encoding='utf-8') as f:
        json.dump([], f)

env_vars = dotenv_values("C:\\Users\\jordanj\\Desktop\\AI-Voice-Assistant\\.env")

Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")

DefaultMessage = f'''{Username}: Hello {Assistantname}, How are you?

{Assistantname}: Welcome {Username}. I am doing well. How may I help you?'''

subprocesses = []

Functions = ["open", "close", "play", "system", "content", "google search", "youtube search"]

def ShowDefaultChatIfNoChats():
    try:
        with open(chatlog_path, "r", encoding='utf-8') as File:
            content = File.read()
            if not content or len(content.strip()) < 5:
                # Initialize with empty array
                with open(chatlog_path, "w", encoding='utf-8') as f:
                    json.dump([], f)
                
                # Set up default display
                with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
                    file.write("")
                with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as file:
                    file.write(DefaultMessage)
    except Exception as e:
        print(f"Error in ShowDefaultChatIfNoChats: {e}")
        # Initialize files if there was an error
        with open(chatlog_path, "w", encoding='utf-8') as f:
            json.dump([], f)
        with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
            file.write("")
        with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as file:
            file.write(DefaultMessage)

def ReadChatLogJson():
    try:
        with open(chatlog_path, 'r', encoding='utf-8') as file:
            content = file.read()
            if content and len(content.strip()) > 0:
                return json.loads(content)
            return []
    except json.JSONDecodeError:
        print("Error decoding JSON from ChatLog.json. Resetting file.")
        with open(chatlog_path, "w", encoding='utf-8') as f:
            json.dump([], f)
        return []
    except Exception as e:
        print(f"Error reading ChatLog.json: {e}")
        return []

def ChatLogIntegration():
    try:
        json_data = ReadChatLogJson()
        formatted_chatlog = ""

        for entry in json_data:
            if entry["role"] == "user":
                formatted_chatlog += f"User: {entry['content']}\n"
            elif entry["role"] == "assistant":
                formatted_chatlog += f"Assistant: {entry['content']}\n"

        formatted_chatlog = formatted_chatlog.replace("User", Username + " ")
        formatted_chatlog = formatted_chatlog.replace("Assistant", Assistantname + " ")

        with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
            file.write(AnswerModifier(formatted_chatlog))
    except Exception as e:
        print(f"Error in ChatLogIntegration: {e}")
        # Create a default database file if there was an error
        with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
            file.write("")

def ShowChatsonGUI():
    try:
        with open(TempDirectoryPath('Database.data'), "r", encoding='utf-8') as File:
            Data = File.read()
            if len(str(Data)) > 0:
                lines = Data.split('\n')
                result = '\n'.join(lines)
                with open(TempDirectoryPath('Responses.data'), "w", encoding='utf-8') as OutFile:
                    OutFile.write(result)
    except Exception as e:
        print(f"Error in ShowChatsonGUI: {e}")
        # Handle error gracefully
        with open(TempDirectoryPath('Responses.data'), "w", encoding='utf-8') as file:
            file.write("An error occurred loading the chat history.")

def InitialExecution():
    try:
        SetMicrophoneStatus("False")
        ShowTextToScreen("")
        ShowDefaultChatIfNoChats()
        ChatLogIntegration()
        ShowChatsonGUI()
    except Exception as e:
        print(f"Error in InitialExecution: {e}")
        # Set a fallback state
        SetMicrophoneStatus("False")
        SetAssistantStatus("Available...")
        ShowTextToScreen("System initialized with errors. Please try again.")

# Make sure to call InitialExecution after defining all required functions
InitialExecution()


def MainExecution():
    try:
        TaskExecution = False
        ImageExecution = False
        ImageGenerationQuery = ""

        SetAssistantStatus("Listening...")
        Query = SpeechRecognition()
        ShowTextToScreen(f"{Username} : {Query}")
        SetAssistantStatus("Thinking...")
        Decision = FirstLayerDMM(Query)
        print("")
        print(f"Decision: {Decision}")
        print("")

        G = any([i for i in Decision if i.startswith("general")])
        R = any([i for i in Decision if i.startswith("realtime")])

        Mearged_query = " and ".join(
            [" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
        )

        for queries in Decision:
            if "generate" in queries:
                ImageGenerationQuery = str(queries)
                ImageExecution = True

        for queries in Decision:
            if TaskExecution == False:
                if any(queries.startswith(func) for func in Functions):
                    run(Automation(list(Decision)))
                    TaskExecution = True

        if ImageExecution == True:
            image_file_path = os.path.join("Frontend", "Files", "ImageGeneratoion.data")
            os.makedirs(os.path.dirname(image_file_path), exist_ok=True)
            
            with open(image_file_path, "w") as file:
                file.write(f"{ImageGenerationQuery}, True")

            try:
                p1 = subprocess.Popen(
                    ['python', os.path.join('Backend', 'ImageGeneration.py')],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    shell=False
                )
                subprocesses.append(p1)
            except Exception as e:
                print(f"Error starting ImageGeneration.py: {e}")

        if G and (R or R):
            SetAssistantStatus("Searching...")
            Answer = RealtimeSearchEngine(QueryModifier(Mearged_query))
            ShowTextToScreen(f"{Assistantname} : {Answer}")
            SetAssistantStatus("Answering...")
            TextToSpeech(Answer)
            return True
        
        else:
            for Queries in Decision:
                if "general" in Queries:
                    SetAssistantStatus("Thinking...")
                    QueryFinal = Queries.replace("general", "")
                    Answer = Chatbot(QueryModifier(QueryFinal))
                    ShowTextToScreen(f"{Assistantname} : {Answer}")
                    SetAssistantStatus("Answering...")
                    TextToSpeech(Answer)
                    return True

                elif "realtime" in Queries:
                    SetAssistantStatus("Searching ... ")
                    QueryFinal = Queries.replace("realtime ", "")
                    Answer = RealtimeSearchEngine(QueryModifier(QueryFinal))
                    ShowTextToScreen(f"{Assistantname} : {Answer}")
                    SetAssistantStatus("Answering...")
                    TextToSpeech(Answer)
                    return True
                
                elif "exit" in Queries:
                    QueryFinal = "Okay, Bye!"
                    Answer = Chatbot(QueryModifier(QueryFinal))
                    ShowTextToScreen(f"{Assistantname} : {Answer}")
                    SetAssistantStatus("Answering...")
                    TextToSpeech(Answer)
                    SetAssistantStatus("Answering...")
                    os._exit(1)
    except Exception as e:
        print(f"Error in MainExecution: {e}")
        SetAssistantStatus("Error occurred")
        ShowTextToScreen(f"{Assistantname} : I encountered an error processing your request. Please try again.")
        return False

def FirstThread():
    while True:
        try:
            CurrentStatus = GetMicrophoneStatus()

            if CurrentStatus == "True":
                MainExecution()
            else:
                AIStatus = GetAssistantStatus()

                if "Available..." in AIStatus:
                    sleep(0.1)
                else:
                    SetAssistantStatus("Available...")
        except Exception as e:
            print(f"Error in FirstThread: {e}")
            SetAssistantStatus("Error occurred")
            sleep(1)  # Prevent CPU spinning in case of repeated errors

def SecondThread():
    try:
        GraphicalUserInterface()
    except Exception as e:
        print(f"Error in GUI: {e}")
        print("GUI has crashed. Exiting application.")
        os._exit(1)

if __name__ == "__main__":
    try:
        thread2 = threading.Thread(target=FirstThread, daemon=True)
        thread2.start()
        SecondThread()
    except Exception as e:
        print(f"Critical error in main thread: {e}")
        os._exit(1)

