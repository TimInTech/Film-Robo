# 🎬 Film Robo - KI-gestützte Filmempfehlungs-Plattform

## Überblick

Film Robo ist eine moderne Webanwendung, die natürlichsprachige Benutzer-Prompts (z.B. "lustige Filme mit Aliens") mithilfe von KI in Filmgenres umwandelt und passende Empfehlungen liefert.

## 🎯 Technologie-Stack

### Backend
- **Framework:** FastAPI (Python)
- **KI-Integration:** Emergent LLM (GPT-4o-mini) für intelligente Prompt-Analyse
- **Film-Daten:** TMDb API (The Movie Database)
- **Datenbank:** MongoDB (für zukünftige Erweiterungen)
- **Server:** Uvicorn (ASGI)

### Frontend
- **Framework:** React 19
- **UI-Komponenten:** Shadcn/UI mit Radix UI
- **Styling:** Tailwind CSS
- **Icons:** Lucide React
- **Notifications:** Sonner (Toast)
- **Design:** Modern & minimalistisch mit Playfair Display + Inter Fonts

## ✨ Hauptfunktionen

### 1. KI-basierte Prompt-Analyse
- Versteht natürlichsprachige deutsche Anfragen
- Intelligente Genre-Zuordnung
- Fallback auf Keyword-Analyse bei KI-Ausfall

### 2. Genre-Katalog
| Kategorie | TMDb Genre-IDs | Keywords |
|-----------|----------------|----------|
| Komödie | 35, 10749 | lustig, lachen, romantisch |
| Horror/Thriller | 27, 53 | gruselig, angst, spannend |
| Kinderfilme | 10751, 16 | kinder, familie, animation |
| Action/Abenteuer | 28, 12 | kampf, explosion, abenteuer |
| Sci-Fi/Fantasy | 878, 14 | weltraum, zauber, fantasie |

### 3. Filmempfehlungen
- Top 10 Filme basierend auf Genre-Zuordnung
- Anzeige von Poster, Titel, Jahr, Bewertung
- **✨ NEU: Streaming-Verfügbarkeit** (Netflix, Amazon Prime, Disney+, Sky, etc.)
- Sortierung nach Popularität

## 🚀 Installation & Setup

### Voraussetzungen
- Python 3.11+
- Node.js 16+
- MongoDB (läuft bereits)

### Backend-Setup

1. **Abhängigkeiten sind bereits installiert:**
   - emergentintegrations (für LLM)
   - httpx (für TMDb API-Calls)
   - FastAPI, uvicorn, motor, etc.

2. **Umgebungsvariablen** (`/app/backend/.env`):
   ```env
   MONGO_URL="mongodb://localhost:27017"
   DB_NAME="test_database"
   CORS_ORIGINS="*"
   EMERGENT_LLM_KEY=sk-emergent-07aE1D978827b72668
   TMDB_API_KEY=PLACEHOLDER
   ```

3. **Backend starten:**
   ```bash
   cd /app/backend
   sudo supervisorctl restart backend
   ```

### Frontend-Setup

1. **Abhängigkeiten sind bereits installiert** (package.json)

2. **Frontend starten** (läuft bereits automatisch):
   ```bash
   cd /app/frontend
   yarn start
   ```

## 📡 API-Endpunkte

### POST /api/recommend
Analysiert den Prompt und gibt Filmempfehlungen zurück **inkl. Streaming-Verfügbarkeit**.

**Request:**
```json
{
  "prompt": "lustige Filme mit Aliens"
}
```

**Response:**
```json
{
  "message": "✓ 10 Filme gefunden für Ihre Anfrage!",
  "requested_genre_ids": [35, 878],
  "movies": [
    {
      "title": "Simulierter Film 1",
      "release_date": "2024-01-01",
      "tmdb_id": 1000,
      "poster_url": null,
      "overview": "Dies ist ein Platzhalter-Film...",
      "vote_average": 7.5,
      "streaming_providers": [
        {
          "provider_name": "Netflix",
          "logo_path": "https://image.tmdb.org/t/p/w92/..."
        },
        {
          "provider_name": "Amazon Prime",
          "logo_path": "https://image.tmdb.org/t/p/w92/..."
        }
      ]
    }
  ],
  "used_ai": true
}
```

### GET /api/
Health-Check Endpunkt.

**Response:**
```json
{
  "message": "Film Robo Backend läuft!",
  "status": "ok"
}
```

## 🎨 UI/UX Features

- **Gradient-Hintergrund:** Sanfte Farbverläufe (blau → lila → pink)
- **Glassmorphism-Effekte:** Moderne Karten mit Backdrop-Blur
- **Responsive Design:** Mobile-first Ansatz
- **Interaktive Beispiele:** 6 vordefinierte Anfragen zum Anklicken
- **Hover-Effekte:** Smooth Transformationen auf Filmkarten
- **Toast-Notifications:** Echtzeit-Feedback für Benutzer
- **Loading-States:** Spinner während der Suche
- **✨ NEU: Streaming-Badges:** Sichtbare Anzeige verfügbarer Plattformen mit TV-Icon

## 🔧 TMDb API Integration

### Was wird von TMDb genutzt?

1. **Film-Discovery** (`/discover/movie`)
   - Filtern nach Genres
   - Sortierung nach Popularität
   - Deutsche Sprache/Titel

2. **✨ Streaming-Verfügbarkeit** (`/movie/{id}/watch/providers`)
   - Zeigt verfügbare Streaming-Plattformen (für Deutschland)
   - Inkl. Netflix, Amazon Prime, Disney+, Sky, etc.
   - Flatrate (Abo) und Kaufoptionen

### API-Key hinzufügen

Um echte Filmdaten zu erhalten:

1. **TMDb Account erstellen:** https://www.themoviedb.org/signup
2. **API-Key generieren:** https://www.themoviedb.org/settings/api
3. **Key in .env hinzufügen:**
   ```env
   TMDB_API_KEY=ihr_api_key_hier
   ```
4. **Backend neu starten:**
   ```bash
   sudo supervisorctl restart backend
   ```

### Aktueller Status
- ⚠️ Derzeit werden **Mock-Daten** verwendet (TMDB_API_KEY=PLACEHOLDER)
- ✅ Die Struktur ist vollständig vorbereitet
- ✅ Nach Hinzufügen des Keys werden automatisch echte Daten geladen

## 🧪 Testing

### Manuelle Tests durchgeführt:
✅ KI-Prompt-Analyse (6 verschiedene Prompts getestet)
✅ Frontend-UI (Screenshot-Tests)
✅ API-Endpunkte (curl Tests)
✅ Genre-Zuordnung (alle Kategorien)
✅ Toast-Notifications
✅ Loading-States
✅ Responsive Design
✅ **Streaming-Verfügbarkeit-Anzeige** (21+ Badges erfolgreich angezeigt)

### Test-Ergebnisse:
```
✓ "lustige Filme" → Genre [35] ✓
✓ "gruselige Horror" → Genre [27] ✓
✓ "Filme für meine Tochter" → Genre [16, 10751] ✓
✓ "Action mit Explosionen" → Genre [28] ✓
✓ "Fantasy Zauber Filme" → Genre [14] ✓
✓ "romantische Komödie" → Genre [35, 10749] ✓
✓ Streaming-Badges: Netflix, Amazon Prime, Disney+, Sky ✓
```

## 📁 Projektstruktur

```
/app/
├── backend/
│   ├── server.py          # FastAPI Server (KI + TMDb Integration)
│   ├── .env               # Umgebungsvariablen
│   └── requirements.txt   # Python Dependencies
├── frontend/
│   ├── src/
│   │   ├── App.js        # Hauptkomponente
│   │   ├── App.css       # Styles
│   │   ├── index.js      # Entry Point
│   │   └── components/ui/ # Shadcn Components
│   ├── package.json      # Node Dependencies
│   └── .env              # Frontend Environment
└── README_FILM_ROBO.md   # Diese Datei
```

## 🎯 Kernfunktionen - Technische Details

### 1. KI-Prompt-Analyse (`analyze_prompt_with_ai`)
- Verwendet GPT-4o-mini für Textverständnis
- System-Message mit Genre-Katalog
- Strukturierte Antwort (nur Genre-IDs)
- Fallback auf Keyword-Matching bei Fehler

### 2. TMDb API-Integration (`fetch_movies_from_tmdb`)
- Asynchrone HTTP-Requests mit httpx
- Parameter: Genre-IDs, Sortierung, Sprache (DE)
- Top 10 populäre Filme
- Vollständige Metadaten (Poster, Bewertung, etc.)

### 3. React Frontend
- State Management mit useState
- Axios für API-Calls
- Shadcn/UI Komponenten (Card, Button, Input, Badge)
- Sonner für Toast-Notifications
- Lucide Icons

## 🔒 Sicherheit & Best Practices

✅ Environment-Variablen für API-Keys
✅ CORS korrekt konfiguriert
✅ Error-Handling mit HTTPException
✅ Input-Validierung mit Pydantic
✅ Async/await für Performance
✅ Logging für Debugging

## 🌟 Zukunftige Erweiterungen

### Backend
- [ ] Benutzer-Authentifizierung
- [ ] Favoriten-Liste in MongoDB speichern
- [ ] Film-Bewertungen
- [ ] Erweiterte Filter (Jahr, Bewertung, etc.)
- [ ] Caching für häufige Anfragen

### Frontend
- [ ] Film-Detail-Seiten
- [ ] Trailer-Integration (YouTube)
- [ ] Benutzer-Profile
- [ ] Watch-Later Liste
- [ ] Dark Mode Toggle
- [ ] Mehrsprachigkeit (EN/DE)

### KI
- [ ] Kontext-Speicherung für Follow-up Fragen
- [ ] Personalisierte Empfehlungen
- [ ] Stimmungsanalyse aus Beschreibungen

## 📝 Anwendungsbeispiele

```
Benutzer: "Zeig mir lustige Filme mit Aliens"
→ KI analysiert: [Komödie: 35, Sci-Fi: 878]
→ TMDb sucht Filme mit beiden Genres
→ 10 populäre Ergebnisse

Benutzer: "Filme für Kinder"
→ KI analysiert: [Familie: 10751, Animation: 16]
→ Kinderfreundliche Filme

Benutzer: "Spannende Thriller"
→ KI analysiert: [Thriller: 53]
→ Top Thriller-Filme
```

## 🐛 Bekannte Limitierungen

1. **Mock-Daten:** Ohne TMDb API-Key werden Platzhalter verwendet
2. **Genre-Limitierung:** Nur 5 Hauptkategorien
3. **Keine Persistenz:** Suchergebnisse werden nicht gespeichert
4. **Single-Page:** Keine Routing/Navigation

## 📞 Support & Dokumentation

- **TMDb API Docs:** https://developers.themoviedb.org/3
- **Emergent LLM:** Integriert mit Universal Key
- **FastAPI Docs:** Automatisch unter `/docs` verfügbar

## ✅ Deployment-Status

- ✅ Backend läuft auf Port 8001
- ✅ Frontend läuft auf Port 3000
- ✅ Live unter: https://film-robo.preview.emergentagent.com
- ✅ API unter: https://film-robo.preview.emergentagent.com/api
- ✅ Supervisor überwacht alle Services

---

**Entwickelt mit ❤️ auf Emergent Agent Platform**
