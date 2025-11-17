# Firebase Setup Guide

This application supports Firebase Realtime Database for persistent cloud storage. Follow these steps to enable Firebase integration.

## Prerequisites

✓ Firebase Admin SDK is already installed (`firebase-admin` package)

## Setup Steps

### 1. Create a Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **"Add project"** or select an existing project
3. Enter a project name (e.g., "Smart Restroom System")
4. Follow the setup wizard

### 2. Enable Realtime Database

1. In your Firebase project console, navigate to **Build** → **Realtime Database**
2. Click **"Create Database"**
3. Select a location (choose closest to your server)
4. Start in **"Test mode"** (you can set security rules later)
5. Note your database URL (e.g., `https://your-project-id.firebaseio.com/`)

### 3. Generate Service Account Credentials

1. In Firebase Console, click the **gear icon** (⚙️) → **Project settings**
2. Navigate to **Service accounts** tab
3. Click **"Generate new private key"**
4. Click **"Generate key"** in the confirmation dialog
5. A JSON file will be downloaded (e.g., `your-project-firebase-adminsdk.json`)

### 4. Configure Your Application

1. **Rename the downloaded file** to `firebase-credentials.json`
2. **Move it to your project root**:
   ```
   C:\Users\ydgn4\Desktop\test_esp32\firebase-credentials.json
   ```
3. **Update the database URL** in `server.py`:
   - Open `server.py`
   - Find the line: `'databaseURL': 'YOUR_FIREBASE_DATABASE_URL'`
   - Replace with your actual database URL:
     ```python
     'databaseURL': 'https://your-project-id.firebaseio.com/'
     ```

### 5. Verify Setup

1. Restart your server:
   ```powershell
   python server.py
   ```

2. Look for this message on startup:
   ```
   ✓ Firebase initialized successfully
   Storage: Firebase
   ```

3. If successful, all room data will now be stored in Firebase!

## Security Rules (Production)

For production use, set proper security rules in Firebase Console:

```json
{
  "rules": {
    "rooms": {
      ".read": true,
      ".write": true
    }
  }
}
```

For better security, you can restrict writes to authenticated users or specific IP addresses.

## Troubleshooting

### "Firebase credentials not found"
- Ensure `firebase-credentials.json` is in the project root directory
- Check the filename is exactly `firebase-credentials.json`

### "Firebase initialization failed"
- Verify your service account key is valid
- Check the database URL is correct
- Ensure your Firebase project has Realtime Database enabled

### "Error loading from Firebase"
- Check your internet connection
- Verify Firebase database rules allow read access
- Check the database URL in your code

## Fallback Mode

If Firebase is not configured, the application automatically falls back to **local JSON storage** (`rooms_data.json`). This ensures the system works even without Firebase.

## Benefits of Firebase

- ☁️ **Cloud Storage**: Access data from anywhere
- 🔄 **Real-time Sync**: Automatic synchronization across devices
- 📱 **Mobile Access**: Integrate with mobile apps
- 💾 **Automatic Backups**: Firebase handles data persistence
- 🚀 **Scalability**: Grows with your needs
- 🔒 **Security**: Built-in authentication and rules

## Data Structure in Firebase

```
/rooms
  ├── 24F1E201
  │   ├── id: "24F1E201"
  │   ├── name: "Main Floor"
  │   ├── type: "restroom"
  │   ├── location: "2nd Floor"
  │   ├── created_at: "2025-11-17 08:20:50"
  │   └── supplies
  │       ├── toilet_paper
  │       │   ├── name: "Toilet Paper"
  │       │   └── status: "full"
  │       ├── soap
  │       │   ├── name: "Soap"
  │       │   └── status: "empty"
  │       └── ...
  └── ...
```

## Next Steps

After Firebase is configured:
1. Create rooms in the dashboard
2. Test ESP32 integration
3. Monitor data in Firebase Console
4. Set up proper security rules
5. Consider adding authentication for admin access
