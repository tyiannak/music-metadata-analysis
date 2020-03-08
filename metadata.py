from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import json
import simplejson
import sys
import time
import csv
import pylast

with open('credentials.json') as json_file:
    CRED = json.load(json_file)

LAST_FM_KEY = CRED["last-fm"]["LAST_FM_KEY"]
LAST_FM_SECRET = CRED["last-fm"]["LAST_FM_SECRET"]
network = pylast.LastFMNetwork(api_key=LAST_FM_KEY, api_secret=LAST_FM_SECRET)

SPOTIPY_CLIENT_ID = CRED["spotify"]["SPOTIPY_CLIENT_ID"]
SPOTIPY_CLIENT_SECRET = CRED["spotify"]["SPOTIPY_CLIENT_SECRET"]
client_credentials_manager = SpotifyClientCredentials(client_id=
                                                      SPOTIPY_CLIENT_ID,
                                                      client_secret=
                                                      SPOTIPY_CLIENT_SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

SLEEP_TIME = 5

def readjson(fileName):
    with open (fileName, "r") as myfile:
        data=myfile.read()    
    jdata = json.loads(data)
    return jdata


def get_metadata(artistName, trackName):
    metadata = {"artist": artistName,
                "track": trackName}

    results = sp.search(q='artist:' + artistName + ' track:'+trackName)
    songs = results['tracks']['items']
    n_songs_found = len(songs)

    T1 = time.time()

    if n_songs_found>0:  # if at least one song is found
        # A. Get spotify metadata:
        sp_song = songs[0]  # get first song
        sp_album_name = sp_song["album"]["name"]
        sp_song_name = sp_song["name"]
        sp_artist_name = sp_song["artists"][0]["name"]
        sp_song_id = sp_song["id"]
        metadata["spotify-trackName"] = sp_song_name
        metadata["spotify-albumName"] = sp_album_name
        metadata["spotify-artistName"] = sp_artist_name
        # get spotify features
        try: 
            sp_feat = sp.audio_features([sp_song_id])
        except simplejson.scanner.JSONDecodeError:
            sp_feat = []

        if len(sp_feat)>0:
            sp_feat = sp_feat[0]  # get 1st spotify feature
        if sp_feat is not None:
            for sN in sp_feat:
                if sN not in ["track_href","type","uri","id","analysis_url"]:
                    metadata["spotify-"+sN] = sp_feat[sN]
    else:
        print("Spotify: NO")
    T2 = time.time()

    # B. Get last-fm metadata:
    lf_track = network.get_track(artistName, trackName)
    try:
        metadata["lastfm-listener-count"] = lf_track.get_listener_count()
        metadata["lastfm-play-count"] = lf_track.get_playcount()
    except:
        print("Last-fm: NO")

    T3 = time.time()

    timeToSleep = SLEEP_TIME - (T3-T1)
    if timeToSleep>0:
        print("Sleeping for {0:.1f} seconds ...".format(timeToSleep))
        time.sleep(SLEEP_TIME)
    return metadata

if __name__ == '__main__':
    if sys.argv[1] == "single":
        artist = sys.argv[2]
        song = sys.argv[3]
        metadata = get_metadata(artist, song)
        print(metadata)
    if sys.argv[1] == "multi":
        csv_file = sys.argv[2]
        # this must be a csv file of the form: id, track name, artist name
        with open(csv_file) as f:
            reader = csv.reader(f)
            data = list(reader)
        metadata = {}
        for r in data[::1000]:
            print(r[0], r[1], r[2])
            metadata[r[0]] = get_metadata(r[1], r[2])
            print(metadata[r[0]])
            with open('output.json', 'w') as outfile:
                json.dump(metadata, outfile)
