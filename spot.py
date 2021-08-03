import pandas as pd
from dataclasses import dataclass, field, asdict
from typing import List, Tuple
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json
import billboard
from collections import defaultdict, Counter
from models import *

#spotipy wraps the official spotify api providing simple python functions.
# TODO: Replace these two variables with the client_id and client_secret that you generated
CLIENT_ID = "44dfa19c82854a37bc9d6385bf4cca4f"
CLIENT_SECRET = "cfe60a68a11a48c29cf20cd80b04a5c3"

#https://developer.spotify.com/dashboard/applications to get client_id and client_secret
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=CLIENT_ID,
                                                           client_secret=CLIENT_SECRET))

def getPlaylist(id: str) -> List[Track]:
    '''
    Given a playlist ID, returns a list of Track objects corresponding to the songs on the playlist. See
    models.py for the definition of dataclasses Track, Artist, and AudioFeatures.
    We need the audio features of each track to populate the audiofeatures list.
    We need the genre(s) of each artist in order to populate the artists in the artist list.

    We've written parts of this function, but it's up to you to complete it!
    '''
    
    # fetch tracks data from spotify given a playlist id
    playlistdata = sp.playlist(id)
    tracks = playlistdata['tracks']['items']

    # fetch audio features based on the data stored in the playlist result
    track_ids = [x['track']['id'] for x in tracks]
    audio_features = sp.audio_features(track_ids)
    audio_info = {}  # Audio features list might not be in the same order as the track list
    for af in audio_features:
        audio_info[af['id']] = AudioFeatures(af['danceability'], \
                                             af['energy'], \
                                             af['key'],  \
                                             af['loudness'],  \
                                             af['mode'],  \
                                             af['speechiness'], \
                                             af['acousticness'], \
                                             af['instrumentalness'], \
                                             af['liveness'], \
                                             af['valence'], \
                                             af['tempo'], \
                                             af['duration_ms'], \
                                             af['time_signature'], \
                                             af['id'])


    # prepare artist dictionary
    artist_ids = [] # TODO: make a list of unique artist ids from tracks list
    for t in tracks:
        for artist in t['track']['artists']:
            if artist['id'] not in artist_ids:
                artist_ids.append(artist['id'])
    artists = {}
    for k in range(1+len(artist_ids)//50): # can only request info on 50 artists at a time!
        artists_response = sp.artists(artist_ids[k*50:min((k+1)*50,len(artist_ids))]) #what is this doing?
        for a in artists_response['artists']: # TODO: create the Artist for each id (see audio_info, above)
            artists[a['id']] = Artist(a['id'], \
                                      a['name'], \
                                      a['genres'])

    # populate track dataclass
    trackList = [Track(id = t['track']['id'], \
                       name= t['track']['name'], \
                       artists= [artists[a['id']] for a in t['track']['artists']], \
                       audio_features= audio_info[t['track']['id']]) \
                 for t in tracks]

    return trackList

''' this function is just a way of naming the list we're using. You can write
additional functions like "top Canadian hits!" if you want.'''
def getHot100() -> List[Track]:
    # Billboard hot 100 Playlist ID URI
    hot_100_id = "6UeSakyzhiEt4NB3UAd6NQ"
    return getPlaylist(hot_100_id)

# ---------------------------------------------------------------------

# part1: implement helper functions to organize data into DataFrames

def getGenres(t: Track) -> List[str]:
    '''
    TODO
    Takes in a Track and produce a list of unique genres that the artists of this track belong to
    '''
    unique_genres = []
    for artist in t.artists:
        for genre in artist.genres:
            if genre not in unique_genres:
                unique_genres.append(genre)
    return unique_genres

def doesGenreContains(t: Track, genre: str) -> bool:
    '''
    TODO
    Checks if the genres of a track contains the key string specified
    For example, if a Track's unique genres are ['pop', 'country pop', 'dance pop']
    doesGenreContains(t, 'dance') == True
    doesGenreContains(t, 'pop') == True
    doesGenreContains(t, 'hip hop') == False
    '''
    for gen in getGenres(t):
        if genre in gen:
            return True
    return False

def getTrackDataFrame(tracks: List[Track]) -> pd.DataFrame:
    '''
    This function is given.
    Prepare dataframe for a list of tracks
    audio-features: 'danceability', 'energy', 'key', 'loudness', 'mode', 'speechiness',
                    'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo',
                    'duration_ms', 'time_signature', 'id',
    track & artist: 'track_name', 'artist_ids', 'artist_names', 'genres',
                    'is_pop', 'is_rap', 'is_dance', 'is_country'
    '''
    # populate records
    records = []
    for t in tracks:
        to_add = asdict(t.audio_features) #converts the audio_features object to a dict
        to_add["track_name"] = t.name
        to_add["artist_ids"] = list(map(lambda a: a.id, t.artists)) # we will discuss this in class
        to_add["artist_names"] = list(map(lambda a: a.name, t.artists))
        to_add["genres"] = getGenres(t)
        to_add["is_pop"] = doesGenreContains(t, "pop")
        to_add["is_rap"] = doesGenreContains(t, "rap")
        to_add["is_dance"] = doesGenreContains(t, "dance")
        to_add["is_country"] = doesGenreContains(t, "country")

        records.append(to_add)

    # create dataframe from records
    df = pd.DataFrame.from_records(records)
    return df

# minor testing code:
top100Tracks = getHot100()
df = getTrackDataFrame(top100Tracks)
df_rap=df[df['is_rap']]
df_notrap=df[~df['is_rap']]
df_pop=df[df['is_pop']]
df_dance=df[df['is_dance']]
df_country=df[df['is_country']]
# you may want to experiment with the dataframe now!
# ---------------------------------------------------------------------
# Part2: The most popular artist of the week

def artist_with_most_tracks(tracks: List[Track]) -> (Artist, int):
    '''
    TODO
    List of tracks -> (artist, number of tracks the artist has)
    This function finds the artist with most number of tracks on the list
    If there is a tie, you may return any of the artists
    '''
    tally = Counter([art.name for t in tracks for art in t.artists]) # these structures will be useful!
    art_name = [name for name,count in tally.most_common(1)]
    num = [count for name,count in tally.most_common(1)]
    for t in tracks:
        for art in t.artists:
            if art.name == art_name[0]:
                return (art, num[0])

# minor testing code:
artist, num_track = artist_with_most_tracks(top100Tracks)
print("%s has the most number of tracks on this week's Hot 100 at a whopping %d tracks!" % (artist.name, num_track))

# Part3: Data Visualization

# 3.1 scatter plot of dancability-tempo colored by genre is_rap
ax=df_rap.plot.scatter(x="danceability", y="tempo",c='orange', label="is rap")
df_notrap.plot.scatter(x="danceability", y="tempo",c='grey',label="not rap", ax=ax)
plt.savefig('dancability-tempo.png')
plt.show()
# 3.1 scatter plot of dancability-speechiness colored by genre is_rap
ax=df_rap.plot.scatter(x="danceability", y="speechiness",c='orange', label="is rap")
df_notrap.plot.scatter(x="danceability", y="speechiness",c='grey',label="not rap", ax=ax)
plt.savefig('dancability-speechiness.png')
plt.show()
# 3.2 scatter plot (which genre is most similar to pop in terms in speechiness and energy?)
axi=df_pop.plot.scatter(x="speechiness", y="energy", c='pink', marker='o', label='pop')
df_dance.plot.scatter(x="speechiness", y="energy", c='cyan', marker='.', label='dance', ax=axi)
plt.savefig('pop-dance.png')
plt.show()
axi=df_pop.plot.scatter(x="speechiness", y="energy", c='pink', marker='o', label='pop')
df_country.plot.scatter(x="speechiness", y="energy", c='yellow', marker='.', label='country', ax=axi)
plt.savefig('pop-country.png')
plt.show()
axi=df_pop.plot.scatter(x="speechiness", y="energy", c='pink', marker='o', label='pop')
df_rap.plot.scatter(x="speechiness", y="energy", c='red', marker='.', label='rap', ax=axi)
plt.savefig('pop-rap.png')
plt.show()

# (Bonus) Part4:
# take a song that's not on the list, compute distance with the songs on the list and see if we get the same artist
def genres_in_top10(tracks: List[Track]) -> dict:
    '''
    Assuming given tracks are ordered form top to bottom in rank, function returns counts of genres in the top 10.
    '''
    tally = Counter([genre for t in tracks[0:10] for art in t.artists for genre in art.genres])
    return tally

