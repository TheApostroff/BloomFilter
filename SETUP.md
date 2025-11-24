# Instrucțiuni de rulare a Bloom Filter Quote Search Engine

## Pentru Windows (PowerShell)

### 1. Terminal 1 - Backend

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Terminal 2 - Frontend

```powershell
cd frontend
npm install
npm run dev
```

## Pentru macOS/Linux

### 1. Terminal 1 - Backend

```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Terminal 2 - Frontend

```bash
cd frontend
npm run dev
```

## Acces

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Credențiale Demo

- **Username**: demo
- **Password**: demo123

## Fișiere Teste

Poți folosi orice fișier .txt pentru testing. Exemple:
- Shakespeare quotes
- Gutenberg Project books
- Propriile fișiere text

---

Odată ce ambele servere rulează, acces frontend-ul și logheaza-te cu credentialele demo!
