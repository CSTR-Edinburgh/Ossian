--------------------------------------
List of some obvious things to do next
--------------------------------------

There are lots of these -- a few that come to mind:

- Merge in recent extensions to trunk from Antti, Peter, Jari...
    - Morfessor
    - ... 
    
- Languages:
    - Add toy demo corpora from all Tundra/Indic languages
    - Train and distribute voices on decent amounts of data for all these languages
    - Make tars of the Tundra etc. data that can be unpacked at $OSSIAN so the data lands 
      in the right place

- Online demo:
    - Get it working at a decent speed -- move from STRAIGHT resynthesis to MLSA?
    - Client/server mode to avoid loading voices per utterance?
  
  
  
  
    
.. - Vocoding:
..    - Currently using SPTK's mcep and hts_engine's MLSA on 16kH speech
..   - Higher sampling rates
..    - Move to STRAIGHT (at least for extraction -- can .cmp files be distributed? )
..   - Incorporate Cassia's modifications to hts_engine
..    - GlottHMM