# Song Lyrics Scraper

## Description

An app that uses your local iTunes files, in Windows, to scrape the web for lyrics and bpms to songs. The lyrics and bpms are stored/embedded in the local music files with the use if iTunes if/when they are successfully found. The lyrics come from a website with "the biggest collection of song lyrics in the world" and the bpms come from the "dominant music streaming provider".

## Getting Started

Add the songs you want to scrape to the corresponding iTunes playlist depending on if you want to scrape based on albums or singles. Scraping albums is faster/more efficient if multiple songs are from the same album, so it's better to add all the songs of the album to the album playlist and scrape that to add them to the songs playlist. You get to choose whether to keep the old data or to replace it with the newly found data when it's time to embed it. 

The albums should be in a playlist called: "Album Metadata Manip"
The songs should be in a playlist called: "Single Metadata Manip"

Download all the dependecies, then run the app by running e.g.: ```python main.py``` and choose what you want to do with the program once it's running.

There are some limits when using the app, more specifically for the bpms. In order to not send too many requests too fast the albums are limited to 20 albums per run. You also need to have your own api key to be able to get them. 

### Dependencies

For lyrics:
* Windows (developed with v. 8.1 Pro)
* Python (developed with v. 3.10.5)
* iTunes (developed with v. 12.10.11.2)
* requests (developed with v. 2.28.2)
* pywin32 (developed with v. 305)
* local music files with the correct metadata (album artist/artist/title/album/track)

For bpms:
* All the above +
* Your own API key
* api_token.txt (file where you store the api key)
