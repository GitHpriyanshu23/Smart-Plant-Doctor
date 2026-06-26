# Smart Plant Doctor

**Smart Plant Doctor** is an AI + IoT plant health platform that combines real-time environmental sensing from ESP32 devices with image-based disease detection and an AI plant care assistant.

Upgraded from the original [Streamlit prototype](app.py) to a full-stack **React + FastAPI** application with Supabase authentication, live WebSocket dashboards, and a production-ready API.

## Demo

<video src="docs/demo.mp4" controls width="100%"></video>

[Download demo video](docs/demo.mp4)

## What's New (Major Upgrades)

| Feature | Before (v1) | Now (v2) |
|---------|---------------|----------|
| Frontend | Streamlit | **React + TypeScript + Vite PWA** |
| Backend | Single `ingest.py` | **FastAPI** with modular routers |
| Auth | None | **Supabase** (email + Google OAuth) |
| Database | SQLite only | **PostgreSQL (Supabase)** or SQLite for local dev |
| Dashboard | Basic charts | **Live metrics, charts, care recommendations, demo mode** |
| Disease detection | Streamlit upload | **Drag-and-drop UI** with treatment cards + history |
| Chat | — | **Gemma 4 AI assistant** with optional plant context |
| Encyclopedia | — | **6 species** with care guides, seasonal tips, diseases |
| Devices | Basic ESP32 ingest | **Device onboarding, multi-pot support, WebSockets** |
| Community | — | **Disease map** (anonymized geohash reports) |
| Landing page | — | **Modern glassmorphism landing** with feature showcase |

## Highlights

- **Real-time IoT dashboard** — temperature, humidity, light, soil moisture, plant health score
- **AI disease detection** — trained MobileNetV2 model, 29 classes, ~92.37% accuracy
- **Plant care chatbot** — Gemma 4 powered assistant with live sensor context
- **Plant encyclopedia** — care guides for Rose, Hibiscus, Aloe Vera, Money Plant, Chrysanthemum, Turmeric
- **Care journal** — log watering, fertilizing, and repotting events
- **Device onboarding** — register ESP32 sensors and stream live readings
- **Disease map** — crowdsourced plant health reports

## Architecture

```
ESP32 Sensors
  → POST /api/v1/ingest (device token)
  → FastAPI backend
  → PostgreSQL / SQLite
  → WebSocket → React dashboard

Leaf image upload
  → POST /api/v1/diagnose
  → MobileNetV2 (ai/inference.py)
  → Disease + confidence + treatment recommendations

Plant care question
  → POST /api/v1/chat
  → Gemma 4 (Google AI)
  → Contextual advice with sensor + diagnosis data
```

## AI Model (Plant Disease Detection)

### Model used

- **Backbone:** MobileNetV2 (PyTorch)
- **Inference:** `SmartPlantDoctor` in `ai/inference.py`
- **Input size:** 224 × 224
- **Output:** 29 plant disease / healthy classes
- **Validation accuracy:** ~92.37%

### Supported plants

| Plant | Disease classes |
|-------|-----------------|
| Rose | 8 |
| Hibiscus | 4 |
| Aloe Vera | 5 |
| Money Plant | 4 |
| Chrysanthemum | 3 |
| Turmeric | 5 |

### Exported artifacts

- `ai/exports/smart_plant_doctor_model.pth`
- `ai/exports/class_mapping.json`

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React, TypeScript, Vite, Tailwind CSS, TanStack Query |
| Backend | FastAPI, SQLAlchemy, Alembic |
| Auth | Supabase (JWT + Google OAuth) |
| Database | PostgreSQL (Supabase) / SQLite (local) |
| AI / ML | PyTorch, MobileNetV2 |
| LLM Chat | Google Gemma 4 via Gemini API |
| IoT | ESP32, PlatformIO, WebSockets |
| Maps | Leaflet (disease map) |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase project (for auth) — see [docs/SUPABASE_SETUP.md](docs/SUPABASE_SETUP.md)

### 1. Clone

```bash
git clone https://github.com/GitHpriyanshu23/Smart-Plant-Doctor.git
cd Smart-Plant-Doctor
```

### 2. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env   # configure DATABASE_URL, SUPABASE_*, GEMINI_API_KEY
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
cp .env.example .env      # add VITE_SUPABASE_URL + VITE_SUPABASE_ANON_KEY
npm install
npm run dev
```

Open **http://localhost:5173** — landing page → sign in → dashboard.

### Environment variables

**Backend** (`backend/.env`):

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string or `sqlite:////tmp/smart_plant_doctor.db` |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_JWT_SECRET` | Supabase JWT secret (Settings → API) |
| `GEMINI_API_KEY` | Google AI API key for chat |
| `MODEL_PATH` | Path to `smart_plant_doctor_model.pth` |

**Frontend** (`frontend/.env`):

| Variable | Description |
|----------|-------------|
| `VITE_SUPABASE_URL` | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon key |

## ESP32 Firmware

Updated firmware in `firmware/` with NVS token storage and multi-pot sensor support.

```bash
cd firmware
# Set WIFI_SSID, WIFI_PASSWORD in platformio.ini or src/main.cpp
pio run -t upload
```

Register your device in the app UI, then claim it with the device token.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/plants` | List user's plants |
| `POST` | `/api/v1/plants` | Add a plant |
| `POST` | `/api/v1/diagnose` | Upload leaf image for disease detection |
| `GET` | `/api/v1/diagnose/history` | Diagnosis history |
| `POST` | `/api/v1/chat` | AI plant care chat |
| `GET` | `/api/v1/encyclopedia` | Species care guides |
| `POST` | `/api/v1/ingest` | ESP32 sensor data (device token) |
| `WS` | `/api/v1/ws/plants/{id}` | Live sensor feed |

## Deployment

| Component | Platform |
|-----------|----------|
| Frontend | [Vercel](https://vercel.com) |
| Backend | [Railway](https://railway.app) / [Render](https://render.com) |
| Database + Auth | [Supabase](https://supabase.com) |

## Legacy Streamlit App

The original Streamlit prototype is preserved at `app.py` for reference. The new app is the recommended version.

## Project Structure

```
smart-plant-doctor/
├── frontend/          # React PWA
├── backend/           # FastAPI API
├── ai/                # ML model + training
├── firmware/          # ESP32 PlatformIO project
├── docs/              # Setup guides + demo video
└── app.py             # Legacy Streamlit app
```

## License

MIT

## Author

[Priyanshu](https://github.com/GitHpriyanshu23)
