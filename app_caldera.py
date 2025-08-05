from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import openai
import os

PUBLIC_URL = os.getenv("PUBLIC_URL", "https://yourdomain.com")

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("SESSION_SECRET", "something-very-secret")

# === Load Caldera System Prompt ===
with open("caldera_prompt_base.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read().replace("https://yourdomain.com", PUBLIC_URL)

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "").lower()

    # === Initialize session memory ===
    if "messages" not in session:
        session["messages"] = []
        session["focus"] = None
        session["budget"] = False
        session["spa_type"] = None
        session["features"] = []

    # === Track preferences ===
    if "relax" in user_msg:
        session["focus"] = "relaxation"
    elif "therapy" in user_msg or "therapeutic" in user_msg:
        session["focus"] = "therapy"
    elif "both" in user_msg:
        session["focus"] = "both"

    if "budget" in user_msg or "$" in user_msg:
        session["budget"] = True

    if "emerge" in user_msg:
        session["spa_type"] = "Emerge cold plunge"
    elif "caldera" in user_msg or "hot tub" in user_msg:
        session["spa_type"] = "Caldera hot tub"

    if "salt" in user_msg and "salt system" not in session["features"]:
        session["features"].append("salt system")

    if "jets" in user_msg and "targeted jets" not in session["features"]:
        session["features"].append("targeted jets")

    # === Build memory summary ===
    memory_summary = ""
    if session.get("focus"):
        memory_summary += f"The user is focused on {session['focus']}. "
    if session.get("budget"):
        memory_summary += "They’ve brought up budget. "
    if session.get("spa_type"):
        memory_summary += f"They're leaning toward a {session['spa_type']}. "
    if session.get("features"):
        memory_summary += "They've shown interest in features like: " + ", ".join(session["features"]) + ". "

    # === Build message history ===
    message_history = [{"role": "system", "content": SYSTEM_PROMPT}]
    if memory_summary:
        message_history.append({"role": "assistant", "content": memory_summary})

    for msg in session["messages"][-10:]:
        message_history.append(msg)

    message_history.append({"role": "user", "content": request.json.get("message", "")})
    session["messages"].append({"role": "user", "content": request.json.get("message", "")})

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=message_history,
            temperature=0.7,
            max_tokens=700
        )
        reply = response.choices[0].message["content"]
        session["messages"].append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    except Exception as e:
        print("🔥 OpenAI Chat Error:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/gallery/<filename>")
def gallery_image(filename):
    return send_from_directory("static/spa_images", filename)

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(debug=True)
