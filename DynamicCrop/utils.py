import os
import subprocess

def extract_audio(video_file_path, output_audio_path):
    """
    Extract audio from a video file using ffmpeg.

    Args:
        video_file_path (str): Local path to the video file.
        output_audio_path (str): Local path to the output audio file.
    """
    print("=> Audio extraction started")

    # Get absolute file paths
    video_file_path = os.path.abspath(video_file_path)
    output_audio_path = os.path.abspath(output_audio_path)
    
    # Define the ffmpeg command
    command = [
        "ffmpeg",
        "-i", r"{}".format(video_file_path),
        "-q:a", "0",
        "-map", "a", r"{}".format(output_audio_path)
    ]
    
    # Execute the ffmpeg command
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        shell=True
    )
    _, stderr = process.communicate()

    if process.returncode != 0:
        print("=> Error during audio extraction:")
        print(stderr.decode("utf-8"))
        raise Exception("Audio extraction failed.")

    print("=> Audio extraction successful\n")
    
def merge_audio(video_path, audio_path, output_path):
    """
    Merge audio from a local audio file into a local video file and save the result to an output file.

    Args:
        video_path (str): Local path to the video.
        audio_path (str): Local path to the audio.
        output_path (str): Local path for the output file.
    """
    
    print("\n=> Audio merging started")
    
    # Define the ffmpeg command for audio merging
    command = [
        'ffmpeg',
        '-i', r"{}".format(video_path),
        '-i', r"{}".format(audio_path),
        '-c:v', 'copy', '-c:a', 'aac',
        '-strict', 'experimental',
        '-map', '0:v:0', '-map', '1:a:0', '-shortest',
        r"{}".format(output_path)
    ]

    # Execute the ffmpeg command
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        shell=True
    )
    _, stderr = process.communicate()

    if process.returncode != 0:
        print("=> Error during audio merging:")
        print(stderr.decode("utf-8"))
        raise Exception("Audio merging failed.")
    
    print("=> Audio merging successful")