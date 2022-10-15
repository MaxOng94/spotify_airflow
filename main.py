import pandas as pd 
import sqlalchemy 
import requests 
import json 
import datetime 
import configparser as ConfigParser
import pathlib
import sqlalchemy
import sqlite3
import spotipy
from spotipy.oauth2 import SpotifyOAuth




# config values ======================================
CURRENT_PATH_DIR= pathlib.Path(__file__).absolute()
PARENT_PATH = pathlib.Path(__file__).parent.absolute()

CONF_PATH = PARENT_PATH.joinpath("configuration/config.ini")

cf_parser= ConfigParser.ConfigParser()
cf_parser.read(CONF_PATH)


# TOKEN = cf_parser.get('spotify_details','token')
WEBSITE = cf_parser.get('spotify_details','website')
CLIENT_ID = cf_parser.get('spotify_details','client_id')
CLIENT_SECRET = cf_parser.get('spotify_details','client_secret')
REDIRECT_URL = cf_parser.get('spotify_details','redirect_url')
SCOPE = cf_parser.get('spotify_details','scope')



DB_LOCATION = cf_parser.get('database','db_location_postgres')
# ===========================================================


def check_if_valid_data(df:pd.DataFrame) -> bool:
    # check if dataframe is empty, it means there were no songs listened to
    if df.empty:
        print('No songs downloaded. Finishing execution')
        return False 

    # Primary key check 
    if pd.Series(df['played_at_list']).is_unique:       # this check helps us understand that there are no duplicate rows in our database
        pass 
    else: 
        raise Exception("Primary Key check if violated")  # here pipeline fail, maybe can send email to me
    yesterday = datetime.datetime.now() - datetime.timedelta(days = 1)
    # just check yesterday's date at 0 hour, 0 minute, 0 second and 0 microseconds
    yesterday = yesterday.replace(hour = 0,minute = 0,second =0,microsecond =0 )
    timestamps = df['timestamps'].tolist()

    for timestamp in timestamps:
        # strptime --> converts string to time
         # if we catch records that are not yesterday, we want the pipeline to raise exception 
        if datetime.datetime.strptime(timestamp,"%Y-%m-%d")!= yesterday:
            raise Exception("At least one of the songs does not come within last 24 hours")
    return True

#=====================spotify functions ===============================
def create_spotify():
    auth_manager=SpotifyOAuth(scope=SCOPE,
                                client_id =CLIENT_ID ,
                                client_secret = CLIENT_SECRET,
                                redirect_uri = REDIRECT_URL)

    spotify = spotipy.Spotify(auth_manager=auth_manager)

    return auth_manager,spotify

def refresh_spotify(auth_manager, spotify):

    token_info = auth_manager.cache_handler.get_cached_token()

    if auth_manager.is_token_expired(token_info):
        auth_manager, spotify = create_spotify()
    return auth_manager, spotify
#=====================================================================


def update_database(DB_LOCATION,songs_table):
    # start database
    engine = sqlalchemy.create_engine(DB_LOCATION)
    # conn = sqlite3.connect('james_played_tracks.sqlite')
    # cursor = conn.cursor()            
    sql_query = """
    CREATE TABLE IF NOT EXISTS james_played_tracks(
        played_at_list VARCHAR(200), 
        timestamps VARCHAR(200),
        artist_name VARCHAR(200), 
        song_names VARCHAR(200),
        CONSTRAINT primary_key_constraint PRIMARY KEY (played_at_list)
    )
    """
    engine.execute(sql_query)
    print("Opened database successfully")  
    
    # update database 
    try: 
        songs_table.to_sql(name = 'james_played_tracks',con = engine, if_exists= 'append',index = False)
    except: 
        print("Data already exists in database")
    # conn.close()
    print("database closed successfully")
        


if __name__ == '__main__':

    # headers = {
    #     "Accept": "application/json",
    #     "Content-Type": "application/json",
    #     "Authorization" : "Bearer {token}".format(token=TOKEN)
    # }

    today = datetime.datetime.now()
    # because everyday we want to see the songs we've listed to for the 
    # previous 24 hrs
    yesterday = today - datetime.timedelta(days =1)
    # unix timestamp in miliseconds, that's why need to * 1000
    yesterday_unix_timestamp = int(yesterday.timestamp()) * 1000


    # r = requests.get(WEBSITE.format(time=yesterday_unix_timestamp),headers = headers)
    # get data in json form
    # data =sp.current_user_recently_played(after =yesterday_unix_timestamp )

    auth_manager, spotify = create_spotify()

    while True:
        auth_manager, spotify = refresh_spotify(auth_manager, spotify)
        data = spotify.current_user_recently_played(after =yesterday_unix_timestamp)

        try:
            # if python not equals to zero 
            if data['items'] != []:
                artist_name = []
                song_names = []
                played_at_list = []
                timestamps = []         
                for i in data['items']:
                    song_names.append(i['track']['name'])
                    played_at_list.append(i['played_at'])
                    timestamps.append(i['played_at'][:10])
                    artist_name.append(i['track']['artists'][0]['name'])            
                # data is in dataframe format now
                songs_table = pd.DataFrame([played_at_list,timestamps,artist_name,song_names]).T
                songs_table.columns = ['played_at_list','timestamps','artist_name','song_names']            

                # update database
                update_database(DB_LOCATION,songs_table)
                break
            # if there are no data that day, don't even open up the database, skip that day    
            else:
                print("No songs played today")
        except:
            print("Error with database or spotify data returned")
    


    # print(CONF_PATH)
    # print(cf_parser.get('spotify_details','user_id'))
    # print(cf_parser.get('sqlite','db_location'))
    # print(r)
    # data = r.json()
    # print(data)

