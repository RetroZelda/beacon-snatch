from . import helpers 

import subprocess
import logging
import time
import re

import progressbar

LOG_VERBOSE = 15
LOG_VERBOSE_NAME = "VERBOSE"

COOKIE_NAME = "cookies.json"
DEFAULT_CACHE = "~/.beacon-snatch"
DEFAULT_OUTPUT = DEFAULT_CACHE + "/downloads"
DEFAULT_COOKIES = DEFAULT_CACHE + "/" + COOKIE_NAME

def sanitize(input_string):
    sanitized = input_string.strip()
    sanitized = re.sub(r'[^\w\s\-.,!?]', '', sanitized)
    sanitized = re.sub(r'\s+', ' ', sanitized)
    sanitized = sanitized.replace(' ', '_')
    sanitized = sanitized.lower()
    return sanitized

def format_duration(seconds):
    milliseconds = int((seconds % 1) * 1000)
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}.{milliseconds:03d} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes} minutes {seconds} seconds"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours} hours {minutes} minutes {seconds} seconds"

def parse_ffmpeg_duration(output):
    match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})', output)
    if match:
        hours, minutes, seconds = map(float, match.groups())
        return hours * 3600 + minutes * 60 + seconds
    return None

def parse_ffmpeg_time(output):
    match = re.search(r'time=(\d{2}):(\d{2}):(\d{2}\.\d{2})', output)
    if match:
        hours, minutes, seconds = map(float, match.groups())
        return hours * 3600 + minutes * 60 + seconds
    return None

def run_ffmpeg_with_progress(command, progress_header: str = "Processing"):
    logging.log(helpers.LOG_VERBOSE, f"Executing ffmpeg")
    logging.debug(f'{" ".join(command)}')

    try:
        process = subprocess.Popen(command, stderr=subprocess.PIPE, universal_newlines=True)
    except Exception as e:
        logging.error(f"Failed to start ffmpeg: {e}")
        return

    duration = None
    progress_bar = None
    start_time = time.time()

    for line in process.stderr:
        if duration is None:
            duration = parse_ffmpeg_duration(line)
            if duration:
                progress_bar = progressbar.ProgressBar(max_value=duration)
                progress_bar.start()

        if progress_bar and duration:
            current_time = parse_ffmpeg_time(line)
            if current_time:
                if current_time > duration:
                    current_time = duration
                progress_bar.update(current_time)

    process.wait()

    if progress_bar:
        progress_bar.finish()

    logging.log(helpers.LOG_VERBOSE, f"Completed in {format_duration(time.time() - start_time)}")
