# steps to run the project...




# Running the Project

## 1. Clone the Repository

```bash
git clone https://github.com/Pushkal-Gupta/Fog-Based-Vehicle-Monitoring.git
cd Fog-Based-Vehicle-Monitoring/Code
```

---

# Backend Setup and Run

## 2. Navigate to Backend Folder

```bash
cd backend
```

## 3. Create Environment File

Create a `.env` file in the backend root and copy values from `.env.example`

```
APP_NAME=
ENV=
FIREBASE=
MONGO_URI=
MONGO_DB_NAME=
ADMIN_SECRET_KEY=
```

Fill in the required values before running the server.

### Backend Environment Variables Explanation

The backend requires a `.env` file configured using values based on your deployment and services. Below is a description of each parameter.

---

### APP_NAME
A generic name for the backend service.  
This is only used internally for identification and logging.

Example:
```
APP_NAME=vehicle-monitoring-backend
```

---

### ENV
Specifies the runtime environment.  
For local development, this can be set to `dev`.

Example:
```
ENV=dev
```

---

### FIREBASE
This field requires the **Firebase Admin SDK JSON credentials** used for verifying authentication tokens.

#### Steps to Obtain Firebase Admin JSON
1. Go to Firebase Console  
   https://console.firebase.google.com  
2. Select your project  
3. Click **Project Settings** (gear icon)  
4. Go to **Service Accounts** tab  
5. Click **Generate new private key**  
6. Download the JSON file  
7. Copy the entire JSON content and paste it as the value of `FIREBASE`

Example:
```
FIREBASE={"type":"service_account","project_id":"..."}
```

---

### MONGO_URI
MongoDB connection string obtained from MongoDB Atlas.

#### Steps to Obtain MongoDB URI
1. Go to MongoDB Atlas  
   https://cloud.mongodb.com  
2. Create a new project  
3. Create a cluster (free tier is sufficient)  
4. Create a database user (username & password)  
5. Go to **Database → Connect**  
6. Choose **Drivers**  
7. Copy the connection string  

Example:
```
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/
```

---

### MONGO_DB_NAME
Name of the database where collections will be stored.

You can choose any name. MongoDB will create it automatically on first write.

Example:
```
MONGO_DB_NAME=vehicle_monitoring
```

---

### ADMIN_SECRET_KEY
A secret key used by dealership administrators when generating new vehicle IDs.  
Only authorized dealership personnel should know this value.

Example:
```
ADMIN_SECRET_KEY=mySecureDealerKey123
```

This key must be sent in the `x-admin-key` header when calling the vehicle generation endpoint.

## 4. Create Virtual Environment (Recommended)

```bash
python -m venv venv
```

Activate the environment

**Windows**
```bash
venv\Scripts\activate
```

**Linux / Mac**
```bash
source venv/bin/activate
```

## 5. Install Dependencies

```bash
pip install -r requirements.txt
```

## 6. Run Backend Server

```bash
uvicorn app.main:app --reload
```

Backend will start at:

```
http://127.0.0.1:8000
```

---

# Frontend Setup and Run

## 7. Navigate to Frontend Folder

Open a new terminal:

```bash
cd Fog-Based-Vehicle-Monitoring/Code/frontend
```

## 8. Create Environment File

Create a `.env` file in the frontend root and copy values from `.env.example`

```
VITE_FIREBASE_API_KEY=
VITE_FIREBASE_AUTH_DOMAIN=
VITE_FIREBASE_PROJECT_ID=
VITE_FIREBASE_STORAGE_BUCKET=
VITE_FIREBASE_MESSAGING_SENDER_ID=
VITE_FIREBASE_APP_ID=
VITE_FIREBASE_MEASUREMENT_ID=
VITE_API_BASE_URL=
```

Fill in the Firebase configuration values.
Each parameter corresponds to Firebase project configuration.

---

### How to Obtain Firebase Configuration Values

1. Go to Firebase Console  
   https://console.firebase.google.com  

2. Select your Firebase project  

3. Click **Project Settings** (gear icon)

4. Under **General** tab, scroll to **Your Apps**

5. Click **Add App → Web App** (if not already created)

6. Register the app with any name

7. Firebase will show configuration values like:

```
const firebaseConfig = {
  apiKey: "XXXX",
  authDomain: "XXXX",
  projectId: "XXXX",
  storageBucket: "XXXX",
  messagingSenderId: "XXXX",
  appId: "XXXX",
  measurementId: "XXXX"
};
```
`VITE_API_BASE_URL` - Deployed Backend Base URL can be local URL too if backend running locally.
## 9. Install Dependencies

```bash
npm install
```

## 10. Run Frontend Development Server

```bash
npm run dev
```

Frontend will start at:

```
http://localhost:5173
```

---

# Running Order

1. Start Backend Server first  
2. Start Frontend Server  
3. Open browser and navigate to frontend URL  
4. Ensure backend API URL is correctly configured in frontend environment variables  

