import { useState } from 'react';
import '@/App.css';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { Film, Sparkles, Search, Star } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [movies, setMovies] = useState([]);
  const [message, setMessage] = useState('');
  const [usedAI, setUsedAI] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    
    if (!prompt.trim()) {
      toast.error('Bitte geben Sie einen Film-Wunsch ein');
      return;
    }

    setLoading(true);
    setMovies([]);
    setMessage('');

    try {
      const response = await axios.post(`${API}/recommend`, {
        prompt: prompt
      });

      setMovies(response.data.movies);
      setMessage(response.data.message);
      setUsedAI(response.data.used_ai);
      
      if (response.data.movies.length === 0) {
        toast.error('Keine Filme gefunden');
      } else {
        toast.success(`${response.data.movies.length} Filme gefunden!`);
      }
    } catch (error) {
      console.error('Fehler:', error);
      toast.error('Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      {/* Header */}
      <div className="container mx-auto px-4 py-12">
        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-4">
            <Film className="w-16 h-16 text-purple-600" />
          </div>
          <h1 className="text-5xl lg:text-6xl font-bold text-gray-900 mb-4 font-['Playfair_Display']">
            Film Robo
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto font-['Inter']">
            Beschreiben Sie einfach, welche Art von Film Sie sehen möchten – unsere KI findet die perfekte Empfehlung für Sie!
          </p>
        </div>

        {/* Search Form */}
        <div className="max-w-3xl mx-auto mb-12">
          <Card className="shadow-lg border-0 backdrop-blur-sm bg-white/80">
            <CardContent className="pt-6">
              <form onSubmit={handleSearch} className="space-y-4">
                <div className="relative">
                  <Input
                    data-testid="prompt-input"
                    type="text"
                    placeholder="z.B. 'Lustige Filme mit Aliens' oder 'Spannende Thriller'"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    className="text-base h-14 pl-12 pr-4 rounded-full border-2 border-gray-200 focus:border-purple-400 transition-colors"
                    disabled={loading}
                  />
                  <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                </div>
                <Button
                  data-testid="search-button"
                  type="submit"
                  disabled={loading}
                  className="w-full h-14 text-base rounded-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 transition-all shadow-md hover:shadow-lg"
                >
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Suche läuft...
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      <Sparkles className="w-5 h-5" />
                      Filme finden
                    </span>
                  )}
                </Button>
              </form>
              
              {message && (
                <div className="mt-4 p-4 bg-purple-50 rounded-lg border border-purple-200">
                  <p className="text-purple-900 text-center font-medium">{message}</p>
                  {usedAI && (
                    <Badge className="mt-2 mx-auto block w-fit bg-purple-600">
                      ✨ KI-unterstützt
                    </Badge>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Movie Results */}
        {movies.length > 0 && (
          <div className="max-w-7xl mx-auto">
            <h2 className="text-3xl font-bold text-gray-900 mb-6 font-['Playfair_Display']">
              Ihre Empfehlungen
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
              {movies.map((movie, index) => (
                <Card
                  key={movie.tmdb_id}
                  data-testid={`movie-card-${index}`}
                  className="group hover:shadow-2xl transition-all duration-300 border-0 overflow-hidden bg-white"
                >
                  <div className="relative aspect-[2/3] overflow-hidden bg-gray-100">
                    {movie.poster_url ? (
                      <img
                        src={movie.poster_url}
                        alt={movie.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-200 to-gray-300">
                        <Film className="w-16 h-16 text-gray-400" />
                      </div>
                    )}
                    {movie.vote_average && (
                      <div className="absolute top-2 right-2 bg-black/80 backdrop-blur-sm px-2 py-1 rounded-full flex items-center gap-1">
                        <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                        <span className="text-white text-sm font-bold">{movie.vote_average.toFixed(1)}</span>
                      </div>
                    )}
                  </div>
                  <CardHeader className="p-4">
                    <CardTitle className="text-base line-clamp-2 font-['Inter']">
                      {movie.title}
                    </CardTitle>
                    {movie.release_date && (
                      <CardDescription className="text-sm">
                        {new Date(movie.release_date).getFullYear()}
                      </CardDescription>
                    )}
                  </CardHeader>
                  {movie.overview && (
                    <CardContent className="pt-0 p-4">
                      <p className="text-sm text-gray-600 line-clamp-3">
                        {movie.overview}
                      </p>
                    </CardContent>
                  )}
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Examples */}
        {!movies.length && !loading && (
          <div className="max-w-4xl mx-auto mt-12">
            <h3 className="text-xl font-semibold text-gray-700 mb-4 text-center font-['Inter']">
              Beispiel-Anfragen:
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[
                'Lustige Filme für den Abend',
                'Spannende Thriller',
                'Filme für Kinder',
                'Action mit viel Explosion',
                'Fantasy-Abenteuer',
                'Gruselige Horror-Filme'
              ].map((example, idx) => (
                <button
                  key={idx}
                  onClick={() => setPrompt(example)}
                  className="p-4 bg-white rounded-lg border-2 border-gray-200 hover:border-purple-400 hover:shadow-md transition-all text-left group"
                >
                  <p className="text-gray-700 group-hover:text-purple-600 font-medium">
                    {example}
                  </p>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;