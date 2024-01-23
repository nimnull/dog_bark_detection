import logging
import os
from datetime import datetime
from os.path import dirname, join

from data.config import message, receiver, sender
from pipelines.communication import create_body, send_files
from pipelines.store import get_batches

LOG = logging.getLogger(__name__)

if __name__ == "__main__":
    n_files = 5
    attempts = 20
    length = 30

    now = datetime.now()
    date = now.strftime("%d-%m-%Y")

    temp_audio_path = join(".", "data", "tmp", "tmp.wav")
    os.makedirs(dirname(temp_audio_path), exist_ok=True)

    output_path = join(".", "data", "jojo_{}".format(date))
    os.makedirs(output_path, exist_ok=True)
    output_path_bark = join(output_path, "bark_{}.wav")
    output_path_howl = join(output_path, "howl_{}.wav")

    while True:
        files = get_batches(
            temp_audio_path,
            output_path_bark,
            output_path_howl,
            length=length,
            n_files=n_files,
            subsampling=4,
            attempts=attempts,
        )
        if not files:
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S on %d-%m-%Y")
            print("No files with bark stored at", current_time)
            continue
        message.update({"body": create_body(files, message)})
        try:
            send_files(files, sender, receiver, message)
        except Exception:
            LOG.exception("Something went wrong while sending a message")
            continue
