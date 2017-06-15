#!/bin/bash
##
## Project: Simple4All - November 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk


#----------------------------------------------------------------------

DIR=$1

[ $# -ne 1 ] && echo "Wrong number of arguments supplied" && exit 1 ;

source $VOICE_BUILD_CONFIG

#----------------------------------------------------------------------





mkdir -p $DIR

cat > $DIR/general.conf<<EOF
NATURALREADORDER      = T
NATURALWRITEORDER     = T
APPLYVFLOOR           = T
VFLOORSCALESTR        = "$VFLOORSCALESTR"
APPLYDURVARFLOOR      = T
DURVARFLOORPERCENTILE = 1.000000
MAXSTDDEVCOEF         = 10
EOF

# VFLOORSCALESTR        = "Vector 5 0.01 0.01 0.01 0.01 0.01"

## Conf to convert engine files specifies non-natural write order (i.e. big-endian) 
## so that the requred big-endian data is produced for hts_engine 
cat > $DIR/engine_convert.conf<<EOF
NATURALREADORDER      = T
NATURALWRITEORDER     = F
APPLYVFLOOR           = T
VFLOORSCALESTR        = "$VFLOORSCALESTR"
APPLYDURVARFLOOR      = T
DURVARFLOORPERCENTILE = 1.000000
MAXSTDDEVCOEF         = 10
EOF


cat > $DIR/general-unfloor.conf<<EOF
NATURALREADORDER      = T
NATURALWRITEORDER     = T
APPLYVFLOOR           = F
APPLYDURVARFLOOR      = F
DURVARFLOORPERCENTILE = 0.000000
MAXSTDDEVCOEF         = 10
EOF

cat > $DIR/clust.conf<<EOF
MINLEAFOCC            =  5
EOF

## SHRINKOCCTHRESH       = "Vector 5  36600.0 2000.0 2000.0 2000.0 6500.0" 

cat > $DIR/clust-dur.conf<<EOF
MINLEAFOCC            = 10
EOF

