import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

INF=2e8

def check_lane_change(_lcs_path,_recording_path,_left_range,_right_range,_img_path):
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
    # print("lane_y_list:")
    # print(lane_y_list)

    lcs_df=pd.read_csv(_lcs_path)
    lane_id_list=[]
    for index,row in lcs_df.iterrows():
        lane_id=int(row["laneId_ego"])
        lane_id_list.append(lane_id)
    lcs_line_num=len(lane_id_list)
    now_lane_id=lane_id_list[0]
    lane_change_lcs_line_id=-1
    for lcs_line_id in range(2,lcs_line_num+1):
        lane_id=lane_id_list[lcs_line_id]
        if(lane_id!=now_lane_id):
            lane_change_lcs_line_id=lcs_line_id
            break
    lcs_line_id_left_endpoint=lane_change_lcs_line_id-_left_range
    lcs_line_id_right_endpoint=lane_change_lcs_line_id+_right_range-1

    left_lane_id=lane_id_list[lane_change_lcs_line_id-1]
    right_lane_id=lane_id_list[lane_change_lcs_line_id]

    left_frames=[]
    left_abs_dists=[]
    right_frames=[]
    right_abs_dists=[]

    lcs_line_left_endpoint=lcs_df.iloc[lcs_line_id_left_endpoint]
    frame_left_endpoint=int(lcs_line_left_endpoint["frames"])
    left_frames=range(frame_left_endpoint,frame_left_endpoint+_left_range)
    left_frames=list(left_frames)
    right_frames=range(frame_left_endpoint+_left_range,frame_left_endpoint+_left_range+_right_range)
    right_frames=list(right_frames)

    frames=left_frames+right_frames
    y_list_left=[]
    y_list_right=[]
    for lcs_line_id in range(lcs_line_id_left_endpoint,\
        lcs_line_id_left_endpoint+_left_range):
        lcs_line=lcs_df.iloc[lcs_line_id]
        tmp_y=float(lcs_line["y_ego"])
        y_list_left.append(tmp_y)
    for lcs_line_id in range(lcs_line_id_left_endpoint+_left_range,\
        lcs_line_id_left_endpoint+_left_range+_right_range):
        lcs_line=lcs_df.iloc[lcs_line_id]
        tmp_y=float(lcs_line["y_ego"])
        y_list_right.append(tmp_y)
    
    y_list=y_list_left+y_list_right
    
    closest_lane=-1
    closest_dist=INF
    frame_num=len(frames)
    for pos in range(frame_num):
        frame_id=frames[pos]
        y=y_list[pos]
        near_lane,near_dist=get_near_lane_and_dist(lane_y_list,y)
        if(near_dist<closest_dist):
            closest_dist=near_dist
            closest_lane=near_lane
    
    closest_lane_y=lane_y_list[closest_lane]
    # print("closest_lane_y: "+str(closest_lane_y))

    dists_left=[]
    for y in y_list_left:
        dist=(y-closest_lane_y)
        dists_left.append(dist)
    
    dists_right=[]
    for y in y_list_right:
        dist=(y-closest_lane_y)
        dists_right.append(dist)
    
    # print(abs_dists_left)
    # print(abs_dists_right)
    plt.bar(left_frames,dists_left,label="laneId= "+str(left_lane_id))
    plt.bar(right_frames,dists_right,label="laneId= "+str(right_lane_id))
    plt.xlabel("frame")
    plt.ylabel("distance")
    plt.legend()
    plt.savefig(_img_path)
    
def get_near_lane_and_dist(_lane_y_list,_y):
    lane_num=len(_lane_y_list)
    near_lane=-1
    near_dist=INF
    for lane_id in range(lane_num):
        lane_y=_lane_y_list[lane_id]
        dist_to_tmp_lane=abs(lane_y-_y)
        if(dist_to_tmp_lane<near_dist):
            near_lane=lane_id
            near_dist=dist_to_tmp_lane
    return near_lane,near_dist




if __name__=="__main__":
    tables_dir="../tables/"
    data_dir="../data/"
    file_id=14
    file_id_str=None
    if(file_id>9):
        file_id_str=str(file_id)
    else:
        file_id_str="0"+str(file_id)
    vehicle_id=2587
    lcs_path=tables_dir+"lcS_R"+file_id_str+"_"+str(vehicle_id)+".txt"
    recording_path=data_dir+file_id_str+"_recordingMeta.csv"
    stat_dir="../statistics/lane_change_statistics/"
    img_path=stat_dir+"img_"+file_id_str+"_"+str(vehicle_id)+".jpg"
    check_lane_change(lcs_path,recording_path,50,50,img_path)



