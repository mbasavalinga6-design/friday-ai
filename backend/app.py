from dotenv import load_dotenv
import os

load_dotenv()

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import datetime
import wikipedia
import pyjokes
from groq import Groq
import requests
import platform
import threading
import time

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

reminders = []

# ---------- DATABASE ----------

def connect_db():
    return sqlite3.connect("friday.db")

def init_db():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        command TEXT,
        response TEXT,
        time TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        username TEXT PRIMARY KEY,
        password TEXT
    )
    """)

    cursor.execute("""
    INSERT OR REPLACE INTO users(username, password)
    VALUES ('admin','1234')
    """)

    conn.commit()
    conn.close()

init_db()

# ---------- GROQ AI ----------

def ask_groq(prompt):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are Friday, a helpful and friendly girl voice assistant just like Iron Man's AI. Keep responses short and clear."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print("Groq error:", e)
        return "Sorry, I couldn't get a response."

# ---------- WEATHER ----------

def get_weather(city):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        res = requests.get(url)
        data = res.json()
        print("Weather API response:", data)
        if data["cod"] == 200:
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]
            humidity = data["main"]["humidity"]
            return f"Weather in {city}: {desc}, Temperature: {temp}°C, Humidity: {humidity}%"
        else:
            return "City not found. Please try again."
    except Exception as e:
        print("Weather error:", e)
        return "Sorry, I couldn't get the weather."

# ---------- YOUTUBE ----------

def get_youtube_video_id(song):
    try:
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={song}&type=video&key={YOUTUBE_API_KEY}&maxResults=1"
        res = requests.get(url)
        data = res.json()
        video_id = data["items"][0]["id"]["videoId"]
        print("YouTube video ID:", video_id)
        return video_id
    except Exception as e:
        print("YouTube error:", e)
        return None

# ---------- SYSTEM CONTROLS ----------

def system_control(action):
    system = platform.system()
    try:
        if action == "shutdown":
            if system == "Windows":
                os.system("shutdown /s /t 5")
            else:
                os.system("shutdown -h now")
            return "Shutting down in 5 seconds Basava!"

        elif action == "restart":
            if system == "Windows":
                os.system("shutdown /r /t 5")
            else:
                os.system("shutdown -r now")
            return "Restarting in 5 seconds Basava!"

        elif action == "lock":
            if system == "Windows":
                os.system("rundll32.exe user32.dll,LockWorkStation")
            return "Locking your system Basava!"

    except Exception as e:
        print("System error:", e)
        return "Sorry, I couldn't perform that action."

# ---------- COMMAND LOGIC ----------

def process_command(command):
    command_lower = command.lower()

    # Greet
    if any(word in command_lower for word in ['hi friday', 'hello friday', 'hey friday']):
        return "GREET"

    # Play
    elif 'play' in command_lower:
        song = command_lower.replace('play', '').strip()
        song = song.replace('.', '').replace(',', '').strip()
        video_id = get_youtube_video_id(song)
        if video_id:
            return f"PLAY:{song}|{video_id}"
        else:
            return f"PLAY:{song}|none"

    # Time
    elif 'time' in command_lower:
        return datetime.datetime.now().strftime('%I:%M %p')

    # Date
    elif 'date' in command_lower:
        return datetime.datetime.now().strftime('%B %d, %Y')

    # Weather
    elif 'weather' in command_lower:
        city = command_lower
        city = city.replace("how's the weather in", "")
        city = city.replace("how is the weather in", "")
        city = city.replace("what is the weather in", "")
        city = city.replace("what's the weather in", "")
        city = city.replace("weather in", "")
        city = city.replace("weather", "")
        city = city.replace("?", "")
        city = city.replace(".", "")
        city = city.replace(",", "")
        city = city.replace("the", "")
        city = city.strip()
        print("Extracted city name is:", city)
        if not city:
            city = "Bengaluru"
        return get_weather(city)

    # Reminder
    elif 'remind' in command_lower:
        try:
            words = command_lower.split()
            minutes = None
            seconds = None
            message_words = []
            skip_next = False

            for i, word in enumerate(words):
                if skip_next:
                    skip_next = False
                    continue

                if word in ['in', 'after'] and i + 1 < len(words):
                    try:
                        number = int(words[i + 1])
                        if i + 2 < len(words) and 'second' in words[i + 2]:
                            seconds = number
                        else:
                            minutes = number
                        skip_next = True
                        continue
                    except:
                        pass

                if word not in ['remind', 'me', 'to', 'in', 'after', 'please']:
                    message_words.append(word)

            message = ' '.join(message_words)
            message = message.replace('minutes', '').replace('minute', '')
            message = message.replace('seconds', '').replace('second', '')
            message = message.strip()

            if minutes is None and seconds is None:
                return "Please say — remind me to drink water in 1 minute"

            sleep_time = 0
            if minutes:
                sleep_time += minutes * 60
            if seconds:
                sleep_time += seconds

            response_text = f"Okay Basava! I will remind you to {message} in "
            if minutes:
                response_text += f"{minutes} minutes!"
            elif seconds:
                response_text += f"{seconds} seconds!"

            def remind():
                time.sleep(sleep_time)
                reminders.append(message)

            thread = threading.Thread(target=remind)
            thread.daemon = True
            thread.start()

            return response_text

        except Exception as e:
            print("Reminder error:", e)
            return "Please say — remind me to drink water in 1 minute"

    # Roast
    elif 'roast' in command_lower:
        return ask_groq("Roast me in a funny and friendly way in 2 sentences")

    # Quote
    elif 'quote' in command_lower or 'motivate' in command_lower:
        return ask_groq("Give me a short powerful motivational quote")

    # Who is
    elif 'who is' in command_lower:
        person = command_lower.replace('who is', '').strip()
        try:
            return wikipedia.summary(person, 1)
        except:
            return "No info found"

    # Joke
    elif 'joke' in command_lower:
        return pyjokes.get_joke()

    # System controls
    elif 'shutdown' in command_lower:
        return system_control("shutdown")

    elif 'restart' in command_lower:
        return system_control("restart")

    elif 'lock' in command_lower:
        return system_control("lock")

    # Groq AI fallback
    else:
        return ask_groq(command)

# ---------- API ----------

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    command = data.get("command")

    response = process_command(command)

    conn = connect_db()
    cursor = conn.cursor()

    time_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO history(command, response, time) VALUES (?,?,?)",
        (command, response, time_now)
    )

    conn.commit()
    conn.close()

    return jsonify({"response": response})


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    )

    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "fail"})


@app.route("/history", methods=["GET"])
def history():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT command, response, time FROM history ORDER BY id DESC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()

    result = [{"command": r[0], "response": r[1], "time": r[2]} for r in rows]
    return jsonify({"history": result})


@app.route("/reminders", methods=["GET"])
def get_reminders():
    global reminders
    if reminders:
        reminder = reminders.pop(0)
        return jsonify({"reminder": reminder})
    return jsonify({"reminder": None})


# ---------- RUN ----------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("🔥 Friday backend running...")
    app.run(host="0.0.0.0", port=port, debug=False)