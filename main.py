from itunes_handler import ItunesHandler
from lyrics_handler import GeniusScraper
from bpm_handler import SpotifyHandler
from song_models import Album



def print_valid_options(options):
    print(" -- Valid Options -- ")
    for k, v in options.items():
        print(f"{k.rjust(3, ' ')}: {v}")


def continue_with_action(action):
    while (ans := input(f"Continue with {action}? (y/n): ")).lower() not in ["y", "n"]: pass
    return ans == "y"


if __name__ == "__main__":
    print("MAIN NOW STARTING")

    valid_options = {
        "0": "Exit",
        "1": "Create a missing lyrics iTunes playlist",
        "2": "Scrape Album Lyrics",
        "3": "Scrape Singles Lyrics",
        "4": "Delete Song lyrics",
        "5": "Scrape Partial Album Lyrics",
        "6": "Song Lyrics Search",
        "7": "Scrape Album BPMs",
        "8": "Scrape Song BPMs",
        "9": "Scrape Playlist BPMs",
        "10": "Search Spotify Albums",
        "11": "Search Spotify Songs",
    }

    print_valid_options(valid_options)
    while (choice := input("Enter an option: ")) not in valid_options:
        print_valid_options(valid_options)

    if int(choice) not in [0, 6, 9, 10, 11]:
        itunes_handler = ItunesHandler()
    lyrics_scraper = GeniusScraper()
    bpm_scraper = SpotifyHandler()
    metadata_scraper = None

    match choice:
        case "0":
            # sys exit ?
            pass
        case "1":
            missing, total = itunes_handler.create_missing_lyrics_playlist()
            print(f"Lyrics missing for {missing} of {total} songs.")
        case "2":
            albums = itunes_handler.get_albums()
            albums = [lyrics_scraper.scrape_album(album) for album in albums]
            itunes_handler.add_album_lyrics(albums)
        case "3":
            singles = itunes_handler.get_singles()
            singles = lyrics_scraper.scrape_singles(singles)
            itunes_handler.add_singles_lyrics(singles)
        case "4":
            if continue_with_action("deleting song lyrics"):
                deleted, total = itunes_handler.delete_song_lyrics()
                print(f"Removed lyrics for {deleted} of {total} songs.")
            else:
                print("Aborted song lyrics deletion!")
        case "5":
            album_songs = itunes_handler.get_album_songs()
            album_songs = [lyrics_scraper.scrape_album(album) for album in album_songs]
            itunes_handler.add_album_lyrics(album_songs)
        case "6":
            lyrics = lyrics_scraper.freeform_search()
            print(lyrics)
        case "7":
            albums = itunes_handler.get_albums()
            albums = bpm_scraper.get_album_bpms(albums)
            itunes_handler.add_album_bpms(albums)
        case "8":
            singles = itunes_handler.get_singles()
            singles = bpm_scraper.get_song_bpms(singles)
            itunes_handler.add_song_bpms(singles)
        case "9":
            playlist = input("Enter link to spotify playlist: ")
            reulst = bpm_scraper.get_playlist_bpms(playlist)
        case "10":
            bpm_scraper.freeform_search("album")
        case "11":
            bpm_scraper.freeform_search("track")
        case _:
            print("Invalid option..... Somehow?!")

    
    print("DONE IN MAIN")

