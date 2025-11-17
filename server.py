print(">>> SMART RESTROOM MANAGEMENT SYSTEM <<<")

from flask import Flask, request, jsonify, render_template, redirect
from datetime import datetime
from flask_socketio import SocketIO, emit
import uuid
import json
import os
import firebase_admin
from firebase_admin import credentials, db

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# Firebase initialization
def init_firebase():
    try:
        # Check if service account key file exists
        if os.path.exists('firebase-credentials.json'):
            cred = credentials.Certificate('firebase-credentials.json')
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://saray-tp-project-default-rtdb.europe-west1.firebasedatabase.app/'  # Will be set from config
            })
            print("✓ Firebase initialized successfully")
            return True
        else:
            print("⚠ Firebase credentials not found. Using local storage.")
            print("  Place 'firebase-credentials.json' in the project root to enable Firebase.")
            return False
    except Exception as e:
        print(f"⚠ Firebase initialization failed: {e}")
        print("  Falling back to local JSON storage.")
        return False

# Check if Firebase is available
firebase_enabled = init_firebase()

# Data storage
rooms = {}
DATA_FILE = 'rooms_data.json'

# Load data from Firebase or file
def load_data():
    global rooms
    if firebase_enabled:
        try:
            ref = db.reference('rooms')
            data = ref.get()
            rooms = data if data else {}
            print(f"Loaded {len(rooms)} rooms from Firebase")
        except Exception as e:
            print(f"Error loading from Firebase: {e}")
            rooms = {}
    else:
        # Fallback to JSON file
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    rooms = json.load(f)
                print(f"Loaded {len(rooms)} rooms from local storage")
            except Exception as e:
                print(f"Error loading data: {e}")
                rooms = {}
        else:
            rooms = {}

# Save data to Firebase or file
def save_data():
    if firebase_enabled:
        try:
            ref = db.reference('rooms')
            ref.set(rooms)
        except Exception as e:
            print(f"Error saving to Firebase: {e}")
    else:
        # Fallback to JSON file
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump(rooms, f, indent=2)
        except Exception as e:
            print(f"Error saving data: {e}")

# Initialize data
load_data()

# Dashboard route
@app.get("/")
def dashboard():
    return render_template('dashboard.html')

# API: Get all rooms
@app.get("/api/rooms")
def get_rooms():
    return jsonify(list(rooms.values()))

# API: Create a new room
@app.post("/api/rooms")
def create_room():
    data = request.get_json()
    
    # Generate unique room ID
    room_id = str(uuid.uuid4())[:8].upper()
    
    room = {
        'id': room_id,
        'name': data.get('name', 'Unnamed Room'),
        'type': data.get('type', 'restroom'),
        'location': data.get('location', ''),
        'supplies': data.get('supplies', {
            'toilet_paper': {'name': 'Toilet Paper', 'status': 'full'},
            'soap': {'name': 'Soap', 'status': 'full'},
            'towel': {'name': 'Paper Towel', 'status': 'full'},
            'trash': {'name': 'Trash Bin', 'status': 'full'}
        }),
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    rooms[room_id] = room
    save_data()
    
    print(f"Room created: {room_id} - {room['name']}")
    socketio.emit('room_update', room)
    
    return jsonify(room), 201

# API: Update room
@app.put("/api/rooms/<room_id>")
def update_room(room_id):
    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    
    data = request.get_json()
    
    rooms[room_id]['name'] = data.get('name', rooms[room_id]['name'])
    rooms[room_id]['type'] = data.get('type', rooms[room_id]['type'])
    rooms[room_id]['location'] = data.get('location', rooms[room_id]['location'])
    
    save_data()
    
    print(f"Room updated: {room_id}")
    socketio.emit('room_update', rooms[room_id])
    
    return jsonify(rooms[room_id])

# API: Delete room
@app.delete("/api/rooms/<room_id>")
def delete_room(room_id):
    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    
    deleted_room = rooms.pop(room_id)
    save_data()
    
    print(f"Room deleted: {room_id}")
    socketio.emit('room_update', {'deleted': room_id})
    
    return jsonify({'success': True, 'deleted': deleted_room})

# API: Resolve supply (mark as full)
@app.route("/api/rooms/<room_id>/supply/<supply_key>/resolve", methods=['POST'])
def resolve_supply(room_id, supply_key):
    print(f"Resolve request - Room: {room_id}, Supply: {supply_key}")
    print(f"Available rooms: {list(rooms.keys())}")
    
    if room_id not in rooms:
        return jsonify({'error': 'Room not found', 'room_id': room_id}), 404
    
    if supply_key not in rooms[room_id]['supplies']:
        return jsonify({'error': 'Supply not found', 'supply_key': supply_key}), 404
    
    # Mark supply as full
    rooms[room_id]['supplies'][supply_key]['status'] = 'full'
    save_data()
    
    print(f"Supply resolved - Room: {room_id}, Item: {supply_key}")
    
    # Emit real-time update
    socketio.emit('supply_update', {
        'room_id': room_id,
        'room_name': rooms[room_id]['name'],
        'item': supply_key,
        'status': 'full'
    })
    
    return jsonify({'success': True})

# ESP32 endpoint: Report supply status
@app.post("/report")
def report():
    """
    ESP32 devices should POST to this endpoint with:
    {
        "room_id": "ABC123",
        "item": "toilet_paper",
        "status": "low" or "empty" or "full"
    }
    """
    data = request.get_json(silent=True) or {}
    
    room_id = data.get('room_id')
    item = data.get('item')
    status = data.get('status', 'unknown')
    
    if not room_id or room_id not in rooms:
        return jsonify({'error': 'Invalid room_id'}), 400
    
    if not item:
        return jsonify({'error': 'Item required'}), 400
    
    # Update the supply status
    if item in rooms[room_id]['supplies']:
        rooms[room_id]['supplies'][item]['status'] = status
        save_data()
        
        print(f"Supply update - Room: {room_id}, Item: {item}, Status: {status}")
        
        # Emit real-time update
        socketio.emit('supply_update', {
            'room_id': room_id,
            'room_name': rooms[room_id]['name'],
            'item': item,
            'status': status
        })
        
        return jsonify({'ok': True, 'room': rooms[room_id]['name']}), 200
    else:
        return jsonify({'error': 'Invalid item'}), 400

# ESP32 endpoint: Get room info
@app.get("/room/<room_id>")
def get_room_info(room_id):
    """ESP32 devices can use this to verify their room_id"""
    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    
    return jsonify(rooms[room_id])

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Smart Restroom Management System")
    print("="*60)
    print(f"Dashboard: http://0.0.0.0:5000")
    print(f"Storage: {'Firebase' if firebase_enabled else 'Local JSON'}")
    print(f"Rooms loaded: {len(rooms)}")
    print("="*60 + "\n")
    
    socketio.run(app, host="0.0.0.0", port=5000)
