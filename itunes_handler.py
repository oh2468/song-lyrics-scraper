import win32com.client
import re
from song_models import Album, Song



class ItunesHandler:
    _ALBUMS_PLAYLIST = "Album Metadata Manip"
    _SINGLES_PLAYLIST = "Single Metadata Manip"
    _MISSING_PLAYLIST = "Missing Metadata Songs"
    _DELETE_PLAYLIST = "Delete Metadata Songs"
    _VERBOSE = False


    def __init__(self):        
        self._itunes = win32com.client.Dispatch("iTunes.Application")
        self._albums_playlist = self._get_playlist(self._ALBUMS_PLAYLIST)
        self._singles_playlist = self._get_playlist(self._SINGLES_PLAYLIST)

    
    def _get_playlist(self, playlist):
        return self._itunes.LibrarySource.Playlists.ItemByName(playlist) or self._itunes.CreatePlaylist(playlist)
    

    def _itunes_track_to_song(self, tr):
        #return Song(tr.AlbumArtist, tr.Name, tr.Album, tr.TrackNumber, tr.DiscNumber, tr.Index, tr.Duration, tr.Lyrics, tr.BPM)
        return Song(tr.Artist.split(",")[0], tr.Name, tr.Album, tr.TrackNumber, tr.DiscNumber, tr.Index, tr.Duration, tr.Lyrics, tr.BPM)


    def _add_lyrics_to_itunes_song(self, song, it_song):
        my_it_song = self._itunes_track_to_song(it_song)

        if it_song.lyrics:
            self._print_padded_msg_song("Already has lyrics, skipping:", my_it_song)
        elif song.instrumental:
            self._print_padded_msg_song("Instrumental song, skipping:", my_it_song)
        elif not song.lyrics:
            self._print_padded_msg_song("Empty lyrics, skipping:", song)
        else:
            invalid_lyrics_chars = ["<", ">"]
            if any(inv in song.lyrics for inv in invalid_lyrics_chars):
                raise ValueError(f" ** ERROR: Invalid chars found in song: {song} **\nLYRICS: {song.lyrics}")

            it_song.lyrics = song.lyrics
            self._print_padded_msg_song("NEW LYRICS ADDED TO:", my_it_song)


    def _print_if_allowed(self, string):
        if self._VERBOSE:
            print(string)


    def _print_found_match(self, type, new_song, old_song):
        self._print_if_allowed(f"\nFOUND {type} MATCH\n New: {new_song}\n Old: {old_song}\n")


    def _print_padded_msg_song(self, msg, song):
        print(f"{msg.ljust(30, ' ')} {song}")


    def _get_user_confirmation(self, confirmation_msg):
        while (answer := input(f"{confirmation_msg}? (y/n):").lower()) not in ["y", "n"]: pass
        return answer == "y"


    def _get_itunes_song(self, playlist, song):
        it_song = None

        if (s_id := song.song_id) and (pl_song := playlist.Tracks.Item(s_id)):
            if song == (cmp_song := self._itunes_track_to_song(pl_song)):
                self._print_found_match("ID", song, cmp_song)
                it_song = pl_song
            else:
                print(f"\n  --  WARNING: ALBUM SONG MISMATCH!  --  \n {song}\n {cmp_song}\n")
                if self._get_user_confirmation("Select it anyway"):
                    it_song = pl_song
        else:
            search_q = re.sub(r"\W+", " ", song.title)
            for srch_song in playlist.Search(search_q, 5) or []:
                if song == (cmp_song := self._itunes_track_to_song(srch_song)):
                    it_song = srch_song
                    self._print_found_match("SEARCH", song, cmp_song)
                    break # ignore duplicates
                else:
                    if self._VERBOSE:
                        print(f"NOT A MATCH: {song} *** {cmp_song}")
            
            if not it_song:
                #print(search_q)
                print(f"\nCOULD NOT FIND AN ITUNES MATCH FOR: {song}\n")
                input(" -- MANUALLY SELECT THE SONG IN ITUNES IF YOU HAVE IT. PRESS ENTER WHEN DONE! -- ")
                selected = self._itunes.BrowserWindow.SelectedTracks or []
                for select in selected:
                    cmp_song = self._itunes_track_to_song(select)
                    if self._get_user_confirmation(f"Is this the correct song: {cmp_song}"):
                        it_song = select
                        self._print_found_match("SELECT", song, cmp_song)
                        break
        
        return it_song


    def create_missing_lyrics_playlist(self):
        self._get_playlist(self._MISSING_PLAYLIST).Delete()
        missing_playlist = self._get_playlist(self._MISSING_PLAYLIST)
        all_itunes_songs = self._itunes.LibraryPlaylist.Tracks
        no_lyric_count = 0

        for song in all_itunes_songs:
            if not song.lyrics:
                missing_playlist.AddTrack(song)
                no_lyric_count += 1

        return (no_lyric_count, all_itunes_songs.Count)


    def get_albums(self):
        return {Album(tr.AlbumArtist, tr.Album, tr.TrackCount, tr.DiscCount) for tr in self._albums_playlist.Tracks}


    def get_album_songs(self):
        albums = {}
        for tr in self._albums_playlist.Tracks:
            album = Album(tr.AlbumArtist, tr.Album, tr.TrackCount, tr.DiscCount)
            if album not in albums:
                albums[album] = album
            song = self._itunes_track_to_song(tr)
            song.artist = album.artist
            albums[album].add_song(song)

        return albums


    def get_singles(self):
        return [self._itunes_track_to_song(track) for track in self._singles_playlist.Tracks]


    def add_singles_lyrics(self, songs, playlist=None):
        for song in songs:
            if not song:
                pass
            elif (it_song := self._get_itunes_song(playlist or self._singles_playlist, song)):
                self._add_lyrics_to_itunes_song(song, it_song)
            else:
                print(f"  -_-_-  COULD NOT FIND A MATCH IN ITUNES FOR THE SONG: {song}  -_-_-  ")


    def add_album_lyrics(self, albums):
        for album in albums:
            if not album: continue
            self.add_singles_lyrics(album.songs, self._albums_playlist)


    def delete_song_lyrics(self):
        playlist_tracks = self._get_playlist(self._DELETE_PLAYLIST).Tracks
        remove_count = 0

        for song in playlist_tracks:
            if song.lyrics:
                song.lyrics = ""
                remove_count += 1
        
        return (remove_count, playlist_tracks.Count)

    
    def _add_bpm_to_itunes_song(self, song):
        pass


    def add_album_bpms(self, albums):
        for album in albums:
            if not album: continue
            self.add_song_bpms(album.songs, self._albums_playlist)


    def add_song_bpms(self, songs, playlist=None):
        for song in songs:
            if not song or not song.bpm:
                continue
            elif (it_song := self._get_itunes_song(playlist or self._singles_playlist, song)):
                if it_song.BPM == song.bpm: continue
                
                update = True
                if it_song.BPM:
                    song_it_song = self._itunes_track_to_song(it_song)
                    print(f" -- WARNING: The current iTunes song already has A BPM -- ")
                    self._print_padded_msg_song(f" Old BPM {it_song.BPM}", song_it_song)
                    self._print_padded_msg_song(f" NEW BPM {song.bpm}", song)
                    update = self._get_user_confirmation("Replace the old bpm with the new")
                if update:
                    it_song.BPM = song.bpm
            else:
                print(f"  -_-_-  COULD NOT FIND A MATCH IN ITUNES FOR THE SONG: {song}  -_-_-  ")
            

