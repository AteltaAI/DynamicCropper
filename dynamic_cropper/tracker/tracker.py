from ultralytics import YOLO
import os

class YOLOTracker:
    def __init__(self, model_path, model_name, tracker_algorithm) -> None:
        
        self.tracker_algorithm = tracker_algorithm
        weights_location = self._check_model_path(model_path, model_name)
        self.model = YOLO(weights_location)
    
    @staticmethod
    def _check_model_path(model_path, model_name):
        default_model_name = "yolov8n.pt"

        if model_path and model_name:
            raise ValueError("Please provide either 'model_path' or 'model_name', not both.")

        if not model_path and not model_name:
            model_name = default_model_name
            print(f"=> WARNING: No model path or model URL was provided, defaulting 'model_name' to '{default_model_name}'")
            return model_name

        if model_path:
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file at '{model_path}' does not exist.")
            return model_path
        return False
    
    def track(self, image):
        results = self.model.track(
            image, 
            persist=True, 
            verbose=False, 
            tracker=self.tracker_algorithm
        )
        
        return {"result": eval(results[0].tojson())}