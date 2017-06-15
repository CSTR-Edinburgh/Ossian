# September 2013
#
# OSW: script to process single utterance, assuming GlottHMM features have already
# been extracted. This script adapted from Antti's mkdta_glott.pl  
#


#
#  GlottHMM Analysis and hts feature constuction
#  contact Antti Suni, antti.suni@helsinki.fi
#


#!/usr/bin/perl

## 25 Sept 2012
## Andrei Barbos
## modified so that to be conformant with the naive_scripts for HMM training
## 1st param-> the path to where the application resides, i.e. the is place where the vocoder resides
## 2nd param-> the name of the configuration file for the vocoder
## 3rd param-> the path to where to output the files for the training process
## 4th param-> the path to the folder where the scripts for the model training reside
## 5th param-> the path to where the win files are located
## 6th param-> the path to where the SPTK executables are found



use File::Path;

my ($base, $glott_conf_f, $out_path);

$base = $ARGV[0]; 
$outDir = $ARGV[1];
$scriptDir = $ARGV[2];
$winDir = $ARGV[3];
$SPTK = $ARGV[4];


# print $base ;
# print "=== ===";
# print $glott_conf_f ;
# exit ;

$gvdir = "$outDir/gv";
$cmpdir = "$outDir/cmp";


$|=1;
use File::Basename;
use Cwd;



$NULL_VAL = "-1.0E10";


# Andrei Barbos
## set the content of some variables
$F0	= "F0";  # Fundamental frequency
$LSF1	= "LSF"; # spectral envelope LSFs
$GAIN1	= "Gain"; # gain
$FLOW	= "LSFsource";  # source LSFs
$HNR_I	= "HNR"; # harmonic to noise ratio with bands
%ordr 	= ('LSF' => "31",    # CHANGE ORDER!
	 'LSFsource' => "15",  
	 'HNR' => "5", 
	 'F0' => "1");

@cmp	= ('LSF', 'LSFsource', 'HNR', 'F0');



# Andrei Barbos
# because the HNR variable does not contain anything I will make it to point to the HNR_I variable
# maybe it should have a value of it's own !!!
#$HNR = $HNR_I;




#
# regression windows for culcurate dynamic and accerelation coefficients 
#
$win[0] = "$winDir/mgc.win1";
$win[1] = "$winDir/mgc.win2";
$win[2] = "$winDir/mgc.win3";

$nwin = @win;
$frameshift = 0.005;

$ordr_sum = 0;
for $p (@cmp){
       $ordr_sum+=$ordr{$p};
}
$byte = 4 * $ordr_sum * $nwin;

# Andrei Barbos
# create the cmp folder
# if(-d "$cmpdir"){ # if it exists remove it
# 	rmtree("$cmpdir");
# }
# mkdir "$cmpdir", 0755;

# Andrei Barbos
# 18.10.2012
# in case errors are encountered in the parameter extraction process
# select only those files for which the process returned no errors

# get the wav list for the files for which the analysis process completed

# unless (-e $list_fval) {
#     $cur_dir = getcwd();
#     chdir ("$outDir/wav/");
#     system("ls *.HNR \| sed -e \'s/\.\[a-zA-Z\]\*\$//\' >$list_fval");
#     chdir($cur_dir);
# }
# 
# open UTTSVAL , $list_fval;
# my @uttsv;
# while (<UTTSVAL>) {    
#     	chomp;
#     	my $utt = $_;
#     	push @uttsv, $utt;
# }
# 
# close UTTSVAL;

#
# build feature vectors (cmp)
#


# foreach $base (@uttsv) {
# 
#     next unless $CMP == 1;
#     
    print "constructing $base\.cmp..\n";
    
    
    # LSF: Combine gain and LSFs:
	system("perl $scriptDir/combine_lsf_and_gain.pl $outDir/wav/$utt.LSF ".($ordr{$LSF1}-1)." $outDir/wav/$utt.Gain > $outDir/$LSF1/$utt.$LSF1");
	
	
	
	
    
    # f0 to log scale
    for $type ($F0) { 

        print "$type\n";
	open  PARAM_F, "$outDir/$type/$base.$type" or die "$outDir/$type/$base.$type not found";
	open TMP, ">$outDir/tmp/tmp.$type.log";
	while(<PARAM_F>) {
	    chomp;
	    $val = $_;
	    if ($val == 0) {	
		print TMP "-1.0E10\n";
	    }
	    else {
		$val = log($val);
		print TMP "$val\n";
	    }
	}
	close TMP;
	# to binary
	system("$SPTK/x2x +af  $outDir/tmp/tmp.$type.log > $outDir/tmp/tmp.$type.bin");
	# add delta and acceleration
	system "perl $scriptDir/window.pl $ordr{$type} $outDir/tmp/tmp.$type.bin @win > $outDir/tmp/tmp.$type";

	# global variance statistics
	 system("mkdir -p $gvdir");
	 system("grep -v \\\\-1.0E10 $outDir/tmp/tmp.$type.log | $SPTK/x2x +af | $SPTK/vstat  -l 1  -o 2 -d >> $gvdir/gvdata.$type" );
    }




   # Other acoustic parameters
   for $type (@cmp) {
       next if $type eq $F0;

       print "$type\n";

       #global variance statistics
       system("mkdir -p $gvdir");
	   system "$SPTK/x2x +af $outDir/$type/$base.$type | $SPTK/vstat -n ".($ordr{$type}-1). " -o 2 -d >> $gvdir/gvdata.$type";
       

       # to binary 
       system("$SPTK/x2x +af  $outDir/$type/$base.$type  > $outDir/tmp/tmp.$type.bin");

       #add delta and acceleration
       system "perl $scriptDir/window.pl $ordr{$type} $outDir/tmp/tmp.$type.bin @win > $outDir/tmp/tmp.$type";
   }
   
	



    # merge parameter types to htk feature vectors
  


	$cur_len = $nwin*$ordr{$cmp[0]};
	system("cp $outDir/tmp/tmp.$cmp[0] $outDir/tmp/tmp.cmp");

	for ($i = 0;$i < scalar(@cmp)-1; $i++) {

	    system "$SPTK/merge +f -s 0 -l ".($nwin*$ordr{$cmp[$i+1]})." -L ".$cur_len." $outDir/tmp/tmp.cmp < $outDir/tmp/tmp.$cmp[$i+1] >  $outDir/tmp/tmp2.cmp";
	    $cur_len += $nwin*$ordr{$cmp[$i+1]};
	    system("mv $outDir/tmp/tmp2.cmp $outDir/tmp/tmp.cmp");
	
	    
	}

	# make HTK header
	@STAT = stat "$outDir/tmp/tmp.cmp";

	$size = $STAT[7]/$byte;
	system "echo $size ".($frameshift * 10000000)." | $SPTK/x2x +ai  > $outDir/tmp/tmp.head";
	system "echo $byte 9 | $SPTK/x2x +as >> $outDir/tmp/tmp.head";   # number 9 corresponds to user specified parameter in HTK

	# combine HTK header and sequence of feature vector 
	system "cat $outDir/tmp/tmp.head $outDir/tmp/tmp.cmp > $cmpdir/${base}.cmp";
   



      # 
# 
# 
# # gv stats
# if ($GV) {
#     print "contextless GV..\n";
#     for $type (@cmp) {
#     
# 	system ("$SPTK/vstat -n ".($ordr{$type}-1). " -o 0 -d $gvdir/gvdata.$type >$gvdir/gv-$type.pdf");
# 	system("rm $gvdir/gvdata.$type");
# 
# 
#     }
# }
# print "done.\n";
# 
# 
