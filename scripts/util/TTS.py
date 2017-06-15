#!/usr/bin/env python

import sys
import re

from Voice import *

def main_work():

    #################################################

    # ======== Get stuff from command line ==========

    def usage():
        print "Usage: ......  "
        sys.exit(1)

    # e.g. 

    try:
        config_file = sys.argv[1]        

    except:
        usage()


    #################################################

    SynthSession(config_file=config_file)


class SynthSession(ConfiguredComponent):

    #extra_required_options = ["VOICES"]
    extra_configspec_options = {"VOICES": "string(default=.)"
                                }

    command_dict = {
            "help": ": get help",
            "quit": ": quit session",
            "voice": " v: load voice v",
            "tts": " t: synthesise from text t",
            "library": ": view voices in voice library"
    }

    

    def load(self):
        print 
        print " -- Start a TTS session -- "
        print 

        sys.path.append(self.config["SCRIPT"] + "/gensim-0.5.0/src/")

        self.current_voice = False

#        if "default_voice" in self.config:
#            #self.current_voice = Voice(self.config["default_voice"])
#            pass

        self.interface_with_user()

    def train(self):
        
        print "SynthSession object is not trainable -- proceed with loading"
        self.load()


    def interface_with_user(self):

        finished_session = False
        while not finished_session:

            entered = raw_input('Enter a command (type "help" for a list of commands): ')
            chunks = re.split("\s+", entered, maxsplit=1)

            command_code = chunks[0]
            arg = False
            if len(chunks) == 2:
                arg = chunks[1]

            if self.validate_command(command_code):

                if command_code == "quit":
                    print " -- Session over -- "
                    finished_session = True

                else:
                    ## Get method from method name string and call it:
                    method = getattr(self, command_code)                   
                    method(arg=arg)




    def validate_command(self, command_code):

        if command_code not in self.command_dict:
            print "Command '%s' is not valid"%(command_code)
            return False
        else:
            return True


    def help(self, arg=False):
        title = "These are the options:"
        items = ["%s%s"%(key, value) for (key, value) in self.command_dict.items()]
        self.print_frame(title, items)
       

    def voice(self, arg=False):

        
        if not arg:
            print "Command 'voice' must be followed by voice to load"
            return
        voice_fname = os.path.join(self.config["VOICES"], arg + ".cfg")
        print "Load voice %s from file %s"%(arg, voice_fname)
        
        self.current_voice = Voice(config_file=voice_fname)

    def tts(self, arg=False):
        text = arg
        text = text.decode(sys.stdin.encoding)  

        if not text:
            print "Command 'tts' must be followed by text to convert"
            return        
        if not self.current_voice:
            print "A voice must be loaded to do TTS"
            return
        print "Synth from text: %s"%(text)
        self.current_voice.synth_utterance(text)


    def library(self, arg=False):
        ## print "View possible voices"
        voice_list = os.listdir(self.config["VOICES"])
        voice_list = [voice for voice in voice_list if not voice.endswith("~")] ## Filter linux temp files
        voice_list = [remove_extension(voice) for voice in voice_list]
        if len(voice_list) == 0:
            print "There are no voices currently in the library at %s"%(self.config["VOICES"])
            return
        title = "Voices currently in the library:"
        items = voice_list
        self.print_frame(title, items)

        
        
    def print_frame(self, title, items, width=30):
        offset = "    "
        bigger_offset = "      "

        print
        print "%s%s"%(offset, "="*width) ## thick line
        print "%s%s"%(offset, string.center(title, width)) ## centered title
        print "%s%s"%(offset, "-"*width) ## thin line
        for item in items:
            print "%s%s"%(bigger_offset, item)
        print "%s%s"%(offset, "="*width) ## thick line
        print


if __name__=="__main__":

    main_work()
