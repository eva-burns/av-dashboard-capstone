import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import os
from datetime import datetime

st.set_page_config(layout="wide")
st.title('Sample AV Dashboard')

DATE_COLUMN = 'Time'
@st.cache_data
def load_data():
    f = []
    w = os.walk("./Data")
    for (dirpath, dirnames, filenames) in w:
        f.extend(dirnames)
    dirnames = sorted(dirnames)
    gps_files = [f'./Data/{dir}/gps.csv' for dir in f]
    velocity_files = [f'./Data/{dir}/velocity.csv' for dir in f]
    mode_files = [f'./Data/{dir}/vehiclemode.csv' for dir in f]

    df = pd.DataFrame()
    i = 1
    for file in gps_files:
        temp_df = pd.read_csv(file)[['Time', 'latitude', 'longitude', 'altitude']]
        temp_df['trip number'] = i
        df = pd.concat([df, temp_df], axis=0)
        i += 1
    df['Time'] = df['Time'].round(3)

    mode_df = pd.DataFrame()
    i = 1
    for file in mode_files:
        temp_df = pd.read_csv(file)[['Time', 'data']]
        mode_df = pd.concat([mode_df, temp_df], axis=0)
        i += 1
    mode_df.rename(columns={'data': 'mode'}, inplace=True)
    mode_df['Time'] = mode_df['Time'].round(3)
    df = pd.merge(df, mode_df, on='Time')

    vel_df = pd.DataFrame()
    i = 1
    for file in velocity_files:
        temp_df = pd.read_csv(file)[['Time', 'data']]
        vel_df = pd.concat([vel_df, temp_df], axis=0)
        i += 1
    vel_df['Time'] = vel_df['Time'].round(3)
    vel_df.rename(columns={'data': 'velocity'}, inplace=True)
    df = pd.merge(df, vel_df, on='Time')

    df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN],unit='s')

    df = df.sort_values(by=['Time'], ignore_index=True)
    
    return df

data = load_data()

@st.cache_data
def get_trip_choices():
    return sorted(list(set(data['trip number'])))

date_choices = get_trip_choices()

def trip_formatter(trip_num):
    date = list(data.loc[data['trip number'] == trip_num,'Time'])[0].floor('s')
    new_str = f'Trip {trip_num} ({date})'
    return new_str

col1, col2 = st.columns([3, 1])


with st.sidebar:
    
    selectbox_state = st.multiselect("Choose a date", date_choices,  date_choices, format_func=trip_formatter)
    if len(selectbox_state) == 0:
        filtered_data = data.copy()
        st.write("Please enter trip number")
    else:
        filtered_data = data[data['trip number'].isin(selectbox_state)]

with col1:
    midpoint = ((np.max(filtered_data['latitude']) + np.min(filtered_data['latitude']))/2, (np.max(filtered_data['longitude']) + np.min(filtered_data['longitude']))/2)

    st.pydeck_chart(pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(
            latitude=midpoint[0],
            longitude=midpoint[1],
            zoom=15,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
                'ScatterplotLayer',
                data=filtered_data,
                get_position='[longitude, latitude]',
                get_color='[200, 30, 0, 160]',
                get_radius=10,
            ),
        ],
    ))

with col2:
    st.metric(label="Average Velocity", value=round(np.mean(filtered_data['velocity']), 4))

    st.write(data)
    