from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import json
import simplejson
import sys
import io
import time
import os
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

SLEEP_TIME = 10;


def readjson(fileName):
    with open (fileName, "r") as myfile:
        data=myfile.read()    
    jdata = json.loads(data)
    return jdata


def metadataGet(artistName, trackName, albumName):
    metadata = {}    

    results = sp.search(q='artist:' + artistName + ' track:'+trackName)
    songs = results['tracks']['items']
    n_songs_found = len(songs)

    T1 = time.time()

    if n_songs_found>0:  # if at least one song is found
        # A. Get spotify metadata:
        spSong = songs[0]  # get first song        
        spAlbumID = spSong["album"]["id"]
        spAlbumName = spSong["album"]["name"]
        sp_song_name = spSong["name"]
        spArtistName = spSong["artists"][0]["name"]
        metadata["spotify-trackName"] = sp_song_name
        metadata["spotify-albumName"] = spAlbumName
        metadata["spotify-artistName"] = spArtistName
        spSongID = spSong["id"]
        
        try:
            # spotify features
            spFeatures = sp.audio_features([spSongID])
        except simplejson.scanner.JSONDecodeError:
            spFeatures = []

        if len(spFeatures)>0:
            spFeatures = spFeatures[0]  # get 1st spotify feature
        if spFeatures is not None:
            for sN in spFeatures:
                if sN not in ["track_href","type","uri","id","analysis_url"]:
                    metadata["spotify-"+sN] = spFeatures[sN]
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
    if sys.argv[1] == "search":
        artist = sys.argv[2]
        song = sys.argv[3]
        album = sys.argv[4]        
        metadata = metadataGet(artist, song, album)
        print(metadata)