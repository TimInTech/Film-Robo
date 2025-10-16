from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import httpx
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Film Robo Backend")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Environment variables
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')
TMDB_API_KEY = os.environ.get('TMDB_API_KEY', 'PLACEHOLDER')
TMDB_BASE_URL = "https://api.themoviedb.org/3"

# Genre-Katalog (Kern der Logik)
GENRE_CATEGORIES = {
    'Komödie': [35, 10749],
    'Horror/Thriller': [27, 53],
    'Kinderfilme': [10751, 16],
    'Action/Abenteuer': [28, 12],
    'Sci-Fi/Fantasy': [878, 14],
}

# Pydantic Models
class PromptRequest(BaseModel):
    """Modell für die Eingabe des Benutzers"""
    prompt: str = Field(..., example="Zeig mir lustige Filme")

class Movie(BaseModel):
    """Modell für einen Film"""
    title: str
    release_date: Optional[str] = None
    tmdb_id: int
    poster_url: Optional[str] = None
    overview: Optional[str] = None
    vote_average: Optional[float] = None

class RecommendationResponse(BaseModel):
    """Modell für die API-Antwort"""
    message: str
    requested_genre_ids: List[int]
    movies: List[Movie]
    used_ai: bool = False

# KI-basierte Prompt-Analyse
async def analyze_prompt_with_ai(prompt: str) -> List[int]:
    """
    Verwendet KI (Emergent LLM) um den Prompt zu analysieren und Genre-IDs zurückzugeben.
    """
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"film-robo-{uuid.uuid4()}",
            system_message="""Du bist ein Filmexperte, der Benutzer-Wünsche analysiert.
            
Deine Aufgabe: Analysiere den Benutzer-Prompt und ordne ihn den passenden Film-Genres zu.
            
Verfügbare Genre-Kategorien:
            - Komödie: Lustige Filme, romantische Komödien, Humor (Genre-IDs: 35, 10749)
            - Horror/Thriller: Gruselige, spannende, angsteinflößende Filme (Genre-IDs: 27, 53)
            - Kinderfilme: Familienfilme, Animationsfilme für Kinder (Genre-IDs: 10751, 16)
            - Action/Abenteuer: Action, Kampf, Abenteuer, Reisen (Genre-IDs: 28, 12)
            - Sci-Fi/Fantasy: Science Fiction, Weltraum, Fantasy, Zauber (Genre-IDs: 878, 14)
            
Antworte NUR mit einer kommagetrennten Liste der passenden Genre-IDs.
            Beispiel: Wenn der Benutzer nach lustigen Alien-Filmen fragt, antworte: 35,878
            Antworte NICHTS anderes, nur die Zahlen!"""
        ).with_model("openai", "gpt-4o-mini")
        
        user_message = UserMessage(text=f"Analysiere diesen Film-Wunsch: '{prompt}'")
        response = await chat.send_message(user_message)
        
        # Parse die Genre-IDs aus der Antwort
        genre_ids = []
        for part in response.split(','):
            try:
                genre_id = int(part.strip())
                genre_ids.append(genre_id)
            except ValueError:
                continue
        
        return list(set(genre_ids))
    
    except Exception as e:
        logging.error(f"KI-Analyse fehlgeschlagen: {e}")
        # Fallback auf Keyword-Analyse
        return analyze_prompt_fallback(prompt)

# Fallback Keyword-Analyse
def analyze_prompt_fallback(prompt: str) -> List[int]:
    """
    Einfache Keyword-basierte Analyse als Fallback.
    """
    lower_prompt = prompt.lower()
    found_genres = []

    if any(keyword in lower_prompt for keyword in ['lustig', 'lachen', 'komödie', 'romantisch']):
        found_genres.extend(GENRE_CATEGORIES['Komödie'])
    if any(keyword in lower_prompt for keyword in ['gruselig', 'angst', 'horror', 'thriller', 'spannend']):
        found_genres.extend(GENRE_CATEGORIES['Horror/Thriller'])
    if any(keyword in lower_prompt for keyword in ['kinder', 'familie', 'animation']):
        found_genres.extend(GENRE_CATEGORIES['Kinderfilme'])
    if any(keyword in lower_prompt for keyword in ['kampf', 'explosion', 'action', 'abenteuer', 'reise']):
        found_genres.extend(GENRE_CATEGORIES['Action/Abenteuer'])
    if any(keyword in lower_prompt for keyword in ['weltraum', 'zauber', 'fantasie', 'science fiction', 'alien']):
        found_genres.extend(GENRE_CATEGORIES['Sci-Fi/Fantasy'])

    return list(set(found_genres))

# TMDb API-Kommunikation
async def fetch_movies_from_tmdb(genre_ids: List[int]) -> List[Movie]:
    """
    Ruft Filme von der TMDb API ab.
    """
    if TMDB_API_KEY == 'PLACEHOLDER':
        # Mock-Daten wenn kein API-Key
        logging.warning("Verwende Mock-Daten. Bitte TMDB_API_KEY setzen.")
        return [
            Movie(
                title=f"Simulierter Film {i+1}",
                release_date="2024-01-01",
                tmdb_id=1000 + i,
                overview="Dies ist ein Platzhalter-Film. Fügen Sie einen TMDb API-Schlüssel hinzu für echte Daten.",
                vote_average=7.5 + (i * 0.1)
            )
            for i in range(10)
        ]
    
    # Echte TMDb API-Anfrage
    try:
        genres_string = ','.join(map(str, genre_ids))
        params = {
            'api_key': TMDB_API_KEY,
            'with_genres': genres_string,
            'sort_by': 'popularity.desc',
            'language': 'de-DE',
            'page': 1
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{TMDB_BASE_URL}/discover/movie", params=params)
            response.raise_for_status()
            data = response.json()
        
        movies = []
        for result in data.get('results', [])[:10]:
            poster_path = result.get('poster_path')
            movies.append(Movie(
                title=result.get('title'),
                release_date=result.get('release_date'),
                tmdb_id=result.get('id'),
                poster_url=f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None,
                overview=result.get('overview'),
                vote_average=result.get('vote_average')
            ))
        
        return movies
    
    except Exception as e:
        logging.error(f"TMDb API-Fehler: {e}")
        raise HTTPException(status_code=500, detail="Fehler bei der TMDb API-Kommunikation")

# Hauptendpunkt
@api_router.post("/recommend", response_model=RecommendationResponse)
async def get_recommendations(request: PromptRequest):
    """
    Verarbeitet den Benutzer-Prompt und gibt Filmempfehlungen zurück.
    """
    logging.info(f"Empfangen: {request.prompt}")
    
    # KI-basierte Analyse
    genre_ids = await analyze_prompt_with_ai(request.prompt)
    used_ai = True
    
    if not genre_ids:
        return RecommendationResponse(
            message="Konnte keine passenden Genres finden. Versuchen Sie es mit: lustig, spannend, Kinder, Action oder Fantasy.",
            requested_genre_ids=[],
            movies=[],
            used_ai=used_ai
        )
    
    # Filme von TMDb abrufen
    movies = await fetch_movies_from_tmdb(genre_ids)
    
    return RecommendationResponse(
        message=f"✓ {len(movies)} Filme gefunden für Ihre Anfrage!",
        requested_genre_ids=genre_ids,
        movies=movies,
        used_ai=used_ai
    )

# Health Check
@api_router.get("/")
async def root():
    return {"message": "Film Robo Backend läuft!", "status": "ok"}

# Include router
app.include_router(api_router)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()