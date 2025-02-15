import logging
import os
import sys
import wave

import pyaudio


LOG = logging.getLogger(__name__)


def record_segment(path, length=30, sampling=44100, chunk=1024):
    """
    path (str): Path where the file will be stored.
    length (float): Length of the recorded segment in seconds.
    sampling (int): Sampling rate of the stream.
    depth (int): The limit values of the dynamic range (for 32bit the maximum value is 2.147.483.648 and minimum -2.147.483.648).
    channels (int): Number of channels being recorded.
    chunk (int): The chunk size that is read from a buffer.
    """
    channels = 1 if sys.platform == 'darwin' else 2
    nsteps = int((sampling / chunk) * length)
    audio_format = pyaudio.paInt32

    audio = pyaudio.PyAudio()
    try:
        stream = audio.open(
            format=audio_format,
            channels=channels,
            rate=sampling,
            input=True,
            frames_per_buffer=chunk,
        )
        frames = [stream.read(chunk, exception_on_overflow=False) for i in range(0, nsteps)]

        stream.stop_stream()
        stream.close()
        audio.terminate()

        return save_segment(
            path,
            frames,
            sampling,
            channels,
            audio.get_sample_size(audio_format),
        )
    except OSError:
        LOG.exception("Can't open capture device")


def save_segment(
    path, frames, sampling=44100, channels=1, sampling_width=4
):
    """
    Parameters:
    path (str): Path where the file will be stored.
    frames (list of binary strings): A list containing the data we want to save in the file.
    length (float): Length of the recorded segment in seconds.
    sampling (int): Sampling rate of the stream.
    depth (int): The limit values of the dynamic range (for 32bit the maximum value is 2.147.483.648 and minimum -2.147.483.648).
    channels (int): Number of channels being recorded.
    sampling_width (int): The sampling width with which we want to record the file.
    """
    output = wave.open(path, "wb")
    output.setnchannels(channels)
    output.setsampwidth(sampling_width)
    output.setframerate(sampling)
    output.writeframes(b"".join(frames))
    output.close()
    return os.path.isfile(path)
