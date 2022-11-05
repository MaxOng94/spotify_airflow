

# require to wrap all our import libraries within the spotify function 
from airflow.decorators import dag, task
from airflow import DAG
from datetime import datetime
from datetime import timedelta
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago 
from airflow.models import xcom_arg
import pathlib
import pandas as pd 
import sqlalchemy 
import configparser as ConfigParser
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# set some default arguments to be used across every operator
default_args = {
    'owner':'airflow',
    'depends_on_past':False,
    'start_date' : datetime(2022,10,17),
    'retries':1,
    'retry_delay': timedelta(minutes=1),
    'email_on_failure':True ,
    'email':['max_ong_@outlook.com'],
    'email_on_retry':False,
    'schedule_interval': '@daily'
    }

# all operators inherit from the baseoperator 

# define our dag 
@dag(
   'spotify_dag_new',
   schedule_interval= '@daily',    # default_args = default_args
    default_args = default_args,
    tags = ['spotify_example']
    )
# @task.virtualenv(task_id="virtualenv_python", requirements=["pandas==1.5.0"], system_site_packages=False)
def full_spotify_etl_function(**kwargs):
   
# ,"SQLAlchemy==1.4.41","spotipy==2.20.0"



    # config values ======================================
    CURRENT_PATH_DIR= pathlib.Path(__file__).absolute()
    GRANDPARENT_PATH = pathlib.Path(__file__).absolute().parents[1]

    CONF_PATH = GRANDPARENT_PATH.joinpath("configuration/config.ini")

    cf_parser= ConfigParser.ConfigParser()
    cf_parser.read(CONF_PATH)


    # TOKEN = cf_parser.get('spotify_details','token')
    WEBSITE = cf_parser.get('spotify_details','website')
    CLIENT_ID = cf_parser.get('spotify_details','client_id')
    CLIENT_SECRET = cf_parser.get('spotify_details','client_secret')
    REDIRECT_URL = cf_parser.get('spotify_details','redirect_url')
    SCOPE = cf_parser.get('spotify_details','scope')
    DB_LOCATION = cf_parser.get('database','db_location_postgres')

    config_dictionary = {
    'website':WEBSITE,
    'client_id':CLIENT_ID,
    'client_secret':CLIENT_SECRET,
    'redirect_url':REDIRECT_URL,
    'scope':SCOPE,
    'db_location':DB_LOCATION
    }

    # ===========================================================

    @task(task_id = 'check_data_valid')
    def check_if_valid_data(df:pd.DataFrame):
        # check if dataframe is empty, it means there were no songs listened to
        if df.empty:
            print('No songs downloaded. Finishing execution')
            return False 

        # Primary key check 
        if pd.Series(df['played_at_list']).is_unique:       # this check helps us understand that there are no duplicate rows in our database
            pass 
        else: 
            raise Exception("Primary Key check if violated")  # here pipeline fail, maybe can send email to me
        yesterday = datetime.now() - timedelta(days = 1)
        # just check yesterday's date at 0 hour, 0 minute, 0 second and 0 microseconds
        yesterday = yesterday.replace(hour = 0,minute = 0,second =0,microsecond =0 )
        # timestamps = df['timestamps'].tolist()
        df = df[df['timestamps']== yesterday.strftime("%Y-%m-%d")]

        songs_json= df.to_json()


        # for timestamp in timestamps:
        #     # strptime --> converts string to time
        #      # if we catch records that are not yesterday, we want the pipeline to raise exception 
        #     if datetime.strptime(timestamp,"%Y-%m-%d")!= yesterday:
        #         raise Exception("At least one of the songs does not come within last 24 hours")
        return songs_json

    #=====================spotify functions ===============================
    # @task(multiple_outputs = True,task_id = 'create_spotfiy_api_details')
    def create_spotify_api_details(config_dictionary):
        auth_manager=SpotifyOAuth(scope=config_dictionary['scope'],
                                    client_id =config_dictionary['client_id'] ,
                                    client_secret = config_dictionary['client_secret'],
                                    redirect_uri = config_dictionary['redirect_url'])

        spotify = spotipy.Spotify(auth_manager=auth_manager)
        return auth_manager,spotify
        # return {'auth_manager':auth_manager,'spotify':spotify}

    # @task(multiple_outputs = True,task_id = 'refresh_spotify_tokens')
    def refresh_spotify_api_details(auth_manager, spotify,config_dictionary):

        token_info = auth_manager.cache_handler.get_cached_token()

        if auth_manager.is_token_expired(token_info):
            auth_manager, spotify = create_spotify_api_details(config_dictionary)
        return auth_manager,spotify
        # return {'auth_manager':auth_manager,'spotify':spotify}
    #=====================================================================

    @task(task_id = 'update_database')
    def update_database(DB_LOCATION,json_data):
        # start database
        # if value:

        songs_table = pd.read_json(json_data)

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
            print("New songs populated in database!")
        except: 
            print("Data already exists in database")
        # conn.close()
        print("database closed successfully")
        # else: 
        #     check_if_valid_data(songs_table)


    # there's a reason to 
    # https://stackoverflow.com/questions/64202437/airflow-got-an-unexpected-keyword-argument-conf
    # @task()
    # def run_spotify_etl(config_dictionary):

       # headers = {
        #     "Accept": "application/json",
        #     "Content-Type": "application/json",
        #     "Authorization" : "Bearer {token}".format(token=TOKEN)
        # }

    today = datetime.now().replace(hour = 0,second = 0,minute =0,microsecond=0)
    # because everyday we want to see the songs we've listed to for the 
    # previous 24 hrs
    yesterday = today - timedelta(days =1)
    # unix timestamp in miliseconds, that's why need to * 1000
    yesterday_unix_timestamp = int(yesterday.timestamp()) * 1000
    # r = requests.get(WEBSITE.format(time=yesterday_unix_timestamp),headers = headers)
    # get data in json form
    # data =sp.current_user_recently_played(after =yesterday_unix_timestamp )
    auth_manager,spotify = create_spotify_api_details(config_dictionary)
    # spotify_api_details_dict = create_spotify_api_details(config_dictionary)
    # # print(dir(spotify_api_details_dict))
    # auth_manager = spotify_api_details_dict['auth_manager']
    # spotify = spotify_api_details_dict['spotify']

    # @task(task_id= "get_data_from_api")
    def get_data_from_api(spotify,yesterday_unix_timestamp):
        data = spotify.current_user_recently_played(after =yesterday_unix_timestamp)
        return data 



    while True:
        auth_manager,spotify = refresh_spotify_api_details(auth_manager, spotify,config_dictionary)

        # spotify = spotify_api_details_dict['spotify']
        # print(spotify['spotify'])
        data = get_data_from_api(spotify,yesterday_unix_timestamp)
        # data = spotify.current_user_recently_played(after =yesterday_unix_timestamp)
        try:
            # if there are any songs, items will not be equals to zero 
            if data['items'] != []:
                artist_name = []
                song_names = []
                played_at_list = []
                timestamps = []         
                for i in data['items']:
                    if i['played_at'][:10]!= today.strftime("%Y-%m-%d"):
                        song_names.append(i['track']['name'])
                        played_at_list.append(i['played_at'])
                        timestamps.append(i['played_at'][:10])
                        artist_name.append(i['track']['artists'][0]['name'])           
                # data is in dataframe format now
                songs_table = pd.DataFrame([played_at_list,timestamps,artist_name,song_names]).T
                songs_table.columns = ['played_at_list','timestamps','artist_name','song_names']            
                # update database only if it pass the check 

                # update_database(config_dictionary['db_location'],songs_table,check_if_valid_data)
                new_songs_table = check_if_valid_data(songs_table)
                update_database(config_dictionary['db_location'],new_songs_table)

                # if check_if_valid_data(songs_table):
                #     update_database(config_dictionary['db_location'],songs_table)
                # else: 
                #     print(check_if_valid_data(songs_table))
                # once you updated the database, break out of the loop
                break
            # if there are no data that day, don't even open up the database, skip that day    
            else:
                print("No songs played yesterday")
                # if there are no songs, break out 
                break 
        except:
            print("Error with database or spotify data returned")
    # run_spotify_etl = run_spotify_etl(config_dictionary)
spotify_etl_full= full_spotify_etl_function()

