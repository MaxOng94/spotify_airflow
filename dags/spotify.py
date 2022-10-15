from airflow import DAG
from datetime import timedelta
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago 



# set some default arguments to be used across every operator
default_args = {
    'owner':'airflow',
    'depends_on_past':False,
    'retries':1,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure':False ,
    'email_on_retry':False
    }

# all operators inherit from the baseoperator 

