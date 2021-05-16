import os

os.environ["PARSE_API_ROOT"] = "https://parseapi.back4app.com"

from parse_rest.connection import register

import headless
import voice_command
import barcode_scanner
import text_to_voice
import ui
import object_detection

# jh SET UP CAMERA SHARED BY BARCODE, OBJECT DETECTION, PICTURES, ...
#
from imutils.video import VideoStream
from imutils.video import PiVideoStream  # note had to add item to __python__ in imutils.video directory
import time
# from object_detection import CamDetect

# PiCamera setup
class Camera:
    def __init__(self, picamera=True):
        self.picamera = picamera
        if picamera:
            self.video_stream = PiVideoStream(resolution=(640, 480)).start()
            # self.video_stream.camera.rotation = 180
            self.video_stream.camera.exposure_mode = 'auto'  # 'night'  'auto'  'night' 'backlight
            # self.vs.camera.iso = 140   # 100-800
        else:   # USB CAMERA
            self.video_stream = cv2.VideoCapture(0)
        time.sleep(2)  # camera warm up

    def read_frame(self):
        if self.picamera:
            frame = self.video_stream.read()
        else:
            grab, frame = self.video_stream.read()
        return frame

    def close(self):
        if self.picamera:
            self.video_stream.stop()
        else:
            self.video_stream.release()
    #
# jh #####################

# TODO: programmatically detect display connection.
DISPLAY_CONNECTED = True

register(APP_ID, API_KEY, master_key=None)

def main():
    # Initialize sensors
    # Camera setup
    camera = Camera()

    # Text to Voice
    speaker = text_to_voice.Speaker()

    # Voice Recognition
    wake = voice_command.WakeWord(speaker)

    # Barcode Scanner
    barcode = barcode_scanner.Barcode(camera, speaker)

    # Object Detection
    detected_object = object_detection.CamDetect(camera)

    # Initialize Cloud DB - ParsePy - deprecated in favor of ParsePy API Object integration.
    # db = cloud_db.CloudDB()

    # Enter either ui or headless mode.
    if DISPLAY_CONNECTED:
        ui.start(barcode, wake, speaker, detected_object)
    else:
        headless.start(barcode, wake, speaker, None)

    print("Closing sensors...")
    barcode.close()
    wake.close()
    detected_object.close()
    camera.close()


if __name__ == '__main__':
    main()
