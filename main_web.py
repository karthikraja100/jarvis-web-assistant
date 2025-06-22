from flask import Flask, request, jsonify, send_from_directory
import json
import os
import re
import dateparser
from datetime import datetime

app = Flask(__name__, static_folder='.')

REMINDER_FILE = "reminders.json"
user_state = {"mode": None, "reminder_content": None}

# This serves index.html when you open http://127.0.0.1:5000/
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/greet')
def greet():
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good Morning!"
    elif hour < 18:
        greeting = "Good Afternoon!"
    else:
        greeting = "Good Evening!"
    return jsonify({"reply": f"{greeting} I am your assistant Jarvis. What can I do for you?"})

@app.route('/process', methods=['POST'])
def process():
    global user_state
    data = request.get_json()
    message = data.get('message', '').lower()

    if user_state["mode"] == "adding_reminder_content":
        user_state["reminder_content"] = message
        user_state["mode"] = "adding_reminder_time"
        return jsonify({"reply": "When should I remind you?"})

    elif user_state["mode"] == "adding_reminder_time":
        date = dateparser.parse(message, settings={'PREFER_DATES_FROM': 'future'})
        if not date:
            return jsonify({"reply": "I couldn't understand the time. Please say it again."})
        save_reminder(user_state["reminder_content"], date)
        user_state = {"mode": None, "reminder_content": None}
        return jsonify({"reply": f"Reminder saved for {date.strftime('%A %B %d, %I:%M %p')}."})

    elif "add reminder" in message:
        user_state["mode"] = "adding_reminder_content"
        return jsonify({"reply": "What should I remind you?"})
    
    elif "view" in message or "show" in message:
        reply = view_reminders()
        return jsonify({"reply": reply})

    elif "remove" in message or "delete" in message:
        removed = remove_reminder(message)
        return jsonify({"reply": removed})

    else:
        return jsonify({"reply": "Sorry, I didn't understand that."})

def save_reminder(content, date):
    reminder_info = {
        "content": content,
        "datetime": date.strftime("%Y-%m-%d %H:%M"),
    }
    reminders = load_reminders()
    reminders[reminder_info["datetime"]] = reminder_info
    with open(REMINDER_FILE, "w") as f:
        json.dump(reminders, f, indent=4)

def view_reminders():
    reminders = load_reminders()
    if not reminders:
        return "You have no reminders."
    upcoming = []
    for time_str, info in reminders.items():
        dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        if dt >= datetime.now():
            upcoming.append((dt, info))
    if not upcoming:
        return "No upcoming reminders."
    upcoming.sort()
    result = []
    for time, info in upcoming:
        result.append(f"{info['content']} on {time.strftime('%A %B %d, %I:%M %p')}")
    return "\n".join(result)

def remove_reminder(message):
    reminders = load_reminders()
    removed = False
    for time_str in list(reminders):
        if any(word in reminders[time_str]["content"].lower() for word in message.split()):
            del reminders[time_str]
            removed = True
    if removed:
        with open(REMINDER_FILE, "w") as f:
            json.dump(reminders, f, indent=4)
        return "Reminder removed."
    return "No matching reminder found."

def load_reminders():
    if os.path.exists(REMINDER_FILE):
        with open(REMINDER_FILE, "r") as f:
            return json.load(f)
    return {}

if __name__ == '__main__':
    app.run(debug=True)


