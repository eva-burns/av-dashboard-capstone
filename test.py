import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk

st.set_page_config(layout="wide")
st.title('Sample AV Dashboard')

DATE_COLUMN = 'Time'
@st.cache_data
def load_data():
    df = pd.read_csv("../AV Sample Data/gps.csv")[['Time', 'latitude', 'longitude', 'altitude']]

    # df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN])
    return df

data = load_data()

# st.subheader('Map of all pickups at %s:00' % hour_to_filter)


col1, col2 = st.columns([3, 1])

with st.sidebar:
    vals = sorted(set(data['Time']))

    start_color, end_color = st.select_slider(
        'Select a range of color wavelength',
        key='slider',
        options=vals,
        value=(vals[0], vals[len(vals)-1]))
    st.write(start_color)
    
    filtered_data = data[data['Time'] >= start_color]
    filtered_data = filtered_data[filtered_data['Time'] <= end_color]
    # st.empty()

with col1:
    midpoint = ((np.max(filtered_data['latitude']) + np.min(filtered_data['latitude']))/2, (np.max(filtered_data['longitude']) + np.min(filtered_data['longitude']))/2)

    st.pydeck_chart(pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(
            latitude=midpoint[0],
            longitude=midpoint[1],
            zoom=12,
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
    st.metric(label="Average Velocity", value=123)
    
    st.write(filtered_data)