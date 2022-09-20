# spotify-lyrics-finder
Using the spotify API and webscraping, find a song's lyrics and print them to the console at their approximate time.

## usage
once youve downloaded this repository (and python), run `python3 -m pip install -r requirements.txt` (might have to modify for your system), which will install the nececcary packages, then run `python3 spotify_lyrics.py`, which will open a web browser to accounts.spotify.com. once you log in, youll be redirected to localhost:8080 (your own computer), where a temporary webserver has been set up to capture the API key. (all of thats done by the spotipy library btw, not me). then a file named `.cache` will be saved in the same folder as `spotify_lyrics.py`, containing the API key, so you dont have to log in again.\
tl;dr, the first time, install the necesarry packages from `requirements.txt`, run `spotify_lyrics.py`, login to spotify, and youre done. after that, all you need to do to run it again is run `spotify_lyrics.py`
