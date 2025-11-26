# 🔍 Bloom Filter - Quote Search Engine

Un web site interactiv care demonstrează utilizarea unui **Bloom Filter** implementat în Python, cu o interfață modernă în React + Vite.

## 📋 Caracteristici

- ✅ **Pagină de Logare** - Autentificare utilizator cu token-based sessions
- 📚 **Adăugare Cărți** - Upload de fișiere .txt și indexare cu Bloom Filter
- 🔎 **Căutare Citate** - Căutare în baza de date folosind Bloom Filter
- ➕ **Adăugare Citații Manual** - Adăugare citații direct din interfață
- 📊 **Dashboard** - Vizualizare statistici despre Bloom Filter și cărțile încărcate
- 🎨 **Interfață Modernă** - Design responsive și intuitiv

## 🛠️ Tehnologii Utilizate

### Backend
- **FastAPI** - API server rapid și modern
- **Python 3.11+** - Limbaj de programare (3.11 or 3.12 recommended)
- **mmh3** - Hash functions pentru Bloom Filter
- **Pydantic** - Validarea datelor
- **SQLAlchemy** - ORM (pentru extensii viitoare)

### Frontend
- **React 19** - Framework JavaScript
- **Vite** - Build tool rapid
- **CSS3** - Styling modern cu gradienți și animații
- **Fetch API** - Comunicare cu backend-ul

## 📦 Instalare

### Backend

1. Mergi în directorul backend:
```bash
cd backend
```

2. Creează un virtual environment (optional, dar recomandat):
```bash
python -m venv .venv
# Windows (PowerShell)
. .venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate
```

3. Instalează dependențele:
```bash
python -m pip install -U pip
python -m pip install -r requirements.txt
```

4. Pornește serverul:
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Serverul va fi disponibil la: `http://localhost:8000`

### Frontend

1. Mergi în directorul frontend:
```bash
cd frontend
```

2. Instalează dependențele:
```bash
npm install
```

3. Pornește serverul de development:
```bash
npm run dev
```

Aplicația va fi disponibilă la: `http://localhost:5173`

## 🚀 Utilizare

### 1. Logare
- Mergi la login page
- Folosește credentialele demo:
  - **Username**: `demo`
  - **Password**: `demo123`
  - Sau creează un cont nou (modifica `users_db` în `main.py`)

### 2. Adăugare Cărți
- Click pe "📚 Add Book"
- Selectează un fișier .txt
- Introdu titlul cărții
- Click "Upload Book"
- Cartea va fi indexată cu Bloom Filter

### 3. Căutare Citate
- Click pe "🔎 Search Quotes"
- Introdu textul pe care dorești să-l cauți
- Click "🔍 Search Quote"
- Vei primi rezultatul: "Gasit" sau "NU gasit"

### 4. Adăugare Citații Manual
- În pagina de căutare, click "➕ Add Quote"
- Introdu titlul cărții
- Citația va fi adăugată în Bloom Filter

## 🔧 Structura Proiectului

```
BloomFilter/
├── backend/
│   ├── main.py              # API endpoints FastAPI
│   ├── bloom_filter.py      # Implementare Bloom Filter
│   ├── pyproject.toml       # Dependențe Python
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Componenta principală
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── AddBook.jsx
│   │   │   └── SearchQuotes.jsx
│   │   ├── components/
│   │   │   └── NavBar.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── README.md
│
└── README.md (acest fișier)
```

## 💡 Cum Funcționează Bloom Filter

### Avantaje
- ⚡ **Viteză** - Verificarea prezenței în O(k) unde k = numărul de hash functions
- 💾 **Spațiu** - Folosește mult mai puțin spațiu decât o hash table normală
- 🎯 **Fără false negatives** - Dacă cuvântul NU e găsit, sigur NU e în set

### Dezavantaje
- ⚠️ **False positives** - Poate spune că e prezent ceva ce NU e
- ❌ **Ștergere** - Nu poți șterge elemente (doar în variante speciale)

### Exemplu
```python
bf = BloomFilter(size=10000, num_hashes=3)
bf.add("Hello World", "Book1")

# Cautare
if bf.possibly_contains("Hello World"):
    print("Posibil gasit")  # ✅ Corect
else:
    print("Sigur NU gasit")

if bf.possibly_contains("Goodbye World"):
    print("Posibil gasit")  # Posibil false positive
else:
    print("Sigur NU gasit")  # ✅ Corect
```

## 📊 Statistici Bloom Filter

Dashboard-ul afișează:
- **Total Books** - Numărul de cărți încărcate
- **Total Quotes** - Numărul de citații indexate
- **Filter Size** - Dimensiunea bit array-ului
- **Bits Set** - Numărul de biți setați la 1
- **Fill %** - Procentul de umplere al filtrului
- **Hash Functions** - Numărul de funcții hash utilizate

## 🔐 Securitate

**Nota**: Aceasta este o implementare de demonstrație. Pentru producție:
- Stochează parolele cu hash (bcrypt, argon2)
- Folosește JWT tokens în loc de stringuri simple
- Implementează rate limiting
- Valideaza input-ul mai riguros
- Folosește HTTPS

## 🐛 Troubleshooting

### Backend nu se conectează
- Verifică dacă FastAPI rulează pe `http://localhost:8000`
- Verifică CORS settings în `main.py`
- Asigură-te că portul 8000 nu este ocupat

### Frontend nu se conectează la backend
- Verifică URL-ul API (ar trebui să fie `http://localhost:8000`)
- Verifica Network tab în DevTools
- Asigură-te că ambele servere rulează

### Upload fișier eșuează
- Verifică că fișierul este .txt
- Verifica că fișierul nu e prea mare
- Verifica console-ul backend pentru erori

## 📝 Licență

MIT License - siți liber să modifici și distribuiți

## 👨‍💻 Autor

Creat pentru demonstrația structurii de date Bloom Filter în cadrul cursului de POO și SDA.

---

**Divertisment în codare! 🚀**
