import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import os
from datetime import datetime
import math

st.set_page_config(layout="wide")
st.title('Sample AV Dashboard')

DATE_COLUMN = 'Time'
@st.cache_data
def load_data():
    f = []
    w = os.walk("./Data")
    for (dirpath, dirnames, filenames) in w:
        f.extend(dirnames)
    directories = sorted(f)
    gps_files = [f'./Data/{dir}/gps.csv' for dir in directories]
    velocity_files = [f'./Data/{dir}/velocity.csv' for dir in directories]
    mode_files = [f'./Data/{dir}/vehiclemode.csv' for dir in directories]

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
    
    vel_df['Timestamp'] = vel_df['Time'].copy()
    vel_df['Time'] = vel_df['Time'].round(3)

    vel_df.rename(columns={'data': 'velocity'}, inplace=True)
    df = pd.merge(df, vel_df, on='Time')
    
    df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN],unit='s')

    df = df.sort_values(by=['Timestamp'], ignore_index=True)

    df = df.groupby(['Timestamp', 'trip number']).agg({'latitude':'mean', 'longitude':'mean', 'altitude':'mean', 'mode':'min', 'velocity':'mean', 'Time':'min'})

    df.reset_index(inplace=True)
    df['Date'] = df['Time'].apply(lambda x: x.strftime('%Y-%m-%d'))

    unique_times = df['Date'].unique()
    unique_times = dict(zip(unique_times,list(range(1, len(unique_times)+1))))
    
    
    return df

data = load_data()

@st.cache_data
def get_trip_choices():
    return sorted(list(data['trip number'].unique()))

date_choices = get_trip_choices()

def trip_formatter(trip_num):
    date = str(data[data['trip number'] == trip_num].reset_index().loc[0, 'Date'])
    new_str = f'Trip {trip_num} ({date})'
    return new_str

col1, col2 = st.columns([3, 1])

# layer = pdk.Layer(
#     "TripsLayer",
#     data,
#     get_path="[longitude, latitude]",
#     get_timestamps="Timestamp",
#     get_color=[253, 128, 93],
#     width_min_pixels=5,
#     rounded=True,
#     trail_length=100000000000,
#     current_time=int(np.max(list(data["Timestamp"]))),
# )
# midpoint = ((np.max(data['latitude']) + np.min(data['latitude']))/2, (np.max(data['longitude']) + np.min(data['longitude']))/2)

# view_state = pdk.ViewState(latitude=midpoint[0],
#             longitude=midpoint[1],
#             zoom=15,
#             pitch=0)

# # Render
# r = pdk.Deck(layers=[layer], initial_view_state=view_state, map_style=None)
# st.pydeck_chart(r)

with st.sidebar:
    selectbox_state = st.multiselect("Choose a date", date_choices,  default=date_choices[0], format_func=trip_formatter)
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

    group_trip = filtered_data.groupby('trip number').agg(min_time = ('Time', 'min'), max_time = ('Time', 'max'))
    tot_seconds = (group_trip['max_time'] - group_trip['min_time']).dt.total_seconds()
    mean_seconds = tot_seconds.mean()
    hours = int(np.floor(((mean_seconds) / 60 / 60)))
    mean_seconds -= hours * 60 * 60
    minutes = int(np.floor(((mean_seconds) / 60)))
    mean_seconds -= minutes * 60
    seconds = int(np.floor(((mean_seconds))))

    st.metric('Mean Duration of Trip(s)', value=f'{str(hours).zfill(2)}:{str(minutes).zfill(2)}:{str(seconds).zfill(2)}')

    st.write(filtered_data)

    
    
    # filtered_data['Simplified Time'] = filtered_data['Time'].dt.second
   