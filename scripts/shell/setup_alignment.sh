#!/bin/bash

alignment=$1    
mfcc_list=$2
align_lab_list=$3
lexicon=$4
HTSDIR=$5
n_utts=$6
# OSW added some steps before those of original Multisyn script:


###### setup directory structure, copy in data:
if [ ! -d $alignment ] ; then
    mkdir $alignment
fi



# copy training lists -- set n_utts to train on a subset then align the whole set (0 means train on all)
if [ $n_utts -gt 0 ] ;
    then
     head -$n_utts $mfcc_list | gsort -R > $alignment/train.scp  ## -R sort by has value -- too many homogenous utts together is rumoured to break HERest...
     head -$n_utts $align_lab_list > $alignment/label.scp
else
    cat $mfcc_list | gsort -R > $alignment/train.scp  ## -R sort by has value -- too many homogenous utts together is rumoured to break HERest...
    cp $align_lab_list $alignment/label.scp
fi

cp $mfcc_list $alignment/full_train.scp
cp $align_lab_list $alignment/full_label.scp
  

## make initial MLF from initial labels:


rm -rf $alignment/null.hed
touch $alignment/null.hed
$HTSDIR/HLEd -A -D -T 1 -V -l '*'   -i $alignment/words.mlf -S $alignment/full_label.scp $alignment/null.hed
rm -rf $alignment/null.hed


## copy in lexicon:
cp $lexicon $alignment/all.lex

## make phone list from lexicon:
## exclude column 1    ...     1 phone per line  ...  unique list
echo "$alignment/all.lex"

#does not work with mac's sed -- need to use gsed : echo "cat dog" |sed 's/ /\n/g' : catndog
cut -f2- -d ' ' $alignment/all.lex | gsed 's/ /\n/g'   |    sort -u  > $alignment/phone_list

cut -f2- -d ' ' $alignment/all.lex | gsed -e 's/ /\'$'\n/g'   |    sort -u  > $alignment/phone_list




# create resource files
echo "CREATING RESOURCE FILES"
mkdir -p $alignment/resources
mkdir -p $alignment/proto


echo "MU 2 {*.state[2-4].mix}" > $alignment/resources/mixup2.hed
echo "MU 3 {*.state[2-4].mix}" > $alignment/resources/mixup3.hed
echo "MU 5 {*.state[2-4].mix}" > $alignment/resources/mixup5.hed
echo "MU 8 {*.state[2-4].mix}" > $alignment/resources/mixup8.hed

cat > $alignment/resources/tie_silence.hed<<EOF
 AT 2 4 0.2 {sil.transP}
 AT 4 2 0.2 {sil.transP}
 AT 1 3 0.3 {sp.transP}
 TI silst {sil.state[3],sp.state[2]}
EOF

cat > $alignment/config<<EOF
NATURALREADORDER      = T
NATURALWRITEORDER     = T
EOF


cat > $alignment/proto/5states<<EOF
~o <VecSize> 39 <MFCC_E_D_A> <DIAGC> <NULLD>
<BeginHMM>
<NumStates> 7 <StreamInfo> 1 39 <VecSize> 39
<State> 2
<Mean> 39
0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0
0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0
<Variance> 39
1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0
1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0
<State> 3
<Mean> 39
0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0
0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0
<Variance> 39
1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0
1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0
<State> 4
<Mean> 39
0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0
0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0
<Variance> 39
1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0
1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0
<State> 5
<Mean> 39
0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0
0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0
<Variance> 39
1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0
1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0
<State> 6
<Mean> 39
0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0
0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0
<Variance> 39
1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0
1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0
<TransP> 7
0.0 1.0 0.0 0.0 0.0 0.0 0.0
0.0 0.5 0.5 0.0 0.0 0.0 0.0 
0.0 0.0 0.5 0.5 0.0 0.0 0.0 
0.0 0.0 0.0 0.5 0.5 0.0 0.0 
0.0 0.0 0.0 0.0 0.5 0.5 0.0
0.0 0.0 0.0 0.0 0.0 0.5 0.5
0.0 0.0 0.0 0.0 0.0 0.0 0.0
<EndHMM>
EOF

cat > $alignment/proto/3states<<EOF
~o <VecSize> 39 <MFCC_E_D_A> <DIAGC> <NULLD>
<BeginHMM>
<NumStates> 3 <StreamInfo> 1 39 <VecSize> 39
<State> 2
<Mean> 39
0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0
0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0
<Variance> 39
1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0
1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0
<TransP> 3
0.0 1.0 0.0
0.0 0.5 0.5
0.0 0.0 0.0
<EndHMM>
EOF

cat > $alignment/proto/3statesnull<<EOF
~o <VecSize> 39 <MFCC_E_D_A> <DIAGC> <NULLD>
~h "#1"
<BeginHMM>
<NumStates> 3 <StreamInfo> 1 39 <VecSize> 39
<State> 2
<Mean> 39
0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0
0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0
<Variance> 39
1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0
1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0
<TransP> 3
0.0 0.0 1.0
0.0 0.5 0.5
0.0 0.0 0.0
<EndHMM>
~h "#2"
<BeginHMM>
<NumStates> 3 <StreamInfo> 1 39 <VecSize> 39
<State> 2
<Mean> 39
0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0
0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0
<Variance> 39
1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0
1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0
<TransP> 3
0.0 0.0 1.0
0.0 0.5 0.5
0.0 0.0 0.0
<EndHMM>
~h "."
<BeginHMM>
<NumStates> 3 <StreamInfo> 1 39 <VecSize> 39
<State> 2
<Mean> 39
0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0
0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0
<Variance> 39
1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0
1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0
<TransP> 3
0.0 0.0 1.0
0.0 0.5 0.5
0.0 0.0 0.0
<EndHMM>
EOF


##echo "Please create \`phone_list' and \`phone_substitutions' in $alignment before continuing."
