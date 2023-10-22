import os
import re
import glob
from tqdm import tqdm
from datetime import datetime

from pytube import YouTube
import numpy as np
import cv2

from .Tracker import YOLOTracker
from .utils import extract_audio, merge_audio


class DynamicCropper:
    """
    A class for dynamically cropping a person in a video based on specified parameters.
    
    Args:
        frame_interval (int): skip frame computation interval.
        model_path: (str): local path to yolov8 model file
        model_url: (str): downloadable link to yolov8 model file
        size_aware: (bool): size_aware parameter
        only_object: (bool): size_aware parameter
        tracker_algorithm: (str): tracker algorithm for yolov8
    """
    
    def __init__(
        self, frame_interval: int = 1, 
        model_path: str = None,
        model_name: str = None,
        size_aware: bool = False,
        only_object: bool = False,
        tracker_algorithm: str = "botsort.yaml",
        n_threads: int = 5
    ) -> None:
        
        self.frame_interval = frame_interval
        self.size_aware = size_aware
        self.only_object = only_object
        self.n_threads = n_threads
        self.tracker = YOLOTracker(model_path, model_name, tracker_algorithm)
    
    def _pre_process_video(self, input_path: str, output_folder_path: str):
        os.makedirs(output_folder_path, exist_ok=True)
        video_folder_path = None
        
        if re.match(r'https?://(www\.)?(youtube\.com|youtu\.be)/', input_path):
            video = YouTube(input_path)
            video_title = video.title
            
            video_folder_path = os.path.join(output_folder_path, video_title)
            
            if os.path.exists(video_folder_path):
                print("=> WARNING:", f"'{video_folder_path}'", "already exists, creating with time-stamp.")
                current_time = datetime.now()
                current_time = current_time.strftime("__%Hh_%Mm_%Ss")
                video_folder_path += str(current_time)
            os.makedirs(video_folder_path, exist_ok=True)
            
            stream = video.streams.get_highest_resolution()
            stream.download(output_path=video_folder_path)
            
            video_file_path = os.path.join(video_folder_path, stream.default_filename)

        elif any(input_path.lower().endswith(ext) for ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv']):
            base_filename = os.path.basename(input_path)
            file_name, _ = os.path.splitext(base_filename)
            
            video_folder_path = os.path.join(output_folder_path, file_name)
            
            if os.path.exists(video_folder_path):
                print("=> WARNING:", f"'{video_folder_path}'", "already exists, creating with time-stamp.")
                current_time = datetime.now()
                current_time = current_time.strftime("__%Hh_%Mm_%Ss")
                video_folder_path += str(current_time)
                print(video_folder_path)
            os.makedirs(video_folder_path, exist_ok=True)
            video_file_path = input_path
        
        else:
            raise ValueError("'input path' unrecognized input")    
             
        video_details = self._get_video_details(video_folder_path, video_file_path)
        self.output_file_path = os.path.join(video_folder_path, "output.mp4")
        return video_details
    
    @staticmethod
    def _get_video_details(video_folder_path, video_file_path):
        frames_folder_path = os.path.join(video_folder_path, "frames")
        operated_frames_folder_path = os.path.join(video_folder_path, "operated_frames")
        os.makedirs(frames_folder_path, exist_ok=True)
        os.makedirs(operated_frames_folder_path, exist_ok=True)

        cap = cv2.VideoCapture(video_file_path)

        frame_width = int(cap.get(3))
        frame_height = int(cap.get(4))
        fps = int(cap.get(5))
        video_size = (frame_width, frame_height)

        base_filename = os.path.basename(video_file_path)
        file_name, _ = os.path.splitext(base_filename)
        audio_file_path = os.path.join(video_folder_path, file_name + ".mp3")

        extract_audio(video_file_path, audio_file_path)

        frame_count = 0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        progress_bar = tqdm(total=total_frames, desc="Extracting Frames")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_filename = f"frame_{frame_count:04d}.jpg"
            frame_path = os.path.join(frames_folder_path, frame_filename)
            cv2.imwrite(frame_path, frame)

            frame_count += 1
            progress_bar.update(1)

        progress_bar.close()
        cap.release()

        return {
            "frames_folder_path": frames_folder_path,
            "operated_frames_folder_path": operated_frames_folder_path,
            "audio_file_path": audio_file_path,
            "video_size": video_size,
            "fps": fps
        }
    
    @staticmethod
    def _interpolate_frames(frame_list):
        
        interpolated_frames = [frame for frame in frame_list if frame['box']]
        for frame_index in tqdm(range(len(interpolated_frames) - 1), desc="Interpolating Frames"):
            frame1 = interpolated_frames[frame_index]
            frame2 = interpolated_frames[frame_index + 1]
            
            total_frames = frame2['frame_id'] - frame1['frame_id'] - 1
            t_values = np.linspace(0, 1, total_frames)
            
            x1_interpolated_values = frame1['box']['x1'] + t_values * (frame2['box']['x1'] - frame1['box']['x1'])
            y1_interpolated_values = frame1['box']['y1'] + t_values * (frame2['box']['y1'] - frame1['box']['y1'])
            
            x2_interpolated_values = frame1['box']['x2'] + t_values * (frame2['box']['x2'] - frame1['box']['x2'])
            y2_interpolated_values = frame1['box']['y2'] + t_values * (frame2['box']['y2'] - frame1['box']['y2'])

            for interpole_frame_index in range(total_frames):
                relative_index = interpole_frame_index + frame1['frame_id'] + 1
                
                frame_list[relative_index]['box']['x1'] = x1_interpolated_values[interpole_frame_index]
                frame_list[relative_index]['box']['y1'] = y1_interpolated_values[interpole_frame_index]
                
                frame_list[relative_index]['box']['x2'] = x2_interpolated_values[interpole_frame_index]
                frame_list[relative_index]['box']['y2'] = y2_interpolated_values[interpole_frame_index]
                
        if frame2['frame_id'] != frame_list[-1]['frame_id']:
            total_remaining_frames = frame_list[-1]['frame_id'] - frame2['frame_id'] + 1
            for frame_index in range(1, total_remaining_frames):
                relative_index = frame2['frame_id'] + frame_index
                frame_list[relative_index]['box'] = frame2['box']
        return frame_list

    @staticmethod
    def _resize(frame, target_width, target_height):
        try:
            current_height, current_width, _ = frame.shape
            frame = cv2.resize(frame, (current_width, target_height))
            current_height, current_width, _ = frame.shape

            scale_factor = target_height / current_height
            resized_frame = cv2.resize(frame, None, fx=scale_factor, fy=scale_factor)
            padding_width = target_width - resized_frame.shape[1]

            left_padding = padding_width // 2

            padded_frame = np.zeros((target_height, target_width, 3), dtype=np.uint8)
            padded_frame[:, left_padding:left_padding + resized_frame.shape[1], :] = resized_frame
        except:
            padded_frame = cv2.resize(frame, (target_width, target_height))

        return padded_frame
    
    @staticmethod
    def _get_largest_width(track_results):
        largest_width = 0
        for json_data in track_results:
            box = json_data["box"]
            if box:
                width = box["x2"] - box["x1"]
                largest_width = max(largest_width, width)
        return int(largest_width)
    
    @staticmethod
    def _get_largest_height(track_results):
        largest_height = 0
        for json_data in track_results:
            box = json_data["box"]
            if box:
                height = box["y2"] - box["y1"]
                largest_height = max(largest_height, height)
        return int(largest_height)
    
    
    def _crop_frames(self, interpolated_frames):
        largest_height = self.video_details['largest_height']
        largest_width = self.video_details['largest_width']
        
        for json_data in tqdm(interpolated_frames, desc="Cropping Frames"):
            frame_path = json_data["frame_path"]
            frame = cv2.imread(frame_path)
            
            box = json_data["box"]
            x1 = int(box.get("x1", 0))
            y1 = int(box.get("y1", 0))
            x2 = int(box.get("x2", 10))
            y2 = int(box.get("y2", 10))
            
            if self.size_aware:
                if self.only_object:
                    cropped_frame = frame[y1:y2, x1:x2]
                else:
                    original_width = x2 - x1
                    delta_x = (largest_width - original_width) // 2
                    frame_width = self.video_details['video_size'][0]
                    
                    if delta_x > 1:
                        new_x1 = x1 - delta_x
                        new_x2 = x2 + delta_x

                        new_x1 = max(0, new_x1)
                        new_x2 = min(new_x2, frame_width)
                        
                        cropped_frame = frame[y1:y2, int(new_x1):int(new_x2)]
                    else:
                        cropped_frame = frame[y1:y2, x1:x2]
                    cropped_frame = cv2.resize(cropped_frame, (largest_width, largest_height))
            else:
                object_width = x2 - x1
                width_margin = (largest_width - object_width) // 2
                
                new_x1 = max(0, x1 - width_margin)
                new_x2 = min(frame.shape[1], x2 + width_margin)
                
                frame_height1 = 0
                frame_height2 = self.video_details['video_size'][1]
                
                object_height = y2 - y1
                height_margin = (largest_height - object_height) // 2
                
                frame_height1 = max(0, y1 - height_margin)
                frame_height2 = min(frame.shape[0], y2 + height_margin)
                
                cropped_frame = frame[frame_height1:frame_height2, new_x1:new_x2]
                
            operated_frame_path = os.path.join(
                self.video_details['operated_frames_folder_path'], 
                os.path.basename(frame_path)
            )
            cv2.imwrite(operated_frame_path, cropped_frame)
            
    
    def _merge_frames(self):       
        fps = self.video_details['fps']
        largest_width = self.video_details['largest_width']
        largest_height = self.video_details['largest_height']
        
        operated_frame_folder = self.video_details['operated_frames_folder_path']
        frame_files = sorted([
            os.path.join(operated_frame_folder, filename) \
                for filename in os.listdir(operated_frame_folder)
        ])

        if not frame_files:
            print("No annotated frames found.")
        else:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(self.output_file_path, fourcc, fps, (largest_width, largest_height))

            for frame_file in tqdm(frame_files, desc="Writing Video"):
                frame = cv2.imread(frame_file)
                frame = cv2.resize(frame, (largest_width, largest_height)) \
                    if not self.size_aware else self._resize(frame, largest_width, largest_height)
                out.write(frame)
            out.release()
            
            print(f"Video saved as {self.output_file_path} at {fps} FPS.")
            
    
    def crop(self, input_path: str, output_folder_path: str):
        
        self.video_details = self._pre_process_video(input_path, output_folder_path)
        frames_path = self.video_details['frames_folder_path']
        all_frames_path = glob.glob(os.path.join(frames_path, "*.jpg"))
        track_results = []
        
        total_frames = len(all_frames_path)
        progress_bar = tqdm(total=total_frames, desc="Extracting Objects")
        
        tracker_response = None
        for i, frame_path in enumerate(all_frames_path):
            if i % self.frame_interval == 0:
                image = cv2.imread(frame_path)
                tracker_response = self.tracker.track(image)
                tracker_response = tracker_response['result']
                person_bounding_box = [result for result in tracker_response if result['name'] == "person"]
                person_bounding_box = max(
                    person_bounding_box, 
                    key=lambda x: x['confidence']
                )['box'] if person_bounding_box else {}
            else:
                person_bounding_box = {}
            response = {
                "box": person_bounding_box, 
                "frame_path": frame_path,
                "frame_id": i
            }
            track_results.append(response)
            progress_bar.update(1)
        progress_bar.close()
        
        interpolated_frames = self._interpolate_frames(track_results)
        
        frame_height = self.video_details['video_size'][1]
        largest_height = frame_height if not self.size_aware else self._get_largest_height(interpolated_frames)
        largest_width = self._get_largest_width(interpolated_frames)
        self.video_details = {
            **self.video_details,
            "largest_height": largest_height,
            "largest_width": largest_width
        }
        
        self._crop_frames(interpolated_frames)
        self._merge_frames()
        
        video_path = self.output_file_path
        audio_path = self.video_details['audio_file_path']
        output_path = self.output_file_path.replace("output.mp4", "output_audio.mp4")
        merge_audio(video_path, audio_path, output_path)
        
        return output_path