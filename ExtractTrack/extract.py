import pandas as pd
import numpy as np
import os.path

# extract from 3 csv files
def extract_file(_recording_path,_meta_path,_tracks_path,_file_id):
    # print(_recording_path)
    recording_df=pd.read_csv(_recording_path)
    meta_df=pd.read_csv(_meta_path)
    tracks_df=pd.read_csv(_tracks_path)
    # car group and truck group, 0 and 1

    # get info from recording
    recording_vehicle_num=None
    recording_car_num=None
    recording_truck_num=None
    recording_series=recording_df.iloc[0]
    recording_vehicle_num=recording_series["numVehicles"]
    recording_car_num=recording_series["numCars"]
    recording_truck_num=recording_series["numTrucks"]

    # print(type(recording_df.iloc[0]))

    vehicle_meta_groups=[]
    vehicle_tracks_groups=[]

    car_id_list=[]
    truck_id_list=[]

    # 0 for car, 1 for truck, sub index begins at 1
    class_list=np.zeros(recording_vehicle_num+1)

    # car_meta_group=[]
    # truck_meta_group=[]
    # car_tracks_group=[]
    # truck_tracks_group=[]

    # print("begin to iterate rows in meta_df")

    for index,row in meta_df.iterrows():
        vehicle_class=row["class"].strip()
        vehicle_id=int(row["id"])
        if(vehicle_class=="Car"):
            car_id_list.append(vehicle_id)
            class_list[vehicle_id]=0
        else:
            truck_id_list.append(vehicle_id)
            class_list[vehicle_id]=1
    
    # print("iterate rows end")
    
    assert len(car_id_list)==recording_car_num
    # print("truck number: ",len(truck_id_list))
    # print("recording truck num: ",recording_truck_num)
    assert len(truck_id_list)==recording_truck_num
    id_list=[car_id_list,truck_id_list]

    # # extract car lane change
    # v_class_index=0
    # v_class_id_list=id_list[v_class_index]

    # consider only cars
    car_lane_change(car_id_list,class_list,1,150,150,meta_df,tracks_df,_file_id)


def car_lane_change(_car_id_list,_class_list,_lane_change_num,
_earliest_frames_range,_latest_frames_range,_meta_df,_tracks_df,_file_id):
    car_num=len(_car_id_list)
    vehicle_num=len(_class_list)-1
    selected_id_list=[]
    # print(_meta_df.iloc[0])
    # print(_meta_df.iloc[1])

    # select by lane change number
    for car_id in _car_id_list:
        meta_df_row_id=car_id-1
        row_series=_meta_df.iloc[meta_df_row_id]
        tmp_lane_changes=int(row_series["numLaneChanges"])
        if(tmp_lane_changes==_lane_change_num):
            selected_id_list.append(car_id)
    
    # frame numbers of each vehicle
    frame_num_list=restore_frame_num_info(_file_id)
    
    tracks_row_begin=np.zeros(vehicle_num+1,int)
    tracks_row_end=np.zeros(vehicle_num+1,int)
    tracks_row_begin[1]=0.
    tracks_row_end[1]=frame_num_list[1]-1
    for v_id in range(2,vehicle_num+1):
        tracks_row_begin[v_id]=tracks_row_begin[v_id-1]+frame_num_list[v_id-1]
        tracks_row_end[v_id]=tracks_row_end[v_id-1]+frame_num_list[v_id]
    vehicles_begin_frame=np.zeros(vehicle_num+1,int)
    vehicles_end_frame=np.zeros(vehicle_num+1,int)
    for v_id in range(1,vehicle_num+1):
        track_begin_row_id=tracks_row_begin[v_id]
        track_begin_row=_tracks_df.iloc[track_begin_row_id]
        track_end_row_id=tracks_row_end[v_id]
        track_end_row=_tracks_df.iloc[track_end_row_id]
        begin_frame=int(track_begin_row["frame"])
        end_frame=int(track_end_row["frame"])
        vehicles_begin_frame[v_id]=begin_frame
        vehicles_end_frame[v_id]=end_frame
    
    # extract lane change information of each selected car id
    # begin frames of lanes of a selected car id (selected by lane change number)
    # selected_id_to_lanes_begin_frames={}

    #test
    for selected_id in selected_id_list:
    # for selected_id in range(2587,2588):
        print("selected_id: "+str(selected_id))
        lanes=[]
        lanes_begin_frames=[]
        car_frame_num=frame_num_list[selected_id]
        if(car_frame_num==0):
            print("selected car "+str(selected_id)+" has no frames")
            continue
        
        # car_begin_frame=vehicles_begin_frame[selected_id]
        # car_end_frame=vehicles_end_frame[selected_id]
        track_begin_row_id=tracks_row_begin[selected_id]
        track_end_row_id=tracks_row_end[selected_id]
        res=extract_surround(selected_id,_meta_df,_tracks_df,track_begin_row_id,
        track_end_row_id,_lane_change_num,_earliest_frames_range,_latest_frames_range,
        vehicles_begin_frame,vehicles_end_frame,tracks_row_begin,tracks_row_end,_file_id)
        print("selected id: "+str(selected_id)+" res: "+str(res))
    
'''
if this ego vehicle does not meet the frame range requirement or its surrounding vehicles
do not meet the frame range requirement, then return False
'''
def extract_surround(_ego_id,_meta_df,_tracks_df,_ego_begin_row_id,_ego_end_row_id,
_lane_change_num,_earliest_frames_range,_latest_frames_range,_vehicles_begin_frame,
_vehicles_end_frame,_vehicles_row_begin,_vehicles_row_end,_file_id):
    ego_lanes=[]
    ego_lanes_begin_frames=[]
    ego_frame_num=_ego_end_row_id-_ego_begin_row_id+1
    ego_begin_row=_tracks_df.iloc[_ego_begin_row_id]
    ego_begin_lane_id=int(ego_begin_row["laneId"])
    ego_begin_frame=int(ego_begin_row["frame"])
    ego_lanes.append(ego_begin_lane_id)
    ego_lanes_begin_frames.append(ego_begin_frame)
    prev_lane_id=ego_begin_lane_id
    # iterate tracks rows of ego car to find all lane changes
    for ego_row_id in range(_ego_begin_row_id+1,_ego_end_row_id+1):
        track_row=_tracks_df.iloc[ego_row_id]
        lane_id=int(track_row["laneId"])
        if(lane_id==prev_lane_id):
            continue
        else:
            # change to a new lane
            prev_lane_id=lane_id
            ego_lanes.append(lane_id)
            tmp_frame=int(track_row["frame"])
            ego_lanes_begin_frames.append(tmp_frame)
    ego_lane_change_cnt=len(ego_lanes)-1

    '''
    ensure that lane change count extracted from tracks data is equal to lane change num
    in meta data
    '''
    assert ego_lane_change_cnt==_lane_change_num
    
    ego_end_row=_tracks_df.iloc[_ego_end_row_id]
    ego_end_frame=int(ego_end_row["frame"])
    ego_frame_range_left_endpoint=ego_lanes_begin_frames[1]-_earliest_frames_range
    ego_frame_range_right_endpoint=ego_lanes_begin_frames[ego_lane_change_cnt]+_latest_frames_range
    
    # print("ego_frame_range_left_endpoint: "+str(ego_frame_range_left_endpoint))
    # print("ego_begin_frame: "+str(ego_begin_frame))
    # print("ego_frame_range_right_endpoint: "+str(ego_frame_range_right_endpoint))
    # print("ego_end_frame: "+str(ego_end_frame))
    # whether it is in range
    if(ego_frame_range_left_endpoint<ego_begin_frame):

        return False
    elif(ego_frame_range_right_endpoint>ego_end_frame):

        return False
    
    # print("ego car "+str(_ego_id)+" meets the required range")

    preceding_id_list=[]
    following_id_list=[]
    left_preceding_id_list=[]
    left_alongside_id_list=[]
    left_following_id_list=[]
    right_preceding_id_list=[]
    right_alongside_id_list=[]
    right_following_id_list=[]

    preceding_frame_range_list=[]
    following_frame_range_list=[]
    left_preceding_frame_range_list=[]
    left_alongside_frame_range_list=[]
    left_following_frame_range_list=[]
    right_preceding_frame_range_list=[]
    right_alongside_frame_range_list=[]
    right_following_frame_range_list=[]


    now_preceding_id=-1
    now_following_id=-1
    now_left_preceding_id=-1
    now_left_alongside_id=-1
    now_left_following_id=-1
    now_right_preceding_id=-1
    now_right_alongside_id=-1
    now_right_following_id=-1

    # first frame
    frame_id=ego_frame_range_left_endpoint
    tmp_row_id=_ego_begin_row_id+frame_id-ego_begin_frame
    row=_tracks_df.iloc[tmp_row_id]
    preceding_id=row["precedingId"]
    following_id=row["followingId"]
    left_preceding_id=row["leftPrecedingId"]
    left_alongside_id=row["leftAlongsideId"]
    left_following_id=row["leftFollowingId"]
    right_preceding_id=row["rightPrecedingId"]
    right_alongside_id=row["rightAlongsideId"]
    right_following_id=row["rightFollowingId"]
    now_preceding_id=preceding_id
    now_following_id=following_id
    now_left_preceding_id=left_preceding_id
    now_left_alongside_id=left_alongside_id
    now_left_following_id=left_following_id
    now_right_preceding_id=right_preceding_id
    now_right_alongside_id=right_alongside_id
    now_right_following_id=right_following_id
    preceding_id_list.append(preceding_id)
    following_id_list.append(following_id)
    left_preceding_id_list.append(left_preceding_id)
    left_alongside_id_list.append(left_alongside_id)
    left_following_id_list.append(left_following_id)
    right_preceding_id_list.append(right_preceding_id)
    right_alongside_id_list.append(right_alongside_id)
    right_following_id_list.append(right_following_id)
    preceding_frame_range=[frame_id,-1]
    following_frame_range=[frame_id,-1]
    left_preceding_frame_range=[frame_id,-1]
    left_alongside_frame_range=[frame_id,-1]
    left_following_frame_range=[frame_id,-1]
    right_preceding_frame_range=[frame_id,-1]
    right_alongside_frame_range=[frame_id,-1]
    right_following_frame_range=[frame_id,-1]
    preceding_frame_range_list.append(preceding_frame_range)
    following_frame_range_list.append(following_frame_range)
    left_preceding_frame_range_list.append(left_preceding_frame_range)
    left_alongside_frame_range_list.append(left_alongside_frame_range)
    left_following_frame_range_list.append(left_following_frame_range)
    right_preceding_frame_range_list.append(right_preceding_frame_range)
    right_alongside_frame_range_list.append(right_alongside_frame_range)
    right_following_frame_range_list.append(right_following_frame_range)

    for frame_id in range(ego_frame_range_left_endpoint+1,ego_frame_range_right_endpoint+1):
        tmp_row_id=_ego_begin_row_id+frame_id-ego_begin_frame
        row=_tracks_df.iloc[tmp_row_id]
        preceding_id=row["precedingId"]
        following_id=row["followingId"]
        left_preceding_id=row["leftPrecedingId"]
        left_alongside_id=row["leftAlongsideId"]
        left_following_id=row["leftFollowingId"]
        right_preceding_id=row["rightPrecedingId"]
        right_alongside_id=row["rightAlongsideId"]
        right_following_id=row["rightFollowingId"]
        if(preceding_id!=now_preceding_id):
            preceding_id_list.append(preceding_id)
            preceding_frame_range_list[-1][1]=frame_id-1
            preceding_frame_range=[frame_id,-1]
            preceding_frame_range_list.append(preceding_frame_range)
            now_preceding_id=preceding_id
        if(following_id!=now_following_id):
            following_id_list.append(following_id)
            following_frame_range_list[-1][1]=frame_id-1
            following_frame_range=[frame_id,-1]
            following_frame_range_list.append(following_frame_range)
            now_following_id=following_id
        if(left_preceding_id!=now_left_preceding_id):
            left_preceding_id_list.append(left_preceding_id)
            left_preceding_frame_range_list[-1][1]=frame_id-1
            left_preceding_frame_range=[frame_id,-1]
            left_preceding_frame_range_list.append(left_preceding_frame_range)
            now_left_receding_id=left_preceding_id
        if(left_alongside_id!=now_left_alongside_id):
            left_alongside_id_list.append(left_alongside_id)
            left_alongside_frame_range_list[-1][1]=frame_id-1
            left_alongside_frame_range=[frame_id,-1]
            left_alongside_frame_range_list.append(left_alongside_frame_range)
            now_left_alongside_id=left_alongside_id
        if(left_following_id!=now_left_following_id):
            left_following_id_list.append(left_following_id)
            left_following_frame_range_list[-1][1]=frame_id-1
            left_following_frame_range=[frame_id,-1]
            left_following_frame_range_list.append(left_following_frame_range)
            now_left_following_id=left_following_id
        if(right_preceding_id!=now_right_preceding_id):
            right_preceding_id_list.append(right_preceding_id)
            right_preceding_frame_range_list[-1][1]=frame_id-1
            right_preceding_frame_range=[frame_id,-1]
            right_preceding_frame_range_list.append(right_preceding_frame_range)
            now_right_preceding_id=left_preceding_id
        if(right_alongside_id!=now_right_alongside_id):
            right_alongside_id_list.append(right_alongside_id)
            right_alongside_frame_range_list[-1][1]=frame_id-1
            right_alongside_frame_range=[frame_id,-1]
            right_alongside_frame_range_list.append(right_alongside_frame_range)
            now_right_alongside_id=left_alongside_id
        if(right_following_id!=now_right_following_id):
            right_following_id_list.append(right_following_id)
            right_following_frame_range_list[-1][1]=frame_id-1
            right_following_frame_range=[frame_id,-1]
            right_following_frame_range_list.append(right_following_frame_range)
            now_right_following_id=left_following_id
    preceding_frame_range_list[-1][1]=ego_frame_range_right_endpoint
    following_frame_range_list[-1][1]=ego_frame_range_right_endpoint
    left_preceding_frame_range_list[-1][1]=ego_frame_range_right_endpoint
    left_alongside_frame_range_list[-1][1]=ego_frame_range_right_endpoint
    left_following_frame_range_list[-1][1]=ego_frame_range_right_endpoint
    right_preceding_frame_range_list[-1][1]=ego_frame_range_right_endpoint
    right_alongside_frame_range_list[-1][1]=ego_frame_range_right_endpoint
    right_following_frame_range_list[-1][1]=ego_frame_range_right_endpoint

    # if all surrounding vehicles meet the range requirement
    surr_in_range=True

    preceding_in_range=check_range(preceding_id_list,preceding_frame_range_list,
    _vehicles_begin_frame,_vehicles_end_frame)
    if(not preceding_in_range):
        surr_in_range=False
    following_in_range=check_range(following_id_list,following_frame_range_list,
    _vehicles_begin_frame,_vehicles_end_frame)
    if(not following_in_range):
        surr_in_range=False
    left_preceding_in_range=check_range(left_preceding_id_list,left_preceding_frame_range_list,
    _vehicles_begin_frame,_vehicles_end_frame)
    if(not left_preceding_in_range):
        surr_in_range=False
    left_alongside_in_range=check_range(left_alongside_id_list,left_alongside_frame_range_list,
    _vehicles_begin_frame,_vehicles_end_frame)
    if(not left_alongside_in_range):
        surr_in_range=False
    left_following_in_range=check_range(left_following_id_list,left_following_frame_range_list,
    _vehicles_begin_frame,_vehicles_end_frame)
    if(not left_following_in_range):
        surr_in_range=False
    right_preceding_in_range=check_range(right_preceding_id_list,right_preceding_frame_range_list,
    _vehicles_begin_frame,_vehicles_end_frame)
    if(not right_preceding_in_range):
        surr_in_range=False
    right_alongside_in_range=check_range(right_alongside_id_list,right_alongside_frame_range_list,
    _vehicles_begin_frame,_vehicles_end_frame)
    if(not right_alongside_in_range):
        surr_in_range=False
    right_following_in_range=check_range(right_following_id_list,right_following_frame_range_list,
    _vehicles_begin_frame,_vehicles_end_frame)
    if(not right_following_in_range):
        surr_in_range=False

    if(surr_in_range==False):
        return False
    

    # surrounding vehicles at each frame
    precedings_by_frame=np.zeros(ego_frame_range_right_endpoint+1)
    precedings_by_frame=get_surr_ids_for_every_frame(precedings_by_frame,preceding_id_list,
    preceding_frame_range_list)

    followings_by_frame=np.zeros(ego_frame_range_right_endpoint+1)
    followings_by_frame=get_surr_ids_for_every_frame(followings_by_frame,following_id_list,
    following_frame_range_list)

    left_precedings_by_frame=np.zeros(ego_frame_range_right_endpoint+1)
    left_precedings_by_frame=get_surr_ids_for_every_frame(left_precedings_by_frame,
    left_preceding_id_list,left_preceding_frame_range_list)

    left_alongsides_by_frame=np.zeros(ego_frame_range_right_endpoint+1)
    left_alongsides_by_frame=get_surr_ids_for_every_frame(left_alongsides_by_frame,
    left_alongside_id_list,left_alongside_frame_range_list)

    left_followings_by_frame=np.zeros(ego_frame_range_right_endpoint+1)
    left_followings_by_frame=get_surr_ids_for_every_frame(left_followings_by_frame,
    left_following_id_list,left_following_frame_range_list)

    right_precedings_by_frame=np.zeros(ego_frame_range_right_endpoint+1)
    right_precedings_by_frame=get_surr_ids_for_every_frame(right_precedings_by_frame,
    right_preceding_id_list,right_preceding_frame_range_list)

    right_alongsides_by_frame=np.zeros(ego_frame_range_right_endpoint+1)
    right_alongsides_by_frame=get_surr_ids_for_every_frame(right_alongsides_by_frame,
    right_alongside_id_list,right_alongside_frame_range_list)

    right_followings_by_frame=np.zeros(ego_frame_range_right_endpoint+1)
    right_followings_by_frame=get_surr_ids_for_every_frame(right_followings_by_frame,
    right_following_id_list,right_following_frame_range_list)

    file_id_str=None
    if(_file_id<10):
        file_id_str="0"+str(file_id)
    else:
        file_id_str=str(_file_id)

    tables_dir="../tables/"
    lca_path=tables_dir+"lcA_R"+file_id_str+"_"+str(_ego_id)+".txt"
    lcs_path=tables_dir+"lcS_R"+file_id_str+"_"+str(_ego_id)+".txt"

    lca_file=open(lca_path,"w")
    lca_file.write("xAcceleration_ego,yAcceleration_ego\n")
    for ego_frame_id in range(ego_frame_range_left_endpoint,ego_frame_range_right_endpoint+1):
        ego_row_id=_ego_begin_row_id+ego_frame_id-ego_begin_frame
        ego_row=_tracks_df.iloc[ego_row_id]
        ego_x_acceleration=ego_row["xAcceleration"]
        ego_y_acceleration=ego_row["yAcceleration"]
        lca_file.write(str(ego_x_acceleration)+","+str(ego_y_acceleration)+"\n")
    lca_file.close()

    lcs_file=open(lcs_path,"w")
    lcs_first_line="frames,id_ego,x_ego,y_ego,width_ego,height_ego,xVelocity_ego,yVelocity_ego,\
    frontSightDistance_ego,backSightDistance_ego,dhw_ego,thw_ego,ttc_ego,precedingXVelocity_ego,\
    precedingId_ego,followingId_ego,leftPrecedingId_ego,leftAlongsideId_ego,leftFollowingId_ego,\
    rightPrecedingId_ego,rightAlongsideId_ego,rightFollowingId_ego,laneId_ego,numLaneChanges_ego,\
    drivingDirection_ego,id_pre,x_pre,y_pre,width_pre,height_pre,xVelocity_pre,yVelocity_pre,\
    xAccelertion_pre,yAcceleration_pre,frontSightDistance_pre,backSightDistance_pre,dhw_pre,\
    thw_pre,ttc_pre,precedingXVelocity_pre,precedingId_pre,followingId_pre,leftPrecedingId_pre,\
    leftAlongsideId_pre,leftFollowingId_pre,rightPrecedingId_pre,rightAlongsideId_pre,\
    rightFollowingId_pre,laneId_pre,numLaneChanges_pre,drivingDirection_pre,id_fol,x_fol,\
    y_fol,width_fol,height_fol,xVelocity_fol,yVelocity_fol,xAccelertion_fol,yAcceleration_fol,\
    frontSightDistance_fol,backSightDistance_fol,dhw_fol,thw_fol,ttc_fol,precedingXVelocity_fol,\
    precedingId_fol,followingId_fol,leftPrecedingId_fol,leftAlongsideId_fol,leftFollowingId_fol,\
    rightPrecedingId_fol,rightAlongsideId_fol,rightFollowingId_fol,laneId_fol,numLaneChanges_fol,\
    drivingDirection_fol,id_lpr,x_lpr,y_lpr,width_lpr,height_lpr,xVelocity_lpr,yVelocity_lpr,\
    xAccelertion_lpr,yAcceleration_lpr,frontSightDistance_lpr,backSightDistance_lpr,dhw_lpr,\
    thw_lpr,ttc_lpr,precedingXVelocity_lpr,precedingId_lpr,followingId_lpr,leftPrecedingId_lpr,\
    leftAlongsideId_lpr,leftFollowingId_lpr,rightPrecedingId_lpr,rightAlongsideId_lpr,\
    rightFollowingId_lpr,laneId_lpr,numLaneChanges_lpr,drivingDirection_lpr,id_las,x_las,y_las,\
    width_las,height_las,xVelocity_las,yVelocity_las,xAccelertion_las,yAcceleration_las,\
    frontSightDistance_las,backSightDistance_las,dhw_las,thw_las,ttc_las,precedingXVelocity_las,\
    precedingId_las,followingId_las,leftPrecedingId_las,leftAlongsideId_las,leftFollowingId_las,\
    rightPrecedingId_las,rightAlongsideId_las,rightFollowingId_las,laneId_las,numLaneChanges_las,\
    drivingDirection_las,id_lfo,x_lfo,y_lfo,width_lfo,height_lfo,xVelocity_lfo,yVelocity_lfo,\
    xAccelertion_lfo,yAcceleration_lfo,frontSightDistance_lfo,backSightDistance_lfo,dhw_lfo,\
    thw_lfo,ttc_lfo,precedingXVelocity_lfo,precedingId_lfo,followingId_lfo,leftPrecedingId_lfo,\
    leftAlongsideId_lfo,leftFollowingId_lfo,rightPrecedingId_lfo,rightAlongsideId_lfo,\
    rightFollowingId_lfo,laneId_lfo,numLaneChanges_lfo,drivingDirection_lfo,id_rpr,x_rpr,y_rpr,\
    width_rpr,height_rpr,xVelocity_rpr,yVelocity_rpr,xAccelertion_rpr,yAcceleration_rpr,\
    frontSightDistance_rpr,backSightDistance_rpr,dhw_rpr,thw_rpr,ttc_rpr,precedingXVelocity_rpr,\
    precedingId_rpr,followingId_rpr,leftPrecedingId_rpr,leftAlongsideId_rpr,leftFollowingId_rpr,\
    rightPrecedingId_rpr,rightAlongsideId_rpr,rightFollowingId_rpr,laneId_rpr,numLaneChanges_rpr,\
    drivingDirection_rpr,id_ras,x_ras,y_ras,width_ras,height_ras,xVelocity_ras,yVelocity_ras,\
    xAccelertion_ras,yAcceleration_ras,frontSightDistance_ras,backSightDistance_ras,dhw_ras,\
    thw_ras,ttc_ras,precedingXVelocity_ras,precedingId_ras,followingId_ras,leftPrecedingId_ras,\
    leftAlongsideId_ras,leftFollowingId_ras,rightPrecedingId_ras,rightAlongsideId_ras,\
    rightFollowingId_ras,laneId_ras,numLaneChanges_ras,drivingDirection_ras,id_rfo,x_rfo,y_rfo,\
    width_rfo,height_rfo,xVelocity_rfo,yVelocity_rfo,xAccelertion_rfo,yAcceleration_rfo,\
    frontSightDistance_rfo,backSightDistance_rfo,dhw_rfo,thw_rfo,ttc_rfo,precedingXVelocity_rfo,\
    precedingId_rfo,followingId_rfo,leftPrecedingId_rfo,leftAlongsideId_rfo,leftFollowingId_rfo,\
    rightPrecedingId_rfo,rightAlongsideId_rfo,rightFollowingId_rfo,laneId_rfo,numLaneChanges_rfo,\
    drivingDirection_rfo\n"
    lcs_file.write(lcs_first_line)
    for ego_frame_id in range(ego_frame_range_left_endpoint,ego_frame_range_right_endpoint+1):
        ego_row_id=_ego_begin_row_id+ego_frame_id-ego_begin_frame
        ego_row=_tracks_df.iloc[ego_row_id]
        lcs_line=gen_lcs_line(ego_row,_meta_df,_tracks_df,_vehicles_begin_frame,_vehicles_end_frame,
        _vehicles_row_begin,_lane_change_num)
        lcs_file.write(lcs_line)
    lcs_file.close()
    return True





# check range for an id list
def check_range(_id_list,_frame_range_list,_vehicles_begin_frame,_vehicles_end_frame):
    list_len=len(_id_list)
    # if all vehicles in _id_list meet the range requirement
    in_range=True
    for pos in range(list_len):
        vehicle_id=int(_id_list[pos])
        if(vehicle_id==0):
            continue
        frame_range_require=_frame_range_list[pos]
        range_left=frame_range_require[0]
        range_right=frame_range_require[1]
        vehicle_begin_frame=_vehicles_begin_frame[vehicle_id]
        vehicle_end_frame=_vehicles_end_frame[vehicle_id]
        if(range_left<vehicle_begin_frame):
            in_range=False
        if(range_right>vehicle_end_frame):
            in_range=False
    return in_range


def get_surr_ids_for_every_frame(_surr_by_frame,_surr_id_list,_surr_frame_range_list):
    list_len=len(_surr_id_list)
    for pos in range(list_len):
        surr_vehicle_id=_surr_id_list[pos]
        surr_frame_range=_surr_frame_range_list[pos]
        for frame_id in range(surr_frame_range[0],surr_frame_range[1]+1):
            _surr_by_frame[frame_id]=surr_vehicle_id
    return _surr_by_frame  

def gen_lcs_line(_ego_row,_meta_df,_tracks_df,_vehicles_begin_frame,_vehicles_end_frame,
_vehicles_row_begin,_lane_change_num):
    lcs_line_str=""

    frame_id_ego=int(_ego_row["frame"])
    frame_id=frame_id_ego
    id_ego=int(_ego_row["id"])
    x_ego=_ego_row["x"]
    y_ego=_ego_row["y"]
    width_ego=_ego_row["width"]
    height_ego=_ego_row["height"]
    xVelocity_ego=_ego_row["xVelocity"]
    yVelocity_ego=_ego_row["yVelocity"]
    frontSightDistance_ego=_ego_row["frontSightDistance"]
    backSightDistance_ego=_ego_row["backSightDistance"]
    dhw_ego=_ego_row["dhw"]
    thw_ego=_ego_row["thw"]
    ttc_ego=_ego_row["ttc"]
    precedingXVelocity_ego=_ego_row["precedingXVelocity"]
    precedingId_ego=_ego_row["precedingId"]
    followingId_ego=_ego_row["followingId"]
    leftPrecedingId_ego=_ego_row["leftPrecedingId"]
    leftAlongsideId_ego=_ego_row["leftAlongsideId"]
    leftFollowingId_ego=_ego_row["leftFollowingId"]
    rightPrecedingId_ego=_ego_row["rightPrecedingId"]
    rightAlongsideId_ego=_ego_row["rightAlongsideId"]
    rightFollowingId_ego=_ego_row["rightFollowingId"]
    laneId_ego=_ego_row["laneId"]
    numLaneChanges_ego=_lane_change_num

    ego_meta_row_id=id_ego-1
    ego_meta_row=_meta_df.iloc[ego_meta_row_id]
    drivingDirection_ego=int(ego_meta_row["drivingDirection"])

    lcs_line_str+=str(frame_id_ego)+","
    lcs_line_str+=str(id_ego)+","
    lcs_line_str+=str(x_ego)+","
    lcs_line_str+=str(y_ego)+","
    lcs_line_str+=str(width_ego)+","
    lcs_line_str+=str(height_ego)+","
    lcs_line_str+=str(xVelocity_ego)+","
    lcs_line_str+=str(yVelocity_ego)+","
    lcs_line_str+=str(frontSightDistance_ego)+","
    lcs_line_str+=str(backSightDistance_ego)+","
    lcs_line_str+=str(dhw_ego)+","
    lcs_line_str+=str(thw_ego)+","
    lcs_line_str+=str(ttc_ego)+","
    lcs_line_str+=str(precedingXVelocity_ego)+","
    lcs_line_str+=str(precedingId_ego)+","
    lcs_line_str+=str(followingId_ego)+","
    lcs_line_str+=str(leftPrecedingId_ego)+","
    lcs_line_str+=str(leftAlongsideId_ego)+","
    lcs_line_str+=str(leftFollowingId_ego)+","
    lcs_line_str+=str(rightPrecedingId_ego)+","
    lcs_line_str+=str(rightAlongsideId_ego)+","
    lcs_line_str+=str(rightFollowingId_ego)+","
    lcs_line_str+=str(laneId_ego)+","
    lcs_line_str+=str(numLaneChanges_ego)+","
    lcs_line_str+=str(drivingDirection_ego)+","

    '''
    preceding
    '''
    id_pre=int(precedingId_ego)
    if(id_pre==0):
        for i in range(26):
            lcs_line_str+="0,"
    else:
        pre_begin_row_id=_vehicles_row_begin[id_pre]
        pre_begin_frame=_vehicles_begin_frame[id_pre]
        pre_row_id=pre_begin_row_id+frame_id-pre_begin_frame
        pre_row=_tracks_df.iloc[pre_row_id]
        x_pre=pre_row["x"]
        y_pre=pre_row["y"]
        width_pre=pre_row["width"]
        height_pre=pre_row["height"]
        xVelocity_pre=pre_row["xVelocity"]
        yVelocity_pre=pre_row["yVelocity"]
        xAcceleration_pre=pre_row["xAcceleration"]
        yAcceleration_pre=pre_row["yAcceleration"]
        frontSightDistance_pre=pre_row["frontSightDistance"]
        backSightDistance_pre=pre_row["backSightDistance"]
        dhw_pre=pre_row["dhw"]
        thw_pre=pre_row["thw"]
        ttc_pre=pre_row["ttc"]
        precedingXVelocity_pre=pre_row["precedingXVelocity"]
        precedingId_pre=pre_row["precedingId"]
        followingId_pre=pre_row["followingId"]
        leftPrecedingId_pre=pre_row["leftPrecedingId"]
        leftAlongsideId_pre=pre_row["leftAlongsideId"]
        leftFollowingId_pre=pre_row["leftFollowingId"]
        rightPrecedingId_pre=pre_row["rightPrecedingId"]
        rightAlongsideId_pre=pre_row["rightAlongsideId"]
        rightFollowingId_pre=pre_row["rightFollowingId"]
        laneId_pre=pre_row["laneId"]
        pre_meta_row_id=id_pre-1
        pre_meta_row=_meta_df.iloc[pre_meta_row_id]
        numLaneChanges_pre=pre_meta_row["numLaneChanges"]
        drivingDirection_pre=pre_meta_row["drivingDirection"]

        lcs_line_str+=str(id_pre)+","
        lcs_line_str+=str(x_pre)+","
        lcs_line_str+=str(y_pre)+","
        lcs_line_str+=str(width_pre)+","
        lcs_line_str+=str(height_pre)+","
        lcs_line_str+=str(xVelocity_pre)+","
        lcs_line_str+=str(yVelocity_pre)+","
        lcs_line_str+=str(xAcceleration_pre)+","
        lcs_line_str+=str(yAcceleration_pre)+","
        lcs_line_str+=str(frontSightDistance_pre)+","
        lcs_line_str+=str(backSightDistance_pre)+","
        lcs_line_str+=str(dhw_pre)+","
        lcs_line_str+=str(thw_pre)+","
        lcs_line_str+=str(ttc_pre)+","
        lcs_line_str+=str(precedingXVelocity_pre)+","
        lcs_line_str+=str(precedingId_pre)+","
        lcs_line_str+=str(followingId_pre)+","
        lcs_line_str+=str(leftPrecedingId_pre)+","
        lcs_line_str+=str(leftAlongsideId_pre)+","
        lcs_line_str+=str(leftFollowingId_pre)+","
        lcs_line_str+=str(rightPrecedingId_pre)+","
        lcs_line_str+=str(rightAlongsideId_pre)+","
        lcs_line_str+=str(rightFollowingId_pre)+","
        lcs_line_str+=str(laneId_pre)+","
        lcs_line_str+=str(numLaneChanges_pre)+","
        lcs_line_str+=str(drivingDirection_pre)+","

    '''
    following
    '''

    id_fol=int(followingId_ego)
    if(id_fol==0):
        for i in range(26):
            lcs_line_str+="0,"
    else:
        fol_begin_row_id=_vehicles_row_begin[id_fol]
        fol_begin_frame=_vehicles_begin_frame[id_fol]
        fol_row_id=fol_begin_row_id+frame_id-fol_begin_frame
        fol_row=_tracks_df.iloc[fol_row_id]
        x_fol=fol_row["x"]
        y_fol=fol_row["y"]
        width_fol=fol_row["width"]
        height_fol=fol_row["height"]
        xVelocity_fol=fol_row["xVelocity"]
        yVelocity_fol=fol_row["yVelocity"]
        xAcceleration_fol=fol_row["xAcceleration"]
        yAcceleration_fol=fol_row["yAcceleration"]
        frontSightDistance_fol=fol_row["frontSightDistance"]
        backSightDistance_fol=fol_row["backSightDistance"]
        dhw_fol=fol_row["dhw"]
        thw_fol=fol_row["thw"]
        ttc_fol=fol_row["ttc"]
        precedingXVelocity_fol=fol_row["precedingXVelocity"]
        precedingId_fol=fol_row["precedingId"]
        followingId_fol=fol_row["followingId"]
        leftPrecedingId_fol=fol_row["leftPrecedingId"]
        leftAlongsideId_fol=fol_row["leftAlongsideId"]
        leftFollowingId_fol=fol_row["leftFollowingId"]
        rightPrecedingId_fol=fol_row["rightPrecedingId"]
        rightAlongsideId_fol=fol_row["rightAlongsideId"]
        rightFollowingId_fol=fol_row["rightFollowingId"]
        laneId_fol=fol_row["laneId"]
        fol_meta_row_id=id_fol-1
        fol_meta_row=_meta_df.iloc[fol_meta_row_id]
        numLaneChanges_fol=fol_meta_row["numLaneChanges"]
        drivingDirection_fol=fol_meta_row["drivingDirection"]

        lcs_line_str+=str(id_fol)+","
        lcs_line_str+=str(x_fol)+","
        lcs_line_str+=str(y_fol)+","
        lcs_line_str+=str(width_fol)+","
        lcs_line_str+=str(height_fol)+","
        lcs_line_str+=str(xVelocity_fol)+","
        lcs_line_str+=str(yVelocity_fol)+","
        lcs_line_str+=str(xAcceleration_fol)+","
        lcs_line_str+=str(yAcceleration_fol)+","
        lcs_line_str+=str(frontSightDistance_fol)+","
        lcs_line_str+=str(backSightDistance_fol)+","
        lcs_line_str+=str(dhw_fol)+","
        lcs_line_str+=str(thw_fol)+","
        lcs_line_str+=str(ttc_fol)+","
        lcs_line_str+=str(precedingXVelocity_fol)+","
        lcs_line_str+=str(precedingId_fol)+","
        lcs_line_str+=str(followingId_fol)+","
        lcs_line_str+=str(leftPrecedingId_fol)+","
        lcs_line_str+=str(leftAlongsideId_fol)+","
        lcs_line_str+=str(leftFollowingId_fol)+","
        lcs_line_str+=str(rightPrecedingId_fol)+","
        lcs_line_str+=str(rightAlongsideId_fol)+","
        lcs_line_str+=str(rightFollowingId_fol)+","
        lcs_line_str+=str(laneId_fol)+","
        lcs_line_str+=str(numLaneChanges_fol)+","
        lcs_line_str+=str(drivingDirection_fol)+","

    '''
    left_preceding
    '''
    id_lpr=int(leftPrecedingId_ego)
    if(id_lpr==0):
        for i in range(26):
            lcs_line_str+="0,"
    else:
        lpr_begin_row_id=_vehicles_row_begin[id_lpr]
        lpr_begin_frame=_vehicles_begin_frame[id_lpr]
        lpr_row_id=lpr_begin_row_id+frame_id-lpr_begin_frame
        lpr_row=_tracks_df.iloc[lpr_row_id]
        x_lpr=lpr_row["x"]
        y_lpr=lpr_row["y"]
        width_lpr=lpr_row["width"]
        height_lpr=lpr_row["height"]
        xVelocity_lpr=lpr_row["xVelocity"]
        yVelocity_lpr=lpr_row["yVelocity"]
        xAcceleration_lpr=lpr_row["xAcceleration"]
        yAcceleration_lpr=lpr_row["yAcceleration"]
        frontSightDistance_lpr=lpr_row["frontSightDistance"]
        backSightDistance_lpr=lpr_row["backSightDistance"]
        dhw_lpr=lpr_row["dhw"]
        thw_lpr=lpr_row["thw"]
        ttc_lpr=lpr_row["ttc"]
        precedingXVelocity_lpr=lpr_row["precedingXVelocity"]
        precedingId_lpr=lpr_row["precedingId"]
        followingId_lpr=lpr_row["followingId"]
        leftPrecedingId_lpr=lpr_row["leftPrecedingId"]
        leftAlongsideId_lpr=lpr_row["leftAlongsideId"]
        leftFollowingId_lpr=lpr_row["leftFollowingId"]
        rightPrecedingId_lpr=lpr_row["rightPrecedingId"]
        rightAlongsideId_lpr=lpr_row["rightAlongsideId"]
        rightFollowingId_lpr=lpr_row["rightFollowingId"]
        laneId_lpr=lpr_row["laneId"]
        lpr_meta_row_id=id_lpr-1
        lpr_meta_row=_meta_df.iloc[lpr_meta_row_id]
        numLaneChanges_lpr=lpr_meta_row["numLaneChanges"]
        drivingDirection_lpr=lpr_meta_row["drivingDirection"]

        lcs_line_str+=str(id_lpr)+","
        lcs_line_str+=str(x_lpr)+","
        lcs_line_str+=str(y_lpr)+","
        lcs_line_str+=str(width_lpr)+","
        lcs_line_str+=str(height_lpr)+","
        lcs_line_str+=str(xVelocity_lpr)+","
        lcs_line_str+=str(yVelocity_lpr)+","
        lcs_line_str+=str(xAcceleration_lpr)+","
        lcs_line_str+=str(yAcceleration_lpr)+","
        lcs_line_str+=str(frontSightDistance_lpr)+","
        lcs_line_str+=str(backSightDistance_lpr)+","
        lcs_line_str+=str(dhw_lpr)+","
        lcs_line_str+=str(thw_lpr)+","
        lcs_line_str+=str(ttc_lpr)+","
        lcs_line_str+=str(precedingXVelocity_lpr)+","
        lcs_line_str+=str(precedingId_lpr)+","
        lcs_line_str+=str(followingId_lpr)+","
        lcs_line_str+=str(leftPrecedingId_lpr)+","
        lcs_line_str+=str(leftAlongsideId_lpr)+","
        lcs_line_str+=str(leftFollowingId_lpr)+","
        lcs_line_str+=str(rightPrecedingId_lpr)+","
        lcs_line_str+=str(rightAlongsideId_lpr)+","
        lcs_line_str+=str(rightFollowingId_lpr)+","
        lcs_line_str+=str(laneId_lpr)+","
        lcs_line_str+=str(numLaneChanges_lpr)+","
        lcs_line_str+=str(drivingDirection_lpr)+","


    '''
    left_alongside
    '''
    id_las=int(leftAlongsideId_ego)
    if(id_las==0):
        for i in range(26):
            lcs_line_str+="0,"
    else:
        las_begin_row_id=_vehicles_row_begin[id_las]
        las_begin_frame=_vehicles_begin_frame[id_las]
        las_row_id=las_begin_row_id+frame_id-las_begin_frame
        las_row=_tracks_df.iloc[las_row_id]
        x_las=las_row["x"]
        y_las=las_row["y"]
        width_las=las_row["width"]
        height_las=las_row["height"]
        xVelocity_las=las_row["xVelocity"]
        yVelocity_las=las_row["yVelocity"]
        xAcceleration_las=las_row["xAcceleration"]
        yAcceleration_las=las_row["yAcceleration"]
        frontSightDistance_las=las_row["frontSightDistance"]
        backSightDistance_las=las_row["backSightDistance"]
        dhw_las=las_row["dhw"]
        thw_las=las_row["thw"]
        ttc_las=las_row["ttc"]
        precedingXVelocity_las=las_row["precedingXVelocity"]
        precedingId_las=las_row["precedingId"]
        followingId_las=las_row["followingId"]
        leftPrecedingId_las=las_row["leftPrecedingId"]
        leftAlongsideId_las=las_row["leftAlongsideId"]
        leftFollowingId_las=las_row["leftFollowingId"]
        rightPrecedingId_las=las_row["rightPrecedingId"]
        rightAlongsideId_las=las_row["rightAlongsideId"]
        rightFollowingId_las=las_row["rightFollowingId"]
        laneId_las=las_row["laneId"]
        las_meta_row_id=id_las-1
        las_meta_row=_meta_df.iloc[las_meta_row_id]
        numLaneChanges_las=las_meta_row["numLaneChanges"]
        drivingDirection_las=las_meta_row["drivingDirection"]

        lcs_line_str+=str(id_las)+","
        lcs_line_str+=str(x_las)+","
        lcs_line_str+=str(y_las)+","
        lcs_line_str+=str(width_las)+","
        lcs_line_str+=str(height_las)+","
        lcs_line_str+=str(xVelocity_las)+","
        lcs_line_str+=str(yVelocity_las)+","
        lcs_line_str+=str(xAcceleration_las)+","
        lcs_line_str+=str(yAcceleration_las)+","
        lcs_line_str+=str(frontSightDistance_las)+","
        lcs_line_str+=str(backSightDistance_las)+","
        lcs_line_str+=str(dhw_las)+","
        lcs_line_str+=str(thw_las)+","
        lcs_line_str+=str(ttc_las)+","
        lcs_line_str+=str(precedingXVelocity_las)+","
        lcs_line_str+=str(precedingId_las)+","
        lcs_line_str+=str(followingId_las)+","
        lcs_line_str+=str(leftPrecedingId_las)+","
        lcs_line_str+=str(leftAlongsideId_las)+","
        lcs_line_str+=str(leftFollowingId_las)+","
        lcs_line_str+=str(rightPrecedingId_las)+","
        lcs_line_str+=str(rightAlongsideId_las)+","
        lcs_line_str+=str(rightFollowingId_las)+","
        lcs_line_str+=str(laneId_las)+","
        lcs_line_str+=str(numLaneChanges_las)+","
        lcs_line_str+=str(drivingDirection_las)+","
    

    '''
    left_following
    '''
    id_lfo=int(leftFollowingId_ego)
    if(id_lfo==0):
        for i in range(26):
            lcs_line_str+="0,"
    else:
        lfo_begin_row_id=_vehicles_row_begin[id_lfo]
        lfo_begin_frame=_vehicles_begin_frame[id_lfo]
        lfo_row_id=lfo_begin_row_id+frame_id-lfo_begin_frame
        lfo_row=_tracks_df.iloc[lfo_row_id]
        x_lfo=lfo_row["x"]
        y_lfo=lfo_row["y"]
        width_lfo=lfo_row["width"]
        height_lfo=lfo_row["height"]
        xVelocity_lfo=lfo_row["xVelocity"]
        yVelocity_lfo=lfo_row["yVelocity"]
        xAcceleration_lfo=lfo_row["xAcceleration"]
        yAcceleration_lfo=lfo_row["yAcceleration"]
        frontSightDistance_lfo=lfo_row["frontSightDistance"]
        backSightDistance_lfo=lfo_row["backSightDistance"]
        dhw_lfo=lfo_row["dhw"]
        thw_lfo=lfo_row["thw"]
        ttc_lfo=lfo_row["ttc"]
        precedingXVelocity_lfo=lfo_row["precedingXVelocity"]
        precedingId_lfo=lfo_row["precedingId"]
        followingId_lfo=lfo_row["followingId"]
        leftPrecedingId_lfo=lfo_row["leftPrecedingId"]
        leftAlongsideId_lfo=lfo_row["leftAlongsideId"]
        leftFollowingId_lfo=lfo_row["leftFollowingId"]
        rightPrecedingId_lfo=lfo_row["rightPrecedingId"]
        rightAlongsideId_lfo=lfo_row["rightAlongsideId"]
        rightFollowingId_lfo=lfo_row["rightFollowingId"]
        laneId_lfo=lfo_row["laneId"]
        lfo_meta_row_id=id_lfo-1
        lfo_meta_row=_meta_df.iloc[lfo_meta_row_id]
        numLaneChanges_lfo=lfo_meta_row["numLaneChanges"]
        drivingDirection_lfo=lfo_meta_row["drivingDirection"]

        lcs_line_str+=str(id_lfo)+","
        lcs_line_str+=str(x_lfo)+","
        lcs_line_str+=str(y_lfo)+","
        lcs_line_str+=str(width_lfo)+","
        lcs_line_str+=str(height_lfo)+","
        lcs_line_str+=str(xVelocity_lfo)+","
        lcs_line_str+=str(yVelocity_lfo)+","
        lcs_line_str+=str(xAcceleration_lfo)+","
        lcs_line_str+=str(yAcceleration_lfo)+","
        lcs_line_str+=str(frontSightDistance_lfo)+","
        lcs_line_str+=str(backSightDistance_lfo)+","
        lcs_line_str+=str(dhw_lfo)+","
        lcs_line_str+=str(thw_lfo)+","
        lcs_line_str+=str(ttc_lfo)+","
        lcs_line_str+=str(precedingXVelocity_lfo)+","
        lcs_line_str+=str(precedingId_lfo)+","
        lcs_line_str+=str(followingId_lfo)+","
        lcs_line_str+=str(leftPrecedingId_lfo)+","
        lcs_line_str+=str(leftAlongsideId_lfo)+","
        lcs_line_str+=str(leftFollowingId_lfo)+","
        lcs_line_str+=str(rightPrecedingId_lfo)+","
        lcs_line_str+=str(rightAlongsideId_lfo)+","
        lcs_line_str+=str(rightFollowingId_lfo)+","
        lcs_line_str+=str(laneId_lfo)+","
        lcs_line_str+=str(numLaneChanges_lfo)+","
        lcs_line_str+=str(drivingDirection_lfo)+","



    '''
    right_preceding
    '''
    id_rpr=int(rightPrecedingId_ego)
    if(id_rpr==0):
        for i in range(26):
            lcs_line_str+="0,"
    else:
        rpr_begin_row_id=_vehicles_row_begin[id_rpr]
        rpr_begin_frame=_vehicles_begin_frame[id_rpr]
        rpr_row_id=rpr_begin_row_id+frame_id-rpr_begin_frame
        rpr_row=_tracks_df.iloc[rpr_row_id]
        x_rpr=rpr_row["x"]
        y_rpr=rpr_row["y"]
        width_rpr=rpr_row["width"]
        height_rpr=rpr_row["height"]
        xVelocity_rpr=rpr_row["xVelocity"]
        yVelocity_rpr=rpr_row["yVelocity"]
        xAcceleration_rpr=rpr_row["xAcceleration"]
        yAcceleration_rpr=rpr_row["yAcceleration"]
        frontSightDistance_rpr=rpr_row["frontSightDistance"]
        backSightDistance_rpr=rpr_row["backSightDistance"]
        dhw_rpr=rpr_row["dhw"]
        thw_rpr=rpr_row["thw"]
        ttc_rpr=rpr_row["ttc"]
        precedingXVelocity_rpr=rpr_row["precedingXVelocity"]
        precedingId_rpr=rpr_row["precedingId"]
        followingId_rpr=rpr_row["followingId"]
        leftPrecedingId_rpr=rpr_row["leftPrecedingId"]
        leftAlongsideId_rpr=rpr_row["leftAlongsideId"]
        leftFollowingId_rpr=rpr_row["leftFollowingId"]
        rightPrecedingId_rpr=rpr_row["rightPrecedingId"]
        rightAlongsideId_rpr=rpr_row["rightAlongsideId"]
        rightFollowingId_rpr=rpr_row["rightFollowingId"]
        laneId_rpr=rpr_row["laneId"]
        rpr_meta_row_id=id_rpr-1
        rpr_meta_row=_meta_df.iloc[rpr_meta_row_id]
        numLaneChanges_rpr=rpr_meta_row["numLaneChanges"]
        drivingDirection_rpr=rpr_meta_row["drivingDirection"]

        lcs_line_str+=str(id_rpr)+","
        lcs_line_str+=str(x_rpr)+","
        lcs_line_str+=str(y_rpr)+","
        lcs_line_str+=str(width_rpr)+","
        lcs_line_str+=str(height_rpr)+","
        lcs_line_str+=str(xVelocity_rpr)+","
        lcs_line_str+=str(yVelocity_rpr)+","
        lcs_line_str+=str(xAcceleration_rpr)+","
        lcs_line_str+=str(yAcceleration_rpr)+","
        lcs_line_str+=str(frontSightDistance_rpr)+","
        lcs_line_str+=str(backSightDistance_rpr)+","
        lcs_line_str+=str(dhw_rpr)+","
        lcs_line_str+=str(thw_rpr)+","
        lcs_line_str+=str(ttc_rpr)+","
        lcs_line_str+=str(precedingXVelocity_rpr)+","
        lcs_line_str+=str(precedingId_rpr)+","
        lcs_line_str+=str(followingId_rpr)+","
        lcs_line_str+=str(leftPrecedingId_rpr)+","
        lcs_line_str+=str(leftAlongsideId_rpr)+","
        lcs_line_str+=str(leftFollowingId_rpr)+","
        lcs_line_str+=str(rightPrecedingId_rpr)+","
        lcs_line_str+=str(rightAlongsideId_rpr)+","
        lcs_line_str+=str(rightFollowingId_rpr)+","
        lcs_line_str+=str(laneId_rpr)+","
        lcs_line_str+=str(numLaneChanges_rpr)+","
        lcs_line_str+=str(drivingDirection_rpr)+","

        
    '''
    right_alongside
    '''
    id_ras=int(rightAlongsideId_ego)
    if(id_ras==0):
        for i in range(26):
            lcs_line_str+="0,"
    else:
        ras_begin_row_id=_vehicles_row_begin[id_ras]
        ras_begin_frame=_vehicles_begin_frame[id_ras]
        ras_row_id=ras_begin_row_id+frame_id-ras_begin_frame
        ras_row=_tracks_df.iloc[ras_row_id]
        x_ras=ras_row["x"]
        y_ras=ras_row["y"]
        width_ras=ras_row["width"]
        height_ras=ras_row["height"]
        xVelocity_ras=ras_row["xVelocity"]
        yVelocity_ras=ras_row["yVelocity"]
        xAcceleration_ras=ras_row["xAcceleration"]
        yAcceleration_ras=ras_row["yAcceleration"]
        frontSightDistance_ras=ras_row["frontSightDistance"]
        backSightDistance_ras=ras_row["backSightDistance"]
        dhw_ras=ras_row["dhw"]
        thw_ras=ras_row["thw"]
        ttc_ras=ras_row["ttc"]
        precedingXVelocity_ras=ras_row["precedingXVelocity"]
        precedingId_ras=ras_row["precedingId"]
        followingId_ras=ras_row["followingId"]
        leftPrecedingId_ras=ras_row["leftPrecedingId"]
        leftAlongsideId_ras=ras_row["leftAlongsideId"]
        leftFollowingId_ras=ras_row["leftFollowingId"]
        rightPrecedingId_ras=ras_row["rightPrecedingId"]
        rightAlongsideId_ras=ras_row["rightAlongsideId"]
        rightFollowingId_ras=ras_row["rightFollowingId"]
        laneId_ras=ras_row["laneId"]
        ras_meta_row_id=id_ras-1
        ras_meta_row=_meta_df.iloc[ras_meta_row_id]
        numLaneChanges_ras=ras_meta_row["numLaneChanges"]
        drivingDirection_ras=ras_meta_row["drivingDirection"]

        lcs_line_str+=str(id_ras)+","
        lcs_line_str+=str(x_ras)+","
        lcs_line_str+=str(y_ras)+","
        lcs_line_str+=str(width_ras)+","
        lcs_line_str+=str(height_ras)+","
        lcs_line_str+=str(xVelocity_ras)+","
        lcs_line_str+=str(yVelocity_ras)+","
        lcs_line_str+=str(xAcceleration_ras)+","
        lcs_line_str+=str(yAcceleration_ras)+","
        lcs_line_str+=str(frontSightDistance_ras)+","
        lcs_line_str+=str(backSightDistance_ras)+","
        lcs_line_str+=str(dhw_ras)+","
        lcs_line_str+=str(thw_ras)+","
        lcs_line_str+=str(ttc_ras)+","
        lcs_line_str+=str(precedingXVelocity_ras)+","
        lcs_line_str+=str(precedingId_ras)+","
        lcs_line_str+=str(followingId_ras)+","
        lcs_line_str+=str(leftPrecedingId_ras)+","
        lcs_line_str+=str(leftAlongsideId_ras)+","
        lcs_line_str+=str(leftFollowingId_ras)+","
        lcs_line_str+=str(rightPrecedingId_ras)+","
        lcs_line_str+=str(rightAlongsideId_ras)+","
        lcs_line_str+=str(rightFollowingId_ras)+","
        lcs_line_str+=str(laneId_ras)+","
        lcs_line_str+=str(numLaneChanges_ras)+","
        lcs_line_str+=str(drivingDirection_ras)+","

    '''
    right_following
    '''
    id_rfo=int(rightAlongsideId_ego)
    if(id_rfo==0):
        for i in range(25):
            lcs_line_str+="0,"
        lcs_line_str+="0"
    else:
        rfo_begin_row_id=_vehicles_row_begin[id_rfo]
        rfo_begin_frame=_vehicles_begin_frame[id_rfo]
        rfo_row_id=rfo_begin_row_id+frame_id-rfo_begin_frame
        rfo_row=_tracks_df.iloc[rfo_row_id]
        x_rfo=rfo_row["x"]
        y_rfo=rfo_row["y"]
        width_rfo=rfo_row["width"]
        height_rfo=rfo_row["height"]
        xVelocity_rfo=rfo_row["xVelocity"]
        yVelocity_rfo=rfo_row["yVelocity"]
        xAcceleration_rfo=rfo_row["xAcceleration"]
        yAcceleration_rfo=rfo_row["yAcceleration"]
        frontSightDistance_rfo=rfo_row["frontSightDistance"]
        backSightDistance_rfo=rfo_row["backSightDistance"]
        dhw_rfo=rfo_row["dhw"]
        thw_rfo=rfo_row["thw"]
        ttc_rfo=rfo_row["ttc"]
        precedingXVelocity_rfo=rfo_row["precedingXVelocity"]
        precedingId_rfo=rfo_row["precedingId"]
        followingId_rfo=rfo_row["followingId"]
        leftPrecedingId_rfo=rfo_row["leftPrecedingId"]
        leftAlongsideId_rfo=rfo_row["leftAlongsideId"]
        leftFollowingId_rfo=rfo_row["leftFollowingId"]
        rightPrecedingId_rfo=rfo_row["rightPrecedingId"]
        rightAlongsideId_rfo=rfo_row["rightAlongsideId"]
        rightFollowingId_rfo=rfo_row["rightFollowingId"]
        laneId_rfo=rfo_row["laneId"]
        rfo_meta_row_id=id_rfo-1
        rfo_meta_row=_meta_df.iloc[rfo_meta_row_id]
        numLaneChanges_rfo=rfo_meta_row["numLaneChanges"]
        drivingDirection_rfo=rfo_meta_row["drivingDirection"]

        lcs_line_str+=str(id_rfo)+","
        lcs_line_str+=str(x_rfo)+","
        lcs_line_str+=str(y_rfo)+","
        lcs_line_str+=str(width_rfo)+","
        lcs_line_str+=str(height_rfo)+","
        lcs_line_str+=str(xVelocity_rfo)+","
        lcs_line_str+=str(yVelocity_rfo)+","
        lcs_line_str+=str(xAcceleration_rfo)+","
        lcs_line_str+=str(yAcceleration_rfo)+","
        lcs_line_str+=str(frontSightDistance_rfo)+","
        lcs_line_str+=str(backSightDistance_rfo)+","
        lcs_line_str+=str(dhw_rfo)+","
        lcs_line_str+=str(thw_rfo)+","
        lcs_line_str+=str(ttc_rfo)+","
        lcs_line_str+=str(precedingXVelocity_rfo)+","
        lcs_line_str+=str(precedingId_rfo)+","
        lcs_line_str+=str(followingId_rfo)+","
        lcs_line_str+=str(leftPrecedingId_rfo)+","
        lcs_line_str+=str(leftAlongsideId_rfo)+","
        lcs_line_str+=str(leftFollowingId_rfo)+","
        lcs_line_str+=str(rightPrecedingId_rfo)+","
        lcs_line_str+=str(rightAlongsideId_rfo)+","
        lcs_line_str+=str(rightFollowingId_rfo)+","
        lcs_line_str+=str(laneId_rfo)+","
        lcs_line_str+=str(numLaneChanges_rfo)+","
        lcs_line_str+=str(drivingDirection_rfo)
    lcs_line_str+="\n"
    return lcs_line_str


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
    



if __name__=="__main__":

    data_prefix="../data/"
    for file_id in range(10,61):
        file_id_str=None
        if(file_id<10):
            file_id_str="0"+str(file_id)
        else:
            file_id_str=str(file_id)
        tracks_path=data_prefix+file_id_str+"_tracks.csv"
        meta_path=data_prefix+file_id_str+"_tracksMeta.csv"
        recording_path=data_prefix+file_id_str+"_recordingMeta.csv"
        # preprocess tracks file to save time
        tracks_is_file=os.path.isfile(tracks_path)
        meta_is_file=os.path.isfile(meta_path)
        recording_is_file=os.path.isfile(recording_path)
        complete_file=tracks_is_file and meta_is_file and recording_is_file
        if(not complete_file):
            continue
        store_frame_num_info(recording_path,tracks_path,file_id)
        extract_file(recording_path,meta_path,tracks_path,file_id)
    