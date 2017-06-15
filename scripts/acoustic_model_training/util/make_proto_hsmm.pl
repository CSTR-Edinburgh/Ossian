#!/usr/bin/perl

## History: public HTS -> Junichi's script -> Reima made stream independent -> Oliver
## put in separate script 

$PROTO                 = $ARGV[0];

#@STATICSTREAMSIZES = (31,15,5,1,1,1);   ### HARDCODED for GlotHMM!!!!!!
#@MDSSTREAMINFO     = ( 0,0,0,1,1,1 );
#@STREAMWEIGHTS = ( '1.0', '0.0', '0.0', '1.0', '1.0', '1.0');
# NUMSTREAMS=6

@STATICSTREAMSIZES = (25,1,1,1);   ### HARDCODED for SPTK
@MDSSTREAMINFO     = (0,1,1,1);
@STREAMWEIGHTS = ( '1.0', '1.0', '1.0', '0.9');
$NUMSTREAMS=4;

$NUMSTATE        = 5;                 # number of states for a HMM

make_proto();


# sub routine for generating proto-type model (Copy from HTS-2.1)
sub make_proto {
   my($i, $j, $k, $s);

   # Made stream-independent 23/4/2012 rk
   

   # calculate total number of vectors including delta and delta-delta
 
   $vsize=0;
   for ($n=0;$n<int(@STATICSTREAMSIZES); $n++) 
   {
       if ($MDSSTREAMINFO[$n] == 1) {
	   $vsize += $STATICSTREAMSIZES[$n];
       } else {
	   $vsize += $STATICSTREAMSIZES[$n] * 3;
       }
   }

   # output prototype definition
   # open proto type definition file 
   open(PROTO,">$PROTO") || die "Cannot open $!";

   # output header 
   # output vector size & feature type
   print PROTO "~o <VecSize> $vsize <USER> <DIAGC>";
   
   # output information about multi-space probability distribution (MSD)
   #   print PROTO "<MSDInfo> 5 0 1 1 1 0 ";
   print PROTO "<MSDInfo> ${NUMSTREAMS} ";
   for ($n=0;$n<$NUMSTREAMS;$n++) {
       print PROTO "$MDSSTREAMINFO[${n}] ";
   }
   print PROTO "\n";

   
   # output information about stream
   print PROTO "<StreamInfo> $NUMSTREAMS ";
   for ($n=0;$n<int(@STATICSTREAMSIZES); $n++) 
    {
	if ($MDSSTREAMINFO[$n]==1) {
	    $size = $STATICSTREAMSIZES[$n];
	} else {
	    $size = $STATICSTREAMSIZES[$n]*3;
	}
	printf PROTO " $size";
	
    }
   print PROTO "\n";
#   $vsizestream1 1 1 1 $vsizestream5";
   


   # output HMMs
   print  PROTO "<BeginHMM>\n";
   printf PROTO "  <NumStates> %d\n", $NUMSTATE+2;

   # output HMM states 
   for ($i=2;$i<=$NUMSTATE+1;$i++) {

      # output state information
      print PROTO "  <State> $i\n";

      # output stream weight
      printf PROTO "  <SWeights> %d", int(@STREAMWEIGHTS);
      for ($k=0;$k<int(@STREAMWEIGHTS);$k++) {
	  printf  PROTO " %f", $STREAMWEIGHTS[$k];
      }
      print  PROTO "\n";	      

      
      for ($s=0;$s<int(@STREAMWEIGHTS);$s++) {

	  # output stream 1 information
	  printf  PROTO "  <Stream> %d\n",$s+1;

	  if ($MDSSTREAMINFO[$s]==0) {

	      # output mean vector 
	      printf PROTO "    <Mean> %d\n", 3*$STATICSTREAMSIZES[$s];
	      for ($k=1;$k<=3*$STATICSTREAMSIZES[$s];$k++) {
		  print PROTO "      " if ($k%10==1); 
		  print PROTO "0.0 ";
		  print PROTO "\n" if ($k%10==0);
	      }
	      print PROTO "\n" if ($k%10!=1);
	      
	      # output covariance matrix (diag)
	      printf PROTO "    <Variance> %d\n", 3*$STATICSTREAMSIZES[$s];
	      for ($k=1;$k<=3*$STATICSTREAMSIZES[$s];$k++) {
		  print PROTO "      " if ($k%10==1); 
		  print PROTO "1.0 ";
		  print PROTO "\n" if ($k%10==0);
	      }
	      print PROTO "\n" if ($k%10!=1);
	  } else {

	      # output MSD
	      print  PROTO "  <NumMixes> 2\n";
	      # output 1st space (non 0-dimensional space)
	      # output space weights
	      
	      print  PROTO "  <Mixture> 1 0.5000\n";
	      # output mean vector 
	      printf PROTO "    <Mean> %d\n",1;
	      for ($k=1;$k<=1;$k++) {
		  print PROTO "      " if ($k%10==1); 
		  print PROTO "0.0 ";
		  print PROTO "\n" if ($k%10==0);
	      }
	      print PROTO "\n" if ($k%10!=1);
	      
	      # output covariance matrix (diag)
	      printf PROTO "    <Variance> %d\n", 1;
	      for ($k=1;$k<=1;$k++) {
		  print PROTO "      " if ($k%10==1); 
		  print PROTO "1.0 ";
		  print PROTO "\n" if ($k%10==0);
	      }
	      print PROTO "\n" if ($k%10!=1);
	      
	      # output 2nd space (0-dimensional space)
	      print PROTO "  <Mixture> 2 0.5000\n";
	      print PROTO "    <Mean> 0\n";
	      print PROTO "    <Variance> 0\n";
 
	  }
      }

  }

   # output state transition matrix
   printf PROTO "  <TransP> %d\n", $NUMSTATE+2;
   print  PROTO "    ";
   for ($j=1;$j<=$NUMSTATE+2;$j++) {
      print PROTO "1.000e+0 " if ($j==2);
      print PROTO "0.000e+0 " if ($j!=2);
   }
   print PROTO "\n";
   print PROTO "    ";
   for ($i=2;$i<=$NUMSTATE+1;$i++) {
      for ($j=1;$j<=$NUMSTATE+2;$j++) {
         print PROTO "6.000e-1 " if ($i==$j);
         print PROTO "4.000e-1 " if ($i==$j-1);
         print PROTO "0.000e+0 " if ($i!=$j && $i!=$j-1);
      }
      print PROTO "\n";
      print PROTO "    ";
   }
   for ($j=1;$j<=$NUMSTATE+2;$j++) {
      print PROTO "0.000e+0 ";
   }
   print PROTO "\n";

   # output footer
   print PROTO "<EndHMM>\n";
   close(PROTO);
}      
