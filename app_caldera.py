from flask import Flask, request, session, jsonify
from flask_cors import CORS
import openai
import os
from dotenv import load_dotenv

# === Load environment variables ===
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# === Flask App Setup ===
app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("SESSION_SECRET", "something-very-secret")

# === Load System Prompt ===
with open("caldera_prompt_base.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# === Chat Route ===
@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "").strip()

    if "messages" not in session:
        session["messages"] = []

    session["messages"].append({"role": "user", "content": user_msg})

    # === Build Message History ===
    message_history = [{"role": "system", "content": SYSTEM_PROMPT}]
    memory_summary = session.get("memory_summary", "")

    if memory_summary:
        message_history.append({"role": "assistant", "content": memory_summary})

    for msg in session["messages"][-10:]:
        message_history.append(msg)

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Change to gpt-3.5-turbo if needed
            messages=message_history
        )
        reply = response.choices[0].message["content"].strip()
        session["messages"].append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": "Oops, something went wrong. Try again shortly."}), 500

# === Optional Session Reset ===
@app.route("/reset", methods=["POST"])
def reset():
    session.clear()
    return jsonify({"status": "reset"})

# === Start App (for Render) ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
