import os
from unittest import result
import requests
from song_models import Album, Song
import json


class SpotifyHandler:
    _USER_AGENT = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0"}
    _SEARCH_URL = "https://api.spotify.com/v1/search" #LIMIT MAX 50
    _ALBUMS_URL = "https://api.spotify.com/v1/albums?ids={ids}" # LIMIT MAX 20
    _TRACKS_URL = "https://api.spotify.com/v1/tracks?ids={ids}" # LIMIT MAX 50?
    _AUDIO_FEATURES_URL = "https://api.spotify.com/v1/audio-features?ids={ids}" # LIMIT MAX 50
    _PLAYLIST_URL = "https://api.spotify.com/v1/playlists/{id}"
    _MAX_ALBUM_LIMIT = 20
    _MAX_TRACK_LIMIT = 50
    _MAX_FEATURE_LIMIT = 100


    def __init__(self):
        self._session = requests.Session()
        with open("bearer_token.txt", "r", encoding="UTF-8") as file: bearer = json.load(file)["access_token"]
        header = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer}",
        }
        self._session.headers.update(header)


    def _search(self, query, type, limit=20):
        response = self._session.get(
            self._SEARCH_URL,
            params={"q": query, "type": type, "limit": limit}
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(response)
            raise RuntimeError("  ***  SPOTIFY DOESN'T SEEM TO RESPOND PROPERLY TO OUR REQUESTS  ***  ")
            #return something?!


    def _spotify_track_to_id_and_song(self, track, album_title=None):
        album_title = album_title or track["album"]["name"]
        artist = track["artists"][0]["name"]
        title = track["name"]
        track_num = track["track_number"]
        disc_num = track["disc_number"]
        duration = track["duration_ms"] // 1000
        id = track["id"]
        return (id, Song(artist, title, album_title, track_num, disc_num, duration=duration))


    def _get_audio_features(self, track_ids):
        audio_features = []
        max_ids = self._MAX_FEATURE_LIMIT

        for i in range(0, len(track_ids), max_ids):
            part = track_ids[i:i + max_ids]
            response = self._session.get(self._AUDIO_FEATURES_URL.format(ids=",".join(part)))
            if response.status_code != 200: break
            audio_features += response.json()["audio_features"]

        #for af in audio_features: print(af)
        return audio_features


    def _rounded_int(self, num):
        return int(num) + (num % 1 >= 0.5)


    def _set_song_bpms(self, song_map, features):
        for feature in features:
            #print(feature)
            if not feature: continue

            """ UNCOMMENT THIS TO HALF BPM WHEN IT'S PROBABLY TOO HIGH """
            # probability_threashold = 0.40
            # if (bpm := feature["tempo"]) >= 130 and feature["danceability"] <= probability_threashold:
            #     bpm /= 2
            #     print(f"BPM WARNING: {feature}")
            # bpm = self._rounded_int(bpm)

            bpm = self._rounded_int(feature["tempo"])
            track_id = feature["id"]
            song_map[track_id].bpm = bpm
        #return song_map


    def get_album_bpms(self, albums):
        if len(albums) > self._MAX_ALBUM_LIMIT:
            print(f"YOU'RE TRYING TO DO {len(albums)} ALBUMS AT ONCE..... NOT OK!")
            raise ValueError(" ** DONT BE GREEDY, 20 ALBUMS IS MORE THAN ENOUGH! ** ")
        
        album_map = {}
        for album in albums:
            if not album: continue
            album_resp = self._search(f"artist:{album.artist} album:{album.title}", "album", 1)
            
            if not (first_match := album_resp["albums"]["items"]):
                print(album_resp)
                continue
            
            album_id = first_match[0]["id"]
            album_map[album_id] = album

        if not album_map:
            print(" -- ERROR -- COULD NOT FIND ANY ALBUM MATCHES ON SPOTIFY....")
            print(f"You're entered albums: {albums}")
            return albums
        
        multi_album_resp = self._session.get(self._ALBUMS_URL.format(ids=",".join(album_map.keys())))
        spotify_albums = multi_album_resp.json()
        #print(spotify_albums)
        
        song_map = {}
        for sp_album in spotify_albums["albums"]:
            for track in sp_album["tracks"]["items"]:
                track_id, song = self._spotify_track_to_id_and_song(track, sp_album["name"])
                print(f"Found song: {song}")
                song_map[track_id] = song
                album_map[sp_album["id"]].add_song(song)
        
        audio_features = self._get_audio_features(list(song_map.keys()))
        self._set_song_bpms(song_map, audio_features)

        return albums


    def get_song_bpms(self, songs):
        song_map = {}
        for song in songs:
            track_resp = self._search(f"artist:{song.artist} track:{song.title}", "track", 1)
            for track in track_resp["tracks"]["items"]:
                track_id, sp_song = self._spotify_track_to_id_and_song(track)
                print(f"Found song: {sp_song}")
                song.artist = sp_song.artist
                song.title = sp_song.title
                song.album = sp_song.album
                song_map[track_id] = song

        audio_features = self._get_audio_features(list(song_map.keys()))
        self._set_song_bpms(song_map, audio_features)

        return songs


    def get_playlist_bpms(self, playlist):
        playlist_id = playlist.split("/")[-1]
        response = self._session.get(self._PLAYLIST_URL.format(id=playlist_id))
        print(response)
        with open(f"spotify responses/playlist_{playlist_id}.json", "w", encoding="UTF-8") as file:
            json.dump(response.json(), file)

    
    def freeform_search(self, type):
        search = input("Enter search query: ")
        response = self._search(search, type, 5)
        with open(f"spotify responses/search_{type}.json", "w", encoding="UTF-8") as file:
            json.dump(response, file)

        item_ids = [item["id"] for item in response[f"{type}s"]["items"]]
        if type == "album":
            response = self._session.get(self._ALBUMS_URL.format(ids=",".join(item_ids))).json()

        with open(f"spotify responses/search_{type}.json", "w", encoding="UTF-8") as file:
            json.dump(response, file)


