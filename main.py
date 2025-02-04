import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json

# Set up Spotify API credentials and authenticate
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id='dac2ac9ea1644b4db3e6cd947c5e7d6d',
                                               client_secret='861f16860471493085fcaf450e455243',
                                               redirect_uri='http://localhost:8888/callback',
                                               scope=['playlist-modify-public', 'playlist-modify-private', 'playlist-read-private', 'user-read-playback-position']))

# Cargar configuración desde el archivo JSON
def load_config():
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    return config

def get_recent_episodes_from_podcast(sp, podcast_id):
    """Obtiene el episodio más reciente del podcast dado (solo el URI y nombre)."""
    try:
        # Obtenemos los detalles del podcast para conseguir su nombre
        podcast = sp.show(podcast_id)
        podcast_name = podcast['name']  # Nombre del podcast

        # Obtenemos los episodios más recientes del podcast (primero con limit=1)
        episodes = sp.show_episodes(podcast_id, limit=1, market="ES")
        
        # Si no hay episodios, probamos con limit=2
        if not episodes or 'items' not in episodes or episodes['items'][0] is None:
            print(f"⚠️ No se encontró un episodio válido con limit=1. Intentando con limit=2...")
            episodes = sp.show_episodes(podcast_id, limit=2, market="ES")
        
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

def get_playlist_episodes(sp, playlist_id):
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


def update_playlist(sp, playlist_id, episode_ids):
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

def main():

    # Cargar los valores
    config = load_config()

    # Extraer los valores de la configuración
    PODCAST_IDS = config['podcast_ids']
    PLAYLIST_ID = config['playlist_id']

    # Ahora puedes usar PODCAST_IDS y PLAYLIST_ID en tu código
    print("Podcast IDs:", PODCAST_IDS)
    print("Playlist ID:", PLAYLIST_ID)
    
    # Obtenemos los episodios más recientes de cada podcast
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
