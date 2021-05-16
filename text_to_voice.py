import os
import sys
import vlc
import time
import urllib.parse

#########################################
# Speaker() text to speech function with beep
# Requires a speaker setup on RPI
# uses READSPEAK service
# new function 'beep' for user feedback
class Speaker:
    def __init__(self):
        self.AUDIO_ON = True
        self.ON = True
        self.READSPEAK_URL = 'https://tts.readspeaker.com/a/speak?'
        self.READSPEAK_TOKEN = READSPEAKER_API_KEY
        vlcInstance = vlc.Instance()
        self.player = vlcInstance.media_player_new()
        if not os.path.isfile('./barcode_beep.mp3'):
            print("MISSING BEEP FILE: ./barcode_beep.mp3")

    def is_on(self):
        return self.ON

    def turn_on(self):
        self.ON = True

    def turn_off(self):
        self.ON = False

    def say(self, mtext):
        # Call the API and put results into a new Item object
        if not self.AUDIO_ON:
            return
        try:
            params = {'key': self.READSPEAK_TOKEN,
                      'lang': 'en_us',
                      'voice': 'Sophie',
                      'text': mtext}
            self.player.set_mrl(self.READSPEAK_URL + urllib.parse.urlencode(params))
            self.player.play()
        except OSError as e:
            print("ERROR: text_to_voice(): Speaker.say(): ", e)
        except:
            print("ERROR: text_to_voice(): Unknown Error", sys.exc_info()[0])
        return

    def beep(self, times=1):
        self.player.set_mrl('./barcode_beep.mp3')
        for i in range(0, times):
            self.player.play()
            time.sleep(.2)




##################################
# (old) Speaker text-to-speech using Google pico service

import subprocess

class Speaker_pico:
    def __init__(self):
        if not os.path.exists('/usr/bin/aplay'):
            print("WARNING: aplay not installed - no voice audio output")
            self.ON = False
        elif not os.path.exists('/usr/bin/pico2wave'):
            print("WARNING: pico2wave not installed - no voice audio output")
            self.ON = False
        else:
            self.ON = True
        vlcInstance = vlc.Instance()
        self.player = vlcInstance.media_player_new()
        if not os.path.isfile('./barcode_beep.mp3'):
            print("MISSING BEEP FILE: ./barcode_beep.mp3")


        # status, result = subprocess.getstatusoutput("pico2wave")
        # status, result = subprocess.getstatusoutput("aplay")

    def is_on(self):
        return self.ON

    def turn_on(self):
        self.ON = True

    def turn_off(self):
        self.ON = False

    def say(self, input_text):
        if not self.ON:
            return
        try:
            # subprocess.Popen(["pico2wave", "-w", "fridge.wav", text_in,"&&", "aplay", "fridge.wav"])
            print("Running pico2wave.")
            subprocess.run(["pico2wave", "-w", "fridge.wav", input_text])
        except OSError as e:
            print("ERROR: text_to_voice(): Speaker.say(): ", e)
        try:
            subprocess.Popen(["aplay", "fridge.wav"])
        except OSError as e:
            print("ERROR:text_to_voice(): Install aplay", e)

    def beep(self, times=1):
        self.player.set_mrl('./barcode_beep.mp3')
        for i in range(0, times):
            self.player.play()
            time.sleep(.5)

