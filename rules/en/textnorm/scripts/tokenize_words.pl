#!/usr/bin/perl -w

# Copyright 2012  Arnab Ghoshal
# (with modifications by Fergus McInnes (FRM), 2013)

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

# This script separates out most of the punctuation symbols from "words" except:
#   - . , + - etc. within numbers
#   - when a ' at the end of a word is preceded by an s (may be possessive)
# These need to be handled in a later processing stage.

use strict;
use Unicode::Normalize;
use open ':encoding(utf8)';
# use feature 'unicode_strings';

# Make sure we are reading and writing in UTF-8. 
binmode(STDIN, ":encoding(utf8)");
binmode(STDOUT, ":encoding(utf8)");
binmode(STDERR, ":encoding(utf8)");

my $help_message="USAGE: tokenize_words.pl abbrevs tlds hyphenated < in > out\n";
die "$help_message" if (scalar(@ARGV) != 3);

my $abbrev_file = $ARGV[0];
my $tld_file = $ARGV[1];
my $hyphenated_file = $ARGV[2];
my %abbrev_map = ();     # List of all abbreviations
my %is_rc_context = ();  # List of left contexts for Roman cardinals
my %is_tld = ();         # List of all top-level domain names
my %is_hyphenated = ();  # List of all hyphenated words that will be preserved

&load_abbrevs($abbrev_file, \%abbrev_map, \%is_rc_context);
&load_tlds($tld_file, \%is_tld);
&load_hyphenated($hyphenated_file, \%is_hyphenated);

while (<STDIN>) {
  chomp;
  $_ = NFD($_);   # UTF8 decompose

  # Process some special cases and symbols:
  s/^IT /It /;  # Otherwise gets converted to I.T.
  s/^AT /At /;  # Otherwise gets converted to A.T.
  s/^HE /He /;  # Otherwise gets converted to H.E. if in abbrev_map
  s/([^,] Me)\./$1 ./g;  # Otherwise gets converted to Maine
  s/(^| )Md (\p{Lu}\p{Ll})/ Muhammad $2/g;  # Md. not converted here: usually "Maryland" in non-Malaysian data
  s/(^| )Muhd\.? (\p{Lu}\p{Ll})/ Muhammad $2/g;
  s/(^| )Mohd\.? (\p{Lu}\p{Ll})/ Mohammed $2/g;
  s/(^| )\#(\d+)(-| )/ number $2$3/g;
  s/(\p{Lu})\.(\p{Lu})\s*\.? /$1.$2. /g;
  s/(\p{Lu})\.\& (\p{Lu}\.?'?s?) /$1.&$2 /g;
  s/(^| )(\p{Lu})\.(-| )/ $2.$3/g;
  s/\s((USD|AED|CHF|Sw?F|D[Hh]s?|EUR|GBP|RMB|Rmb|Rs|Rp|(US|C|CDN|NZ|HK|NT|Z|A)?\$|\x{00A3}|\x{FFE1}|\x{00A5}|\x{20AC})?[\d\.,]*\d)\/(\p{L}+)/ $1 per $+/g;
  s/(^| )([Ee])\-([Mm][Aa][Ii][Ll])/ $2$3/g;
  s/(^| )C\-SPAN(\W)/ C.Span$2/g;
  s/(^| )Bre\-X(\W)/ Bre.X.$2/g;
  s/(^| )V\-8/ V8/g;
  s/(^| )V\-6/ V6/g;
  s/(^| )V\-12/ V12/g;
  s/(^| )G\-(\d)/ G$2/g;
  s/(^| )(\d)\-D(\W)/ $2D$3/g;
  s/(^| )C[O0]\^2\s/ CO2 /g;
  s/(^| )C02\s/ CO2 /g;
  s/(^| )MC\^?2\s/ m c squared /gi;
  s/(\p{L}|\d)\s*\+\s*(\p{L}|\d)/$1 plus $2/g;
  s/(\p{L}|\d)\s*\+\s*(\p{L}|\d)/$1 plus $2/g;  # repeated for "A+B+C" etc
  s/(^| )W\.?W\.? I/ WWI/g;  # otherwise becomes "WW one" etc instead of "World War ..."
  s/(^| )3M share/ three.M. share/g;  # otherwise becomes "three million"
  s/(^| )a k a / a.k.a. /gi;
  s/Det\.?\s*Ch\.?\s*Insp\.?\s/Detective Chief Inspector /g;
  s/Ch\.?\s*Insp\.?\s/Chief Inspector /g;
  s/Det\.?\s*Insp\.?\s/Detective Inspector /g;
  s/Det\.?\s*Ch\.?\s*Supt\.?\s/Detective Chief Superintendent /g;
  s/Ch\.?\s*Supt\.?\s/Chief Superintendent /g;
  s/Det\.?\s*Supt\.?\s/Detective Superintendent /g;
  s/(^| )AS Roma(\s|-)/ A.S. Roma$1/g;
  s/,\s+Ct\. /, Connecticut /g;  # otherwise becomes "Court"
  s/\s([DR])-(Back|Class|Day|Fenders?|League|List|Luxe?|Light|Lite|Major|Mark|Mart|Major|Max|Mode|Plan|Ram|Rated|Ray|Series|Type|War)(\'?s?\'?)\s/ $1.$2$3 /g;  # exceptions to next
  s/\sD-(\p{Lu}[\p{Ll}\.])/ Democrat , $1/g;
  s/\sR-(\p{Lu}[\p{Ll}\.])/ Republican , $1/g;
  s/(^| )\+ve\s/ positive /g;
  s/(^| )\-ve\s/ negative /g;
  s/(^| )HIV\s*\+\s/ HIV positive /g;
  s/(\p{Lu})\+\s/$1 plus /g;
  s/(^| )BB[-\s](rating|rated|plus|minus)/ double B. $2/g;
  s/(^| )CCC[-\s](rating|rated|plus|minus)/ triple C. $2/g;
  s/(\d)\s*([AP])\.?M\.?\s/$1 $2.M. /g;
  s/(\d)\s*([ap])\.?m\.?\s/$1 $2.m. /g;
  s/(\d)(k|m|bn|tn)-([\$\x{00A3}\x{FFE1}\x{00A5}\x{20AC}])/$1$2 to $3/gi;
  s/(\d)(k|m|bn|tn)-/$1$2 /gi;
  s/(\d)\s*[Mm]ln\.?\s/$1 million /g;
  s/(\d)\s*[Bb]ln\.?\s/$1 billion /g;
  s/(\d)\s*[Tt]rln\.?\s/$1 billion /g;
  s/(\d)\s*[Bb][Nn]\.?\s/$1 billion /g;
  s/(\d)\s*[Tt][Nn]\.?\s/$1 trillion /g;
  s/(\d)(million|billion|trillion|percent|per )/$1 $2/g;
  s/(\d) per cent /$1 percent /g;  # seems to be right most of time
  s/(^| )A\* / A.star /g;
  s/[\x{2665}\x{2764}]/ love /g;  # heart: could be "love" or "heart(s)"
  # repeated currency symbols:
  s/(^| )\${2,}\'?s?\s+([^\s\d])/ dollars $2/g;
  s/(^| )\x{00A3}{2,}\'?s?\s+([^\s\d])/ pounds $2/g;
  s/(^| )\x{20AC}{2,}\'?s?\s+([^\s\d])/ euros $2/g;
  s/(^| )\${2,}\s*(\d)/ \$$2/g;
  s/(^| )\x{00A3}{2,}\s*(\d)/ \x{00A3}$2/g;
  s/(^| )\x{20AC}{2,}\s*(\d)/ \x{20AC}$2/g;
  s/(\d)1\/2(\s|-)/$1 1\/2$2/g;  # right most of time, but not for odds "11/2"
  s/(\d)-in\.?\s/$1-inch /g;

  # Change hyphens after numbers so that "100-km" etc are converted correctly
  # (but exempt things like "1-800-Flowers" to get right results in numproc):
  s/(^| )(1-\d\d\d)-/ $2__/g;
  s/(\d)-(\p{L})/$1 $2/g;
  s/__/-/g;

  # Rate units (with "per") (could alternatively go in numproc):
  s/(\d)\s*g\/t\s/$1 grams per tonne /g;
  s/(\d)\s*m\s*b\/d\s/$1 million barrels per day /gi;
  s/(\d)\s*MM\s*bbls?\/(d|day)\s/$1 million barrels per day /gi;
  s/(\d|\s)bbls?\/(d|day)\s/$1 barrels per day /gi;
  s/(\d)\s*b\/(d|day)\s/$1 barrels per day /g;
  s/(\d)\s*MM\s*cfe\/d\s/$1 million cubic feet equivalent per day /gi;
  s/(\d)\s*M\s*cfe\/d\s/$1 thousand cubic feet equivalent per day /gi;
  s/(\d)\s*MM\s*cf\/d\s/$1 million cubic feet per day /gi;
  s/(\d)\s*M\s*cf\/d\s/$1 thousand cubic feet per day /gi;
  s/bits?\/s\s/bits per second /g;
  s/Mb\/s\s/megabits per second /g;
  s/[Mm]bps\s/megabits per second /g;
  s/Gb\/s\s/gigabits per second /g;
  s/MB\/s\s/megabytes per second /g;
  s/GB\/s\s/gigabytes per second /g;
  s/(\d)\s*g\.?\/(\p{L})/$1 grams per $2/g;
  s/(\d)\s*mi\.?\/(\p{L})/$1 miles per $2/g;
  s/\/\s*hr?\.?\s/ per hour /g;
  s/\/\s*min\.?\s/ per minute /g;
  s/\/\s*sec\.?\s/ per second /g;
  s/(\/\s*| per )[Kk][Mm]\.?2\s/ per square kilometer /g;
  s/(\/\s*| per )m\.?2\s/ per square meter /g;
  s/(\/\s*| per )m\.?3\s/ per cubic meter /g;
  s/(\/\s*| per )[Kk][Mm]\.?\s/ per kilometer /g;
  s/(\/\s*| per )ft\.?\s/ per foot /g;
  s/(\/\s*| per )sq\.?\s*ft\.?\s/ per square foot /g;
  s/(\/\s*| per )lb\.?\s/ per pound /g;
  s/(\/\s*| per )oz\.?\s/ per ounce /g;
  s/(\/\s*| per )g\.?\s/ per gram /g;
  s/(\/\s*| per )[Kk]g\.?\s/ per kilogram /g;
  s/ a [Kk]g\.?\s/ a kilogram /g;
  s/(\/\s*| per )mg\.?\s/ per milligram /g;
  s/(\/\s*| per )kWh\.?\s/ per kilowatt hour /gi;
  s/(\/\s*| per )MWh\.?\s/ per megawatt hour /gi;
  s/(\/\s*| per )bbl\.?\s/ per barrel /gi;
  s/(\/\s*| per )Mcfe\.?\s/ per thousand cubic feet equivalent /gi;
  s/(\/\s*| per )Mcf\.?\s/ per thousand cubic feet /gi;
  s/\/\s*(second|minute|hour|day|week|month|year)\s/ per $1 /gi;
  s/\/\s*(share|ton|tonne|barrel|pound|ounce|[a-z]*gram)\s/ per $1 /gi;

  # Other special cases involving "/":
  s?(^| )AD/SAT\s? AD__SAT ?g;
  s?(^| )c/o\s? care of ?g;
  s?(^| )he/she\s? he or she ?g;
  s?(^| )his/her\s? his or her ?g;
  s?(^| )is/are\s? is or are ?g;
  s?(^| )is/was\s? is or was ?g;
  s?(^| )s/he\s? she or he ?g;
  s?(^| )was/is\s? was or is ?g;
  s?(^| )A/V\s? AV ?g;
  s/Minneapolis\/St\.?\s/Minneapolis Saint /g;
  # URLs:
  s?\.(\S*)/ ?.$1 ?g;
  s?\.(\S*)/?.$1__?g;
  s?\.(\S*)/?.$1__?g;
  s?\.(\S*)/?.$1__?g;
  s?\.(\S*)/?.$1__?g;
  s?\.(\S*)/?.$1__?g;

  # Convert remaining slashes to spaces except in numeric expressions:
  s?(\D)/+(.)?$1 $2?g;
  s?(\d)/+(\D)?$1 $2?g;
  s?__?/?g;

  # Units of measurement (could alternatively go in numproc):
  s/([023456789])\s*st\.?\s/$1 stones /g;
  s/\s11\s*st\.?\s/ 11 stones /g;
  s/(\d)\s*lb\.?\s/$1 pound /g;
  s/(\d)\s*lbs\.?\s/$1 pounds /g;
  s/(\d)\s*fl\.*\s+oz\.?\s/$1 fluid ounce /g;
  s/(\d)\s*fl\.*\s+ozs\.?\s/$1 fluid ounces /g;
  s/(\d)\s*oz\.?\s/$1 ounce /g;
  s/(\d)\s*ozs\.?\s/$1 ounces /g;
  s/(\d)\s*cwt\.?\s/$1 hundredweight /g;
  s/(^| )(1|one)\s*Mt\.?\s/ $2 megatonne /g;
  s/(\d)\s*Mt\.?\s/$1 megatonnes /g;
  s/(^| )(1|one)\s*[Kk]g\.?\s/ $2 kilogram /g;
  s/(\d|[mbr]illion)\s*[Kk]gs?\.?\s/$1 kilograms /g;
  s/(^| )(1|one)\s*mg\.?\s/ $2 milligram /g;
  s/(\d)\s*mg\.?\s/$1 milligrams /g;
  s/(^| )(1|one)\s*g\.?\s/ $2 gram /g;
  s/(^| )(\d[\d\.,]*)\s*g\.?\s/ $2 grams /g;
  s/(^| )(1|one)\s*dwt\.?\s/ $2 deadweight ton /gi;
  s/(^| )(of|up|total\p{L}*)\s+(\d[\d\.,]*)\s*dwt\.?\s/ $2 $3 deadweight tons /gi;
  s/(^| )(\d[\d\.,]*)\s*dwt\.?\s/ $2 deadweight ton /gi;
  s/(^| )(\d[\d\.,]*)\s*dwts\.?\s/ $2 deadweight tons /gi;
  s/(^| )(1|one|24)\s*hr\.?\s/ $2 hour /g;
  s/(\d)\s*hrs?\.?\s/$1 hours /g;
  s/(^| )(1|one)\s*min\.?\s/ $2 minute /g;
  s/(\d)\s*mins?\.?\s/$1 minutes /g;
  s/(^| )(1|one)\s*sec\.?\s/ $2 second /g;
  s/(\d)\s*secs?\.?\s/$1 seconds /g;
  s/(\d)\s*Hz\.?\s/$1 hertz /g;
  s/(\d)\s*[Kk]Hz\.?\s/$1 kilohertz /g;
  s/(\d)\s*MHz\.?\s/$1 megahertz /g;
  s/(\d)\s*GHz\.?\s/$1 gigahertz /g;
  s/(\d)\s*THz\.?\s/$1 terahertz /g;
  s/(\d)\s*[Kk](b\.?|bits?)\s/$1 kilobits /g;
  s/(\d)\s*M(b\.?|bits?)\s/$1 megabits /g;
  s/(\d)\s*G(b\.?|bits?)\s/$1 gigabits /g;
  s/(\d)\s*T(b\.?|bits?)\s/$1 terabits /g;
  # "GB" etc often adjectival, so don't pluralise:
  s/(\d)\s*MB\.?\s/$1 megabyte /g;
  s/(\d)\s*GB\.?\s/$1 gigabyte /g;
  s/(\d)\s*TB\.?\s/$1 terabyte /g;
  s/(\d)\s*Kbyte/$1 kilobyte/gi;
  s/(\d)\s*Mbyte/$1 megabyte/gi;
  s/(\d)\s*Gbyte/$1 gigabyte/gi;
  s/(\d)\s*Tbyte/$1 terabyte/gi;
  s/(\d)\s*[kK][Ww]\.?\s+(of|in|at|by|to|a|per)\s/$1 kilowatts $2 /g;
  s/\s(of|to)\s+(\d[\d,\.]*)\s*[kK][Ww]\.?\s/ $1 $2 kilowatts /g;
  s/(\d)\s*[kK][Ww]\.?\s(\W)*$/$1 kilowatts $2/g;
  s/(\d)\s*[kK][Ww]\.?\s/$1 kilowatt /g;
  s/(^| )(1|one) kilowatts / $2 kilowatt /g;
  s/(\d)\s*MW\.?\s+(of|in|at|by|to|a|per)\s/$1 megawatts $2 /g;
  s/\s(of|to)\s+(\d[\d,\.]*)\s*MW\.?\s/ $1 $2 megawatts /g;
  s/(\d)\s*MW\.?\s/$1 megawatt /g;
  s/(^| )(1|one) megawatts / $2 megawatt /g;
  s/(^| )4GW(\W)/ four.G.W.$2/g;  # special case: can be "4th generation war"
  s/(\d)\s*GW\.?\s+(of|in|at|by|to|a|per)\s/$1 gigawatts $2 /g;
  s/\s(of|to)\s+(\d[\d,\.]*)\s*GW\.?\s/ $1 $2 gigawatts /g;
  s/(\d)\s*GW\.?\s/$1 gigawatt /g;
  s/(^| )(1|one) gigawatts / $2 gigawatt /g;
  s/(\d|\s)[Kk][Ww]hs?\s/$1 kilowatt hours /g;
  s/(\d|\s)[Mm][Ww]hs?\s/$1 megawatt hours /g;
  s/(\d|\s)[Gg][Ww]hs?\s/$1 gigawatt hours /g;
  s/(\d|\s)[Tt][Ww]hs?\s/$1 terawatt hours /g;
  s/(\d)\s*[Mm][Mm]bbls?\s/$1 million barrels /g;
  s/(\d)\s*[Mm]bbls?\s/$1 thousand barrels /g;
  s/(\d|\s)bbls?\s/$1 barrels /g;
  s/(\d|\s)boe\s/$1 barrels of oil equivalent /gi;
  s/(\d)\s*[Mm][Bb][Dd]\s/$1 million barrels a day /g;  # seems to be common usage e.g. in Gigaword afp_eng_* data, contrary to Wikipedia
  s/(\d)\s*[Bb]cfe\s/$1 billion cubic feet equivalent /g;
  s/(\d)\s*[Mm][Mm]cfe\s/$1 million cubic feet equivalent /g;
  s/(\d)\s*[Mm]cfe\s/$1 thousand cubic feet equivalent /g;
  s/(\d)\s*[Bb]cf\s/$1 billion cubic feet /g;
  s/(\d)\s*[Mm][Mm]cf\s/$1 million cubic feet /g;
  s/(\d)\s*[Mm]cf\s/$1 thousand cubic feet /g;
  s/\s1\s*ml\.?\s/ 1 millilitre /g;
  s/(\d)\s*ml\.?\s/$1 millilitres /g;
  s/\s(\d\/\d|1)\s*tsp\.?\s/ $1 teaspoon /g;
  s/(\d)\s*tsp\.?\s/$1 teaspoons /g;
  s/\s(\d\/\d|1)\s*tbsp\.?\s/ $1 tablespoon /g;
  s/(\d)\s*tbsp\.?\s/$1 tablespoons /g;
  s/(\d|illion|thousand|hundred)\s*sq\.?\s?(foot|feet|inch|inches|meters?|metres?|miles?)\s/$1 square $2 /g;
  s/(\d|illion|thousand|hundred)\s*cu\.?\s?(foot|feet|inch|inches|meters?|metres?|miles?)\s/$1 cubic $2 /g;
  s/((the|a)\s+[\d,\.]+\d)\s*sq(\.\s?|\s)ft\.?\s/$1 square foot /g;
  s/((the|a)\s+[\d,\.]+\d)\s*cu(\.\s?|\s)ft\.?\s/$1 cubic foot /g;
  s/((the|a)\s+[\d,\.]+\d)\s*sq(\.\s?|\s)in\.?\s/$1 square inch /g;
  s/((the|a)\s+[\d,\.]+\d)\s*sq(\.\s?|\s)m\.?\s/$1 square meter /g;
  s/((the|a)\s+[\d,\.]+\d)\s*cu(\.\s?|\s)m\.?\s/$1 cubic meter /g;
  s/((the|a)\s+[\d,\.]+\d)\s*sq(\.\s?|\s)[Kk][Mm]\.?\s/$1 square kilometer /g;
  s/((the|a)\s+[\d,\.]+\d)\s*[Kk][Mm]\.?2\s/$1 square kilometer /g;
  s/((the|a)\s+[\d,\.]+\d)\s*m\.?2\s/$1 square meter /g;
  s/((the|a)\s+[\d,\.]+\d)\s*m\.?3\s/$1 cubic meter /g;
  s/((the|a)\s+[\d,\.]+\d)\s*ha\.?\s/$1 hectare /g;
  s/(\d|illion|thousand|hundred)\s*sq(\.\s?|\s)ft\.?\s/$1 square feet /g;
  s/(\d|illion|thousand|hundred)\s*cu(\.\s?|\s)ft\.?\s/$1 cubic feet /g;
  s/(\d|illion|thousand|hundred)\s*sq(\.\s?|\s)in\.?\s/$1 square inches /g;
  s/(\d|illion|thousand|hundred)\s*sq(\.\s?|\s)m\.?\s/$1 square meters /g;
  s/(\d|illion|thousand|hundred)\s*cu(\.\s?|\s)m\.?\s/$1 cubic meters /g;
  s/(\d|illion|thousand|hundred)\s*sq(\.\s?|\s)[Kk][Mm]s?\.?\s/$1 square kilometers /g;
  s/(\d|illion|thousand|hundred)\s*[Kk][Mm]s?\.?2\s/$1 square kilometers /g;
  s/(\d|illion|thousand|hundred)\s*m\.?2\s/$1 square meters /g;
  s/(\d|illion|thousand|hundred)\s*m\.?3\s/$1 cubic meters /g;
  s/(\d|illion|thousand|hundred)\s*ha\.?\s/$1 hectares /g;
  # distances often adjectival, so use singular unless explicitly plural unit
  # or contextual cue (including being sentence-final):
  s/ (\d+)\s*ft\.?\s*(\d+)\s+in\.?[\-\s](tall|long|wide|high|deep)\s/ $1 feet $2 inches $3 /g;
  s/ (\d+)\s*ft\.?\s*(\d+)ins?\.?\s/ $1 feet $2 inches /g;
  s/(\d)\s*ft\.?\s(tall|long|wide|high|deep|away|from|of|up|down|above|below)\s/$1 feet $2 /g;
  s/(\d)\s*ft\.?\-(tall|long|wide|high|deep)\s/$1 foot $2 /g;
  s/(\s[\d\.,]*\d)\s*m\.?\s(tall|long|wide|high|deep|away|from|above|below)\s/$1 meters $2 /g;
  s/(\d)\s*m\.?\-(tall|long|wide|high|deep)\s/$1 meter $2 /g;
  s/(\d)\s*[Kk][Mm]\.?\-(tall|long|wide|high|deep)\s/$1 kilometer $2 /g;
  s/(\s[\d\.,]*\d)\s*m\.?\s(pool)\s/$1 meter $2 /g;
  s/(\d)\s*ft\.?\s(\W*)$/$1 feet $2/g;
  s/(\d)\s*ft\.?\s([\.\?]\s)/$1 feet $2/g;
  s/(\d)in\.?\s(\W*)$/$1 inches $2/g;
  s/(\d)in\.?\s([\.\?]\s)/$1 inches $2/g;
  s/ 1 feet / 1 foot /g;
  s/ 1 inches / 1 inch /g;
  s/ 1 meters / 1 meter /g;
  s/(\d)\s*ft\.?\s/$1 foot /g;
  s/(\d)in\.?\s/$1 inch /g;
  s/(\d)ins\.?\s/$1 inches /g;
  s/(^| )(1|one)\s*[Kk][Mm]\.?\s/ one kilometer /g;
  s/(\d|\s)[Kk][Mm]s\.?\s/$1 kilometers /g;
  s/(\d|\s)[Kk][Mm]\.?\s+(north|south|east|west|away|from|per|long|wide|up|down|out(side)?|above|below)/$1 kilometers $2/g;
  s/(\d|\s)km\.?\s(\W*)$/$1 kilometers $2/g;
  s/(\d)\s*[Kk][Mm]\.?\s(\W*)$/$1 kilometers $2/g;
  s/(\d|\s)cm\.?\s(\W*)$/$1 centimeters $2/g;
  s/(\d|\s)mm\.?\s(\W*)$/$1 millimeters $2/g;
  s/(\d|\s)nm\.?\s(\W*)$/$1 nanometers $2/g;
  s/(\d|\s)km\.?\s([\.\?]\s)/$1 kilometers $2/g;
  s/(\d)\s*[Kk][Mm]\.?\s([\.\?]\s)/$1 kilometers $2/g;
  s/(\d|\s)cm\.?\s([\.\?]\s)/$1 centimeters $2/g;
  s/(\d|\s)mm\.?\s([\.\?]\s)/$1 millimeters $2/g;
  s/(\d|\s)nm\.?\s([\.\?]\s)/$1 nanometers $2/g;
  s/(\d|\s)km\.?\s/$1 kilometer /g;
  s/(\d)\s*[Kk][Mm]\.?\s/$1 kilometer /g;
  s/(\d)\s*cms\.?\s/$1 centimeters /g;
  s/(\d)\s*cm\.?\s/$1 centimeter /g;
  s/(\d)\s*mm\.?\s/$1 millimeter /g;
  s/(\d)\s*nm\.?\s/$1 nanometer /g;
  s/(\d)\s*pc\.?\s/$1 percent /g;
  s/(\d)\s*pct\s/$1 percent /g;
  s/(^| )([Tt]he|men's|women's|run|ran|[Ww]orld) ([\d,]+00|50|60|110)m\.? / $2 $3 meters /g;
  s/([0-9]x[0-9]+)m\.? /$1 meters /g;
  s/(^| )(meters ?,?) ([\d,]+)m\.? / $2 $3 meters /g;
  s/(^| )(meters and) ([\d,]+)m\.? / $2 $3 meters /g;
  s/(^| )([\d,]+00|50|60|110)m\.? (race|relay|freestyle|backstroke|breaststroke|butterfly|(individual )?medley|steeplechase|hurdles|([Ww]orld )?(champion|record|title|final)|runner|gold|silver|bronze|[Oo]lympic|victory)/ $2 meters $3/g;
  s/(^| )([\d,]+)m\.? (and [\d,]+ meters)/ $2 meters $3/g;
  s/(^| )([\d,]+)m\.? (,? ?[\d,]+ meters)/ $2 meters $3/g;
  s/(\d)\s*b\.?p\.?\s(rise|fall|cut|hike|increase|reduction)\s/$1 basis point $2 /g;
  s/\s1\s*b\.?p\.?\s/ 1 basis point /g;
  s/(^| )([\d,\.\-]*\d)\s*b\.?p\.?s?\s/ $2 basis points /g;
  s/(\d)mph\s/$1 mph /gi;
  s/(\d)kph\s/$1 kph /gi;
  s/(\d)mpg\s/$1 mpg /gi;
  s/(\d)\s*dpb\s/$1 dollars per barrel /g;
  s/(^| )([\+\-]?[\d,\.\-]*\d)C\s/ $2 C /g;
  s/(^| )([\+\-]?[\d,\.\-]*\d)F\s/ $2 F /g;
  s/(^| )Win2[Kk]\s/ Win.two.K. /g; # exception to next
  s/(^| )Y2[Kk]\s/ Y.two.K. /g; # exception to next
  s/(^| )([\+\-]?[\d,\.\-]*\d)K\s/ $2 K /g;
  s/(^| )([\+\-]?[\d,\.\-]*\d)k\s/ $2 k /g;
  s/(^| )1080p\s/ ten.eighty.p. /g; # exception to next
  s/(^| )720p\s/ seven.twenty.p. /g; # exception to next
  s/(^| )([\+\-]?[\d,\.\-]*\d)p\s/ $2 p /g;
  s/\s+/ /g;

  # Abbreviations specific to context with following number:
  s/(^| )p\.?\s*(\d)/ page $2/g;
  s/(^| )pp\.?\s*(\d)/ pages $2/g;
  s/(^| )[Cc]h\.?\s*(\d)/ chapter $2/g;
  s/(^| )[Nn][Oo]\.?(\d)/ number $2/g;
  s/(^| )[Nn][Oo]\.\s+(\d)/ number $2/g;

  if (/school|class|child|pupil|teacher/i) { # exception to "Y" meaning "yen"
    s/ Y(\d|1\d)(\D\D)/ year $1$2/gi;
  }

  # Attach separated currency symbols and codes, and normalise non-standard codes:
  s/( |^)[Dd]lrs\.?\s*(\d)/ \$$2/g;
  s/( |^)U\.S\.\s+(\$|[Dd]lrs)/ US $2/g;
  s/( |^)N\.Z\. / NZ /g;
  s/( |^)H\.K\. / HK /g;
  s/( |^)N\.T\. / NT /g;
  s/( |^)(US|C|CDN|NZ|HK|NT|Z)\s+\$\s*(\d)/ $2\$$3/g;  # don't include "A $": too many false positives
  s/( |^)(US|C|CDN|NZ|HK|NT|Z|A)\$\s*(\d)/ $2\$$3/g;
  s/( |^)USD\s+(\d)/ USD$2/g;
  s/( |^)AED\s+(\d)/ AED$2/g;
  s/( |^)CHF\s+(\d)/ CHF$2/g;
  s/( |^)Sw?Fr\s*(\d)/ CHF$2/g;
  s/( |^)D[Hh]s?\s*(\d)/ Dh$2/g;
  s/( |^)EUR\s+(\d)/ EUR$2/g;
  s/( |^)GBP\s+(\d)/ GBP$2/g;
  s/( |^)RMB\s+(\d)/ RMB$2/g;
  s/( |^)Rmb\s*(\d)/ RMB$2/g;
  s/( |^)[Rr]s\s+(\d)/ Rs$2/g;
  s/( |^)[Rr]p\s+(\d)/ Rp$2/g;
  s/( |^)RP\s*(\d[\d,\.]*\s*(m|b|tr)illion)/ Rp$2/gi;
  s/( |^)RM\s+(\d)/ RM$2/g;
  s/([Ff]light|[Nn]umber) TK\s*(\d)/$1 _TK$+/g;  # exception to next
  s/( |^)TK\s+(\d)/ Tk$2/gi;
  s/_TK/TK/g;
  s/( |^)[Tt]aka\s*(\d)/ Tk$2/g;
  s/( |^)([\$\x{00A3}\x{FFE1}\x{00A5}\x{20AC}])\s+(\d)/ $2$3/g;

  # Attach separated ordinal suffixes:
  s/1 st(\W)/1st$1/g;
  s/2 nd(\W)/2nd$1/g;
  s/3 rd(\W)/3rd$1/g;
  s/(\d) th(\W)/$1th$2/g;

  # Process "m" or "M", "b" or "B", and "k" or "K", in money amounts and
  # certain other phrases:
  s/([\$\x{00A3}\x{FFE1}\x{00A5}\x{20AC}][\d\.]+)\s*[Mm]\.?\s/$1 million /g;
  s/(USD[\d\.]+)\s*[Mm]\.?\s/$1 million /g;
  s/(AED[\d\.]+)\s*[Mm]\.?\s/$1 million /g;
  s/(CHF[\d\.]+)\s*[Mm]\.?\s/$1 million /g;
  s/(D[Hh]s?[\d\.]+)\s*[Mm]\.?\s/$1 million /g;
  s/(EUR[\d\.]+)\s*[Mm]\.?\s/$1 million /g;
  s/(GBP[\d\.]+)\s*[Mm]\.?\s/$1 million /g;
  s/(RMB[\d\.]+)\s*[Mm]\.?\s/$1 million /g;
  s/(Rmb[\d\.]+)\s*[Mm]\.?\s/$1 million /g;
  s/(Rs[\d\.]+)\s*[Mm]\.?\s/$1 million /g;
  s/(Rp[\d\.]+)\s*[Mm]\.?\s/$1 million /g;
  s/(RM[\d\.]+)\s*[Mm]\.?\s/$1 million /g;
  s/(Tk[\d\.]+)\s*[Mm]\.?\s/$1 million /g;
  s/(Y[\d\.]+)\s*[Mm]\.?\s/$1 million /g;
  s/(\d)\s*[Mm]\.?\s(euro|yuan|ton|barrel|people|year|user|passenger|job|share)/$1 million $2/g;
  s/([\$\x{00A3}\x{FFE1}\x{00A5}\x{20AC}][\d\.]+)\s*[Bb]\.?\s/$1 billion /g;
  s/(USD[\d\.]+)\s*[Bb]\.?\s/$1 billion /g;
  s/(AED[\d\.]+)\s*[Bb]\.?\s/$1 billion /g;
  s/(CHF[\d\.]+)\s*[Bb]\.?\s/$1 billion /g;
  s/(D[Hh]s?[\d\.]+)\s*[Bb]\.?\s/$1 billion /g;
  s/(EUR[\d\.]+)\s*[Bb]\.?\s/$1 billion /g;
  s/(GBP[\d\.]+)\s*[Bb]\.?\s/$1 billion /g;
  s/(RMB[\d\.]+)\s*[Bb]\.?\s/$1 billion /g;
  s/(Rmb[\d\.]+)\s*[Bb]\.?\s/$1 billion /g;
  s/(Rs[\d\.]+)\s*[Bb]\.?\s/$1 billion /g;
  s/(Rp[\d\.]+)\s*[Bb]\.?\s/$1 billion /g;
  s/(RM[\d\.]+)\s*[Bb]\.?\s/$1 billion /g;
  s/(Tk[\d\.]+)\s*[Bb]\.?\s/$1 billion /g;
  s/(Y[\d\.]+)\s*[Bb]\.?\s/$1 billion /g;
  s/([\$\x{00A3}\x{FFE1}\x{00A5}\x{20AC}][\d\.]+)\s*[Kk]\.?\s/$1 thousand /g;
  s/(USD[\d\.]+)\s*[Kk]\.?\s/$1 thousand /g;
  s/(AED[\d\.]+)\s*[Kk]\.?\s/$1 thousand /g;
  s/(CHF[\d\.]+)\s*[Kk]\.?\s/$1 thousand /g;
  s/(D[Hh]s?[\d\.]+)\s*[Kk]\.?\s/$1 thousand /g;
  s/(EUR[\d\.]+)\s*[Kk]\.?\s/$1 thousand /g;
  s/(GBP[\d\.]+)\s*[Kk]\.?\s/$1 thousand /g;
  s/(RMB[\d\.]+)\s*[Kk]\.?\s/$1 thousand /g;
  s/(Rmb[\d\.]+)\s*[Kk]\.?\s/$1 thousand /g;
  s/(Rs[\d\.]+)\s*[Kk]\.?\s/$1 thousand /g;
  s/(Rp[\d\.]+)\s*[Kk]\.?\s/$1 thousand /g;
  s/(RM[\d\.]+)\s*[Kk]\.?\s/$1 thousand /g;
  s/(Tk[\d\.]+)\s*[Kk]\.?\s/$1 thousand /g;
  s/(Y[\d\.]+)\s*[Kk]\.?\s/$1 thousand /g;

  # Prevent expansion of words in capitalised phrases as abbreviations:
  s/(^| )ADD A\.?D\.?H\.?D\.? / A.D.D. A.D.H.D. /g;
  s/(^| )ADD (\p{Lu}[\p{Lu} ])/ add $2/g;
  s/(^| )ADS (\p{Lu}[\p{Lu} ])/ ads $2/g;
  s/(^| )AL (\p{Lu}[\p{Lu} ])/ Al $2/g;
  s/(^| )AT (\p{Lu}[\p{Lu} ])/ at $2/g;
  s/(^| )BOA (\p{Lu}[\p{Lu} ])/ boa $2/g;
  s/(^| )DAB (\p{Lu}[\p{Lu} ])/ dab $2/g;
  s/(^| )COO (\p{Lu}[\p{Lu} ])/ coo $2/g;
  s/(^| )COP (\p{Lu}[\p{Lu} ])/ cop $2/g;
  s/(^| )DI (\p{Lu}[\p{Lu} ])/ Di $2/g;
  s/(^| )DR CONGO/ D.R. CONGO/g;  # exception to next one
  s/(^| )DR (\p{Lu}[\p{Lu}\. ])/ Dr $2/g;
  s/(^| )ED (\p{Lu}[\p{Lu} ])/ Ed $2/g;
  s/(^| )ERA (\p{Lu}[\p{Lu} ])/ era $2/g;
  s/\-ERA (\p{Lu}[\p{Lu} ])/-era $1/g;
  s/(^| )HA (\p{Lu}[\p{Lu} ])/ ha $2/g;
  s/(^| )HE (\p{Lu}[\p{Lu} ])/ he $2/g;
  s/(^| )IT (\p{Lu}[\p{Lu} ])/ it $2/g;
  s/(^| )LOT (\p{Lu}[\p{Lu} ])/ lot $2/g;
  s/(^| )ME (\p{Lu}[\p{Lu} ])/ me $2/g;
  s/(^| )NUT (\p{Lu}[\p{Lu} ])/ nut $2/g;
  s/(^| )PER([\- ]\p{Lu}[\p{Lu} ])/ per$2/g;
  s/\-PER([\- ]\p{Lu}[\p{Lu} ])/-per$1/g;
  s/(^| )RE([\- ]\p{Lu}[\p{Lu} ])/ re$2/g;
  s/(^| )RIP (\p{Lu}[\p{Lu} ])/ rip $2/g;
  s/(^| )SO (\p{Lu}[\p{Lu} ])/ so $2/g;
  s/(^| )SPA (\p{Lu}[\p{Lu} ])/ spa $2/g;
  s/(^| )ST\.? (\p{Lu}[\p{Lu} ])/ St $2/g;
  #s/(^| )US (\p{Lu}[\p{Lu} ])/ us $2/g; # gives too many false positives
  s/(^| )WHO (\p{Lu}[\p{Lu} ])/ who $2/g;
  s/A\.?D\.?H\.?D\.? ADD /A.D.H.D. A.D.D. /g;
  s/(\p{Lu}\p{Lu}) ADD /$1 add /g;
  s/(\p{Lu}\p{Lu}) ADS /$1 ads /g;
  s/(\p{Lu}\p{Lu}) AL /$1 Al /g;
  s/(^| )SANTA\sANA\s/ Santa Ana /g;
  s/(\p{Lu}\p{Lu}) AT /$1 at /g;
  s/(\p{Lu}\p{Lu}) BOA /$1 boa /g;
  s/(\p{Lu}\p{Lu}) COP /$1 cop /g;
  s/(\p{Lu}\p{Lu}) DAB /$1 dab /g;
  s/(\p{Lu}\p{Lu}) ED /$1 Ed /g;
  s/(\p{Lu}\p{Lu}) ERA /$1 era /g;
  s/ ha HA / ha ha /g;
  s/(\p{Lu}\p{Lu}) HA /$1 ha /g;
  s/(\p{Lu}\p{Lu}) HE /$1 he /g;
  s/(\p{Lu}\p{Lu}) IT /$1 iT /g; # gives false positives with abbrevs before - fixed later
  s/(\p{Lu}\p{Lu}) LOT /$1 lot /g;
  s/(\p{Lu}\p{Lu}) ME /$1 me /g;
  s/(\p{Lu}\p{Lu}) NUT /$1 nut /g;
  s/(\p{Lu}\p{Lu}) PER /$1 per /g;
  s/(\p{Lu}\p{Lu}) RIP /$1 rip /g;
  s/(\p{Lu}\p{Lu}) SPA /$1 spa /g;
  s/(\p{Lu}\p{Lu}) SO /$1 so /g;
  s/(\p{Lu}\p{Lu}) ST\.? /$1 St /g;
  s/THE US /THE U.S. /g;
  s/(^| )([NS][EW]) US / $2 U.S. /g;
  s/(\p{Lu}\p{Lu}) US /$1 us /g;
  s/(\p{Lu}\p{Lu}) WHO /$1 who /g;

  # Disambiguate "Street" and "Saint" and "State":
  s/Minneapolis\-St\.?\s/Minneapolis Saint /g;
  s/(^| |-)St\.?(-| )/ St /g;
  s/1st\s+St\.?\s/1st Street /g;
  s/2nd\s+St\.?\s/2nd Street /g;
  s/3rd\s+St\.?\s/3rd Street /g;
  s/(\d)th\s+St\.?\s/$1th Street /g;
  s/Wall\s+St\.?\s/Wall Street /g;
  s/Main\s+St\.?\s/Main Street /g;
  s/Downing\s+St\.?\s/Downing Street /g;
  #s/(\d\s+\p{Lu}\p{L}*\.?)\s+St\.?\s/$1 Street /g;
  #s/(\d\s+\p{Lu}\p{L}*\.?\s+\p{Lu}\p{L}*\.?)\s+St\.?\s/$1 Street /g;
  # above for "28 North Grove St" etc; but too many false positives
  # sports teams with "State":
  s/Arizona\s+St\.?\s/Arizona State /g;
  s/Chicago\s+St\.?\s/Chicago State /g;
  s/Florida\s+St\.?\s/Florida State /g;
  s/Illinois\s+St\.?\s/Illinois State /g;
  s/Kansas\s+St\.?\s/Kansas State /g;
  s/Michigan\s+St\.?\s/Michigan State /g;
  s/Mississippi\s+St\.?\s/Mississippi State /g;
  s/Ohio\s+St\.?\s/Ohio State /g;
  s/Penn\s+St\.?\s/Penn State /g;
  s/San Jose\s+St\.?\s/San Jose State /g;
  s/Tennessee\s+St\.?\s/Tennessee State /g;
  s/Washington\s+St\.?\s/Washington State /g;
  s/Wichita\s+St\.?\s/Wichita State /g;
  s/(\p{Lu}\p{L}*\.?)\s+St\.?\s+([NSEW][NSEW\.]*)\s/$1 Street $2 /g;
  s/(^| )St\.?\s+(\p{Lu})/ Saint $2/g;
  s/(\p{Lu}\p{L}*\.?)\s+St\.?\s/$1 Street /g;

  # Correcting some mistakes where Greek or Cyrillic capital letters are 
  # used instead of Roman ones that look similar.
  s/(^| )[\x{0391}\x{0410}]([A-Za-z]+)(-| )/ A$2$3/g;
  s/(^| )[\x{0392}\x{0412}]([A-Za-z]+)(-| )/ B$2$3/g;
  s/(^| )[\x{0395}\x{0415}]]([A-Za-z]+)(-| )/ E$2$3/g;
  s/(^| )[\x{0396}]([A-Za-z]+)(-| )/ Z$2$3/g;
  s/(^| )[\x{0397}\x{041D}]]([A-Za-z]+)(-| )/ H$2$3/g;
  s/(^| )[\x{0399}]([A-Za-z]+)(-| )/ I$2$3/g;
  s/(^| )[\x{039A}\x{041A}]([A-Za-z]+)(-| )/ K$2$3/g;
  s/(^| )[\x{041C}\x{039C}]([A-Za-z]+)(-| )/ M$2$3/g;
  s/(^| )[\x{039D}]([A-Za-z]+)(-| )/ N$2$3/g;
  s/(^| )[\x{039F}\x{041E}]([A-Za-z]+)(-| )/ O$2$3/g;
  s/(^| )[\x{03A1}\x{0420}]([A-Za-z]+)(-| )/ P$2$3/g;
  s/(^| )[\x{03A4}\x{0422}]([A-Za-z]+)(-| )/ T$2$3/g;
  s/(^| )[\x{03A5}]([A-Za-z]+)(-| )/ Y$2$3/g;
  s/(^| )[\x{03A7}]([A-Za-z]+)(-| )/ X$2$3/g;

  # Correct mistaken use of other non-Roman letters, e.g. dotless i:
  s/(^| )([A-Za-z]*)[\x{0131}]([A-Za-z])/ $2i$3/g;
  s/([A-Za-z])[\x{0131}]([A-Za-z]*)(-| )/$1i$2$3/g;

  # Convert Roman numerals to cardinals in specified contexts:
  my @words = split;
  $_ = "";
  for my $w (@words) {
    $_ .= "$w ";
    $_ .= "_" if (defined($is_rc_context{$w}));
  }
  s/(_[IVX]+)-([IVX]+ )/$1 to _$2/g;
  s/(_[IVX]+ )(and|to|or) (I[IVX]+ )/$1$2 _$3/g;
  s/(_[IVX]+ )(and|to|or) ([VX][IVX]* )/$1$2 _$3/g;
  s/_I( |'|-)/one$1/g;
  s/_I\. /one . /g;
  s/_II( |'|-)/two$1/g;
  s/_III( |'|-)/three$1/g;
  s/_IV( |'|-)/four$1/g;
  s/_V( |'|-)/five$1/g;
  s/_VI( |'|-)/six$1/g;
  s/_VII( |'|-)/seven$1/g;
  s/_VIII( |'|-)/eight$1/g;
  s/_IX( |'|-)/nine$1/g;
  s/_X( |'|-)/ten$1/g;
  s/_XI( |'|-)/eleven$1/g;
  s/_XII( |'|-)/twelve$1/g;
  s/_XIII( |'|-)/thirteen$1/g;
  s/_XIV( |'|-)/fourteen$1/g;
  s/_XV( |'|-)/fifteen$1/g;
  s/_XVI( |'|-)/sixteen$1/g;
  s/_XVII( |'|-)/seventeen$1/g;
  s/_XVIII( |'|-)/eighteen$1/g;
  s/_XIX( |'|-)/nineteen$1/g;
  s/_XX( |'|-)/twenty$1/g;
  s/_XXI( |'|-)/twenty one$1/g;
  s/_XXII( |'|-)/twenty two$1/g;
  s/_XXIII( |'|-)/twenty three$1/g;
  s/_XXIV( |'|-)/twenty four$1/g;
  s/_XXV( |'|-)/twenty five$1/g;
  s/_XXVI( |'|-)/twenty six$1/g;
  s/_XXVII( |'|-)/twenty seven$1/g;
  s/_XXVIII( |'|-)/twenty eight$1/g;
  s/_XXIX( |'|-)/twenty nine$1/g;
  s/_XXX( |'|-)/thirty$1/g;
  s/_XXXI( |'|-)/thirty one$1/g;
  s/_XXXII( |'|-)/thirty two$1/g;
  s/_XXXIII( |'|-)/thirty three$1/g;
  s/_XXXIV( |'|-)/thirty four$1/g;
  s/_XXXV( |'|-)/thirty five$1/g;
  s/_XXXVI( |'|-)/thirty six$1/g;
  s/_XXXVII( |'|-)/thirty seven$1/g;
  s/_XXXVIII( |'|-)/thirty eight$1/g;
  s/_XXXIX( |'|-)/thirty nine$1/g;
  s/_XL( |'|-)/forty$1/g;
  s/_XLI( |'|-)/forty one$1/g;
  s/_XLII( |'|-)/forty two$1/g;
  s/_XLIII( |'|-)/forty three$1/g;
  s/_XLIV( |'|-)/forty four$1/g;
  s/_XLV( |'|-)/forty five$1/g;
  s/_XLVI( |'|-)/forty six$1/g;
  s/_XLVII( |'|-)/forty seven$1/g;
  s/_XLVIII( |'|-)/forty eight$1/g;
  s/_XLIX( |'|-)/forty nine$1/g;
  s/_//g;

  # Context-sensitive processing for certain Roman ordinals:
  s/(^| )(\p{Lu}\p{Ll}+) IV( |')/ $2 the fourth$3/g;  # otherwise becomes "I.V."
  s/Alexander I( |')/Alexander the first$1/g;
  s/Benedict I( |')/Benedict the first$1/g;
  s/Celestine I( |')/Celestine the first$1/g;
  s/Charles I( |')/Charles the first$1/g;
  s/Edward I( |')/Edward the first$1/g;
  s/Elizabeth I( |')/Elizabeth the first$1/g;
  s/Francis I( |')/Francis the first$1/g;
  s/George I( |')/George the first$1/g;
  s/Gustav I( |')/Gustav the first$1/g;
  s/Haakon I( |')/Haakon the first$1/g;
  s/Harald I( |')/Harald the first$1/g;
  s/Henry I( |')/Henry the first$1/g;
  s/James I( |')/James the first$1/g;
  s/John I( |')/John the first$1/g;
  s/Kamehameha I( |')/Kamehameha the first$1/g;
  s/Louis I( |')/Louis the first$1/g;
  s/Ludwig I( |')/Ludwig the first$1/g;
  s/Mohamed I( |')/Mohamed the first$1/g;
  s/Napoleon I( |')/Napoleon the first$1/g;
  s/Nicholas I( |')/Nicholas the first$1/g;
  s/Paul I( |')/Paul the first$1/g;
  s/Peter I( |')/Peter the first$1/g;
  s/Philip I( |')/Philip the first$1/g;
  s/Pius I( |')/Pius the first$1/g;
  s/Ptolemy I( |')/Ptolemy the first$1/g;
  s/Richard I( |')/Richard the first$1/g;
  s/Tupou I( |')/Tupou the first$1/g;
  s/Wilhelm I( |')/Wilhelm the first$1/g;
  s/William I( |')/William the first$1/g;
  s/Alexander V( |')/Alexander the fifth$1/g;
  s/Benedict V( |')/Benedict the fifth$1/g;
  s/Celestine V( |')/Celestine the fifth$1/g;
  s/Charles V( |')/Charles the fifth$1/g;
  s/Edward V( |')/Edward the fifth$1/g;
  s/Elizabeth V( |')/Elizabeth the fifth$1/g;
  s/Francis V( |')/Francis the fifth$1/g;
  s/George V( |')/George the fifth$1/g;
  s/Gustav V( |')/Gustav the fifth$1/g;
  s/Haakon V( |')/Haakon the fifth$1/g;
  s/Harald V( |')/Harald the fifth$1/g;
  s/Henry V( |')/Henry the fifth$1/g;
  s/James V( |')/James the fifth$1/g;
  s/John V( |')/John the fifth$1/g;
  s/Kamehameha V( |')/Kamehameha the fifth$1/g;
  s/Louis V( |')/Louis the fifth$1/g;
  s/Ludwig V( |')/Ludwig the fifth$1/g;
  s/Mohamed V( |')/Mohamed the fifth$1/g;
  s/Napoleon V( |')/Napoleon the fifth$1/g;
  s/Nicholas V( |')/Nicholas the fifth$1/g;
  s/Paul V( |')/Paul the fifth$1/g;
  s/Peter V( |')/Peter the fifth$1/g;
  s/Philip V( |')/Philip the fifth$1/g;
  s/Pius V( |')/Pius the fifth$1/g;
  s/Ptolemy V( |')/Ptolemy the fifth$1/g;
  s/Richard V( |')/Richard the fifth$1/g;
  s/Tupou V( |')/Tupou the fifth$1/g;
  s/Wilhelm V( |')/Wilhelm the fifth$1/g;
  s/William V( |')/William the fifth$1/g;

  # Change hyphens to spaces except in specified hyphenated words and
  # between or before numbers (latter exceptions added by FRM):
  @words = split;
  $_ = "";
  for my $w (@words) {
    if ($w =~ /\-/ && $w !~ /(^|[0-9])\-[0-9\.,]+([%\$sxKkMmcpCF]?|[AaPp]\.?[Mm]\.?|oz|lbs?|kph|mph|mpg)$/) {
      $w =~ s/\-/ /g unless (defined($is_hyphenated{$w}));
    }
    $_ .= "$w ";
  }

  # Separate word-initial and word-final single quotes or apostrophes (done in
  # normalize_puncts.pl but repeated here for any newly exposed above):
  s/([^s\s])\' /$1 ' /g;
  s/ \'\s*/ ' /g;

  # Process top-level domains with preceding dot:
  @words = split;
  $_ = "";
  for my $w (@words) {
    if ($w =~ /\.([a-z]+)(\'?s?$|\/\S+)/ && defined($is_tld{$1})) {
      my $tld = $1;
      my $suffix = $2;
      $suffix =~ s/\// slash /g;
      $_ .= "dot ";
      if ($tld =~ m/aero|arpa|asia|biz|com|gov|info|jobs|museum|name|net|org|travel/) {
	$_ .= "$tld$suffix ";
      } else {
        $tld =~ s/(\p{L})/$1./g;
	$_ .= uc($tld)."$suffix "; 
      }
    } else { $_ .= "$w "; }
  }

  # Expand abbreviations:
  @words = split;
  $_ = "";
  for my $w (@words) {
    if (defined($abbrev_map{$w})) {
#print "> abbr $w\n";
      $w = $abbrev_map{$w};
    } else {
      my $suffix = "";
      if ($w =~ s/(\+|\'s|s\')$//) { # Remove common suffixes
        $suffix = $1;
      } elsif ($w =~ s/([^\p{Ll}])(s|th|ing|ed)$/$1/) {
        $suffix = $2;
      }
      if (defined($abbrev_map{$w})) {
#print "> abbr $w suffix $suffix\n";
	$w = $abbrev_map{$w};
      } elsif ($w =~ /^\p{L}(\.\p{L})+\.?$/) {
#print "> match $w\n";
	$w =~ s/\.?$/./;
      }
      $w .= $suffix unless ($suffix eq "th" && $w =~ /th$/);
    }
    $_ .= "$w ";
  }

  # Fix special cases:
  s/(\p{Lu}\.) iT (\P{Lu})/$1 I.T. $2/g;
  s/ iT / it /g;

  s/vis\-\x{00E0}\-vis/vis-a-vis/ig;

  s/^\s*//;  s/\s*$//;  s/\s+/ /g;  # Normalize spaces
  next if /^$/;  # Skip empty lines
  print NFC($_), "\n";  # UTF8 recompose & reorder canonically
}


sub load_abbrevs {
  # changed by FRM to recognise Roman cardinal contexts and allow digits in keys
  my ($abbrev_file, $abbrev_ref, $is_rc_context) = @_;
  die "Wrong arguments: '@_'" unless (defined($abbrev_file) and 
				      defined($abbrev_ref));
  open(FH, $abbrev_file) or die "Cannot read from '$abbrev_file': $!";
  while (<FH>) {
    chomp;
    $_ = NFD($_);   # UTF8 decompose
    next if ($_ =~ /^\#/ or $_ =~ /^$/);  # skip empty lines & comments
    if ($_ =~ /^\*r\s+([\p{L}\.]+)\s*$/) {
      # left context for Roman cardinal numeral
      $is_rc_context->{$1} = 1;
    } elsif ($_ =~ /^([\p{L}\.\/\&\d\-]+)\s+([\p{L} \.\-\&\/]+)\s*$/) {
      $abbrev_ref->{$1} = $2;
    } else {
      print STDERR "Ignoring unexpected line format: '$_'";
    }
  }
  close(FH);
}


sub load_tlds {
  my ($tld_file, $tld_ref) = @_;
  die "Wrong arguments: '@_'" unless (defined($tld_file) and 
				      defined($tld_ref));
  open(FH, $tld_file) or die "Cannot read from '$tld_file': $!";
  while (<FH>) {
    chomp;
    next if ($_ =~ /^\#/ or $_ =~ /^$/);  # skip empty lines & comments
    $_ = NFD($_);   # UTF8 decompose: not needed at this point, but why not!
    $tld_ref->{$_} = 1;
  }
  close(FH);
}


sub load_hyphenated {
  my ($hyphenated_file, $hyphenated_ref) = @_;
  die "Wrong arguments: '@_'" unless (defined($hyphenated_file) and 
				      defined($hyphenated_ref));
  open(FH, $hyphenated_file) or die "Cannot read from '$hyphenated_file': $!";
  while (<FH>) {
    chomp;
    next if ($_ =~ /^\#/ or $_ =~ /^$/);  # skip empty lines & comments
    $_ = NFD($_);   # UTF8 decompose: not needed at this point, but why not!
    $hyphenated_ref->{$_} = 1;
  }
  close(FH);
}
