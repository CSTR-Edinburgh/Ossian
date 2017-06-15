#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Antti Suni - Antti.Suni@helsinki.fi
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk



import default.fnames as fname
import default.const as c


import sys
import os






"""                                                                                                                                                                                                                                                                        
manage external resources of the voice

The resources types can be files,  flags, values, objects?
and are stored in dictionary format

-should provide abstraction regarding directories and filename extensions
in loading and saving resources

- processors should be able to add and query resources by name


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  
"""

class Resources(object):  ## osw: no longer subclass of ConfiguredComponent
    
    def __init__(self, **init_config):  ## osw -- could fix args to:  speaker, language, configuration, DIRS ??
  
        self.speaker = init_config["speaker"]
        self.lang = init_config["language"]
        self.configuration = init_config["configuration"]
            
        if not init_config.has_key('DIRS'):
            print "ERROR: paths not defined for resources."
            sys.exit(1)
        
                ### simplification for now: no separate language level models
        self.path = {}
        self.path[c.CORPUS] = "/".join([init_config['DIRS']['CORPUS'], self.lang, c.SPEAKER, self.speaker])
        self.path[c.RULES] = "/".join([init_config['DIRS']['RULES'], self.lang])
        self.path[c.TRAIN] = "/".join([init_config['DIRS']['TRAIN'], self.lang, c.SPEAKER, self.speaker, self.configuration])
        
        ## language-general models that can be reused by different voices (by copying...)
        self.path[c.COMPONENT] = "/".join([init_config['DIRS']['TRAIN'], self.lang, c.COMPONENT])
        
        self.path[c.VOICE] = "/".join([init_config['DIRS']['VOICES'], self.lang, \
                                                        self.speaker, self.configuration])
        self.path[c.CONFIG] = "/".join([init_config['DIRS']['CONFIG'], self.configuration])
        
        self.path[c.SCRIPT] = "/".join([init_config['DIRS']['ROOT'],"scripts","shell"])
        self.path[c.LANG] = "/".join([init_config['DIRS']['CORPUS'], self.lang])

        ## osw added:
        self.path[c.BIN] = "/".join([init_config['DIRS']['BIN']])
        self.path[c.ACOUSTIC_MODELLING_SCRIPT] = "/".join([init_config['DIRS']['ROOT'], "scripts", "acoustic_model_training", "subrecipes", "script"])
        self.path[c.ACOUSTIC_MODELLING_CONFIG] = "/".join([init_config['DIRS']['ROOT'], "scripts", "acoustic_model_training", "subrecipes", "config_template"])
        
        if not os.path.isdir(self.path[c.TRAIN]):
            os.makedirs(self.path[c.TRAIN])
            
            
    
        # get some paths from enironment for now, compatible with oliver's version
        ## Oliver: migrating to Antti's paths...
    #     try:
#             self.path["CONTEXTS"] = os.environ["CONTEXTS"]
#         except:
#             pass
# 
#         try:
#             self.path[c.EST] = os.environ["ESTDIR"]
#         except:
#             self.path[c.EST] = "/".join([init_config['DIRS']['BIN'], c.EST])
#             
#         try:
#             self.path[c.HTS] =os.environ["HTSDIR"]
#         except:
        self.path[c.HTS] = "/".join([init_config['DIRS']['BIN'], c.HTS])



        # ..and some hard coded
        self.path["GENSIM"] =  init_config['DIRS']['ROOT']+"/tools/gensim-0.5.0/src/"
        self.path["GLOTT"] =  init_config['DIRS']['ROOT']+"/tools/GlottHMM/"

            

        for p in self.path:
            #print self.path[p]
            if not os.path.exists(self.path[p]):
                #print "ERROR: "+p +" directory " + self.path[p]+ " does not exist\n"
                #sys.exit(1)
                pass 
                
        self.resources = {}

    def load(self):

        pass

    def add_resource(self, key, value, rtype=None):
        if rtype == c.FILE:
            pass
        self.resources[key] = value

    def add_file(self, key, rtype, file):
        self._check(rtype, file)
        
        if type(file) == type([]):
            for i in range(len(file)):
                file[i] = os.path.join(self.path[rtype],file[i])
        else:
                file = os.path.join(self.path[rtype],file)
        if key in self.resources:
            print " multiple resources with the same name: "+key
        self.resources[key] = file
        return file

    def has_key(self, key):
        return self.resources.has_key(key) 

    def get(self, key):
        if key not in self.resources:
            print "ERROR: resource "+key+ "not available"
            
            sys.exit(1)

        return self.resources[key]

    def get_path(self, type, name=None):
        self._check(type, None)
        if not name:
            return self.path[type]
        
        if name.startswith("/") or name.startswith("~/"):
            if os.path.isdir(name):
                #print "path exists, ok"
                pass
            else:
                print "absolute path does not exist and will not be created", name
                sys.exit(1)
        else:
            name = "/".join([self.path[type],  name])
        try:
            os.makedirs(os.path.split(name)[0])
        except:
            pass
        return name





    def get_processors(self, config):
        
        print config
    
        if not config.has_key("run_mode") or not config.has_key(config["run_mode"]):
            print "ERROR: called with mode '"+config["run_mode"]+"', which is not defined in the config file."
            sys.exit(1)
        print "what: ",config[config["run_mode"]]

        return config[config["run_mode"]].walk(self._load_item, call_on_sections=False)



    def get_filename(self, name, rtype, subtype=""):
        """
        get full path of file "name", based on 
        language, speaker, configuration and type of file
        
        make directory if it does not exist?
        """

        self._check(rtype, subtype)

        # if full path given, ok
        if name.startswith("/") or name.startswith("~/"):
            if os.path.isfile(name):
                #print "file fname exists, ok"
                return name
        elif name.find("/")> 0:
            name="/".join([self.path[rtype], name])
        else:
            name = "/".join([self.path[rtype], subtype, name])
        try:
            os.makedirs(os.path.split(name)[0])
        except:
            pass
        return name
        

    def get_dirname(self, name, rtype, subtype="", create=True):
        """
        osw -- mainly duplicated from get_filename -- merge?
        """

        self._check(rtype, subtype)

        # if full path given, ok
        if name.startswith("/") or name.startswith("~/"):
            if os.path.isdir(name):
                #print "file fname exists, ok"
                return name
        elif name.find("/")> 0:
            name="/".join([self.path[rtype], name])
        else:
            name = "/".join([self.path[rtype], subtype, name])
        if create:
            try:
                os.makedirs(name)
            except:
                pass
        return name
                


                
    
    def make_dir(self, rtype, subtype):
    
        self._check(rtype, subtype)
        path = os.path.join(self.path[rtype], subtype)
        

        if not os.path.exists(path):
            os.mkdir(path)
        
        return path
          
    
    
    def _check(self, rtype, subtype):

        if rtype not in self.path:
            sys.exit( "type of resource "+rtype +" unknown")

                   
