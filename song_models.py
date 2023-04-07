import re


def replace_apostrophe(strings):
    return [string.replace(u"\u2019", "'") for string in strings]


def cmp_caseless_strings(this, that):
    this, that = replace_apostrophe([this, that])
    return this.casefold() == that.casefold()
    # x = this.casefold() == that.casefold()
    # #print(f"EQUAL: {x}, THIS: {this}, THAT: {that}")
    # return x


def cmp_caseless_start(this, that):
    shortest = min(len(this), len(that))
    return cmp_caseless_strings(this[0:shortest], that[0:shortest])


def alphanum_only(strings):
    return [ re.sub(r"\W+", " ", string).strip() for string in strings]


class Album:
    
    def __init__(self, artist, title, num_tracks, num_discs, album_id=None):
        self.artist = artist.casefold()
        self.title = title.casefold()
        self.num_tracks = num_tracks
        self.num_discs = num_discs
        self.songs = []


    def to_tuple(self):
        return (self.artist, self.title, self.num_tracks)


    def __eq__(self, other):
        if isinstance(other, Album):
            return self.to_tuple() == other.to_tuple()
        return False


    def __hash__(self):
        return hash(self.to_tuple())

    
    def __repr__(self):
        return f"Album({self.artist}, {self.title}, {self.num_tracks}, {self.num_discs}, {len(self.songs)})"


    def add_song(self, song):
        if song in self.songs:
            return
        elif isinstance(song, Song) and cmp_caseless_strings(self.artist, song.artist) and cmp_caseless_strings(self.title, song.album):
            self.songs.append(song)
        else:
            print(self)
            print(song)
            #print(song.album)
            if cmp_caseless_start(self.title, song.album):
                print("WARNING THE ALBUM/SONG/ARTIST DOES NOT MATCH.... CONTINUING ANYWAY!")
                self.songs.append(song)
            else:
                raise ValueError(f"Trying to add a song to the wrong album! ME: {self.title}, INCOMING: {song.album}")



class Song:

    def __init__(self, artist, titel, album, track_num, dics_num, song_id=None, duration=None, lyrics=None, bpm=None, instrumental=False):
        self.song_id = song_id
        self.artist = artist
        self.title = titel
        self.album = album
        self.track_num = track_num
        self.disc_num = dics_num
        self.duration = duration
        self.lyrics = lyrics
        self.bpm = bpm
        self.instrumental = instrumental


    def __eq__(self, other) -> bool:
        if isinstance(other, Song):
            #return self.artist == other.artist and self.title == other.title and self.album == other.album and self.track_num == other.track_num and self.disc_num == other.disc_num
            track_num_check = self.track_num == other.track_num if self.disc_num == other.disc_num else True
            return (cmp_caseless_strings(self.artist, other.artist) and \
                    cmp_caseless_strings(self.title, other.title) and \
                    cmp_caseless_strings(self.album, other.album) and \
                    track_num_check) or \
                    (cmp_caseless_strings(*alphanum_only([self.artist, other.artist])) and \
                    cmp_caseless_strings(*alphanum_only([self.title, other.title])) and \
                    cmp_caseless_strings(*alphanum_only([self.album, other.album])) and \
                    track_num_check)
        return False


    def __str__(self):
        #return f"Aritst: {self.artist}, Title: {self.title}, TrackNumber: {self.track_num}, ID: {self.song_id}"
        #return f"Aritst: {self.artist}, Title: {self.title}, TrackNumber: {self.track_num}, ALBUM: {self.album}"
        return f"{self.artist} - {self.title} - {self.track_num} - {self.album}"
