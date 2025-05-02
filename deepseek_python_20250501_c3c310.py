import os
import json
import datetime
import time
import threading
import speech_recognition as sr
import pyttsx3
import dateparser
from difflib import get_close_matches

# ===== CONFIGURE THESE =====
WAKE_WORD = "hey computer"  # Change to whatever you like
USER_NAME = "Alex"          # Your name for personalization
# ==========================

class UltraReliableAssistant:
    def __init__(self):
        # Voice engine setup
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 170)  # Natural speaking speed
        self.engine.setProperty('volume', 1.0)
        
        # Voice recognition setup
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Data storage
        self.data_file = "assistant_data.json"
        self.load_data()
        
        # Background reminder checker
        self.keep_running = True
        self.reminder_thread = threading.Thread(target=self.reminder_watcher)
        self.reminder_thread.daemon = True
        self.reminder_thread.start()
        
        # Noise adjustment
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        
        print(f"{USER_NAME}'s Assistant Ready!")

    def load_data(self):
        """Load or create data storage"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    self.data = json.load(f)
            else:
                self.data = {"reminders": [], "notes": []}
        except:
            self.data = {"reminders": [], "notes": []}

    def save_data(self):
        """Save data safely"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except:
            print("Couldn't save data")

    def speak(self, text):
        """Speak and print"""
        print(f"Assistant: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self):
        """Listen with better error handling"""
        with self.microphone as source:
            print("\nListening...")
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=8)
                text = self.recognizer.recognize_google(audio).lower()
                print(f"You: {text}")
                return text
            except sr.WaitTimeoutError:
                return None
            except:
                return None

    # ===== ROCK-SOLID REMINDERS =====
    def add_reminder(self, what, when):
        """Add reminder with triple-checked time parsing"""
        # First try normal parsing
        reminder_time = dateparser.parse(
            when,
            settings={
                'PREFER_DATES_FROM': 'future',
                'RELATIVE_BASE': datetime.datetime.now()
            }
        )
        
        # If that fails, try with "in" prefix
        if not reminder_time:
            reminder_time = dateparser.parse(f"in {when}")
            
        # Final fallback - try simple time
        if not reminder_time:
            try:
                reminder_time = datetime.datetime.strptime(when, "%I:%M %p")
                if reminder_time < datetime.datetime.now():
                    reminder_time += datetime.timedelta(days=1)
            except:
                return "Sorry, I didn't understand that time"
        
        # Store the reminder
        self.data["reminders"].append({
            "what": what,
            "when": reminder_time.strftime("%Y-%m-%d %H:%M"),
            "created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        self.save_data()
        
        # Speak confirmation
        time_str = reminder_time.strftime("%I:%M %p on %A")
        self.speak(f"Got it {USER_NAME}! I'll remind you to {what} at {time_str}")

    def reminder_watcher(self):
        """Constantly check for due reminders"""
        while self.keep_running:
            now = datetime.datetime.now()
            triggered = []
            
            for reminder in self.data["reminders"]:
                when = datetime.datetime.strptime(reminder["when"], "%Y-%m-%d %H:%M")
                if now >= when:
                    triggered.append(reminder)
            
            if triggered:
                for reminder in triggered:
                    self.speak(f"🔔 Reminder! {reminder['what']}")
                    self.data["reminders"].remove(reminder)
                self.save_data()
                time.sleep(2)  # Pause between reminders
            
            time.sleep(10)  # Check every 10 seconds

    def show_reminders(self):
        """List all upcoming reminders"""
        if not self.data["reminders"]:
            return "You have no reminders set"
            
        reminders = sorted(
            self.data["reminders"],
            key=lambda x: x["when"]
        )
        
        response = "📅 Your reminders:\n"
        for i, reminder in enumerate(reminders, 1):
            when = datetime.datetime.strptime(reminder["when"], "%Y-%m-%d %H:%M")
            response += f"{i}. {reminder['what']} ({when.strftime('%a %I:%M %p')})\n"
        
        return response

    # ===== SIMPLE NOTES =====
    def add_note(self, text):
        """Add a quick note"""
        self.data["notes"].append({
            "text": text,
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        self.save_data()
        return f"Note added: {text}"

    def show_notes(self):
        """List all notes"""
        if not self.data["notes"]:
            return "You have no notes"
            
        response = "📝 Your notes:\n"
        for i, note in enumerate(self.data["notes"][-5:][::-1], 1):  # Show last 5
            response += f"{i}. {note['text']}\n"
        return response

    # ===== MAIN COMMANDS =====
    def process_command(self, command):
        """Handle all voice commands"""
        if not command:
            return None
            
        # Reminder commands
        if "remind me" in command or "set reminder" in command:
            if " to " in command:
                parts = command.split(" to ", 1)
                when, what = parts[0].replace("remind me", "").strip(), parts[1].strip()
            elif " at " in command:
                parts = command.split(" at ", 1)
                what, when = parts[0].replace("remind me", "").strip(), parts[1].strip()
            else:
                return "Try saying 'remind me to [action] at [time]' or 'remind me at [time] to [action]'"
            
            return self.add_reminder(what, when)
            
        elif "my reminders" in command or "show reminders" in command:
            return self.show_reminders()
            
        # Note commands
        elif "add note" in command:
            note = command.replace("add note", "").strip()
            return self.add_note(note)
            
        elif "my notes" in command or "show notes" in command:
            return self.show_notes()
            
        # Basic commands
        elif any(word in command for word in ["hello", "hi", "hey"]):
            return f"Hello {USER_NAME}! What can I do for you?"
            
        elif any(word in command for word in ["time", "what time"]):
            return f"It's {datetime.datetime.now().strftime('%I:%M %p')}"
            
        elif any(word in command for word in ["date", "what day"]):
            return f"Today is {datetime.datetime.now().strftime('%A, %B %d')}"
            
        elif any(word in command for word in ["goodbye", "exit", "quit"]):
            self.speak(f"Goodbye {USER_NAME}!")
            self.keep_running = False
            time.sleep(1)
            exit()
            
        else:
            return "I didn't understand that. Try saying 'remind me to...' or 'add note...'"

    def run(self):
        """Main assistant loop"""
        self.speak(f"Say '{WAKE_WORD}' when you need me")
        
        while True:
            command = self.listen()
            
            if command and WAKE_WORD in command:
                self.speak("Yes?")
                while True:
                    command = self.listen()
                    if not command:
                        self.speak("...")
                        break
                        
                    response = self.process_command(command)
                    if response:
                        self.speak(response)
                        
                    if not self.keep_running:
                        return

if __name__ == "__main__":
    assistant = UltraReliableAssistant()
    try:
        assistant.run()
    except KeyboardInterrupt:
        assistant.speak("Shutting down...")
        assistant.keep_running = False
        assistant.save_data()