#PYTHONPATH=${PYTHONPATH}:/afs/inf.ed.ac.uk/group/project/dnn_tts/tools/site-packages/

#PYTHON=~/my_python
PYTHON=python


## Generic script for submitting any Theano job to GPU
# usage: submit.sh [scriptname.py script_arguments ... ]


## location of this script:
THIS_DIR="$( cd "$( dirname "$0" )" && pwd )"

echo $THIS_DIR

gpu_id=$(python $THIS_DIR/gpu_lock.py --id-to-hog)


if [ $gpu_id -gt -1 ]; then
    #THEANO_FLAGS="cuda.root=/opt/cuda-5.0.35,mode=FAST_RUN,device=gpu$gpu_id,floatX=float32"
    THEANO_FLAGS="cuda.root=/opt/6.5.19,mode=FAST_RUN,device=gpu$gpu_id,floatX=float32,on_unused_input=ignore"
    export THEANO_FLAGS
    
    $PYTHON $@
    
    python $THIS_DIR/gpu_lock.py --free $gpu_id
else
    echo 'Let us wait! No GPU is available!'

fi
