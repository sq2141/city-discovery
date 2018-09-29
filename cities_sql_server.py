#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import psycopg2
import pandas as pd

# Database and connection specifics
username = 'postgres'
password = 'samsam'
host     = 'localhost'
port     = '5432'
db_name  = 'cities_db'

# Create an engine, or a connection to a database
engine = create_engine( 'postgresql://{}:{}@{}:{}/{}'.format(username, password, host, port, db_name) )
print(engine.url)

# Create the database if it doesn't exist already
if not database_exists(engine.url):
    create_database(engine.url)
print(database_exists(engine.url))

# Read and insert narrow cities dataframe
cities_narrow = pd.read_csv('cities_narrow.csv', index_col = 0)
cities_narrow.to_sql('cities_narrow', engine, if_exists='replace')

# Read .csv into pandas dataframe
#cities = pd.read_csv('cities_text_processed_df.csv', index_col = 0 )
#cosims_stacked = pd.read_csv('data/cos_sims_stacked.csv', index_col=[0,1], header = None)

# Insert my data tables into SQL database
#cities.to_sql('cities_table', engine, if_exists='replace')
#cosims_stacked.to_sql('cosims_stacked_table', engine, if_exists='replace')

print('Insert finished')
