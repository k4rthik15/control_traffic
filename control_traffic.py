import cv2
import numpy as np
from yolov5 import detect
import time
def load_yolo_model(config_path,weights_path):
    net=cv2.dnn.readNet(weights_path,config_path)
    return net
def load_yolo_classes(classes_path):
    with open(classes_path,'r') as f:
        classes=f.read().strip().split('\n')
        return classes

def initialize_signal_states(lanes):
    signal_states={}
    for lane in lanes:
        signal_states[lane]={
            'straight/right':'red',
            'left':'red',
            'pedestrian':'red'}
    return signal_states
def detect_vehicles(frame,confidence_threshold=0.5):
    results=detect(frame,conf=confidence_threshold)
    vehicle_boxes=[(int(box[0]),int(box[1]),int(box[2]-box[0]),int(box[3]-box[1])) for box in results[:, :4]]
    return vehicle_boxes

def count_vehicles(vehicle_boxes,roi_map):
    lane_counts={lane:0 for lane in roi_map}
    for box in vehicle_boxes:
        x,y,w,h=box
        for lane,roi in roi_map.itmes():
            if roi[0][0]<x+w<roi[1][0] and roi[0][1]<y+h<roi[1][1]:
                lane_counts[lane]+=1
                break
    return lane_counts

def control_traffic(lane_counts, signal_states, pedestrian_buttons_pressed, pedestrian_signal_wait_time, pedestrian_signal_green_duration=15, green_signal_time=60, extra_green_time=15, yellow_signal_time=5):
  sorted_lanes = sorted(lane_counts, key=lane_counts.get, reverse=True)
    next_lane_index = 0
    for current_lane_index, lane in enumerate(sorted_lanes):
        count = lane_counts[lane]
        next_lane_index = (current_lane_index + 1) % len(sorted_lanes)
        next_lane = sorted_lanes[next_lane_index]
        time.sleep(yellow_signal_time)
        signal_states[lane]['straight/right'] = 'yellow'
        signal_states[lane]['left'] = 'yellow'
        print(f"Vehicle signals for {lane} set to yellow before turning green")
        
        if count > 20:
            signal_states[lane]['straight/right'] = 'green'
            signal_states[lane]['left'] = 'green'
            print(f"Signals for {lane} set to green for {green_signal_time + extra_green_time} seconds")
            time.sleep(green_signal_time + extra_green_time)
        else:
            signal_states[lane]['straight/right'] = 'green'
            signal_states[lane]['left'] = 'green'
            print(f"Signal for {lane} set to green for {green_signal_time} seconds")
            time.sleep(green_signal_time)
        time.sleep(yellow_signal_time)
        signal_states[next_lane]['straight/right'] = 'yellow'
        signal_states[next_lane]['left'] = 'yellow'
        print(f"Vehicle signals for {next_lane} set to yellow after turning green")
        
        signal_states[lane]['straight/right'] = 'red'
        signal_states[lane]['left'] = 'red'
        print(f"Vehicle signals for {lane} set to red after turning yellow")
        
            # Pedestrian signal
    if pedestrian_buttons_pressed.get(lane, False) and pedestrian_signal_wait_time[lane] > 0:
        print(f"Pedestrian signal for {lane} will change to green in {pedestrian_signal_wait_time[lane]} seconds")
        time.sleep(pedestrian_signal_wait_time[lane])
        signal_states[lane]['pedestrian'] = 'green'
        print(f"Pedestrian signal for {lane} changed to green")
        time.sleep(pedestrian_signal_green_duration - yellow_signal_time)
        signal_states[lane]['straight/right'] = 'yellow'
        signal_states[lane]['left'] = 'yellow'
        print(f"Vehicle signals for {lane} set to yellow before pedestrian signal turns green")            
        print(f"Pedestrian signal for {lane} will stay green for {pedestrian_signal_green_duration} seconds")
        time.sleep(pedestrian_signal_green_duration)
        signal_states[lane]['pedestrian'] = 'red'
        print(f"Pedestrian signal for {lane} changed to red")
        time.sleep(pedestrian_signal_wait_time[lane] - pedestrian_signal_green_duration - yellow_signal_time)
        signal_states[lane]['straight/right'] = 'yellow'
        signal_states[lane]['left'] = 'yellow'
        print(f"Vehicle signals for {lane} set to yellow before turning red")
        
        # Synchronize left signal with other lanes' signals
    '''left_signal_lane = None
    for lane, signals in signal_states.items():
        if signals['left'] == 'green':
            left_signal_lane = lane
            break

    if left_signal_lane:
        for lane, signals in signal_states.items():
            if lane != left_signal_lane:
                signals['left'] = signal_states[left_signal_lane]['left']'''

    return signal_states


def main():
    cap=cv2.VideoCapture(0)
    roi_map={
        'lane1':[(0,0),(300,720)],
        'lane2':[(300,0),(600,720)],
        'lane3': [(600, 0), (900, 720)],
        'lane4': [(900, 0), (1200, 720)]
        #add more lanes or directions as needed
    }
    signal_states=initialize_signal_states(roi_map.keys())
    pedestrian_signal_wait_time={'lane1':15,'lane2':15,'lane3':15,'lane4':15}
    pedestrian_buttons_pressed={'lane1':False,'lane2':False,'lane3':False,'lane4':False}
    while cap.isOpened():
        ret,frame=cap.read()
        if not ret:
            break
        vehicle_boxes=detect_vehicles(frame)
        lane_counts=count_vehicles(vehicle_boxes,roi_map)
        signal_states=control_traffic(lane_counts,signal_states,pedestrian_buttons_pressed,pedestrian_signal_wait_time=pedestrian_signal_wait_time)
        for lane,signals in signal_states.items():
            if signals['straight/right']=='green' or signals['left']=='green':
                cv2.rectangle(frame,(roi_map[lane][0][0],20),(roi_map[lane][1][0],70),(0,255,0),-1)
                cv2.putText(frame,f"{lane}:GREEN",(roi_map[lane][0][0]+10,50),cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,0),2)
            elif signals['straight/right']=='yellow' or signals['left']=='yellow':
                cv2.rectangle(frame,(roi_map[lane][0][0],20),(roi_map[lane][1][0],70),(0,255,255),-1)
                cv2.putText(frame,f"{lane}:YELLOW",(roi_map[lane][0][0]+10,50),cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,0),2)
            else:
                cv2.rectangle(frame,(roi_map[lane][0][0],20),(roi_map[lane][1][0],70),(0,0,255),-1)
                cv2.putText(frame,f"{lane}:RED",(roi_map[lane][0][0]+10,50),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),2)
        cv2.imshow('Traffic Signals',frame)
        if cv2.waitKey(1) & 0xFF==ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
