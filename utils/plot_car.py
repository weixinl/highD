import numpy as np
import matplotlib.plot as plot
import pandas as pd
import os.path



def get_color_by_laneid(_lane_id):
    # lane id: 1-8
    color=[None,"red","blue","darkviolet","orange","green","magenta","blue","black"]
    return color[_lane_id]

def get_file_id_str(_file_id):
    file_id_str=None
    if(file_id>9):
        file_id_str=str(file_id)
    else:
        file_id_str="0"+str(file_id)
    return file_id_str

def store_frame_num_info(_recording_path,_tracks_path,file_id):
    recording_df=pd.read_csv(_recording_path)
    recording_series=recording_df.iloc[0]
    num_vehicles=int(recording_series["numVehicles"])
    tracks_df=pd.read_csv(_tracks_path)
    frame_num_list=np.zeros(num_vehicles+1,int)
    for index,row in tracks_df.iterrows():
        if((index%1000)==0):
            print("index: "+str(index))
        id=int(row["id"])
        frame_num_list[id]+=1
    info_dir="../infos/"
    info_path=info_dir+"frame_num_info_"+str(file_id)+".txt"
    info_file=open(info_path,"w")
    for vehicle_id in range(1,num_vehicles+1):
        info_file.write(str(frame_num_list[vehicle_id])+"\n")
    info_file.close()

def restore_frame_num_info(_file_id):
    info_dir="../infos/"
    info_path=info_dir+"frame_num_info_"+str(file_id)+".txt"
    info_file=open(info_path,"r")
    frame_num_list_prev=[]
    lines=info_file.readlines()
    for line in lines:
        tmp=int(line.strip())
        frame_num_list_prev.append(tmp)
    info_file.close()
    vehicle_num=len(frame_num_list_prev)
    frame_num_list=np.zeros(vehicle_num+1,int)
    for vehicle_id in range(1,vehicle_num+1):
        frame_num_list[vehicle_id]=frame_num_list_prev[vehicle_id-1]
    return frame_num_list

def get_lane_y_list(_recording_path):

    recording_df=pd.read_csv(_recording_path)
    recording_series=recording_df.iloc[0]
    upper_lane_markings_str=str(recording_series["upperLaneMarkings"])
    # print("upper_lane_markings:")
    # print(upper_lane_markings_str)
    upper_lane_markings_str_list=upper_lane_markings_str.strip().split(";")
    lower_lane_markings_str=str(recording_series["lowerLaneMarkings"])
    lower_lane_markings_str_list=lower_lane_markings_str.strip().split(";")
    lane_y_list=[]
    for lane_y_str in upper_lane_markings_str_list:
        lane_y_list.append(float(lane_y_str))
    for lane_y_str in lower_lane_markings_str_list:
        lane_y_list.append(float(lane_y_str)) 
    return lane_y_list


def plot_car(_recording_path,_meta_path,_track_path,_file_id,_vehicle_id):
    frame_info_path="../infos/frame_num_info_"+str(_file_id)+".txt"


    frame_num_list=None
    if(os.path.exists(frame_info_path)):
        frame_num_list=restore_frame_num_info(_file_id)
    else:
        store_frame_num_info(_recording_path,_track_path,_file_id)
        frame_num_list=restore_frame_num_info(_file_id)
    car_begin_line_id=0
    for i in range(_vehicle_id-1):
        car_begin_line_id +=frame_num_list[i]
    car_frame_num=frame_num_list[_vehicle_id-1]
    
    




if __name__=="__main__":
    file_id=14
    vehicle_id=2587

    data_dir="../data/"
    file_id_str=get_file_id_str(file_id)

    recording_path=data_dir+file_id_str+"_recordingMeta.csv"
    meta_path=data_dir+file_id_str+"_tracksMeta.csv"
    track_path=data_dir+file_id_str+"_tracks.csv"


    stat_dir="../statistics/car_tracks/"
    img_path=stat_dir+"img_"+file_id_str+"_"+str(vehicle_id)+".jpg"
    plot_car(recording_path,meta_path,track_path,file_id,vehicle_id)