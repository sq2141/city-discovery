#!/usr/bin/env python
# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import pandas as pd
import numpy as np
import psycopg2
from dash.dependencies import Input, Output, State

from matplotlib import pyplot as plt
import seaborn as sns
import folium
from folium import plugins

### Read data from SQL

# Python code to connect to Postgres
# You may need to modify this based on your OS, 
# as detailed in the postgres dev setup materials.
username = 'postgres'
password = 'samsam'
host     = 'localhost'
port     = '5432'
db_name  = 'cities_db'
engine = create_engine( 'postgresql://{}:{}@{}:{}/{}'.format(username, password, host, port, db_name) )

con = None
con = psycopg2.connect(database = db_name, user = username, password = password, 
                       host = host, port = port)

# Get cities table from SQL server
sql_query = """
SELECT * FROM cities_table;
"""
cities_df = pd.read_sql_query(sql_query,con, index_col = 'index')

# Get cos sims table from SQL server
sql_query = """
SELECT * FROM cosims_stacked_table;
"""
cosims_stacked_df = pd.read_sql_query(sql_query,con, index_col = ['0','1'])
cosims_df = cosims_stacked_df.unstack()



###

def generate_table(input_city, max_rows=10):
    
    input_index = cities_df.index[cities_df['City']==input_city][0] # Get index of input
    input_sims = pd.DataFrame(cosims_df.iloc[input_index]) # Get sims for input city
    sims_sorted = input_sims.sort_values(by=input_index, ascending=False) # Sort sims
    sims_top10 = sims_sorted.iloc[1:11]
    top10_index = sims_top10.index.get_level_values(1)
    top10_cities = cities_df.iloc[top10_index][['City','Country','Lat','Lon']]
    top10_names = cities_df.iloc[top10_index][['City','Country']]
    dataframe = top10_names    
    
    cities_map = folium.Map(location=[30, top10_cities['Lon'].mean()], zoom_start=2, 
    tiles='Mapbox Bright', width=950, height=550)
    top10_cities.apply(lambda row: folium.Marker(location=[row['Lat'], row['Lon']], popup = folium.Popup(row['City']+', '+row['Country'], parse_html=True)).add_to(cities_map), axis=1)
    cities_map.save('cities_map.html')
    
    out = html.Div(
        [html.Table(
            [html.Tr(            
            
                # Left column
                [html.Td(
                    # Header Row
                    [html.Tr([html.Th(col) for col in dataframe.columns])] +

                    # Body Row
                    [html.Tr([
                        html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
                    ]) for i in range(min(len(dataframe), max_rows))]
                )] +
                
                
                # Right column
                [html.Td(
                    html.Iframe(id='map', srcDoc=open('cities_map.html','r').read(), width='290%', height='500')
                )]                
            )]
             
        
        )]
    )
    return out


###


app = dash.Dash()
app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})

app.layout = html.Div(children=[
    
    html.H1(children='Suggested Cities',
           style = {'textAlign': 'center'}),
    
        
    dcc.Input(id='input-1-state', type='text', value='Montréal'),
    html.Button(id='submit-button', n_clicks=0, children='Submit'),
    html.Div(id='output-state')
 
])


@app.callback(Output('output-state', 'children'),
              [Input('submit-button', 'n_clicks')],
              [State('input-1-state', 'value')])
def update_output(n_clicks, input1):
    return generate_table(input1)


if __name__ == '__main__':
    app.run_server(debug=True)
