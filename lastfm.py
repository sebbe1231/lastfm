import requests
from PIL import Image
import pylast
import click
import json
import datetime
import os

api_key = [API_KEY]
api_secret = [API_SECRET]

network = pylast.LastFMNetwork(
    api_key=api_key, api_secret=api_secret)


@click.group(help='ANY AND ALL ARGUMENTS BEST INCASED IN \" \"')
def lastfm():
    pass

def asciify(img):
    try:
        r = requests.get(img, stream=True)
        if r.status_code != 200:
            raise
        img = Image.open(r.raw)
    except:
        print("Image could not be loaded")

    iw, ih = img.size
    height = os.get_terminal_size().lines
    width = round(height*2.5)
    img = img.resize((width, height))

    img = img.convert("L")
    pixels = img.getdata()
    imgchars = ["$", "@", "B", "%", "8", "&", "W", "M", "#", "*", "o", "a", "h", "k", "b", "d", "p", "q", "w", "m", "Z", "O", "0", "Q", "L", "C", "J", "U", "Y", "X", "z", "c", "v", "u", "n", "x", "r", "j", "f", "t", "/", "\\", "|", "(", ")", "1", "{", "}", "[", "]", "?", "-", "_", "+", "~", "<", ">", "i", "!", "l", "I", ";", ":", "\"", "^", "`", "'", ".", " "][::-1]
    ascii_img = ""

    for i, pixel in enumerate(pixels):
        if i%width == 0:
            ascii_img += "\n"
        ascii_img += imgchars[int(pixel/256*len(imgchars))]
    return ascii_img

@lastfm.command()
@click.argument('artist', nargs=-1)
def artist(artist):
    """Find the profile of a specific artist, must use the artist exact name"""
    artist = " ".join(artist)
    try:
        artist = network.get_artist(artist)
        
        #get short bio of artist
        print(f"\n{artist.get_bio_summary()} \n")
    except pylast.WSError:
        return print("Artist not found")
    print(f"\n{artist.get_name()}")

    # get the top tags for the artist
    top_tags = ""
    for tag in artist.get_top_tags(limit=10):
        top_tags = (f"{top_tags} | {tag[0]}")
    print(f"Tags: {top_tags}")
    # get the playcount for the artist
    print(f"Plays: {artist.get_playcount()}")
    # get similar artists
    print(f"Similar artists to {artist.name}:")
    for a in artist.get_similar(limit=10):
        print(f"    {a[0]}")
    # get top songs
    print("Top tracks:")
    for track in artist.get_top_tracks(limit=5):
        print(f"    {track[0]}")
    # get top albums
    print("Top albums:")
    for album in artist.get_top_albums():
        print(f"    {album[0]}")
    # url
    print(f"\n{artist.get_url()}")

@lastfm.command()
@click.argument('artist', nargs=-1)
def artist_bio(artist):
    """Get the full bio of an artist, as writen on last.fm"""
    artist = " ".join(artist)
    try:
        artist = network.get_artist(artist)
        print(f"{artist.get_name()} \n")
        print(f"{artist.get_bio_content()} \n")
        print(f"Bio created: {artist.get_bio_published_date()}")
    except pylast.WSError:
        return print("Artist not found")
    
@lastfm.command()
@click.argument('artist', nargs=-1)
def search_artist(artist):
    """Search in last.fm for an artist and get the 10 first ones"""
    artist = " ".join(artist)
    print(f"Searching for {artist}")
    artist_list = network.search_for_artist(artist)
    for i, a in enumerate(artist_list.get_next_page()):
        if i >= 10:
            break
        a = network.get_artist(a)
        print(f"{a} ({a.get_playcount()} plays): \n{a.get_url()} \n")


@lastfm.command()
@click.argument('user')
@click.argument('track_name', default=None, required=False)
@click.argument('track_artist', default=None, required=False)
@click.option('--period', '-p', default="PERIOD_OVERALL", required=False)
def user(user, track_name, track_artist, period):
    """Search for a user. To see users scrobbles on a track, use track_artist and track_name of that given song (must use "" for artist and name)(Leaving this unassinged gives user basic info)
    
    \b
    To get statistics during a period, set 'period' as:
    [alltime | all] = all time
    [7days | 7d] = past 7 days
    [1month| 1m] = past 1 month
    [3months | 3m] = past 3 months
    [6months | 6m] = past 6 months
    [12months | 12m] = past 12 months
    """
    try:
        user = network.get_user(user)
        print(user)
        print(f"Country: {user.get_country()}")
    except pylast.WSError:
        return print("User nor found")

    if track_artist and track_name:
        try:
            comp_track = user.get_track_scrobbles(artist=track_artist, track=track_name)
            print(f"\n{comp_track[0].track}")
            print(f"From \"{comp_track[0].album}\"")
            print(f"Last listened to: {comp_track[0].playback_date}")
            print(f"{user} has listened to {comp_track[0].track}, {len(comp_track)} times")
            return
        except IndexError:
            print("Wrong artist or track name \nUsage: lastfm [user] <artist> <track>")
            return
    
    periodtxt = "all time"
    if period != "PERIOD_OVERALL":
        period = period.lower()
        if period == "alltime" or period == "all":
            period = "PERIOD_OVERALL"
            periodtxt = "all time"
        if period == "7days" or period == "7d" or period == "7":
            period = "PERIOD_7DAYS"
            periodtxt = "Past 7 days"
        if period == "1month" or period == "1m":
            period = "PERIOD_1MONTH"
            periodtxt = "Past 1 month"
        if period == "3months" or period == "3m":
            period = "PERIOD_3MONTHS"
            periodtxt = "Past 3 months"
        if period == "6months" or period == "6m":
            period = "PERIOD_6MONTHS"
            periodtxt = "Past 6 months"
        if period == "12months" or period == "12m":
            period = "PERIOD_12MONTHS"
            periodtxt = "Past 12 months"

    #User currently listening activity, if there is activity
    print(f"Currently listening to: {user.get_now_playing()}")

    #User scrobbles
    print(f"Total scrobbles: {user.get_playcount()}")

    #User bio
    print(f"Account created: {str(datetime.datetime.fromtimestamp(user.get_unixtime_registered()))[:-8]}")

    #User recent tracks
    recent_tracks = '\n'.join([f'{i}. {track.track}' for i, track in enumerate(user.get_recent_tracks(limit=5), 1)])
    print(f"\nRecent tracks: \n{recent_tracks}")

    #User loved tracks
    loved_tracks = '\n'.join([f'{i}. {track.track}' for i, track in enumerate(user.get_loved_tracks(limit=3), 1)])
    print(f"\nLoved tracks: \n{loved_tracks}")

    #User top artists
    top_artists = '\n'.join([f'{i}. {artist.item.name}' for i, artist in enumerate(
        user.get_top_artists(limit=5, period=period), 1)])
    print(f"\nTop artists ({periodtxt}):\n{top_artists}")
    
    #User top tracks
    top_tracks = '\n'.join([f'{i}. {track.item}' for i, track in enumerate(user.get_top_tracks(limit=5, period=period), 1)])
    print(f"\nTop tracks ({periodtxt}): \n{top_tracks}")

    #User top albums
    top_albums = '\n'.join([f'{i}. {album.item}' for i, album in enumerate(user.get_top_albums(limit=5, period=period), 1)])
    print(f"\nTop albums ({periodtxt}): \n{top_albums}")
    
    print(f"\n{user.get_url()}")

@lastfm.command()
@click.argument('track_name')
@click.argument('artist_name')
def track(track_name, artist_name):
    """Get info on a track, must use the exact artist name and track name, incase each part in \" \""""
    try:
        track = network.get_track(artist_name, track_name)
        print(f"Track: {track.get_name()}")
    except pylast.WSError:
        return print("Track not found")

    top_tags = ""
    for tag in track.get_top_tags(limit=10):
        top_tags = (f"{top_tags} | {tag[0]}")
    try:
        print(asciify(track.get_cover_image()))
    except IndexError:
        print("No uploaded cover image on last.fm")

    print(f"\nTags: {top_tags}")
    print(f"Artist: {track.get_artist()}")
    print(f"From: {track.get_album()}")
    print(f"Plays: {track.get_playcount()}")

    similar_tracks = '\n'.join([f'{i}. {tracks.item}' for i, tracks in enumerate(track.get_similar(limit=10), 1)])
    print(f"\nSimilar artists: \n{similar_tracks}")

    track.get_url()

@lastfm.command()
@click.argument('track_name')
@click.argument('track_artist', required=False, default="")
def search_track(track_name, track_artist):
    """Search for a trackname, artist name is not required"""
    track = network.search_for_track(artist_name=track_artist, track_name=track_name)
    for i, t in enumerate(track.get_next_page()):
        if i >= 10:
            break
        #find the track and print the info
        t = network.get_track(artist=t.get_artist(), title=t.get_title())
        print(f"{t.get_artist()} - {t.get_name()} ({t.get_playcount()} plays) \n{t.get_url()}\n")

@lastfm.command()
@click.argument('title')
@click.argument('artist')
def album(title, artist):
    """Search up a specific album"""
    try:
        album = network.get_album(artist=artist, title=title)
        print(album.get_title())
    except pylast.WSError:
        return print("Album not found")

    top_tags = ""
    for tag in album.get_top_tags(limit=10):
        top_tags = (f"{top_tags} | {tag[0]}")
    try:
        print(asciify(album.get_cover_image()))
    except AttributeError:
        print("No cover image uploaded on last.fm")
    print(f"\nTitle: {album.get_title()}")
    print(f"Tags: {top_tags}")
    print(f"Artist: {album.get_artist()}")
    print(f"Plays: {album.get_playcount()}")
    for i, track in enumerate(album.get_tracks(), 1):
        track = network.get_track(artist=track.get_artist(), title=track.get_title())
        print(f"{i}. {track.get_artist()} - {track.get_name()} ({track.get_playcount()})")

@lastfm.command()
@click.argument('album_title')
def search_album(album_title):
    """Search for an album"""
    album = network.search_for_album(album_name=album_title)
    for i, track in enumerate(album.get_next_page()):
        if i >=10:
            break
        print(f"{track} \n{track.get_url()}\n")

@lastfm.command()
def top_artist():
    """Get the world wide top artists"""
    for art in network.get_top_artists(limit=15):
        print(f"{art.item} ({network.get_artist(art.item).get_playcount()} plays)")

@lastfm.command()
def top_track():
    """Get the world wide top tracks"""
    for t in network.get_top_tracks(limit=15):
        print(f"{t.item} ({network.get_track(artist=t.item.get_artist(), title=t.item.get_title()).get_playcount()} plays)")

@lastfm.command()
@click.argument('country', nargs=-1)
def geo_top_artists(country):
    """Get the top artist of a country (use "countries" for the list of countries)"""
    country = " ".join(country)
    if country == "countries":
        with open('C:\\Run\\requirements\\ISO_3166-1.json') as file:
            data = json.load(file)

        for code, country in data.items():
            print(f"{code} - {country}")
        return
    try:
        country = network.get_geo_top_artists(country=country, limit=15)
    except pylast.WSError:
        return print("Invalid country")
    for i, artist in enumerate(country, 1):
        print(f"{i}. {artist.item} ({network.get_artist(artist.item).get_playcount()} plays)")
@lastfm.command()
@click.argument('country', nargs=-1)
def geo_top_tracks(country):
    """Get the top tracks of a country (use "countries" for the list of countries)"""
    country = " ".join(country)
    if country == "countries":
        if country == "countries":
            with open('C:\\Run\\requirements\\ISO_3166-1.json') as file:
                data = json.load(file)

            for code, country in data.items():
                print(f"{code} - {country}")
            return
    try:
        country = network.get_geo_top_tracks(country=country, limit=15)
    except pylast.WSError:
        return print("Invalid country")
    for i, t in enumerate(country, 1):
        print(f"{i}. {t.item} ({network.get_track(artist=t.item.get_artist(), title=t.item.get_title()).get_playcount()} plays)")

if __name__ == '__main__':
    lastfm()
