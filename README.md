# DynamicCropper

DynamicCropper is a Python library that allows you to dynamically crop a person in a video based on various parameters.

## TODOs

This section outlines the tasks and improvements planned for the DynamicCropper project.

- [ ] Improve performance for large video files.
- [ ] Add threading to operations.
- [ ] Create verbose control.
- [ ] Better outputs and error prints.
- [ ] Logger.
- [ ] Better file structure.
- [ ] Add better `requirements.txt`

## How to Use

### Step 1: Clone the Repository

Clone the repository to your local machine using the following command:

```bash
git clone https://github.com/AteltaAI/DynamicCropper.git
```

### Step 2: Create a Test File

Inside the repository folder, create a new Python test file (e.g., `test_cropper.py`). You can use the following example code in your test file:

```python
from dynamic_cropper import DynamicCropper

cropper = DynamicCropper(
    frame_interval=10,
    size_aware=True,
    only_object=True
)

# 'input_path' can be a youtube link or local video file path.
result = cropper.crop(
    input_path="https://youtu.be/GcZJMiHds3U",
    output_folder_path="output_folder"
)
```

### Step 3: Run the Test File

Run the test file to see how DynamicCropper works.

```bash
python test_cropper.py
```

## Showcase of Results

### Original Clip

https://github.com/AteltaAI/DynamicCropper/assets/78687109/5c9db786-c912-49e1-af6b-73da2c1c71b3

### Test Video 1:

#### Code:

```python
from dynamic_cropper import DynamicCropper

cropper = DynamicCropper(
    frame_interval=10,
    size_aware=False,
    only_object=False
)

result = cropper.crop(
    input_path=rf"input-video (2).mp4",
    output_folder_path="output_folder"
)

print(result)
```

#### Output:

https://github.com/AteltaAI/DynamicCropper/assets/78687109/f4964f55-319b-41fc-ab9c-014930f01df0

### Test Video 2:

#### Code:

```python
from dynamic_cropper import DynamicCropper

cropper = DynamicCropper(
    frame_interval=10,
    size_aware=True,
    only_object=True
)

result = cropper.crop(
    input_path=rf"input-video (2).mp4",
    output_folder_path="output_folder"
)

print(result)
```

#### Output:

https://github.com/AteltaAI/DynamicCropper/assets/78687109/4f7625d1-2dc9-490e-962f-a02917eb88c8

### Test Video 3:

#### Code:

```python
from dynamic_cropper import DynamicCropper

cropper = DynamicCropper(
    frame_interval=10,
    size_aware=True,
    only_object=False
)

result = cropper.crop(
    input_path=rf"input-video (2).mp4",
    output_folder_path="output_folder"
)

print(result)
```

#### Output:

https://github.com/AteltaAI/DynamicCropper/assets/78687109/b03c155b-d2cd-4ed9-9175-f202c16e7a55
