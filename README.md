



# Ossian + DNN demo

TODO:
OSSIAN variable

This repository contains a stripped-down and more up-to-date version of Ossian than that which is publicly 
available. It forms the basis of a toolkit whose repository we plan to make public this summer, so all
comments and feedback about ways to improve it are very welcome. 


# Getting the tools

[put some notes here -- compilation etc. ]


# Acquire some data

Ossian expects its training data to be in the directories:

```
 ./corpus/<LANG>/speakers/<DATA_NAME>/txt/*.txt
 ./corpus/<LANG>/speakers/<DATA_NAME>/wav/*.wav
```

Text and wave files should be numbered consistently with each other. ```<LANG>``` and ```<DATA_NAME>``` are both arbitrary strings, but it is sensible to choose ones which make obvious sense. Take a look at a toy (Romanian) corpus distributed with the tools for some guidance:

```
./corpus/rm/speakers/rss_toy_demo/
```

Let's start by building some voices on this tiny dataset. The results will sound bad, but if you can get it to speak, no matter how badly, the tools are working and you can retrain on more data of your own choosing.

You can download 1 hour sets of data in various languages we prepared here: http://tundra.simple4all.org/ssw8data.html

# A) HMM-based voice

Ossian trains voices according to a given 'recipe' -- the recipe specifies a sequence of processes which are applied to an utterance to turn it from text into speech, and is given in a file called ```$OSSIAN/recipes/<RECIPE>.cfg``` (where ```<RECIPE>``` is the name of a the specific recipe you are using). We will start with a recipe called ```naive_01_hts```. If you want to add components to the synthesiser, the best way to start will be to take the file for an existing recipe, copy it to a file with a new name and modify it.

The recipe ```naive_01_hts``` is a language independent recipe which naively uses letters as acoustic modelling units. It will work reasonably for languages with sensible orthographies (e.g. Romanian) and less well for e.g. English.

Ossian will put all files generated during training on the data ```<DATA_NAME>``` in language ```<LANG>``` according to recipe ```<RECIPE>``` in a directory called:

```
 $OSSIAN/train/<LANG>/speakers/<DATA_NAME>/<RECIPE>/
```

When if has successfully trained a voice, the components needed at synthesis are copied to:

```
 $OSSIAN/voices/<LANG>/<DATA_NAME>/<RECIPE>/
```

Assuming that we want to start by training a voice from scratch, we might want to check that these locations do not already exist for our combination of data/language/recipe:

```
rm -r $OSSIAN/train/rm/speakers/rss_toy_demo/naive_01_hts/ $OSSIAN/voices/rm/rss_toy_demo/naive_01_hts/
```

Then to train, do this:

```
cd $OSSIAN
python ./scripts/train.py -s rss_toy_demo -l rm naive_01_hts
```

If training went OK, you can synthesise speech. There is an example Romanian sentence in ```$OSSIAN/test/txt/romanian.txt``` -- we will synthesise a wave file for it in ```$OSSIAN/test/wav/romanian_toy_naive.wav``` like this:

```
mkdir $OSSIAN/test/wav/

python ./scripts/speak.py -l rm -s rss_toy_demo -o ./test/wav/romanian_toy_HTS.wav naive_01_hts ./test/txt/romanian.txt
```

# B) NN-based voice

Use the recipe naive_01_nn to build a NN-based voice. If you compare naive_01_hts and naive_01_nn, you will see that many steps are the same. The differences are that state-level labels suitable for NN training are produced instead of phone-level labels for HTS training, and instead of specifying an HTS acoustic model, NN-based duration and acoustic models are specified.

The call to train with this recipe is the same as before, but with the recipe name updated:

```
cd $OSSIAN
python ./scripts/train.py -s rss_toy_demo -l rm naive_01_nn
```

However, as various messages printed during training will inform you, NN training is not directly supported within Ossian. Before the voice will speak, you will need to take the acoustic features and labels produced by Ossian and use the Merlin toolkit you used previously to train both a duration and acoustic model, and then convert the NNs it produces back to a suitable format for Ossian. This is a little messy, but better integration between Ossian and Merlin is an ongoing area of development. Here's how to do this:

## 1) Acoustic features

The 'composed' features (acoustic features files containing multiple streams and delta features within each stream) which Ossian should have output at:

```
    train/rm/speakers/rss_toy_demo/naive_01_nn/cmp/*.cmp
```

... are similar but not identical to the ones we will use for NN training. Main differences: Ossian's files contain HTK headers and a single discontinuous F0 feature, whereas Merlin's can't handle the header and use F0 interpolated through unvoiced regions and a separate voiced/unvoiced feature. The static features inside Ossian's cmp files are fine, however, so to avoid extracting them a second time, we can split the cmp file into streams and keep only the static parts of those streams. To do so, call the following script:

```
./scripts/shell/split_cmp.py -cmp train/rm/speakers/rss_toy_demo/naive_01_nn/cmp/ -out train/rm/speakers/rss_toy_demo/naive_01_nn/dnn_streams -streams mgc,lf0,bap -widths 60,1,5
```

The flag 'widths' is used to say what the dimensions of your extracted feature streams are. The dimension of mgc will be mcep_order in your Ossian config + 1 for energy; lf0 will always be 1; bap will depend on sample rate, e.g. at 16000Hz it will be 1, at 48000Hz it will be 5.

<!---
bap can be worked out from the sample rate using this formula in Python: 

```
  bapsize= int(min(15000.0, (( rate / 2.0) - 3000.0)) / 3000.0)      
  ```

... where rate is a variable giving the sample rate you specified in the Ossian recipe file (this comes to 5 for the 48000 Hz used in naive_01_nn, hence the above command line).
-->

If this worked OK, data for the separate streams will have been output in subdirectories of train/rm/speakers/rss_toy_demo/naive_01_nn/dnn_streams, and the path to this directory will be used as an input in NN training (below).

## 2) Duration features

Take a look at the duration data output at train/rm/speakers/rss_toy_demo/naive_01_nn/dur_data/*. Each line of these text files represents the durations (in frames) of the 5 HMM states in a phone/letter segment. To use this data with the DNN training, we need to flatten this to a single column and convert to binary (float) format:

```
cd $OSSIAN/train/rm/speakers/rss_toy_demo/naive_01_nn/
mkdir ./dur
for FNAME in ./dur_data/*.dur_data ; do
    BASE=`basename $FNAME .dur_data`;
    echo $BASE ; 
    cat $FNAME | tr ' ' '\n' | $OSSIAN/tools/bin/x2x +af > ./dur/$BASE.dur ;
done
```

## 3) Labels and questions

Labels for training DNNs both for acoustic and duration models will have been produced here, and don't need any modification:

```
train/rm/speakers/rss_toy_demo/naive_01_nn/dnn_lab/*.dnn_lab
```

and here:

```
train/rm/speakers/rss_toy_demo/naive_01_nn/lab_dur/*.lab_dur
```

respectively. Take a look -- their format is designed to be easier for humans to process than the equivalent labels used in the HTS and Merlin demos. The question files to use with these labels are also in train/rm/speakers/rss_toy_demo/naive_01_nn/; you should use questions_dnn.hed.cont and questions_dur.hed.cont for acoustic and duration model training, respectively. The .cont suffix means that these question files extract continuous features (lines starting CQS) as well as binary ones (lines starting QS). The corresponding files ending .key are to give a human-readable explanation of the numbered features used in label and question files -- take a look if you are interested.

## 4) Training DNN acoustic and duration models

If you have set up your tools properly (e.g. if setup_tools.sh ran OK for you), then the Merlin tools should be located here:

```
$OSSIAN/tools/merlin
```

To use the tools we need a list of sentences available for training/development/testing which you can make like this:

```
cd $OSSIAN/train/rm/speakers/rss_toy_demo/naive_01_nn
ls lab_dnn/ | while read line ; do basename $line .lab_dnn ; done > filelist.txt
```

To find out how many sentences we have (this will be useful when you adjust the config files):

```
wc -l filelist.txt 
```

To train each of the acoustic and duration models, you will need to prepare a config file. Examples are given under $OSSIAN/scripts/merlin_interface/, named feed_forward_dnn_ossian.conf and feed_forward_dnn_ossian_DUR.conf. Make a copy of these for each voice you train and adjust as necessary. I have added comments to help: lines starting ##!!! precede lines you will probably have to adjust for your own data, lines starting ## without the !!! I put there just to give you some more information about what the following line does.

After copying and adjusting feed_forward_dnn_ossian_DUR.conf, try training a model like this (but using whatever name you gave your modified config):

```
cd $OSSIAN/
python ./tools/merlin/src/run_merlin.py ./scripts/merlin_interface/feed_forward_dnn_ossian_DUR.conf
```

If training went OK, then you can export the trained model to a better format for Ossian. The basic problem is that the NN-TTS tools store the model as a Python pickle file -- if this is made on a GPU machine, it can only be used on a GPU machine. This script converts to a more flexible format understood by Ossian -- call it with the same config file you used for training and the name of a directory when the new format should be put:

```
python ./scripts/util/store_merlin_model.py ./scripts/merlin_interface/feed_forward_dnn_ossian_DUR.conf ./voices/rm/rss_toy_demo/naive_01_nn/processors/duration_predictor
```

Repeat the same for the acoustic model:

```
cd $OSSIAN/
python ./tools/merlin/src/run_merlin.py ./scripts/merlin_interface/feed_forward_dnn_ossian.conf
python ./scripts/util/store_merlin_model.py ./recipes/dnn/feed_forward_dnn_ossian.conf $OSSIAN/voices/rm/rss_toy_demo/naive_01_nn/processors/acoustic_predictor
```


## 5) Synthesis

Now everything we need to synthesise is stored under $OSSIAN/voices/rm/rss_toy_demo/naive_01_nn/, we can generate sentences with the new model:

```
cd $OSSIAN
python ./scripts/speak.py -l rm -s rss_toy_demo -o ./test/wav/romanian_toy_DNN.wav naive_01_nn ./test/txt/romanian.txt
```

You can compare the audio produced by the HTS system previously (./test/wav/romanian_toy_HTS.wav) with that produced by the DNN system (./test/wav/romanian_toy_DNN.wav)


## Etc etc







The file extra_parts_ossian_lexicon.tar contains some extra binaries and other resources
for building voices using a lexicon and letter-to-sound rules. Copy it into your Ossian
directory and unpack it like this to put everything in place:

cd Ossian
tar xvf extra_parts_ossian_lexicon.tar 

There is an extra small corpus of English here:

corpus/en/speakers/tundra_toy_demo/

and an example toy lexicon here:

corpus/en/labelled_corpora/cmudict_demo/

Note that the name of this directory (cmudict_demo) is the lexicon name which will
be specified in a recipe. This toy lexicon contains 1000 randomly selected entries from the
CMU pronunciation lexicon for demonstration purposes. These entries are contained (in 
Festival's Scheme format) in a file in the lexicon directory ending in .out, in this case:

cmudict_demo.out

Note that I have been careful to include only 1 pronunciation for each word form -- you
can in theory include multiple forms and then disambiguate by POS tag, but the recipe 
included doesn't have access to POS tags. The second element in each lexicon entry
is a POS tag, which in this case can be some arbitrary placeholder.

Information about the phones in the dictionary are given in a phoneset description --
a file in the lexicon directory ending .table, in this case:

cmudict_phones.table 

This is a lookup table of phonetic features of each phone. The only feature (column) which
is required for the lexicon to be applied is vowel_cons -- vowels must have the value 
'vowel' in this column. (This is used for determining a set of legal onsets which is
then used for syllabifying unseen words.)

The file called letter.names gives the pronunciation of letters -- we will not use this 
here, but if you make your own lexicon, please include a copy of this file (for English
phoneset even) to keep the tools happy.   

The recipe msc_demo_03.cfg adds this lexicon on top of naive_01_nn.cfg. Try it out on
English data like this:

python ./scripts/train.py -s tundra_toy_demo -l en msc_demo_03

(...and then build DNN duration and acoustic models as before).

You can try adding a lexicon for you own language. Also, many features added during 
lexicon lookup are not exploited in the duration and acoustic model input features in
msc_demo_03 as it stands. Try adding extra xpath expressions to the '[[contexts]]'
sections of dur_label_maker and dnn_label_maker to query things like the phones' phonetic
features that have been added, stress of current and surrounding syllables, position of
phone in syllable etc. Following existing xpaths in msc_demo_* should help a lot.










To install some missing resources for the lexicon-based voice described in 
msc_ossian_notes_part_2.txt, copy extra_parts_ossian_lexicon_B.tar into your Ossian
directory and unpack it like this:

cd Ossian
tar xvf extra_parts_ossian_lexicon_B.tar 









----------------------------------------------------------------------------------------
"Could you send me some instructions on adding syllable structures and tone information?"
 
It looks like your text input:

 kǒng bài huǒ wèi tā àn mó .

... contains space-delimited syllables. Using the tokeniser as it stands in the 
recipes I made for you (msc_demo_0*.cfg) will split this into syllables. This is how the
tokeniser is configured in those recipes:
 
 [tokeniser]
    class = BasicTokenisers.RegexTokeniser
    target_nodes = //utt
    split_attribute = text
    child_node_type = token 
    add_terminal_tokens = True
    split_pattern = (${SPACE_PATT}*${PUNC_PATT}*${SPACE_PATT}+|${SPACE_PATT}*${PUNC_PATT}+\Z)  
    
This instructs Ossian to process an utterance by iterating over all nodes matched by 
the xpath expression '//utt', and for each of those nodes, taking the 'text'
attribute, splitting it using the regular expression in split_pattern, and adding children
of type 'token'. In fact, Ossian initialises utterances with a single 'utt' node at their
root, so the xpath expression '//utt' will return just the root node.


The regular expression
in split_pattern is long and ugly, and composed of smaller regular expressions defined 
previously in the config file (${SPACE_PATT} etc.). An important point is the parentheses 
surrounding it -- the effect of these is to keep all chunks when splitting, including the 
spaces. These are used later to allow silences inserted between words to be detected in 
forced alignment.                                                                                                                                                                                               


If you pre-processed your input and
know how it will be formatted, you can simplify this, and also add separate level for 
word and syllable. If your 7 syllables consist of 2 2-syllable words and 3 1-syllables 
words, for example, you could represent them in pre-processing like this (I know this
is probably not correct):

kǒng bài| |huǒ wèi| |tā| |àn| |mó|.

Then a first processor would split into tokens (words, spaces and punctuation):

 [tokeniser]
    class = BasicTokenisers.RegexTokeniser
    target_nodes = //utt
    split_attribute = text
    child_node_type = token 
    add_terminal_tokens = True
    split_pattern = \|
    
Here, we just split on | (the backslash just says this is a string, not special regular 
expression character). There are no parentheses so the |s are discarded.

Next, you can split words into syllables with another RegexTokeniser:

 [syllabifier]
    class = BasicTokenisers.RegexTokeniser
    target_nodes = //token
    split_attribute = text
    child_node_type = syll 
    add_terminal_tokens = False
    split_pattern = ${SPACE_PATT}

The utterance structure made by applying these 2 processors will look something like:


<utt text="kǒng bài| |huǒ wèi| |tā| |àn| |mó|.">
  <token text="kǒng bài">
    <syll text="kǒng">
    <syll text="bài">
    ...

Now you want to add tone as a feature of the syllable. The best way to do this -- and
to add custom processing in general -- might be to define a subclass of the processor Ossian/scripts/processors/NodeEnricher.py. Take a look in the documentation in the 
source code there. E.g. make a new file  Ossian/scripts/processors/MyCustomProcessors.py
and then define:

from NodeEnricher import NodeEnricher

class ToneProcessor(NodeEnricher):
        
    def enriching_function(self, input):
        ...

Then you can add a processor called e.g. tone_processor to your train and runtime pipeline,
and define it in your recipe like e.g.: 

 [tone_processor]
    class = MyCustomProcessors.ToneProcessor
    target_nodes = //syll
    input_attribute = text
    output_attribute = tone

You just need to write enriching_function in order to take e.g. "kǒng" and return some
representation of the tone, e.g. 'tone_2' or 'fall_rise' etc.

You might want to define a second processor to provide a pronunciation of the word
stripped of tone:

 [tone_remover]
    class = MyCustomProcessors.ToneRemover
    target_nodes = //syll
    input_attribute = text
    output_attribute = pronunciation

Here, the enriching_function needs to take "kǒng" and return "kong".

You will need to check that later processors' input features are consistent with the
output names you have used, e.g. that a processor splitting syllable pronunciations into
phones operates on syllables' pronunciation attribute rather than their text attribute
(assuming you want to use the tone-stripped version).

Also, you need to add contexts to later processors like dnn_label_maker which make use
of the features you have added to the utterance structure. These will correspond to
questions which are output in the question file used for DNN training.

----------------------------------------------------------------------------------------    
"We would like to know if it is possible to implement different features like stress rules, 
allophones etc., to the model."
    
The guidelines just given about adding subclasses of NodeEnricher will help you add
rules about stress, allophones, etc. Again, make sure that any features you add to the
utterance structure are queries appropriately by contexts in dnn_label_maker etc.

-----------------------------------------------------------------------------------------
    







    ongoing




Ossian lexicon & Italian
------------------------

Hi Giorgia (and others CC'd as it might be relevant to all of you),

First a tip for all of you which I should have mentioned at the outset -- call train.py with the flag '-p 1' in the command line -- this turns off some parallel processing which can make errors much harder to find when you are debugging.

Please find an updated version of scripts/processors/Lexicon.py attached -- please swap it for the one currently in your Ossian directory.



I modified the code to use utf8 everywhere and preserve diacritics. The lexicon file is now expected to be encoded as utf8 -- please make sure your file called corpus/it/labelled_corpora/cmudict_demo/cmu_dict.out is in this encoding rather than ISO8859-1 as the version you sent me.

Things seem to be working OK now; there are a couple of warnings like:

WARNING: couldnt run LTS for virtù

… but I think this is just because there are no examples of the character ù in the data on which the LTS rules are trained -- when you migrate to the full lexicon this shouldn't be a problem.

In your toy lexicon there were a few examples of multiple pronunciations disambiguated with POS tags -- this broke things for utterances containing such words as you have no POS tags in your utterances. I changed this to arbitrarily choose the first pronunciation where there are several but no POS tags -- I also added this warning:

WARNING: no pos tag to disambiguate pronunciation -- take first entry in lexicon

This explains why for some utterances no labels were produced.

Finally, the issue of missing apostrophes -- I haven't looked carefully into this because it seems that apostrophes have been wrongly stripped in the input (Tundra) data, e.g.  deglingredienti in the utterance corpus/it/speakers/rss_toy_demo/txt/galatea_01_00021.txt . If there are still issues when apostrophes are actually input but stripped, we could investigate that later.

I will mail about other issues raised on Wednesday soon.

Regards,

Oliver



Ossian: tips for debugging new processors and features
------------------------------------------------------

Dora pointed out that it can be hard to see whether an added processor is having the desired effect. Some tips for checking and debugging:

1) run on the smallest database possible until you are happy things are working

2) call train.py with '-p 1' on the command line  until you are happy things are working: this
   turns off parallel processing and makes it easier to diagnose problems
   
3) run the smallest number of processors you need to check your new processor. You can temporarily exclude processors by altering the specification of pipelines in your recipe file. For example, the train pipeline in your recipe might look like this:

[train]
stages =   tokenisation, tagging, alignment, dnn_speech_generation

That is, it consists of 4 stages, each of which consists of a sequence of processors:

[tokenisation]
processors = tokeniser, new_processor, lexicon_lookup, syllable_adder

If new_processor has just been added and we want to check it, we only need to run up to that point. We can temporarily exclude most of the stages and processors by commenting them out:

[train]
stages =   tokenisation  # , tagging, alignment, dnn_speech_generation

[tokenisation]
processors = tokeniser, new_processor # , lexicon_lookup, syllable_adder

When you are happy that new_processor is doing what it should be, move the # to add some of the processors back in.

4) Check a sample utterance in Ossian/train/<LANGUAGE>/speakers/<SPEAKER>/<RECIPE>/utt/*.utt to check your new processor has added the things you think it should have added. The tree structure of these XML files reflects the structure of the utterances you are building. 

5) The role of dur_label_maker and dnn_label_maker in the example recipes is to extract features from the utt structures for each phone or state. E.g. dur_label_maker is configured like this:

    target_nodes = //segment

    [[contexts]]

        ll_segment =     preceding::segment[2]/attribute::pronunciation
        l_segment =      preceding::segment[1]/attribute::pronunciation
        c_segment =                          ./attribute::pronunciation
        
This relies heavily on XPATH, a language for matching nodes of XML files (http://www.w3schools.com/xsl/xpath_intro.asp).  The expression in target_nodes will match all XML nodes with the tag 'segment' in the utterance. The label maker will then iterate over each of these nodes and extract the features in [[contexts]] for that node.  The features are specified with an arbitrary human readable name (ll_segment) and and XPATH which is relative to them. E.g. preceding::segment[2]/attribute::pronunciation is an instruction to start at a given segment node, move to the segment 2 places to the left, and extract the information contained in its pronunciation attribute.

6) A way to make sure that XPATHs are extracting what you want is to look at the resulting files in Ossian/train/<LANGUAGE>/speakers/<SPEAKER>/<RECIPE>/dnn_lab/* . The question files in Ossian/train/<LANGUAGE>/speakers/<SPEAKER>/<RECIPE>/ ending .key and .values are summaries of what the label files contain -- the .key file relates the numbers in the label file to the arbitrary human readable names in your recipe file. 


----------------


I'll CC the others in case this information is useful to them too. I'll include step-by-step description of the debugging I did so the process as well as the results should be clear. 

First of all, general advice about debugging -- please always delete existing attempts at voice building when debugging, like this:

rm -r train/zh/ voices/zh

(I used the language code zh -- substitute it for whatever you used.)

Then run the train script again, including '-p 1' to turn off parallel processing and make errors more obvious.

python ./scripts/train.py -s toy -l zh -p 1 msc_demo_chinese_debug

(note I renamed your recipe file msc_demo_chinese_debug.cfg and used the speaker code 'toy' for the data you sent me).

I get these errors when running the above command:

1)  TypeError: enriching_function() takes exactly 1 argument (2 given)

This is because the first line of your 2 enriching functions needs to be:

    def enriching_function(self, input):

…instead of:

    def enriching_function(input):

The 'self' must be included because this is a method (function associated with a class).

I fixed that, cleaned up and ran again, giving this error:

2)   File "/afs/inf.ed.ac.uk/group/cstr/projects/simple4all_2/oliver/repos/Ossian/scripts/processors/ChineseCustomProcessors.py", line 10, in enriching_function
    tone = "tone_"+tones.findall(input)[0]
IndexError: list index out of range

(Note I renamed your MyCustomProcessors.py to ChineseCustomProcessors.py)

To debug, I added  'print input' inside the problematic method -- the text of the first token was printed:

_END_

This is an end-of-utternace token, added to hold utterance-initial silences. To only extract syllables from tokens of type 'word', I changed your [syllable_adder]'s

    target_nodes = //token

to:

    target_nodes = //token[@token_class='word']

I fixed that, cleaned up and ran again, giving this error:

3)     File "/afs/inf.ed.ac.uk/group/cstr/projects/simple4all_2/oliver/repos/Ossian/scripts/processors/ChineseCustomProcessors.py", line 12, in enriching_function
    tone = "tone_"+tones.findall(input)[0]
IndexError: list index out of range

To debug, I added another print statement under 'print input': print tones.findall(input) . The printed output is now:

tou
[]

In fact, you handle the case where there is no tone number, but too late. Reordering and modifying your code to:


    found_tones = tones.findall(input)
    if len(found_tones) == 0:
        tone = "tone_0"
    else:
        tone = "tone_"+found_tones[0]
    return tone


… does what I think you intended. 

4) The script runs OK now, so I looked at an utt file (utt/a002.utt) and saw this:

  <token text="ko3ng ba4i huo3  " token_class="word"… >
    <segment text="k" segment_name="k".../>
    ...
    <syll text="ko3ng" tone="tone_3" pronunciation="kong"/>
    <syll text="ba4i" tone="tone_4" pronunciation="bai"/>
    <syll text="huo3" tone="tone_3" pronunciation="huo"/>
  </token>
 
Segments have been added as sisters of syll nodes, rather than their daughters. Looking at the sequence of processors in your recipe, segment_adder is used before the syllables are added:

segment_adder, syllable_adder, tone_processor, tone_remover,

I changed that to:

syllable_adder, tone_processor, tone_remover, segment_adder

Also, I changed [segment_adder]'s 

    target_nodes = //token[@token_class='word']
    split_attribute = text
to 

    target_nodes = //syll
    split_attribute = pronunciation 

I then had to change [letter_safetexter]'s 


    input_attribute = text

to:

    input_attribute = pronunciation

… to match changes 'upstream'.

5) Another look at a generated utt showed that space between words is deleted -- we want to keep this in order to allow silences between words at run time. 

Modifying your input text file from 

|ko3ng ba4i huo3  |we4i  |ta1  |a4n mo2  | 。

to:

|ko3ng ba4i huo3 | |we4i | |ta1 | |a4n mo2  | 。

… has the desired effect. (I think I mentioned including the spaces as 'words' in a previous note.)

See if you can follow and make the changes I made and let me know how things are looking / sounding.







## Cuts

```diff
+ ; also, I have obtained and compiled the necessary tools for you to save some time. They should run on a DICE machine running Scientific Linux 7, like those in the  lab.  The compiled tools this demo will use are in Ossian/tools/bin/ 

The latest version of Python 2.7 on DICE has some of the dependencies we need, but not 
everything. Please do this on DICE to add the required extra Python packages locally: 

```
pip install --user configobj
pip install --user scikit-learn
pip install --user regex
pip install --user argparse

pip install --user bandmat
pip install --user theano
```

Set an environment variable to point to the top level of the Ossian package -- we will use 
this in the notes below:

```
cd /path/to/my/copy/of/Ossian
OSSIAN=$PWD
```

If you have trouble using the compiled tools (like incompatible shared libraries), you can
recompile locally as follows (please try the compiled versions I provided first: I tried them in the Forrest Road computer lab and they worked fine for me there):

```
### compilation:
cd $OSSIAN/tools/downloads/htk
./configure --prefix=$OSSIAN/tools/ --without-x --disable-hslab
make clean
make
make install

cd $OSSIAN/tools/downloads/hts_engine_API-1.05
./configure --prefix=$OSSIAN/tools/
make clean
make
make install

cd $OSSIAN/tools/downloads/SPTK-3.6
./configure --prefix=$OSSIAN/tools/
make clean
make
make install

cd $OSSIAN/tools/world/working/World-master
rm -rf  build/*
make -f makefile analysis
make -f makefile synth
cp build/analysis $OSSIAN/tools/bin/
cp build/synth $OSSIAN/tools/bin/
```









