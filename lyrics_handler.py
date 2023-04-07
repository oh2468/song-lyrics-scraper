import requests
import re
import time
import random
import html
from song_models import Album, Song



class GeniusScraper:
    _USER_AGENT = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0"}
    _SEARCH_URL = "https://genius.com/api/search/multi?per_page=5&q={search}"
    _ALBUM_URL = "https://genius.com/api/page_data/album?page_path=/albums/{artist}/{title}"
    _SONG_URL = "https://genius.com/api/page_data/song?page_path=/{artist}-{title}-lyrics"
    _FALLBACK_URL = "https://genius.com/api/page_data/album?page_path={fallback}"
    _EMBED_LYRICS = "https://genius.com/songs/{song_id}/embed.js"
    _ARTIST_PAGE = "https://genius.com/artists/{artist}"
    _MAX_REQUEST_COUNT = 100
    #_ALBUM_URL = "https://genius.com/albums/{artist}/{album}"
    #_TRACK_URL = "https://genius.com/Adele-strangers-by-nature-lyrics"


    def __init__(self, silent_mode=False):
        self._silent_mode = silent_mode
        self._session = requests.Session()
        self._session.headers.update(self._USER_AGENT)
        self._made_requests = 0
        self._already_printed = False


    def _send_get_request(self, url):
        self._made_requests += 1
        return self._session.get(url)

    
    def _send_page_request(self, path, item, type=None):
        artist, title = self.fix_name_string([item.artist, item.title])
        page_url = path.format(artist=artist, title=title)
        print(f"Getting item: {page_url}")
        
        return self._send_get_request(page_url)

    
    def _send_embed_request(self, song_id, song=None):
        url = self._EMBED_LYRICS.format(song_id=song_id)
        print(f"Getting song: {song}, From url: {url}")
        return self._send_get_request(url)


    def _sleep_a_little_before_next_track(self):
        sleep = random.uniform(1, 3)
        print(f"Sleeping: {sleep}")
        time.sleep(sleep)


    def _enough_is_enough(self, songs):
        enough = len(songs) + self._made_requests > self._MAX_REQUEST_COUNT
        if enough and not self._already_printed:
            print()
            print("  --  ERROR: YOU ARE TRYING TO DO TOO MANY REQUESTS!!!!  --  ")
            print(f"  --  WE'RE ONLY ALLOWING UP TO {self._MAX_REQUEST_COUNT} REQUESTS OR AT LEAST ONE ALBUM  --  ")
            print("  --  PER SESSION AT THE MOMENT, CHANGE IT IF YOU'RE FEELING RISKY  -- ")
            print("  --  TRY WITH FEWER SONGS NEXT TIME!!  --  ")
            print()
            self._already_printed = True
        return enough


    def _scrape_song_embed(self, embed_lyrics):
        try:
            lyrics = embed_lyrics.split('<p>')[1].split("<\/p>")[0]
            lyrics = re.sub('<.*?>', "", lyrics)
            lyrics = lyrics.replace("\\n", "\n")
            lyrics = lyrics.replace("\\", "")
            return html.unescape(lyrics)
        except IndexError as err:
            print(f" ******** ERROR PARSING LYRICS EMBED: {embed_lyrics}")
            return ""


    def _fallback_search(self, type):
        search = input("\nEnter search query: ")
        if not search: return None
        
        search = self._remove_illegal_chars_and_whitespace(search, "+")
        url = self._SEARCH_URL.format(search=search)

        resp = self._send_get_request(url)
        jresp = resp.json()

        type_sect = [sect["hits"] for sect in jresp["response"]["sections"] if sect["type"] == type][0]
        results= []
        for i, srch_item in enumerate(type_sect, 1):
            srch_res = srch_item["result"]
            full_title = srch_res["full_title"]
            results.append(srch_res)
            print(f"{i} - {full_title}")

        try:
            opt = int(input("\nEnter matched option, 0 to exit if not found: "))
            print()
            return results[opt - 1] if 0 < opt <= len(results) else None
        except:
            pass
            
        return None


    def scrape_singles(self, songs):
        if self._enough_is_enough(songs): return []

        for song in songs:
            if song.lyrics or song.instrumental: continue
            self._sleep_a_little_before_next_track()
            resp = self._send_page_request(self._SONG_URL, song)
            
            if resp.status_code != 200:
                print(f" -- ERROR FINDING SINGLE.....: {song}--  ")
                song_resp = self._fallback_search("song")
                if not song_resp: continue
            else:
                song_resp = resp.json()["response"]["page_data"]["song"]
            
            song.instrumental = song_resp["instrumental"]

            if not song.instrumental:
                song_id = song_resp["id"]
                emb_resp = self._send_embed_request(song_id, song)
                song.lyrics = self._scrape_song_embed(emb_resp.text)

            #print(song.lyrics.replace("\n", "  **  "))
            #print(song.lyrics)
        return songs


    def _get_album_content(self, album_resp, specific_songs={}):
        page = album_resp["response"]["page_data"]
        info = page["dmp_data_layer"]["page"]
        #type = info["type"]

        album_artist = info["artist"]
        album_title = info["title"]

        #album = page["album"]
        album_songs = page["album_appearances"]
        album_path_ids_and_songs = []

        if any(tr.disc_num != 1 for tr in specific_songs):
            #raise ValueError("Cannot handle multi disc tracks at this point...")
            print("  --  ERROR WITH SPECIFIED ALBUM SONGS: Cannot handle multi disc tracks at this point...  --  ")
            print("Aborting scrape attempt!")
            return []
        
        tracks_to_scrape = {song.track_num: song for song in specific_songs}

        for song in album_songs:
            track_num = song["track_number"]
            song = song["song"]
            path_id = song["id"]
            song_title = song["title"]
            instrumental = song["instrumental"]

            if tracks_to_scrape:
                if (album_track := tracks_to_scrape.get(track_num, None)):
                    album_track.artist = album_artist
                    album_track.title = song_title
                    album_track.album = album_title
                    album_track.instrumental = instrumental
                    album_path_ids_and_songs.append((path_id, album_track))
            else:
                album_path_ids_and_songs.append((path_id, Song(album_artist, song_title, album_title, track_num, 1, instrumental=instrumental)))
        
        return album_path_ids_and_songs

    
    def scrape_album(self, album):
        if self._enough_is_enough(album.songs):
            print(f"Skipping album: {album}")
            return None

        response = self._send_page_request(self._ALBUM_URL, album)
        jresp = response.json()

        if response.status_code != 200:
            print(f" -- ERROR FINDING ALBUM.....: {album}--  ")
            if (search_res:= self._fallback_search("album")):
                new_url = search_res["url"]
                path = new_url[new_url.find("/"):]
                fallback_url = self._FALLBACK_URL.format(fallback=path)
                jresp = self._send_get_request(fallback_url).json()
            else:
                return None

        album_ids_and_songs = self._get_album_content(jresp, album.songs)
        for song_id, song in album_ids_and_songs:
            if song.lyrics or song.instrumental: continue

            self._sleep_a_little_before_next_track()
            emb_resp = self._send_embed_request(song_id, song)
            lyrics = self._scrape_song_embed(emb_resp.text)

            song.lyrics = lyrics
            album.add_song(song)

        return album


    def _remove_illegal_chars_and_whitespace(self, string, ws_replace):
        string = string.replace("'", "")
        string = string.replace("&", "and")
        return re.sub(r"\W+", ws_replace, string).strip(ws_replace)
    

    def fix_name_string(self, names):
        names = [name.split("feat")[0] if not name.startswith("feat") else name for name in names]
        return [self._remove_illegal_chars_and_whitespace(name, "-") for name in names]


    def freeform_search(self):
        song = self._fallback_search("song")
        if song:
            emb_resp = self._send_embed_request(song["id"])
            return self._scrape_song_embed(emb_resp.text)
        return "Could not find any lyrics...."


