import os
import serial
import threading
import time

import parsepy
import upc_api

EXPECTED_UPC_LENGTH = 13

#############################
# BARCODE CLASS DEFINITION (CAMERA)
# ** Requires arguments Barcode(video_stream, speaker)
#    video stream = camera video_stream object
#        in PiVideoStream format (picamera) or cv2.VideoCapture format (USB)
#    speaker = text to voice object (uses beep() function)
# new code for PiCamera barcode scanner
#  Runs in threat in background that detects, looks ups and reports barcodes
#  Checks that they are 13 characters.
#  Reports product name

from pyzbar import pyzbar
import cv2
import subprocess
import text_to_voice


class Barcode:
    def __init__(self, camera, speaker):
        self.camera = camera
        self.spk = speaker
        self.connected = True  # True when serial port is active
        self.ON = True  # A False value ends the barcode loop and the thread
        self.running = True
        self.scanner = None

        self.upc_flag = False  # True for found barcode *and* successful description lookup
        self.new_item = None
        self.spk = text_to_voice.Speaker()

        self.barcode_thread = threading.Thread(target=self.barcode_run, name="barcode_run")
        self.barcode_thread.start()
        print("Barcode scanner initialized")

    def __call__(self):
        if self.upc_flag:
            self.upc_flag = False
            return True
        return False

    # Get the latest item based on upc scan search
    def get_item(self):
        return self.new_item

    # closes and cleans up the thread
    def close(self):
        print("close barcode")
        self.ON = False
        time.sleep(0.5)
        self.barcode_thread.join()

    # returns True if barcode serial connection is active
    def is_connected(self):
        if self.connected:
            return True
        return False

    def barcode_run(self):
        last_upc = ' '
        while self.ON:
            # Read frame from camera connection
            frame = self.camera.read_frame()
            # find the barcodes in the frame and decode each of the barcodes
            barcodes = pyzbar.decode(frame)

            # barcodes are found, loop over the detected barcodes
            for barcode in barcodes:
                # the barcode data is a bytes object so if we want to draw it
                # on our output image we need to convert it to a string first
                upc_code = barcode.data.decode("utf-8")
                if len(upc_code) == EXPECTED_UPC_LENGTH and upc_code != last_upc:
                    print('found barcode', upc_code)
                    self.new_item = upc_api.search(upc_code)
                    self.new_item.upc = upc_code
                    self.upc_flag = True  # indicates to other thread that a new u
                    last_upc = upc_code
                    self.spk.beep()  # feedback to user that upc found
        print('Leaving Barcode loop')
        return


################################
# BARCODE CLASS DEFINITION (BLUETOOCH SCANNING DEVICE)
#  Runs background thread that listens to the serial (usb or bluetooth) port,
#  grabs UPCs, looks up descriptions and publish this info for other threads
# TODO: try connecting with pybluez using MAC address.
class Barcode_bt:
    def __init__(self):
        # if /dev.rfcomm0 (bluetooth serial port) is missing, running
        # sudo rfcomm bind /dev/rfcomm0 {bluetooth address}} 1
        # print('sudo rfcomm bind /dev/rfcomm0 AA:A8:A0:01:1B:44 1')

        self.device = '/dev/rfcomm0'
        self.connected = False  # True when serial port is active
        self.ON = True  # A False value ends the barcode loop and the thread
        self.scanner = None

        self.upc_flag = False  # True for found barcode *and* successful description lookup
        self.new_item = None

        self.barcode_thread = threading.Thread(target=self.barcode_run, name="barcode_run")
        self.barcode_thread.start()
        print("Barcode scanner initialized")

    # returns true if new upc & description is available
    def __call__(self):
        if self.upc_flag:
            self.upc_flag = False
            return True
        return False

    # closes and cleans up the thread
    def close(self):
        self.ON = False
        time.sleep(0.5)
        self.barcode_thread.join()

    # Get the latest item based on upc scan search
    def get_item(self):
        return self.new_item

    # returns True if barcode serial connection is active
    def is_connected(self):
        if self.connected:
            return True
        return False

    # background thread that listens to the serial port,
    #  acquires upcs and looks up description
    def barcode_run(self):
        print('barcode_run thread started')
        while self.ON:
            if not self.connected:
                print('barcode_scanner not connected')
                if not os.path.exists(self.device):
                    print('barcode device not found', self.device)
                    self.connected = False
                    time.sleep(5)
                    continue
                try:
                    self.scanner = serial.Serial(self.device, baudrate=9600,
                                                 timeout=0.25)  # increase timeout to 3.5. seconds from .5
                except IOError as err:
                    print('Error opening barcode device: ', err)
                    self.connected = False
                    time.sleep(5)
                    continue
            self.connected = True
            time.sleep(1)
            try:
                upc_raw = self.scanner.readline()
            except IOError:
                continue
            if upc_raw:
                if len(upc_raw) != EXPECTED_UPC_LENGTH:
                    print('Incomplete barcode - try again')
                    continue
                upc_code = upc_raw.strip().decode("utf-8")
                self.new_item = upc_api.search(upc_code)
                self.upc_flag = True  # indicates to other thread that a new upc is ready
        print('Leaving Barcode loop')
        return
