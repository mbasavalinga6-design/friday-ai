from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import datetime
import wikipedia
import pyjokes
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ---------- DATABASE ----------

def connect_db():
    return sqlite3.connect("arix.db")

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
                    "content": "You are Arix, a helpful and friendly girl voice assistant. Keep responses short and clear."
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

# ---------- COMMAND LOGIC ----------

def process_command(command):
    command_lower = command.lower()

    if 'hi arix' in command_lower or 'hello arix' in command_lower or 'hey arix' in command_lower:
        return "GREET"

    elif 'play' in command_lower:
        song = command_lower.replace('play', '').strip()
        query = song.replace(' ', '+')
        url = f"https://www.youtube.com/results?search_query={query}"
        return f"PLAY:{url}"

    elif 'time' in command_lower:
        return datetime.datetime.now().strftime('%I:%M %p')

    elif 'who is' in command_lower:
        person = command_lower.replace('who is', '').strip()
        try:
            return wikipedia.summary(person, 1)
        except:
            return "No info found"

    elif 'joke' in command_lower:
        return pyjokes.get_joke()

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

    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO history(command, response, time) VALUES (?,?,?)",
        (command, response, time)
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


# ---------- RUN ----------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("🔥 Arix backend running...")
    app.run(host="0.0.0.0", port=port, debug=False)