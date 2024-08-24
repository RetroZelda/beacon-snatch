from .authentication import BeaconAuthentication
from .stream import BeaconStreamInfo
from . import helpers

import subprocess
import requests
import logging
import json
import m3u8
import os

from selenium import webdriver
from selenium.webdriver.common.by import By

content_url = "https://beacon.tv/content"

class BeaconContent:
    def __init__(self, auth : BeaconAuthentication):
        self.auth = auth
        self.id = None                  
        self.title = None               
        self.description = None         
        self.duration = None            
        self.slug = None                
        self.publishedDate = None       
        self.primaryCollection = None   
        self.closedCaptions = None
        self.m3u8_url = None
        self.m3u8_obj = None
        self.available_streams = []

    @property
    def video_only_streams(self):
        return [stream for stream in self.available_streams if not stream.audio_codec and stream.video_codec]
    
    @property
    def audio_only_streams(self):
        return [stream for stream in self.available_streams if stream.audio_codec and not stream.video_codec]
    
    @property
    def video_and_audio_streams(self):
        return [stream for stream in self.available_streams if stream.audio_codec and stream.video_codec]

    @classmethod
    def create(cls, auth : BeaconAuthentication, content_id : str):

        # Initialize the browser
        driver = auth.get_driver()        
        new_content = None
    
        # grab the chunk of json that holds the key to where we can get our m3u8 url
        driver.get(f"{content_url}/{content_id}")
        script_block = driver.find_element(By.ID, '__NEXT_DATA__') 
        json_data = script_block.get_attribute('innerHTML')
        json_blob = json.loads(json_data)

        # Traverse the JSON to find the "Content_ContentVideo" block
        # this block is under a block with a key of "Content:[content_id]" 
        # so we need to find an element under "__APOLLO_STATE__" with "__typename" of "Content" first
        apollo_state = json_blob.get("props", {}).get("pageProps", {}).get("__APOLLO_STATE__", {})
        content_block = None
        for key, value in apollo_state.items():
            if isinstance(value, dict) and value.get("__typename") == "Content":
                if value["slug"] != content_id:
                    continue
                content_block = value
                break

        if not content_block:
            logging.warn(f"cant find content for content_id \"{content_id}\"")
            return None

        if "video" not in content_block["contentType"]:
            logging.warn(f"Skipping non-video content \"{ content_block["contentType"] }\" for Content \"{content_id}\"")
            return None

        content_video_block = content_block["contentVideo"]
        if content_video_block and "video" in content_video_block:

            new_content = BeaconContent(auth)

            # Extract all the info for this video from the block
            new_content.id                  = content_block["id"]
            new_content.title               = content_block["title"]
            new_content.description         = content_block["description"]
            new_content.duration            = content_block["duration"]
            new_content.slug                = content_block["slug"]
            new_content.publishedDate       = content_block["publishedAt"]
            new_content.primaryCollection   = content_block["primaryCollection"]["__ref"]
            new_content.m3u8_url            = content_video_block["video"]["video"]
            new_content.closedCaptions      = content_video_block["video"]["closedCaptions"]
            
            new_content.fetch()
        else:
            logging.error("Content_ContentVideo block or video data not found.")

        return new_content

    # Fetches the m3u8 playlist to get all available streams that we can download
    def fetch(self):

        try:
            # Fetch the m3u8 playlist content
            response = requests.get(self.m3u8_url)
            response.raise_for_status()

            self.m3u8_obj = m3u8.loads(response.text)
            logging.log(helpers.LOG_VERBOSE, f'M3U8 file fetched')

            # create BeaconStreamInfo for every found in this m3u8's playlist
            for stream_info in self.m3u8_obj.playlists:
                new_stream = BeaconStreamInfo.from_m3u8_playlist(stream_info)
                if new_stream is not None:
                    self.available_streams.append(new_stream)

            self.available_streams.sort(
                key=lambda stream: ((stream.width or 0) * (stream.height or 0), stream.bandwidth or 0),
                reverse=True)

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching the M3U8 file: {e}")

    # Downloads the given stream using ffmpeg and saves it to the destination folder.
    def download(self, stream: BeaconStreamInfo, destination_folder: str = "."):

        # Ensure the destination folder exists
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)

        # Sanitize the title to create a safe filename
        safe_title = helpers.sanitize(self.slug)
        file_extension = "mp4" if stream.video_codec else "m4a"
        output_filename = f"{safe_title}.{file_extension}"
        output_path = os.path.join(destination_folder, output_filename)

        # Build the ffmpeg command
        command = [
            "ffmpeg",
            "-i", stream.m3u8_uri,       # Input M3U8 URI from the stream
            "-c", "copy",                # Copy codecs without re-encoding
            "-bsf:a", "aac_adtstoasc",   # Bitstream filter for AAC audio
            "-y",
            output_path
        ]

        # Run the ffmpeg command and capture output
        logging.log(helpers.LOG_VERBOSE, f"Starting download for {self.title}...")        
        helpers.run_ffmpeg_with_progress(command=command, progress_header=f"Downloading \"{self.title}\"")
        logging.log(helpers.LOG_VERBOSE, f"Download saved at '{output_path}'")    

