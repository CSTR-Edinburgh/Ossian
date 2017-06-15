#args
# 1: lsf 2: lsf coeff count 3: gain


$DIM = $ARGV[1];
open GAIN, $ARGV[2];
@gain = <GAIN>;
close GAIN;
$i = 1;
open LSF, "$ARGV[0]";
while (<LSF>){

    print;
    if ($i % $DIM == 0) {
	print shift @gain;
    }
    $i++;

}
close LSF;
