from airflow import DAG
from datetime import datetime
from datetime import timedelta
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago 
# from spotify_etl import full_spotify_etl_function



# set some default arguments to be used across every operator
default_args = {
    'owner':'airflow',
    'depends_on_past':False,
    'start_date' : datetime(2022,10,15),
    'retries':1,
    'retry_delay': timedelta(minutes=1),
    'email_on_failure':True ,
    'email':['max_ong_@outlook.com'],
    'email_on_retry':False
    }

# all operators inherit from the baseoperator 

# # define our dag 
# dag = DAG(
#     'spotify_dag',
#     default_args = default_args,
#     description= 'Our first DAG with etl process',
#     schedule_interval = '@daily')


# run_etl = PythonOperator(
#     task_id = 'whole_spotify_etl',
#     provide_context = True,
#     python_callable = full_spotify_etl_function,
#     dag = dag
# )



# run_etl