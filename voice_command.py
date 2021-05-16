import sounddevice as sd
import speech_recognition as sr
import timeit
import scipy.signal
import threading
import numpy as np

import python_speech_features

import tflite_runtime
from tflite_runtime.interpreter import Interpreter

import parsepy

import struct
import pyaudio
import pvrhino
import time


class WakeWord:
    def __init__(self, speaker):
        self.speaker = speaker  # used to create the beep() sound

        self.handle = pvrhino.create(context_path='./models/Irma_Rules_2.rhn', sensitivity=0.25)
        print("sample_rate", self.handle.sample_rate, "frame_len:", self.handle.frame_length)
        self.pa = pyaudio.PyAudio()
        self.audio_stream = self.pa.open(
            rate=self.handle.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.handle.frame_length)
        self.recognizer = sr.Recognizer()  # obtain audio from the microphone
        print('NONSPEAKING', self.recognizer.non_speaking_duration)
        print('PAUSE THRESHOLD', self.recognizer.pause_threshold)
        self.recognizer.pause_threshold = 0.5  # default 0.8
        self.recognizer.operation_timeout = 2
        self.recognizer.energy_threshold = 3000

        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source)

        # Thread and flags
        self.ON = True
        self.running = True
        self.wakeword_flag = False
        self.voice_item = parsepy.item()
        self.voice_item.upc = ' '
        self.voice_item.imageURL = ' '
        self.voice_item.name = ' '
        self.command = 'None'
        self.wakeword_thread = threading.Thread(target=self.wakeword_run, name="wakeword_thread")
        self.wakeword_thread.start()
        print('WakeWord Initialized')

    def close(self):
        self.running = False
        self.wakeword_thread.join()
        if self.handle is not None:
            self.handle.delete()
        if self.audio_stream is not None:
            self.audio_stream.close()
        if self.pa is not None:
            self.pa.terminate()
        print('wake closed')
        return

    def __call__(self):
        if self.wakeword_flag:
            self.wakeword_flag = False
            return True
        return False

    # Function listens for voice and sends back text
    def get_item(self):
        print('getting command')
        return self.command, self.voice_item


    # Background loop that continuously checks for wake words
    def wakeword_run(self):
        print('go wake')
        ww_listen = 0
        while self.running:
            if ww_listen < 1:
                print("WAITING FOR WAKE WORD")
                ww_listen = 10
            pcm = self.audio_stream.read(self.handle.frame_length)
            pcm = struct.unpack_from("h" * self.handle.frame_length, pcm)
            is_finalized = self.handle.process(pcm)
            if is_finalized:
                inference = self.handle.get_inference()
                if inference.is_understood:
                    print('voice:------FOUND WAKE WORD')
                    intent = inference.intent
                    slots = inference.slots
                    print('voice:intent', intent, slots)

                    try:
                        print('voice:--------READY FOR TEXT')
                        self.speaker.beep()
                        with sr.Microphone() as source:
                            # self.recognizer.adjust_for_ambient_noise(source)
                            self.recognizer.energy_threshold = 1000
                            self.recognizer.pause_threshold = 0.5  # default 0.8
                            audio = self.recognizer.listen(source)
                    except sr.WaitTimeoutError:
                        print('voice: listening timeout')
                        ww_listen = 0
                        continue
                    # recognize speech using Google Speech Recognition
                    # for testing purposes, we're just using the default API key
                    self.speaker.beep(2)
                    try:
                        print('voice: -------converting ')
                        name = self.recognizer.recognize_google(audio)
                    except sr.UnknownValueError:
                        print("voice:Google Speech Recognition could not understand audio.")
                        ww_listen = 0
                        continue
                    except sr.RequestError as err:
                        print("voice:Could not request results from Google Speech Recognition service: {0}".format(err))
                        ww_listen = 0
                        continue
                    self.command = intent
                    self.voice_item.upc = ' '
                    self.voice_item.imageURL = ' '
                    self.voice_item.name = name
                    self.wakeword_flag = True
                    ww_listen = 0

                #else:
                #    print('unsupported command')
                #    pass








####################################################
# Wake() #2 class when initialized starts a thread that listens for the wake word
#  if wake word detects, sets self.trigger to true
#  main program calls Wake.active() to check for wake

WORD_THRESHOLD = 0.5
RECORD_DURATION = 0.5
WINDOW_STRIDE = 0.5
SAMPLE_RATE = 48000
RESAMPLE_RATE = 8000
DOWNSAMPLE = int(SAMPLE_RATE / RESAMPLE_RATE)
NUM_CHANNELS = 1
NUM_MFCC = 16

WAKEWORD_MODEL_PATH = './models/wake_word_go_lite.tflite'

DEBUG_TIME = False
DEBUG_ACC = False


class WakeWord2:
    def __init__(self):
        # Sliding window
        self.window = np.zeros(int(RECORD_DURATION * RESAMPLE_RATE) * 2)

        # Load model
        self.interpreter = Interpreter(WAKEWORD_MODEL_PATH)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        # Thread and flags
        self.ON = True
        self.running = True
        self.wakeword_flag = False
        self.wakeword_thread = threading.Thread(target=self.wakeword_run, name="wakeword_thread")
        self.wakeword_thread.start()
        print('WakeWord Initialized')

    def close(self):
        self.running = False
        self.wakeword_thread.join()
        return

    # Background loop that continuously checks for wake words
    def wakeword_run(self):
        with sd.InputStream(channels=NUM_CHANNELS,
                            samplerate=SAMPLE_RATE,
                            blocksize=int(SAMPLE_RATE * RECORD_DURATION),
                            callback=self.wakeword_process):
            while self.running:
                pass

    def __call__(self):
        if self.wakeword_flag:
            self.wakeword_flag = False
            return True
        return False

    def wakeword_process(self, rec, frames, time, error):
        # Start timing for testing
        start_time = timeit.default_timer()
        # Notify if errors
        if error:
            print("Error: ", error)

        # Remove 2nd dimension from recording sample and downsample
        rec = np.squeeze(rec)
        rec = scipy.signal.decimate(rec, DOWNSAMPLE)

        # Analyze a sliding window if the sound that overlaps with last window by 50%
        # to catch wake words that might span time segments
        self.window[:len(self.window) // 2] = self.window[len(self.window) // 2:]
        self.window[len(self.window) // 2:] = rec

        # Process image with MFCC (Mel Frequency Cepstrum) that scales the frequency in order
        # to match more closely what the human ear can hear
        mfccs = python_speech_features.base.mfcc(self.window,
                                                 samplerate=RESAMPLE_RATE,
                                                 winlen=0.256,
                                                 winstep=0.050,
                                                 numcep=NUM_MFCC,
                                                 nfilt=26,
                                                 nfft=2048,
                                                 preemph=0.0,
                                                 ceplifter=0,
                                                 appendEnergy=False,
                                                 winfunc=np.hanning)
        mfccs = mfccs.transpose()

        # Make prediction from model
        in_tensor = np.float32(mfccs.reshape(1, mfccs.shape[0], mfccs.shape[1], 1))
        self.interpreter.set_tensor(self.input_details[0]['index'], in_tensor)
        self.interpreter.invoke()
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        val = output_data[0][0]
        # test for the wake word ('go')
        if val > WORD_THRESHOLD:
            print('listening')
            self.wakeword_flag = True
        if DEBUG_ACC:  # print accuracy of each detection
            print(val)
        if DEBUG_TIME:  # print processing time for a sound clip
            print(timeit.default_timer() - start_time)
