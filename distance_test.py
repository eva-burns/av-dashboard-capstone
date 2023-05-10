import math
from geopy import distance
import pandas as pd
import numpy as np
import time
import os
import scipy
# def load_data():
#     f = []
#     w = os.walk("./Data")
#     for (dirpath, dirnames, filenames) in w:
#         f.extend(dirnames)
#     dirnames = sorted(dirnames)
#     gps_files = [f'./Data/{dir}/gps.csv' for dir in f]
#     velocity_files = [f'./Data/{dir}/velocity.csv' for dir in f]
#     mode_files = [f'./Data/{dir}/vehiclemode.csv' for dir in f]

#     df = pd.DataFrame()
#     i = 1
#     for file in gps_files:
#         temp_df = pd.read_csv(file)[['Time', 'latitude', 'longitude', 'altitude']]
#         temp_df['trip number'] = i
#         df = pd.concat([df, temp_df], axis=0)
#         i += 1
#     df['Time'] = df['Time'].round(3)

#     mode_df = pd.DataFrame()
#     i = 1
#     for file in mode_files:
#         temp_df = pd.read_csv(file)[['Time', 'data']]
#         mode_df = pd.concat([mode_df, temp_df], axis=0)
#         i += 1
#     mode_df.rename(columns={'data': 'mode'}, inplace=True)
#     mode_df['Time'] = mode_df['Time'].round(3)
#     df = pd.merge(df, mode_df, on='Time')

#     vel_df = pd.DataFrame()
#     i = 1
#     for file in velocity_files:
#         temp_df = pd.read_csv(file)[['Time', 'data']]
#         vel_df = pd.concat([vel_df, temp_df], axis=0)
#         i += 1
#     vel_df['Time'] = vel_df['Time'].round(3)
#     vel_df.rename(columns={'data': 'velocity'}, inplace=True)
#     df = pd.merge(df, vel_df, on='Time')

#     df['Time'] = pd.to_datetime(df['Time'],unit='s')

#     df = df.sort_values(by=['Time'], ignore_index=True)
    
#     return df

# df = load_data()
def calculate_distance(p1, p2):
    flat_distance = distance.distance(p1[:2], p2[:2]).meters
    euclidian_distance = math.sqrt(flat_distance**2 + (p2[2] - p1[2])**2)
    return euclidian_distance

df = pd.read_csv("./Data/Trip 2/gps.csv")[['latitude', 'longitude', 'altitude','Time']].iloc[0:100,:]

def dist_array(data):
    distances = []
    for i in range(data.shape[0]-1):
        distances.append(calculate_distance(data.loc[i,['latitude', 'longitude', 'altitude']], data.loc[i+1,['latitude', 'longitude', 'altitude']]))
    return distances

start_time =time.time()
print(dist_array(df))
end_time =time.time()
print(end_time - start_time)

# total_dist = np.sum(dists)

end_time =time.time()

print(end_time - start_time)

