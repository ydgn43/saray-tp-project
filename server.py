print(">>> SMART RESTROOM MANAGEMENT SYSTEM <<<")
import eventlet
eventlet.monkey_patch()

from flask import Flask, request, jsonify, render_template
from datetime import datetime
from flask_socketio import SocketIO
import uuid
import json
import os
import firebase_admin
from firebase_admin import credentials, db


# -------------------------
# Flask App & Socket.IO Setup
# -------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'  # Replace later in production

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="eventlet",
    ping_interval=25,
    ping_timeout=60,
    cookie=None)



# -------------------------
# Firebase Initialization
# -------------------------
def init_firebase():
    try:
        if os.path.exists("firebase-credentials.json"):
            cred = credentials.Certificate("firebase-credentials.json")
            firebase_admin.initialize_app(cred, {
                "databaseURL": "https://saray-tp-project-default-rtdb.europe-west1.firebasedatabase.app/"
            })
            print("✓ Firebase initialized successfully")
            return True
        else:
            print("⚠ Firebase credentials missing. Using local storage.")
            return False
    except Exception as e:
        print(f"⚠ Firebase initialization failed: {e}")
        return False


firebase_enabled = init_firebase()


# -------------------------
# Local / Firebase Data Storage
# -------------------------
rooms = {}
DATA_FILE = "rooms_data.json"


def load_data():
    global rooms

    if firebase_enabled:
        try:
            ref = db.reference("rooms")
            data = ref.get()
            rooms = data if data else {}
            print(f"✓ Loaded {len(rooms)} rooms from Firebase")
        except Exception as e:
            print(f"⚠ Firebase load error: {e}")
            rooms = {}
    else:
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    rooms = json.load(f)
                print(f"✓ Loaded {len(rooms)} rooms locally")
            except:
                rooms = {}
        else:
            rooms = {}


def save_data():
    if firebase_enabled:
        try:
            db.reference("rooms").set(rooms)
        except Exception as e:
            print(f"⚠ Firebase save error: {e}")
    else:
        try:
            with open(DATA_FILE, "w") as f:
                json.dump(rooms, f, indent=2)
        except:
            pass


load_data()


# -------------------------
# Dashboard
# -------------------------
@app.get("/")
def dashboard():
    return render_template("dashboard.html")


# -------------------------
# REST API
# -------------------------
@app.get("/api/rooms")
def get_rooms():
    return jsonify(list(rooms.values()))


@app.post("/api/rooms")
def create_room():
    data = request.get_json()
    room_id = str(uuid.uuid4())[:8].upper()

    room = {
        "id": room_id,
        "name": data.get("name", "Unnamed Room"),
        "type": data.get("type", "restroom"),
        "location": data.get("location", ""),
        "supplies": data.get("supplies", {
            "toilet_paper": {"name": "Toilet Paper", "status": "full"},
            "soap": {"name": "Soap", "status": "full"},
            "towel": {"name": "Paper Towel", "status": "full"},
            "trash": {"name": "Trash Bin", "status": "full"},
        }),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    rooms[room_id] = room
    save_data()

    socketio.emit("room_update", room)
    return jsonify(room), 201


@app.put("/api/rooms/<room_id>")
def update_room(room_id):
    if room_id not in rooms:
        return jsonify({"error": "Room not found"}), 404

    data = request.get_json()
    rooms[room_id]["name"] = data.get("name", rooms[room_id]["name"])
    rooms[room_id]["type"] = data.get("type", rooms[room_id]["type"])
    rooms[room_id]["location"] = data.get("location", rooms[room_id]["location"])

    save_data()
    socketio.emit("room_update", rooms[room_id])

    return jsonify(rooms[room_id])


@app.delete("/api/rooms/<room_id>")
def delete_room(room_id):
    if room_id not in rooms:
        return jsonify({"error": "Room not found"}), 404

    deleted = rooms.pop(room_id)
    save_data()

    socketio.emit("room_update", {"deleted": room_id})
    return jsonify({"success": True, "deleted": deleted})


@app.post("/api/rooms/<room_id>/supply/<supply_key>/resolve")
def resolve_supply(room_id, supply_key):
    if room_id not in rooms:
        return jsonify({"error": "Room not found"}), 404

    if supply_key not in rooms[room_id]["supplies"]:
        return jsonify({"error": "Invalid supply"}), 404

    rooms[room_id]["supplies"][supply_key]["status"] = "full"
    save_data()

    socketio.emit("supply_update", {
        "room_id": room_id,
        "item": supply_key,
        "status": "full",
        "room_name": rooms[room_id]["name"]
    })

    return jsonify({"success": True})


# -------------------------
# ESP32 Webhook /report
# -------------------------
@app.post("/report")
def report():
    data = request.get_json(silent=True) or {}

    room_id = data.get("room_id")
    item = data.get("item")
    status = data.get("status", "unknown")

    if not room_id or room_id not in rooms:
        return jsonify({"error": "Invalid room_id"}), 400

    if item not in rooms[room_id]["supplies"]:
        return jsonify({"error": "Invalid item"}), 400

    rooms[room_id]["supplies"][item]["status"] = status
    save_data()

    socketio.emit("supply_update", {
        "room_id": room_id,
        "item": item,
        "status": status,
        "room_name": rooms[room_id]["name"]
    })

    return jsonify({"ok": True}), 200


# -------------------------
# ESP32 Verify Room ID
# -------------------------
@app.get("/room/<room_id>")
def get_room(room_id):
    if room_id not in rooms:
        return jsonify({"error": "Room not found"}), 404
    return jsonify(rooms[room_id])


# -------------------------
# Start Server (eventlet)
# -------------------------
if __name__ == "__main__":
    print("\n" + "="*60)
    print("Smart Restroom Management System")
    print("="*60)
    print("Running on http://0.0.0.0:5000")
    print("Storage:", "Firebase" if firebase_enabled else "Local JSON")
    print(f"Rooms loaded: {len(rooms)}")
    print("="*60 + "\n")

    socketio.run(app, host="0.0.0.0", port=5000)

