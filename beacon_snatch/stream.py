import logging 
import m3u8

class BeaconStreamInfo:
    def __init__(self,  width : int = None, 
                        height : int = None, 
                        bandwidth : int = None,
                        video_codec : str = None,
                        audio_codec : str = None,
                        m3u8_uri=None):
        self.width = width
        self.height = height
        self.bandwidth = bandwidth
        self.video_codec = video_codec
        self.audio_codec = audio_codec
        self.m3u8_uri = m3u8_uri
        self.source_playlist = None

    # Returns the resolution as a tuple (width, height).
    @property
    def resolution(self):
        if self.width is not None and self.height is not None:
            return (self.width, self.height)
        return None
        
    # Creates an instance of MediaFile from an m3u8.model.Playlist object.
    @classmethod
    def from_m3u8_playlist(cls, playlist : m3u8.model.Playlist):

        stream_info = getattr(playlist, 'stream_info', None)
        if stream_info is None:
            logging.error(f"Unable to get stream_info '{codec}'")
            return None
        
        # Extract resolution if available
        width, height = None, None
        if stream_info.resolution:
            width, height = stream_info.resolution

        bandwidth = stream_info.bandwidth

        # Extract codecs if available
        codecs = stream_info.codecs if playlist.stream_info else None
        video_codec, audio_codec = None, None
        if codecs is not None:
            codec_list = codecs.split(",")
            for codec in codec_list:
                # Determine if the codec is for video or audio
                if codec.startswith("avc1") or codec.startswith("avc3") or codec.startswith("hev1") or codec.startswith("hvc1"):
                    if video_codec:
                        logging.warn(f"Attempting to set video codec '{codec}' but video codec '{video_codec}' is already set.")
                    else:
                        video_codec = codec
                elif codec.startswith("mp4a") or codec.startswith("ac-3") or codec.startswith("ec-3"):
                    if audio_codec:
                        logging.warn(f"Attempting to set audio codec '{codec}' but audio codec '{audio_codec}' is already set.")
                    else:
                        audio_codec = codec
                else:
                    logging.error(f"Unable to match codec '{codec}'")

        # Extract URI
        uri = getattr(playlist, 'absolute_uri', None)

        stream_info = cls(width=width, 
                          height=height, 
                          bandwidth=bandwidth, 
                          video_codec=video_codec, 
                          audio_codec=audio_codec, 
                          m3u8_uri=uri)
        stream_info.source_playlist = playlist
        return stream_info
