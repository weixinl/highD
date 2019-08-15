import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os.path



def get_color_by_laneid(_lane_id):
    # lane id: 1-8
    color=[None,"blue","red","yellow","darkviolet","orange","green","magenta","brown"]
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

def get_car_track(_track_path,_car_begin_line_id,_car_frame_num):
    tracks_df=pd.read_csv(_track_path)
    x_list_list=[]
    y_list_list=[]
    laneid_list=[]
    x_list=[]
    y_list=[]
    laneid_prev=-1
    for line_id in range(_car_begin_line_id,_car_begin_line_id+_car_frame_num):
        line_serie=tracks_df.iloc[line_id]
        x=float(line_serie["x"])
        y=float(line_serie["y"])
        laneid=int(line_serie["laneId"])
        if(laneid!=laneid_prev):
            laneid_prev=laneid
            laneid_list.append(laneid)
            if(line_id!=_car_begin_line_id):
                x_list_list.append(x_list)
                y_list_list.append(y_list)
            x_list=[x]
            y_list=[y]
        else:
            x_list.append(x)
            y_list.append(y)
    x_list_list.append(x_list)
    y_list_list.append(y_list)

    return x_list_list,y_list_list,laneid_list
    




def plot_car(_recording_path,_meta_path,_track_path,_file_id,_vehicle_id,_img_path):
    lane_y_list=get_lane_y_list(_recording_path)

    frame_info_path="../infos/frame_num_info_"+str(_file_id)+".txt"
    frame_num_list=None
    if(os.path.exists(frame_info_path)):
        frame_num_list=restore_frame_num_info(_file_id)
    else:
        store_frame_num_info(_recording_path,_track_path,_file_id)
        frame_num_list=restore_frame_num_info(_file_id)
    car_begin_line_id=0
    for i in range(_vehicle_id):
        car_begin_line_id +=frame_num_list[i]
    car_frame_num=frame_num_list[_vehicle_id]
    # print("frame_num_list:")
    # print(frame_num_list)
    # print("car_frame_num:"+str(car_frame_num))
    x_list_list,y_list_list,lane_id_list=get_car_track(_track_path,car_begin_line_id,car_frame_num)

    # print(x_list_list)
    x_left=x_list_list[0][0]
    x_right=x_list_list[-1][-1]

    # plot lanes
    for lane_y in lane_y_list:
        plt.plot([x_left,x_right],[lane_y,lane_y],linewidth=1,color="black")


    #get width
    meta_df=pd.read_csv(_meta_path)
    car_meta_serie=meta_df.iloc[_vehicle_id-1]
    car_width=float(car_meta_serie["width"])
    # print(car_width)
    half_width=car_width/2

    # upper_y_list_list=[]
    # lower_y_list_list=[]
    # for y_list in y_list_list:
    #     upper_y_list=[]
    #     lower_y_list=[]
    #     for y in y_list:
    #         upper_y_list.append(y+half_width)
    #         lower_y_list.append(y-half_width)
    #     upper_y_list_list.append(upper_y_list)
    #     lower_y_list_list.append(lower_y_list)

    


    plot_one_track(x_list_list,y_list_list,lane_id_list)
    # plot_one_track(x_list_list,upper_y_list_list,lane_id_list)
    # plot_one_track(x_list_list,lower_y_list_list,lane_id_list)

        
    # plt.plot(x_list,y_list,marker=".",markersize=2)

    plt.xlabel("x")
    plt.ylabel("y")
    # plt.legend()
    plt.savefig(_img_path)


    
def plot_one_track(_x_list_list,_y_list_list,_lane_id_list):
    diff_lane_num=len(_lane_id_list)
    for pos in range(diff_lane_num):
        x_list=_x_list_list[pos]
        y_list=_y_list_list[pos]
        lane_id=_lane_id_list[pos]
        tmp_color=get_color_by_laneid(lane_id)
        plt.plot(x_list,y_list,linewidth=2,color=tmp_color)




if __name__=="__main__":
    file_id=14
    vehicle_id=1000

    data_dir="../data/"
    file_id_str=get_file_id_str(file_id)

    recording_path=data_dir+file_id_str+"_recordingMeta.csv"
    meta_path=data_dir+file_id_str+"_tracksMeta.csv"
    track_path=data_dir+file_id_str+"_tracks.csv"


    stat_dir="../statistics/car_tracks/"
    img_path=stat_dir+"img_"+file_id_str+"_"+str(vehicle_id)+".jpg"
    plot_car(recording_path,meta_path,track_path,file_id,vehicle_id,img_path)