import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import requests
from bs4 import BeautifulSoup
import urllib.parse
from threading import Thread


'''settings'''
beginning_offset = 10
ending_offset = 10
debug = 0

'''advanced settings'''
song_changed_check_delay = 10 # will check if the current song changed every this number of seconds
musical_substrs = [' - ', '- from', ' from the', '(feat', '(remix', ' - feat', ' - remix', '[remix', '[feat', 'remix', 'feat.', 'featuring', '(with'] # cut everything after this in a song. ex "let it go from the original motion picture frozen sound track" -> "let it go", bc the  first one wont find lyrics
musical_title_length = 2#0 # wont modify title if under this len
headers={'User-Agent': 'Mozilla/5.0'} # try not to get blocked by lyrics site
redirect_uri='http://localhost:8080'
scope = 'app-remote-control streaming user-read-playback-state user-modify-playback-state user-read-currently-playing user-read-playback-position' # I probably dont need all of these, but I dont feel like figuring out what I dont need so oh well

'''global variables setup'''
potential_title_assumption = ''
song_changed = False
go = True
wait=False
client_ID = '43f62d7e55af48d3b79509c6eec09f86'
client_secret = '767bcbfde46d483d94f6ad071a72d305' # okay, so yes, putting this directly into the public source code is a bad idea, but from what I can tell the worst someone would be able to do would be to impersonate my app or something? but I dont think they could like, steal my information or anything, and my only other options are publish unusable code, or to make like a whole server somewhere to communicate with this app, and thats way too much just for a little python script, so here we are.


def get_current_track_info():
    global sp, debug
    current_track = sp.currently_playing()
    track = current_track['item']['name']
    artist = current_track['item']['artists'][0]['name']
    progress = current_track['progress_ms']/1000 # in seconds
    duration = current_track['item']['duration_ms']/1000 # in seconds
    return {'track':track,'artist':artist,'progress':progress,'duration':duration}


def get_musical_track_title(title): # converts track titles like "let it got from the major motion picture 'Frozen'" to just "let it go" to get lyrics easier
    global musical_substrs,musical_title_length, debug
    if len(title) > musical_title_length:
        for substr in musical_substrs:
            if substr in title.lower():
                if debug:
                    print('MUSICAL TITLE DETECTED:', title.lower(), substr, title.lower().find(substr))
                title = title[:title.lower().find(substr)]
                return title
    if debug:
        print('MUSICAL TITLE NOT DETECTED')
    return title


def get_lyrics(track, artist):
    global debug, headers

    track = get_musical_track_title(track) # converts title like "let it go from the original motion picture frozen soundtrack" to "let it go", otherwise the search wont find it
    search_str = track + ' ' + artist
    search_url = 'https://search.azlyrics.com/search.php?q=' + urllib.parse.quote(search_str, safe='')
    if debug:
        print('searching for lyrics page with url:',search_url)
    search_page = requests.get(search_url, headers=headers)
    if debug:
        print('status code:', search_page.status_code)
    search_soup = BeautifulSoup(search_page.text,'html.parser')
    lyrics_url_div_container = search_soup.find('div',{'class':'panel'})
    if lyrics_url_div_container:
        lyrics_url = lyrics_url_div_container.find('a').get('href')
    else:
        return ''

    if debug:
        print('lyrics url:', lyrics_url)
    lyrics_page = requests.get(lyrics_url, headers=headers)
    if debug:
        print('status code:',lyrics_page.status_code)
    lyrics_soup = BeautifulSoup(lyrics_page.text,'html.parser')
    lyrics = lyrics_soup.find('div', {'class':'col-xs-12 col-lg-8 text-center'}).find('div', {'class':None})
    return lyrics.text.replace('â€™',"'").replace('\xe2\x80\x99',"'") # .replace() to fix this bug: https://askleo.com/why_do_i_get_odd_characters_instead_of_quotes_in_my_documents/


def check_if_song_changed(title, artist):
    global song_changed, song_changed_check_delay, go, debug
    while go and not song_changed:
        track_info = get_current_track_info()
        if track_info['track'] != title or track_info['artist'] != artist:
            if debug:
                print('changed from',title,'by',artist,'to',track_info['track'],'by',track_info['artist'])
            song_changed = True
            return 0
        else:
            for _ in range(10):
                if song_changed or not go:
                    return 0
                time.sleep(song_changed_check_delay/10)



def print_lyrics(lyrics, track_info):
    global song_changed, go
    song_changed = False
    song_changed_thread = Thread(target=check_if_song_changed, args=[track_info['track'],track_info['artist']])
    song_changed_thread.start()


    current_progress = track_info['progress'] + time.time() - start_time # current progress in song accounting for time to get lyrics

    lyrics_start_time = beginning_offset
    lyrics_end_time = track_info['duration'] - ending_offset
    offset_duration = lyrics_end_time - lyrics_start_time

    if current_progress > lyrics_start_time:
        offset_progress = current_progress - lyrics_start_time
    else:
        time.sleep(lyrics_start_time - current_progress)
        offset_progress = 0

    lyrics_playing_now = int(offset_progress/offset_duration * len(lyrics))
    if debug:
        print('offset_progress: {}\n offset_duration: {}\n lyrics_playing_now: {}\n length of lyrics: {}\n lyrics left: {}'.format(offset_progress,offset_duration,lyrics_playing_now, len(lyrics), len(lyrics)-lyrics_playing_now))

    print(lyrics[:lyrics_playing_now], end='', flush=True) # prints alrady heard lyrics

    print_start_time=time.time()
    print_end_time=print_start_time + offset_duration - offset_progress

    for i in range(lyrics_playing_now, len(lyrics)):
        if song_changed or not go:
            if debug:
                print('song_changed: {}, go: {}'.format(song_changed,go))
            return 0

        char = lyrics[i]
        print(char,end='', flush=True)

        chars_left = len(lyrics) - i
        time_left = print_end_time - time.time()
        sleep_time = time_left/chars_left
        if sleep_time > 0:
            time.sleep(sleep_time)

    song_changed = True
    song_changed_thread.join()
    song_changed = False

    sleep_time = (print_end_time + ending_offset + 1)-time.time()
    if sleep_time > 0:
        time.sleep(sleep_time)

if __name__=='__main__':
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, client_id=client_ID, client_secret=client_secret, redirect_uri=redirect_uri))#cache_path='.cacheee'))
    while go:
        try:
            track_info = get_current_track_info()
            if debug:
                print('playing',track_info['track'], 'by', track_info['artist'], '. current time is',track_info['progress'], 'out of', track_info['duration'], 'which is', track_info['progress']/track_info['duration'], '% complete')
            start_time = time.time()
            title_str = ' '.join((track_info['track'],'by',track_info['artist']))
            print('\n\n\n\n', '-' * (len(title_str)+10), '\n\n' + ' '*5,title_str, '\n\n', '-'*(len(title_str)+10), '\n\n')

            lyrics = get_lyrics(track_info['track'], track_info['artist'])
            restart = False
            while 1:
                if len(lyrics) < 1:
                    print('unable to find lyrics for {} by {}'.format(track_info['track'],track_info['artist']))
                    potential_title = potential_title_assumption or input('press enter when the next song is playing OR enter title to try searching for lyrics with OR type "wait" to auto-detect when next song is playing OR type "always wait" to stop asking this: ')
                    if potential_title.lower() == "wait":
                        lyrics = '..........\n'*10
                        wait=True
                    elif potential_title.lower() == 'always wait':
                        potential_title_assumption = 'wait'
                    elif len(potential_title) > 0:
                        lyrics = get_lyrics(potential_title, track_info['artist'])
                    else:
                        restart = True
                        break
                else:
                    break
            if restart:
                continue

            print_lyrics(lyrics,track_info)
            time.sleep(1) # bug fix: sometimes @ end of song it would go into the 'next song' but it was just the same song again and it would pring out the whole thing really quickly.
            if wait: # only continue when new song is playing
                current_song = track_info['track']
                current_artist = track_info['artist']
                while wait:
                    new_track_info = get_current_track_info()
                    if current_song != new_track_info['track'] and current_artist != new_track_info['artist']:
                        wait = False
                        break
                    else:
                        time.sleep(song_changed_check_delay)

        except KeyboardInterrupt:
            print('\n\nkeyboard interrupt, attempting to exit')
            go = False
            break
