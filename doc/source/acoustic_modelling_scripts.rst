============================================
Scripts for acoustic model training
============================================

Ossian includes a collection of scripts for training acoustic models which in the normal course of things are used to train HMMs after speech coding and text analysis have been done. Infact, some of these scripts will have been called if the commands given in this documentation to build  demonstration voices have been run.  This collection of scripts can be found under:

.. code-block:: bash

    ossian-v.?.?/scripts/acoustic_model_training/

A number of different subrecipes are available, and can be added to. These subrecipes specify different ways of training acoustic models, and are selected by the relevant processors of top-level recipes. E.g. the recipe ``ossian-v.1.2/recipes/naive.cfg`` configures an acoustic model which is to be trained using the subrecipe called ``quick_voicebuild_01``:

.. code-block:: ini

    [acoustic_model]
        class = AcousticModel.AcousticModel
        acoustic_subrecipe = quick_voicebuild_01
        [[training_settings]]
            BINMOD = " -B "

The scripts for these subrecipes are contained in ``ossian-v.?.?/scripts/acoustic_model_training/subrecipes/script``, and default configurations for them are in ``ossian-v.?.?/scripts/acoustic_model_training/subrecipes/config_templates``. The default configuration settings are overridden by top-level recipes by ``training_settings`` subsections: in the above excerpt from ``naive.cfg``, for example, the value of ``BINMOD`` is set to be ``" -B "`` instead of the default ``" "`` -- this means that acoustic models will be written out in HTK binary model format instead of the default ASCII.  


Using the scripts without Ossian's text processing
--------------------------------------------------

As well as using these scripts as part of an Ossian recipe, it is also possible to use them with already parameterised and annotated data (i.e. without using Ossian to do any speech coding or text analysis). This might be done to try out e.g. alternative TTS front-ends using acoustic models trained in a comparable way. 

With the environment variable $OSSIAN pointing to the top directory of an Ossian installation (called something like ``./ossian-v.1.2``), the following command line can be used to train an acoustic model from some acoustic feature files in ``$FEAT_DIRECTORY``, label files in ``$LABEL_DIRECTORY``, and the question file at ``$QUESTIONS``, and output a trained model under ``$OUTPUT``:

.. code-block:: bash

    $OSSIAN/scripts/acoustic_model_training/subrecipes/script/standard_voicebuild.sh \
        $FEAT_DIRECTORY $LABEL_DIRECTORY $QUESTIONS $OSSIAN/tools/bin/ $OUTPUT \
        $OSSIAN/scripts/acoustic_model_training/subrecipes/config_template/standard_voicebuild.cfg 


.. comment:: $OSSIAN/script/standard_voicebuild.sh ~/temp/ossian-v.1.2/train/rm/speakers/rss_toy_demo/naive/cmp/ ~/temp/ossian-v.1.2/train/rm/speakers/rss_toy_demo/naive/lab/ ~/temp/ossian-v.1.2/train/rm/speakers/rss_toy_demo/naive/questions.hed ~/temp/ossian-v.1.2/tools/bin/  ~/temp/voicetest1/ ./config_template/standard_voicebuild.cfg 

Please modify ``standard_voicebuild.cfg`` or a copy of it to change default settings (e.g. 4 streams, 25 mel cepstral coefficients in the spectrum stream, etc.). ``standard_voicebuild_STRAIGHT.cfg`` is given for use with acoustic features like those used in the `Voice Cloning Toolkit  <http://homepages.inf.ed.ac.uk/jyamagis/software/page37/page37.html>`_.



