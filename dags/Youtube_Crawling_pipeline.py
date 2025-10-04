import os
import airflow
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.operators.email_operator import EmailOperator
from airflow.operators.slack_operator import SlackAPIPostOperator
from airflow.operators.postgres_operator import PostgresOperator
from airflow.operators.mysql_operator import MySqlOperator
from airflow.operators.sftp_operator import SFTPOperator
from airflow.operators.hive_operator import HiveOperator


















