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

# === Load Prompt ===
with open("caldera_prompt_base.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# === Chat Route ===
@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "").lower()

    if "messages" not in session:
        session["messages"] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    session["messages"].append({"role": "user", "content": user_msg})

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=session["messages"]
        )
        reply = response.choices[0].message["content"]
        session["messages"].append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === Optional Reset Endpoint ===
@app.route("/reset", methods=["POST"])
def reset():
    session.pop("messages", None)
    return jsonify({"status": "reset"})

# === Start App (for Render) ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
