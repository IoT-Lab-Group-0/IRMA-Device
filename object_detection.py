import os
import sys
import time
import cv2
import tflite_runtime
from tflite_runtime.interpreter import Interpreter
import threading
import numpy as np

import parsepy

# https://www.pyimagesearch.com/2018/05/21/an-opencv-barcode-and-qr-code-scanner-with-zbar/
SHOW_DETECTION_VIDEO = True

class CamDetect:
    def __init__(self, camera):
        self.camera = camera
        MODEL_DIR = 'models/coco_ssd_1'
        MODEL_NAME = 'detect.tflite'
        LABELMAP_NAME = 'labelmap.txt'
        PATH_TO_MODEL = os.path.join(MODEL_DIR, MODEL_NAME)
        PATH_TO_LABELS = os.path.join(MODEL_DIR, LABELMAP_NAME)

        self.min_conf_threshold = .40

        # Load Labels
        with open(PATH_TO_LABELS, 'r') as f:
            self.labels = [line.strip() for line in f.readlines()]
        # Have to do a weird fix for label map if using the COCO "starter model" from
        # https://www.tensorflow.org/lite/models/object_detection/overview
        # First label is '???', which has to be removed.
        if self.labels[0] == '???':
            del (self.labels[0])

        # Load Model
        self.interpreter = Interpreter(model_path=PATH_TO_MODEL)
        self.interpreter.allocate_tensors()
        # Get model details
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        self.height = self.input_details[0]['shape'][1]
        self.width = self.input_details[0]['shape'][2]
        print('MODEL IMAGE SHAPE: ', self.input_details[0]['shape'])

        self.floating_model = (self.input_details[0]['dtype'] == np.float32)

        self.obj_flag = False  # True for found new objects
        self.new_item = None

        self.ON = True  # A False value ends the barcode loop and the thread
        self.running = True
        self.detection_thread = threading.Thread(target=self.detection_loop, name="detection_loop")
        self.detection_thread.start()
        print("Object Detection initialized")

    def __call__(self):
        if self.obj_flag:
            self.obj_flag = False
            return True
        return False

    # Get the latest item based on upc scan search
    def get_item(self):
        return self.new_item

    def close(self):  # Clean up
        self.ON = False
        cv2.destroyAllWindows()

    def detection_loop(self):
        print("detection loop started")
        while self.ON:
            # Read frame from camera connection
            frame = self.camera.read_frame()

            in_height, in_width, in_channels = frame.shape
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(frame_rgb, (self.width, self.height))
            input_data = np.expand_dims(frame_resized, axis=0)
            # Normalize pixel values if using a floating model (i.e. if model is non-quantized)
            if self.floating_model:
                input_data = (np.float32(input_data) - 127.5) / 127.5
                print('Floating model')
            # Perform the actual detection by running the model with the image as input
            self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
            self.interpreter.invoke()
            # Retrieve detection results
            boxes = self.interpreter.get_tensor(self.output_details[0]['index'])[0]  # Bounding box coordinates of detected objects
            classes = self.interpreter.get_tensor(self.output_details[1]['index'])[0]  # Class index of detected objects
            scores = self.interpreter.get_tensor(self.output_details[2]['index'])[0]  # Confidence of detected objects

            # Loop over all detections and draw detection box if confidence is above minimum threshold
            ilist = [51, 52, 53, 54, 55, 56, 57, 58, 59, 60]
            object_name = ' '
            top_score = 0
            top_name = ' '
            last_name = ' '
            for i in range(len(scores)):
                if ((int(classes[i]) in ilist) and (scores[i] > self.min_conf_threshold) and (scores[i] <= 1.0)):
                    # Get bounding box coordinates and draw box
                    # Interpreter can return coordinates that are outside of image dimensions, need to force them to be within image using max() and min()
                    ymin = int(max(0, boxes[i][0]) * in_height)
                    xmin = int(max(0, boxes[i][1]) * in_width)
                    ymax = int(min(1, boxes[i][2]) * in_height)
                    xmax = int(min(1, boxes[i][3]) * in_width)
                    cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (10, 255, 0), 1)

                    # Draw label into **input frame**
                    object_name = self.labels[int(classes[i])]  # Look up object name from "labels" array using class index
                    item_txt = '%s: %d%%' % (object_name, int(scores[i] * 100))  # Example: 'person: 72%'
                    labelSize, baseLine = cv2.getTextSize(item_txt, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)  # Get font size
                    label_ymin = max(ymin, labelSize[1] + 10)  # Make sure not to draw label too close to top of window
                    cv2.rectangle(frame,
                                  (xmin, label_ymin - labelSize[1] - 10),
                                  (xmin + labelSize[0], label_ymin + baseLine - 10),
                                  (255, 255, 255),
                                  cv2.FILLED)  # Draw white box to put label text in
                    cv2.putText(frame, item_txt,
                                (xmin, label_ymin - 7),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.5, (0, 0, 0), 2)  # Draw label text

                    # Draw circle in center
                    xcenter = xmin + (int(round((xmax - xmin) / 2)))
                    ycenter = ymin + (int(round((ymax - ymin) / 2)))
                    cv2.circle(frame, (xcenter, ycenter), 5, (0, 0, 255), thickness=-1)
                    if scores[i] > top_score:
                        top_score = scores[i]
                        top_name = self.labels[int(classes[i])]
                    # Print info
                    print('Object ', str(classes[i]), ': ', object_name, 'score:', scores[i])

            # SELECT WHICH ITEM GETS SAVED
            if top_name != last_name:
                last_name = top_name
                object_item = parsepy.item()
                object_item.name = top_name
                object_item.upc = ' '
                object_item.imageURL = ' '
                print("writing new object", object_item.name)
                self.new_item = object_item
                self.obj_flag = True

            # All the results have been drawn on the frame, so it's time to display it.
            if SHOW_DETECTION_VIDEO and in_height > 0:
                out_scale_fct = 1
                frame = cv2.resize(frame, (int(in_width * out_scale_fct), int(in_height * out_scale_fct)))
                frame = cv2.normalize(frame, frame, 0, 255, cv2.NORM_MINMAX)
                cv2.imshow('Objects', frame)
                cv2.moveWindow('Objects', 10, 10)
                cv2.waitKey(200)



