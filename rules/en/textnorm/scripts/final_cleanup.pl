#!/usr/bin/perl -w

# Copyright 2012  Arnab Ghoshal
# Modified by Fergus McInnes (FRM), 2013

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# THIS CODE IS PROVIDED *AS IS* BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT LIMITATION ANY IMPLIED
# WARRANTIES OR CONDITIONS OF TITLE, FITNESS FOR A PARTICULAR PURPOSE,
# MERCHANTABLITY OR NON-INFRINGEMENT.
# See the Apache 2 License for the specific language governing permissions and
# limitations under the License.


use strict;
use Unicode::Normalize;
use open ':encoding(utf8)';
# use feature 'unicode_strings';

# Make sure we are reading and writing in UTF-8. 
binmode(STDIN, ":encoding(utf8)");
binmode(STDOUT, ":encoding(utf8)");
binmode(STDERR, ":encoding(utf8)");

my $help_message="USAGE: final_cleanup.pl < in > out\n";

while (<STDIN>) {
  chomp;
  $_ = NFD($_);   # UTF8 decompose

  s/^/ /;
  s/$/ /;

  # Heuristics by FRM to distinguish article "A" from initial "A.":
  s/ A\&/ A. and /g;
  s/ A (ROD|Rod|BAT) / A. $1 /g;
  s/ A A / A. A. /g;
  s/ A A / A. A. /g;
  s/A\. A\. A /A. A. A. /g;
  s/ ([B-Z]) A / $1 A. /g;
  s/ ([B-Z]) A / $1 A. /g;
  s/ A ([A-Z][A-Z])/ a $1/g;  # prevent conversion to "A." in capitalised text
  # Exceptions and default for title case (correct for "Dial A Book" etc, but
  # not for names like "David A Cardona"):
  s/ (Single|Double|Triple|Type|Class|Serie|Series|Group|Model|Avenue|The|An) A / $1 A. /g;
  s/ ([A-Z][a-z\']+) A ([A-Z][a-z])/ $1 a $2/g;
  # Default for "A" in lower-case context:
  s/([a-z\&]) A /$1 A. /g;
  # After a comma, "A Title" keeps "A", but "A P Herbert" or "A to Z" gets "A.":
  s/, A ([^A-Z])/, A. $1/g;
  s/, A ([A-Z] )/, A. $1/g;
  # After any other punctuation, retain "A" with no dot

  # Convert email and Twitter notation:
  s/\@/ at /g;
  #s/ \#(\p{L}+) )/ hashtag $1 /g;  # judged not worth doing for ASR LM
  # "#" on its own is sometimes "number", but not always

  # Remove punctuation:
  s/( [\"\'\-\.\?\!\,\:\;]+)+ / /g;
  s/([^\.])\&/$1 and /g;	# this leaves "A.T.&T." etc unchanged
  s/[\|\$\#\%\*\+\,\^\:\;\?\~\\\/\!]/ /g;  # will handle a**holes incorrectly
  s/\.{2,}/ /g;

  s/\p{M}//g;  # Remove diacritics
  s/[\x{007F}-\x{00BF}]/ /g;  # Remove some other unicode junk
  s/[\x{2190}-\x{21FF}]/ /g;  # Remove arrows

  $_ = lc($_);

  s/(^| )(b|c|d|e|f|g|h|j|k|l|m|n|o|p|q|r|s|t|u|v|w|x|y|z)( |$)/ $2. /g;
  s/(^| )(b|c|d|e|f|g|h|j|k|l|m|n|o|p|q|r|s|t|u|v|w|x|y|z)( |$)/ $2. /g;

  s/^\s*//;  s/\s*$//;  s/\s+/ /g;  # Normalize spaces
  next if /^$/;  # Skip empty lines
  print NFC($_), "\n";  # UTF8 recompose & reorder canonically
}
