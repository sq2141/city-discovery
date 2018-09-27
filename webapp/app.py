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
from nltk import FreqDist
import ast
import unicodedata
import base64
from matplotlib import pyplot as plt
import seaborn as sns
import folium
from folium import plugins
import glob

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
cities_df.sort_index(inplace=True)

# Get cos sims table from SQL server
sql_query = """
SELECT * FROM cosims_stacked_table;
"""
cosims_stacked_df = pd.read_sql_query(sql_query,con, index_col = ['0','1'])
cosims_df = cosims_stacked_df.unstack()

# Load background image
bg_image = base64.b64encode(open('chicago_skyline3.jpg', 'rb').read())


def strip_accents_lowercase(text):
    try:
        text = unicode(text, 'utf-8')
    except NameError: # unicode is a default on python 3 
        pass
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore')
    text = text.decode("utf-8")
    return str(text).lower()


def get_descriptors(pooled_tokens):
    words = []
    for item in ast.literal_eval(pooled_tokens):
        words.append(item)
            
    fdist = FreqDist(words)

    common_words = []
    for item in fdist.most_common(5):
        common_words.append(item[0])
        
    return ', '.join(common_words)+'...'

def load_photos(my_index, img_num):
    folder_path = '../data/dl-images/'+str(my_index)+'/'
    img_list = [f for f in glob.glob(folder_path+'*.jpg')] # get all image file names for a given city
    try:
        encoded_image = base64.b64encode(open(img_list[img_num], 'rb').read())   # open img
    except IndexError:
        encoded_image = base64.b64encode(b'null')
    return encoded_image    


def generate_table(input_city, max_rows=10):
    
    # preprocess input text and city names to be comparable
    input_city = input_city.lower() # 
    cities_df['City_unicode'] = cities_df['City'].apply(strip_accents_lowercase)
    
    # check if input city exists in database
    if input_city not in cities_df['City_unicode'].values:
        return html.Div('Sorry, this city is not in the dataset',style = {'textAlign': 'center', 'margin-bottom':'100px'})   
        
    # get top suggestions
    input_index = cities_df.index[cities_df['City_unicode']==input_city][0] # Get index of input
    input_sims = pd.DataFrame(cosims_df.iloc[input_index]) # Get sims for input city
    sims_sorted = input_sims.sort_values(by=input_index, ascending=False) # Sort sims
    sims_top = sims_sorted.iloc[1:21]
    top_index = sims_top.index.get_level_values(1)
    top_cities = cities_df.iloc[top_index][['City','Country','Lat','Lon','Pooled_tokens']]
    
#     # Add frequent words, filter out cities with empty data/Ffrequent words
#     top_cities['Frequent words'] = top_cities['Pooled_tokens'].apply(get_descriptors)
#     top_names = top_cities[['City','Country','Frequent words','Lat','Lon']]
#     top_names = top_names[top_names['Frequent words']!='...'].head(10) #First 10 results with frequent words)
        
    ### TESTING
    # get photos for top hits 
    top_cities['my_index'] = top_cities.index # get index for top cities only
    top_cities['Photos'] = top_cities['my_index'].apply(load_photos, img_num=0)
    top_cities['Photo1'] = top_cities['my_index'].apply(load_photos, img_num=1)
    top_cities['Photo2'] = top_cities['my_index'].apply(load_photos, img_num=2)
    top_cities['Photo3'] = top_cities['my_index'].apply(load_photos, img_num=3)
    top_cities['Photo4'] = top_cities['my_index'].apply(load_photos, img_num=4)


    
    
    top_names = top_cities[['City','Country','Photos','Photo1','Photo2','Photo3','Photo4','Lat','Lon']].head(10)
    dataframe = top_names[['City','Country','Photos','Photo1','Photo2','Photo3','Photo4']]    
    ### TESTING
    
    # make map
    cities_map = folium.Map(location=[30, top_cities['Lon'].mean()], zoom_start=2, 
    tiles='Mapbox Bright', width=950, height=550)
    top_names.apply(lambda row: folium.Marker(location=[row['Lat'], row['Lon']], 
                                              popup = folium.Popup(row['City']+','+row['Country'],
                                              parse_html=True)).add_to(cities_map), axis=1)
    cities_map.save('cities_map.html')
    
    out = html.Div(
        [html.Table(
            
            # Header Row
            [html.Tr([html.Th(col, style={'border':'none'}) for col in dataframe.columns[:2]])] +

            # Body Rows
            [html.Tr([
                html.Td(dataframe.iloc[i][col]) for col in dataframe.columns[:2]] ### fill name and country cols only
                + 
                [html.Td(
                    [html.Img(src='data:image/jpeg;base64,{}'.format(dataframe.iloc[i]['Photos'].decode('ascii')),
                                 style = {'height':'100px', 'width':'150px'}),
                    html.Img(src='data:image/jpeg;base64,{}'.format(dataframe.iloc[i]['Photo1'].decode('ascii')),
                                 style = {'height':'100px', 'width':'150px','margin-left':'10px'}),
                    html.Img(src='data:image/jpeg;base64,{}'.format(dataframe.iloc[i]['Photo2'].decode('ascii')),
                                 style = {'height':'100px', 'width':'150px','margin-left':'10px'}),
                    html.Img(src='data:image/jpeg;base64,{}'.format(dataframe.iloc[i]['Photo3'].decode('ascii')),
                                 style = {'height':'100px', 'width':'150px','margin-left':'10px'}),
                    html.Img(src='data:image/jpeg;base64,{}'.format(dataframe.iloc[i]['Photo4'].decode('ascii')),
                                 style = {'height':'100px', 'width':'150px','margin-left':'10px'})
                    ]
                ) 
            ]) for i in range(min(len(dataframe), max_rows))],

  

            
            # Table style
            style = {'width':'80%','margin':'auto','display':'block', 'padding-left':'7%'}
        ),
        
        # World Map Div
        html.Div(
            html.Iframe(id='map', srcDoc=open('cities_map.html','r').read(), width='100%', height='570'),
            style = {'padding-left':'15%','padding-right':'15%','padding-top':'50px'}
        )]            
    )
    return out


###



app = dash.Dash()
app.css.config.serve_locally = True
app.scripts.config.serve_locally = True
dcc._css_dist[0]['relative_package_path'].append('mycss.css')
#app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})
app.title = 'LeapFrog'

app.layout = html.Div(children=[
    
    # Header
    html.Div(
        html.H3(
            children='LeapFrog',style = {'textAlign': 'center'}),
        style = {'position':'fixed','z-index':'10','background-color':'white','width':'100%'}
    ),
    
    # Splash background image
    html.Div(html.Img(src='data:image/jpeg;base64,{}'.format(bg_image.decode('ascii')),
                      style = {'width':'100%', 'padding':'0','margin':'0','box-sizing':'border-box'})),
    
    # Space and Prompt
    html.H5('Enter a city you like:', style = {'margin':'auto', 'display':'block', 'margin-top':'50px', 
                                               'margin-bottom':'10px','text-align':'center'},
           id='prompt-text'),
    
    # Input/Output
    html.Div([
        dcc.Input(id='input-1-state', type='text', placeholder='e.g. Buenos Aires',
                  style = {'margin':'auto','display':'block'}),
        html.Button(id='submit-button', n_clicks=0, children='Submit',
                    style = {'margin':'auto', 'margin-top':'10px','display':'block', 'margin-bottom':'50px'}),
        html.Div(id='output-state', style = {'margin':'auto', 'display':'block'})
    ],
    style = {'width':'100%','margin':'auto', 'display':'block'}
    
    ),
    
    # Footer
    html.Div(style = {'height':'200px'})
    
 
])


@app.callback(Output('output-state', 'children'),
              [Input('submit-button', 'n_clicks')],
              [State('input-1-state', 'value')])
def update_output(n_clicks, input1):
    return generate_table(input1)


if __name__ == '__main__':
    app.run_server(debug=True)
