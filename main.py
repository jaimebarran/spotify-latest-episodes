import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json, os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the credentials from environment variables
client_id = os.getenv('SPOTIPY_CLIENT_ID')
client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')

# Set up Spotify API credentials and authenticate
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                               client_secret=client_secret,
                                               redirect_uri=redirect_uri,
                                               scope=['playlist-modify-public', 'playlist-modify-private', 'playlist-read-private', 'user-read-playback-position']))

# Cargar configuración desde el archivo JSON
def load_config():
    # TODO: add type annotations for parameters/return type
    with open('./config.json', 'r', encoding="utf-8") as config_file:
        config = json.load(config_file)

    # Filtrar los podcasts (mantener el orden original del archivo)
    config["podcasts"] = [pod for pod in config["podcasts"] if not pod.get("ignore", False)]

    return config

def get_recent_episodes_from_podcast(sp, podcast_id: int) -> list:
    # TODO: add type annotations for remaining parameters/return type
    """Obtiene el episodio más reciente del podcast dado (solo el URI y nombre)."""
    try:
        # Obtenemos los detalles del podcast para conseguir su nombre
        podcast = sp.show(podcast_id)
        podcast_name = podcast['name']  # Nombre del podcast

        # Obtenemos los episodios más recientes del podcast (primero con limit=1)
        episodes = sp.show_episodes(podcast_id, limit=1, market="ES")
        
        # Si no hay episodios, probamos con limit=2 => Esta no te la sabes
        # Esto es porque tendrán episodios nuevos subidos pero no públicos todavía
        if not episodes or 'items' not in episodes or episodes['items'][0] is None:
            print(f"⚠️ No se encontró un episodio válido con limit=1. Intentando con limit=2...")
            episodes = sp.show_episodes(podcast_id, limit=2, market="ES")
        
        # Si aún no hay episodios, probamos con limit=3 => No es el fin del mundo
        # Esto es porque tendrán episodios nuevos subidos pero no públicos todavía
        if not episodes or 'items' not in episodes or episodes['items'][0] is None:
            print(f"⚠️ No se encontró un episodio válido con limit=2. Intentando con limit=3...")
            episodes = sp.show_episodes(podcast_id, limit=3, market="ES")
        
        if not episodes or 'items' not in episodes or not any(episodes['items']):
            print(f"⚠️ No se encontraron episodios para el podcast {podcast_name}.")
            return []
        
        # Filtramos el primer episodio válido
        recent_episode = next((episode for episode in episodes['items'] if episode), None)
        if not recent_episode:
            print(f"⚠️ No se encontraron episodios válidos para el podcast {podcast_name}.")
            return []

        # Sacamos el URI y nombre del episodio más reciente
        recent_episode_uri = recent_episode['uri']
        recent_episode_name = recent_episode['name']  # Nombre del episodio
        
        # Mostrar el nombre del podcast y el nombre del episodio
        print(f"🎧 Podcast: {podcast_name} | Episodio más reciente: {recent_episode_name}")
        
        return [recent_episode_uri]
    
    except spotipy.exceptions.SpotifyException as e:
        print(f"⚠️ Error al obtener episodios del podcast {podcast_id}: {e}")
        return []
    except Exception as e:
        print(f"⚠️ Error inesperado: {e}")
        return []

def get_playlist_episodes(sp, playlist_id: int) -> list:
    # TODO: add type annotations for remaining parameters/return type
    """Obtiene las URIs de los episodios actuales de la playlist."""
    try:
        # Obtenemos las pistas de la playlist
        episodes = sp.playlist_tracks(playlist_id)
        # print(f"Respuesta de la API para la playlist {episodes}")
        
        if not episodes or 'items' not in episodes or not episodes['items']:
            print(f"⚠️ No se encontraron episodios en la playlist {playlist_id}.")
            return []
        
        # Extraemos solo las URIs de los episodios (campo 'uri' dentro de 'track' o 'episode')
        episode_uris = [
            episode['track']['uri'] if episode.get('track') else episode['episode']['uri']
            for episode in episodes['items']
            if episode.get('track') or episode.get('episode')
        ]
        return episode_uris
        
    except spotipy.exceptions.SpotifyException as e:
        print(f"⚠️ Error al obtener episodios de la playlist: {e}")
        return []
    except Exception as e:
        print(f"⚠️ Error inesperado al obtener episodios de la playlist: {e}")
        return []


def update_playlist(sp, playlist_id: int, episode_ids) -> None:
    # TODO: add type annotations for remaining parameters/return type
    """Reemplaza los episodios en la playlist con los nuevos episodios."""
    try:
        # Eliminamos todos los episodios actuales de la playlist
        current_tracks = get_playlist_episodes(sp, playlist_id)
        print(f"🚫 Eliminando episodios anteriores de la playlist...")
        if current_tracks:
            sp.playlist_replace_items(playlist_id, episode_ids)
        else:
            print(f"❌ No se encontraron episodios previos para eliminar.")
        
        # Añadimos los nuevos episodios a la playlist
        print(f"🔄 Añadiendo episodios a la playlist...")
        response = sp.playlist_replace_items(playlist_id, episode_ids)
        print(f"✅ Respuesta del API: {response}")
    except Exception as e:
        print(f"⚠️ Error al actualizar la playlist: {e}")

def main() -> None:

    # Remove the status.log file
    open('./status.log', 'w', encoding="utf-8").close()

    # Cargar los valores
    config = load_config()

    # Extraer los valores de la configuración
    PLAYLIST_ID = config['playlist']['id']
    PODCAST_IDS = [podcast['id'] for podcast in config['podcasts']]

    # Ahora puedes usar PODCAST_IDS y PLAYLIST_ID en tu código
    print("Podcast IDs:", PODCAST_IDS)
    print("Playlist ID:", PLAYLIST_ID)
    
    # Obtenemos los episodios más recientes de cada podcast
    # TODO: obtener un episodio en concreto por su nombre (e.g. "Las tres noticias de Carlos Alsina" de "Más de uno")
    episode_ids = []
    for podcast_id in PODCAST_IDS:
        recent_episodes = get_recent_episodes_from_podcast(sp, podcast_id)
        episode_ids.extend(recent_episodes)
        
    # Actualizamos la playlist con los nuevos episodios
    if episode_ids:
        update_playlist(sp, PLAYLIST_ID, episode_ids)
    else:
        print("⚠️ No se obtuvieron episodios para actualizar la playlist.")

if __name__ == "__main__":
    main()
