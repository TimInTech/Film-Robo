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
from typing import Tuple
try:
    from openai import AsyncOpenAI  # type: ignore
except Exception:
    AsyncOpenAI = None  # Optional dependency

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
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
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

class StreamingProvider(BaseModel):
    """Modell für einen Streaming-Anbieter"""
    provider_name: str
    logo_path: Optional[str] = None

class Movie(BaseModel):
    """Modell für einen Film"""
    title: str
    release_date: Optional[str] = None
    tmdb_id: int
    poster_url: Optional[str] = None
    overview: Optional[str] = None
    vote_average: Optional[float] = None
    streaming_providers: List[StreamingProvider] = []

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
        if not OPENAI_API_KEY or AsyncOpenAI is None:
            raise RuntimeError("OpenAI nicht konfiguriert")
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        system = (
            "Du bist ein Filmexperte. Analysiere den Benutzer-Prompt und gib NUR eine kommagetrennte Liste "
            "von passenden TMDb Genre-IDs zurück. Kategorien: "
            "Komödie(35,10749), Horror/Thriller(27,53), Kinderfilme(10751,16), Action/Abenteuer(28,12), Sci-Fi/Fantasy(878,14). "
            "Beispiel: lustige Alien-Filme → 35,878. Keine weiteren Wörter."
        )
        msg_user = f"Analysiere diesen Film-Wunsch: '{prompt}'"
        chat = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": msg_user},
            ],
            temperature=0,
        )
        content = chat.choices[0].message.content if chat.choices else ""
        genre_ids: List[int] = []
        for part in (content or "").split(','):
            try:
                genre_ids.append(int(part.strip()))
            except Exception:
                continue
        return list(set(genre_ids))
    except Exception as e:
        logging.warning(f"KI-Analyse nicht verfügbar, nutze Fallback: {e}")
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

# TMDb API-Kommunikation: Streaming-Verfügbarkeit
async def fetch_streaming_providers(movie_id: int) -> List[StreamingProvider]:
    """
    Ruft Streaming-Verfügbarkeit für einen Film ab (für Deutschland).
    """
    if TMDB_API_KEY == 'PLACEHOLDER':
        # Mock-Daten
        mock_providers = ['Netflix', 'Amazon Prime', 'Disney+', 'Sky']
        import random
        selected = random.sample(mock_providers, k=random.randint(1, 3))
        return [StreamingProvider(provider_name=p, logo_path=None) for p in selected]

    try:
        params = {'api_key': TMDB_API_KEY}

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{TMDB_BASE_URL}/movie/{movie_id}/watch/providers",
                params=params
            )
            response.raise_for_status()
            data = response.json()

        # Deutsche Streaming-Anbieter (DE)
        providers_data = data.get('results', {}).get('DE', {})

        # Flatrate = Subscription-Streaming (Netflix, Prime, etc.)
        flatrate = providers_data.get('flatrate', [])

        streaming_providers = []
        for provider in flatrate:
            streaming_providers.append(StreamingProvider(
                provider_name=provider.get('provider_name'),
                logo_path=f"https://image.tmdb.org/t/p/w92{provider.get('logo_path')}" if provider.get('logo_path') else None
            ))

        return streaming_providers

    except Exception as e:
        logging.warning(f"Streaming-Provider-Fehler für Film {movie_id}: {e}")
        return []

# TMDb API-Kommunikation: Filme abrufen mit PARALLELER Streaming-Verfügbarkeit
async def fetch_movies_from_tmdb(genre_ids: List[int]) -> List[Movie]:
    """
    Ruft Filme von der TMDb API ab inkl. Streaming-Verfügbarkeit.
    OPTIMIERT: Streaming-Provider werden parallel abgerufen (asyncio.gather).
    """
    if TMDB_API_KEY == 'PLACEHOLDER':
        # Mock-Daten wenn kein API-Key
        logging.warning("Verwende Mock-Daten. Bitte TMDB_API_KEY setzen.")

        # Erstelle Mock-Filme
        mock_movies = []
        for i in range(10):
            mock_movies.append({
                'title': f"Simulierter Film {i+1}",
                'release_date': "2024-01-01",
                'tmdb_id': 1000 + i,
                'overview': "Dies ist ein Platzhalter-Film. Fügen Sie einen TMDb API-Schlüssel hinzu für echte Daten.",
                'vote_average': 7.5 + (i * 0.1)
            })

        # PARALLEL: Alle Streaming-Provider auf einmal abrufen
        import asyncio
        streaming_tasks = [fetch_streaming_providers(movie['tmdb_id']) for movie in mock_movies]
        streaming_results = await asyncio.gather(*streaming_tasks)

        # Movies mit Streaming-Daten zusammenführen
        movies = []
        for movie_data, providers in zip(mock_movies, streaming_results):
            movies.append(Movie(**movie_data, streaming_providers=providers))

        return movies

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

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{TMDB_BASE_URL}/discover/movie", params=params)
            response.raise_for_status()
            data = response.json()

        # Filme vorbereiten
        movie_results = data.get('results', [])[:10]

        # PARALLEL: Alle Streaming-Provider für alle Filme gleichzeitig abrufen
        import asyncio
        streaming_tasks = [fetch_streaming_providers(result.get('id')) for result in movie_results]
        streaming_results = await asyncio.gather(*streaming_tasks)

        # Movies mit allen Daten zusammenbauen
        movies = []
        for result, streaming_providers in zip(movie_results, streaming_results):
            poster_path = result.get('poster_path')
            movies.append(Movie(
                title=result.get('title'),
                release_date=result.get('release_date'),
                tmdb_id=result.get('id'),
                poster_url=f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None,
                overview=result.get('overview'),
                vote_average=result.get('vote_average'),
                streaming_providers=streaming_providers
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
