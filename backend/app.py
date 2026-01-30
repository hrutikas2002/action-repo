from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
CORS(app)

client = MongoClient("mongodb://localhost:27017/")
db = client["github_events"]
collection = db["events"]

@app.route("/")
def home():
    return "Backend running"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    event_type = request.headers.get("X-GitHub-Event")

    author = data["sender"]["login"]
    timestamp = datetime.utcnow().strftime("%d %B %Y - %I:%M %p UTC")

    if event_type == "push":
        document = {
            "request_id": data["after"],
            "author": author,
            "action": "PUSH",
            "from_branch": None,
            "to_branch": data["ref"].split("/")[-1],
            "timestamp": timestamp
        }

    elif event_type == "pull_request":
        pr = data["pull_request"]
        document = {
            "request_id": str(pr["id"]),
            "author": author,
            "action": "PULL_REQUEST",
            "from_branch": pr["head"]["ref"],
            "to_branch": pr["base"]["ref"],
            "timestamp": timestamp
        }

    else:
        return jsonify({"msg": "Ignored"}), 200

    collection.insert_one(document)
    return jsonify({"status": "stored"}), 201

@app.route("/events")
def events():
    data = list(collection.find({}, {"_id": 0}).sort("timestamp", -1))
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)
