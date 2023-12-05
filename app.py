import streamlit as st
import pandas as pd
import numpy as np
import folium
import branca.colormap as cm
import streamlit.components.v1 as components
import plotly.express as px 
import pyodbc

st.set_page_config(layout="wide")
st.title('US Ignite Fort Carson AV Dashboard')

DATE_COLUMN = 'Time'
@st.cache_data
def load_data():
    # # Construct the connection string
    connection_string = 'Driver={ODBC Driver 17 for SQL Server};Server=tcp:avops.database.windows.net,1433;Database=avops-sql-dev;Uid=eva;Pwd=enkAEcwIZnKmlb/S;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
    connection=None
    try:
        # Connect to the Azure Database
        connection = pyodbc.connect(connection_string)
        connection.setdecoding(pyodbc.SQL_CHAR, encoding='latin1')
        connection.setencoding('latin1')

        df = pd.read_sql('SELECT * FROM dbo."1s_av_data";',connection)

    except Exception as e:
        print(f"Error: {str(e)}")

    finally:
        # Close the connection
        if connection:
            connection.close()

    # df = pd.read_csv("1s_av_data.csv")
    df['real time'] = pd.to_datetime(df['real_time'])

    def vel_distance(vel1, time1):
        return vel1 * time1
    
    def haversine_distance(lat1, lon1, lat2, lon2):
        """Calculate the Haversine distance between two points on the earth given their latitude and longitude."""
        # Radius of the earth in kilometers
        R = 6371.0
        
        # Convert degrees to radians
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        
        # Differences in coordinates
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        # Haversine formula
        a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        distance = R * c
        
        return distance

    def dist_array(data):
        distances = []
        for i in range(data.shape[0]):
            if data.loc[i,'delta_t'] > 10:
                dist = haversine_distance(data.loc[i,'latitude'], data.loc[i,'longitude'], data.loc[i+1,'latitude'], data.loc[i+1,'longitude'])
            else:
                dist = vel_distance(data.loc[i,'velocity'], data.loc[i,'delta_t'])
            distances.append(dist)
        return distances

    df = df.sort_values('Time', axis=0)
    df.reset_index(inplace=True, drop=True)
    df['distance'] = dist_array(df)
    df['Date'] = df['real time'].apply(lambda x: x.strftime('%Y-%m-%d'))
    mode_dict = {'0': 'OFF', '1': 'INITIALIZE', '2': 'INACTIVE', '3': 'SHUTDOWN', '4': 'READY_IDLE', '5': 'READY_HUMAN', '6': 'READY_ROBOT'}
    df['mode label'] = df['mode'].apply(lambda x: mode_dict[str(x)])

    trans_dict = {'0': 'GEAR_PARK', '1': 'GEAR_REVERSE', '2': 'GEAR_NEUTRAL', '3': 'GEAR_DRIVE'}
    df['trans label'] = df['trans'].apply(lambda x: trans_dict[str(x)])

    return df

data = load_data()

@st.cache_data
def get_trip_choices():
    return sorted(list(data['trip'].unique()))

date_choices = get_trip_choices()

def trip_formatter(trip_num):
    date = str(data[data['trip'] == trip_num].reset_index().loc[0, 'Date'])
    new_str = f'Trip {trip_num} ({date})'
    return new_str

# @st.cache_data
def display_map(midpoint, filtered_data):

    def mode_color(mode):
        mode_dict = {6: 'green', 5: 'red', 4: 'grey', 3: 'grey', 2: 'grey', 1: 'grey', 0: 'grey'}
        return mode_dict[mode]
    
    def mode_switch_color(mode_switch):
        mode_dict = {0: 'grey', 1: 'red'}
        return mode_dict[mode_switch]
    vel_colormap = cm.LinearColormap(['green','yellow','red'], vmin=filtered_data['velocity'].min(), vmax=filtered_data['velocity'].max())
    vel_colormap.caption = "Velocity"

    map = folium.Map(location=[midpoint[0], midpoint[1]], zoom_start=16,  tiles='CartoDB positron',width="100%",height="100%")

    base_map = folium.FeatureGroup(name='Basemap', overlay=False, control=False)

    feature_group = folium.FeatureGroup(name='Vehicle Mode', overlay=False)
    feature_group2 = folium.FeatureGroup(name='Velocity', overlay=False)
    feature_group3 = folium.FeatureGroup(name='Mode Switch', overlay=False)
    vel_colormap.add_to(map)

    for trip in filtered_data['trip'].unique():
        temp_data = filtered_data[filtered_data['trip'] == trip].sort_values('Time', axis=0).reset_index()
        folium.Marker(location=[temp_data.loc[0, 'latitude'], temp_data.loc[0, 'longitude']], icon=folium.Icon(color="green"), popup=f"Trip {trip} start").add_to(map)
        folium.Marker(location=[temp_data.loc[len(temp_data)-1, 'latitude'], temp_data.loc[len(temp_data)-1, 'longitude']], icon=folium.Icon(color="red"), popup=f"Trip {trip} end").add_to(map)

        for i in range(len(temp_data) - 1):
            loc = [(temp_data.loc[i, 'latitude'], temp_data.loc[i, 'longitude']),
            (temp_data.loc[i+1, 'latitude'], temp_data.loc[i+1, 'longitude'])]
            if (temp_data.loc[i+1, 'real time'] - temp_data.loc[i, 'real time']).seconds < 60:
                folium.PolyLine(loc,
                                color=mode_color(temp_data.loc[i, 'mode']),
                                weight=5,
                                opacity=0.7,
                                tooltip=f"Trip: {temp_data.loc[i, 'trip']}<br>Time: {temp_data.loc[i, 'real time']}<br>Lat: {round(temp_data.loc[i, 'latitude'], 6)}<br>Long: {round(temp_data.loc[i, 'longitude'], 6)}<br>Altitude: {round(temp_data.loc[i, 'altitude'], 6)}<br>Mode: {temp_data.loc[i, 'mode label']}<br>Velocity: {round(temp_data.loc[i, 'velocity'], 4)}<br>Transmission: {temp_data.loc[i, 'trans label']}"
                                ).add_to(feature_group)
                
                folium.PolyLine(loc,
                                color=vel_colormap(temp_data.loc[i, 'velocity']),
                                weight=5,
                                opacity=0.7,tooltip=f"Trip: {temp_data.loc[i, 'trip']}<br>Time: {temp_data.loc[i, 'real time']}<br>Lat: {round(temp_data.loc[i, 'latitude'], 6)}<br>Long: {round(temp_data.loc[i, 'longitude'], 6)}<br>Altitude: {round(temp_data.loc[i, 'altitude'], 6)}<br>Mode: {temp_data.loc[i, 'mode label']}<br>Velocity: {round(temp_data.loc[i, 'velocity'], 4)}<br>Transmission: {temp_data.loc[i, 'trans label']}"
                                ).add_to(feature_group2)
                
                folium.PolyLine(loc,
                                color='grey',
                                weight=5,
                                opacity=0.7,tooltip=f"Trip: {temp_data.loc[i, 'trip']}<br>Time: {temp_data.loc[i, 'real time']}<br>Lat: {round(temp_data.loc[i, 'latitude'], 6)}<br>Long: {round(temp_data.loc[i, 'longitude'], 6)}<br>Altitude: {round(temp_data.loc[i, 'altitude'], 6)}<br>Mode: {temp_data.loc[i, 'mode label']}<br>Velocity: {round(temp_data.loc[i, 'velocity'], 4)}<br>Transmission: {temp_data.loc[i, 'trans label']}"
                                ).add_to(feature_group3)
                
        for i in range(len(temp_data) - 1):
            if (temp_data.loc[i, 'mode_switch'] == 1) and ((temp_data.loc[i+1, 'real time'] - temp_data.loc[i, 'real time']).seconds < 60):
                loc = [(temp_data.loc[i, 'latitude'], temp_data.loc[i, 'longitude']), (temp_data.loc[i+1, 'latitude'], temp_data.loc[i+1, 'longitude'])]
                folium.PolyLine(loc,
                                color='red',
                                weight=8,
                                opacity=1,tooltip=f"Trip: {temp_data.loc[i, 'trip']}<br>Time: {temp_data.loc[i, 'real time']}<br>Lat: {round(temp_data.loc[i, 'latitude'], 6)}<br>Long: {round(temp_data.loc[i, 'longitude'], 6)}<br>Altitude: {round(temp_data.loc[i, 'altitude'], 6)}<br>Mode: {temp_data.loc[i, 'mode label']}<br>Velocity: {round(temp_data.loc[i, 'velocity'], 4)}<br>Transmission: {temp_data.loc[i, 'trans label']}"
                                ).add_to(feature_group3)
    
    folium.TileLayer(tiles='CartoDB positron').add_to(base_map)
    base_map.add_to(map)
    map.add_child(feature_group)
    map.add_child(feature_group2)
    map.add_child(feature_group3)

    map.add_child(folium.map.LayerControl())
    
    legend_html = '''
<div style="margin:auto">
<div style="float:left; margin-right: 0.5rem;"><b>Vehicle Mode</b></div>
<div style="border-radius:5px; width:1rem; height:1.2rem; background:red; float:left; margin-right:.2rem"></div>
<div style="float:left; margin-right:.5rem">Manual Mode</div>
<div style="border-radius:5px; width:1rem; height:1.2rem; background:green; float:left; margin-right:.2rem"></div>
<div style="float:left; margin-right:.5rem">Autonomous Mode</div>
<div style="border-radius:5px; width:1rem; height:1.2rem; background:grey; float:left; margin-right:.2rem"></div>
<div style="float:left; margin-right:.5rem">Other</div>
</div>
'''

    map.get_root().html.add_child(folium.Element( legend_html ))

    html = map.get_root()._repr_html_()
    return html



with st.sidebar:
    st.write('''US Ignite successfully deployed an Automated Vehicle (AV) shuttle at Fort Carson to advance the
                Department of Defense’s (DoD) understanding of the latest private-sector transportation and technology
                solutions and how they may address safety, budgetary, and operational challenges on the post.\n\nThis dashboard visualizes the operation insights found during this pilot program, including velocity, vehicle mode type, and complete stops. The data is shown through maps and charts.\n\nClick on the map layers to view vehicle mode, velocity, or vehicle mode changes throughout the trip.''')
    selectbox_state = st.multiselect("Choose a date", date_choices,  default=date_choices[0], format_func=trip_formatter)
    if len(selectbox_state) == 0:
        filtered_data = pd.DataFrame(columns=data.columns)
        st.write("Please enter trip")
    else:
        filtered_data = data[data['trip'].isin(selectbox_state)]

    select_map = st.toggle("Display Map?", value=True)

with st.container():
    dates_str = ""
    for date in filtered_data['Date'].unique():
        dates_str += f"{date}, "
    dates_str = dates_str[0: len(dates_str)-2]
    st.subheader(dates_str)

col1, col2 = st.columns([3, 1])

with col1:
    if select_map:
        if len(filtered_data) > 0:
            midpoint = ((np.max(filtered_data['latitude']) + np.min(filtered_data['latitude']))/2, (np.max(filtered_data['longitude']) + np.min(filtered_data['longitude']))/2)

            html = display_map(midpoint, filtered_data)
            components.html(html, height=600)

    # st.write("hi")


with col2:
    if len(filtered_data) > 0:
        group_trip = filtered_data.groupby('trip').agg(total_time = ('delta_t', 'sum'), total_distance = ('distance', 'sum'))

        avg_vel = group_trip['total_distance'].sum()/group_trip['total_time'].sum()
        st.metric(label="Average Velocity", value=f"{round(avg_vel, 4)} m/s")

        # tot_seconds = (group_trip['max_time'] - group_trip['min_time']).dt.total_seconds()
        mean_seconds = group_trip['total_time'].sum()
        hours = int(np.floor(((mean_seconds) / 60 / 60)))
        mean_seconds -= hours * 60 * 60
        minutes = int(np.floor(((mean_seconds) / 60)))
        mean_seconds -= minutes * 60
        seconds = int(np.floor(((mean_seconds))))

        st.metric('Total Duration of Trip(s)', value=f'{str(hours).zfill(2)}:{str(minutes).zfill(2)}:{str(seconds).zfill(2)}')

        st.metric('Total Distance of Trip(s)', value=f"{round(group_trip['total_distance'].sum(), 2)} meters")

        st.metric('Total Number of Stops for Trip(s)', value=f"{filtered_data['complete_stop'].sum()}")

        st.metric('Total Number of Mode Changes for Trip(s)', value=f"{filtered_data['mode_switch'].sum()}")

        group_mode_time = filtered_data.groupby('mode label').agg(total_time = ('delta_t', 'sum')).reset_index()
        group_mode_time['i'] = 0
        total_trip_time = group_mode_time['total_time'].sum()
        group_mode_time['perc'] = round(group_mode_time['total_time'] * 100 /total_trip_time, 2)
        group_mode_time['text label'] = group_mode_time.apply(lambda x: f"{x['mode label']}<br>{x['perc']} %", axis=1)

        fig=px.bar(group_mode_time,x='perc',y='i', orientation='h', color='mode label', text="text label", title="Mode Distribution",
                hover_data={'i':False, 'text label':False
                })
        fig.update_layout(uniformtext_minsize=6, uniformtext_mode='hide', width=400, showlegend=False, 
        height=100,
        margin=dict(
            l=0,
            r=0,
            b=0,
            t=30,
            pad=0
        ))
        fig.update_yaxes(title='', visible=False, showticklabels=False)
        fig.update_xaxes(title='', visible=False, showticklabels=False)
        # fig.update_traces(textangle=90, selector=dict(type='bar'), textposition='outside')
        st.write(fig)

    # st.write(filtered_data)

    
   
col3, col4 = st.columns(2)

with col3:
    if len(filtered_data) > 0:
        subcol1, subcol2 = st.columns(2)
        with subcol1:
            group_trip_manual = filtered_data[filtered_data['mode'] == 5].groupby('trip').agg(total_time = ('delta_t', 'sum'), total_distance = ('distance', 'sum'), max_vel = ('velocity', 'max'))
            avg_vel = group_trip_manual['total_distance'].sum()/group_trip_manual['total_time'].sum()

            st.metric(label="Average Velocity (Manual Mode)", value=f"{round(avg_vel, 4)} m/s")
            st.metric(label="Max Velocity (Manual Mode)", value=f"{round(max(group_trip_manual['max_vel']), 4)} m/s")
            st.metric(label="Percent Time in Manual Mode", value=f"{round((sum(group_trip_manual['total_time'])/filtered_data['delta_t'].sum())*100, 2)}%")
        with subcol2:
            group_trip_auto= filtered_data[filtered_data['mode'] == 6].groupby('trip').agg(total_time = ('delta_t', 'sum'), total_distance = ('distance', 'sum'), max_vel = ('velocity', 'max'))
            avg_vel = group_trip_auto['total_distance'].sum()/group_trip_auto['total_time'].sum()

            st.metric(label="Average Velocity (Autonomous Mode)", value=f"{round(avg_vel, 4)} m/s")
            st.metric(label="Max Velocity (Autonomous Mode)", value=f"{round(max(group_trip_auto['max_vel']), 4)} m/s")
            st.metric(label="Percent Time in Autonomous Mode", value=f"{round((sum(group_trip_auto['total_time'])/filtered_data['delta_t'].sum())*100, 2)}%")
        fig = px.histogram(filtered_data[filtered_data['velocity'] != 0], x="velocity", color='mode label')
        st.plotly_chart(fig, theme="streamlit")

        fig2 = px.histogram(filtered_data[filtered_data['velocity'] != 0], x="acceleration", color='mode label')
        st.plotly_chart(fig2, theme="streamlit")
    # print(filtered_data.columns)
    

    # st.write(filtered_data[filtered_data['delta_t']> 5])

with col4:
    if len(filtered_data) > 0:
        st.line_chart(filtered_data, x='real time', y='velocity', color='mode label')

        st.line_chart(filtered_data, x='real time', y='mode')

        st.write(filtered_data[['trip', 'real time', 'mode label', 'velocity', 'latitude',
        'longitude', 'altitude', 'delta_v', 'delta_t', 'acceleration',
        'distance', 'trans label', 'complete_stop', 'mode_switch']])
        