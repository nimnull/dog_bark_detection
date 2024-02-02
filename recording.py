import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import sounddevice as sd

from pipelines.detect import detect_bark_howl
from pipelines.io import save_audio

DURATION = 7
SAMPLING = 44100
CHUNK = 1024
CHANNELS = 2
subsampling = 1
nsteps = int((SAMPLING / CHUNK) * DURATION)


def get_output_path() -> str:
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    output_path = Path(".") / "data" / date
    output_path.mkdir(exist_ok=True)
    filename = now.strftime("%Y-%m-%d-%H:%M:%s")
    return str(output_path / f"bark_{filename}.wav")


def init_sounddevice():
    sd.default.samplerate = SAMPLING
    sd.default.channels = CHANNELS
    sd.default.device = 1


async def inputstream_generator(channels=1, **kwargs):
    """Generator that yields blocks of input data as NumPy arrays."""
    q_in = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def callback(indata, frame_count, time_info, status):
        # print(frame_count)
        loop.call_soon_threadsafe(q_in.put_nowait, (indata.copy(), status))

    stream = None
    for _ in range(10):

        try:
            stream = sd.InputStream(callback=callback, channels=channels, **kwargs)
        except sd.PortAudioError:
            logging.error("Cant open capture device")

        if stream is not None:
            break

    with stream:
        while True:
            indata, status = await q_in.get()
            yield indata, status


async def print_input_infos(**kwargs):
    """Show minimum and maximum value of each incoming audio block."""
    target = None
    async for indata, status in inputstream_generator(**kwargs):
        if status:
            print(status)

        if target is None:
            target = indata.copy()
        elif len(target) < SAMPLING * 7:
            target = np.append(target, [indata.copy()])
        else:
            bark, clipped_audio = detect_bark_howl(target.copy(), SAMPLING, clip=3)
            if bark:
                output = get_output_path()
                print(f"Bark: {output}")
                save_audio(output, clipped_audio, int(SAMPLING / subsampling))
            target = None

async def main(**kwargs):
    print('Some informations about the input signal:')
    try:
        await print_input_infos()
    except asyncio.TimeoutError:
        pass


if __name__ == "__main__":
    init_sounddevice()
    try:
        asyncio.run(main(blocksize=1024))
    except KeyboardInterrupt:
        sys.exit('\nInterrupted by user')
