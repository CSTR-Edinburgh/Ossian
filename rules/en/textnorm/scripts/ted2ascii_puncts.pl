#!/usr/bin/perl -w

# Copyright 2012  Arnab Ghoshal
# Modified by Fergus McInnes (FRM), 2013
# This version modified for encoding in TED talk transcripts (ISO/IEC 8859-1,
# with Windows-1252 variants for codes from 80 to 9F) - many lines of script
# may be unnecessary, but it seems simplest and safest to leave them in

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

# This script converts different punctuations in UTF-8 and HTML to standard 
# ASCII punctuations.

use strict;
use Unicode::Normalize;
use HTML::Entities;  # For HTML -> UTF8 conversion
# use open ':encoding(utf8)';
# use feature 'unicode_strings';

# Make sure we are reading in ISO-8859-1 and writing in UTF8
binmode(STDIN, ":encoding(iso-8859-1)");
binmode(STDOUT, ":encoding(utf8)");
binmode(STDERR, ":encoding(utf8)");

my $help_message="";

while (<STDIN>) {
  # Convert Windows-1252 codes:
  s/\x{0085}/\x{2026}/g;  # ellipsis
  s/\x{0092}/'/g;
  s/\x{0096}/-/g;
  s/\x{0097}/-/g;

  $_ = NFD($_);   # decompose
  $_ = decode_entities($_);  # Convert from HTML hex symbols to UTF8
  s/\&euro\;/\x{20AC}/g;     # HTML euro sign (probably already converted)
  s/[\x{E000}-\x{F8FF}]//g;  # Remove anything in UTF-8 Private Use Area!

  # Convert single quotes:
  s/\`/'/g;
  s/\&[lrs][sb]quo\;/'/g;     # HTML single quotes (left, right, low)
  s/[\x{02B9}-\x{02BD}]/'/g;  # various single quotes
  s/\x{00B4}/'/g;             # acute accent
  s/[\x{2018}-\x{201B}]/'/g;  # single quotes (left, right, low, high-reversed)
  s/\x{2032}/'/g;             # prime
  s/\x{2035}/'/g;             # reversed prime
  s/[\x{2039}\x{203A}]/'/g;   # left & right single angle quote
  s/[\x{3008}-\x{3009}]/'/g;  # left & right angle brackets (for CJK)  
  s/[\x{300C}-\x{300D}]/'/g;  # left & right corner brackets (for CJK)
  s/a\x{0302}\x{20AC}\x{2122}/'/g;  # not clear why this occurs, but it does

  # Convert double quotes:
  s/\&quot\;/"/g;             # HTML "
  s/\&[lrb]dquo\;/'/g;        # HTML double quotes (left, right, low)
  s/\x{00AB}/"/g;             # left-pointing double angle quote
  s/\x{00BB}/"/g;             # right-pointing double angle quote
  s/[\x{201C}-\x{201F}]/"/g;  # double quotes (left, right, low, high-reversed)
  s/[\x{2033}-\x{2034}]/"/g;  # double and triple primes
  s/[\x{2036}-\x{2037}]/"/g;  # reversed double and triple primes
  s/[\x{300A}-\x{300B}]/"/g;  # left & right double angle brackets (for CJK)
  s/[\x{300E}-\x{300F}]/"/g;  # left & right white corner brackets (for CJK)
  s/[\x{00A7}\x{00A8}]/"/g;   # section sign & diaeresis (used in error)

  # Collapse multiple quotes
  s/\'{2,}/"/g;
  s/\"{2,}/"/g;
  s/"/ " /g;

  # Remove lines with replacement characters or (maybe inverted) question marks
  # embedded in words: e.g. "Ch\x{FFFD}\x{FFFD}vez" for "Cha\x{0301}vez"
  # - the only way to recover these correctly would be to do it case by case
  next if /\p{L}[\x{FFFC}\x{FFFD}\x{00BF}]/;
  next if /[\x{FFFC}\x{FFFD}\x{00BF}\?]\p{L}/;

  # Convert dashes:
  # (changed by FRM to put spaces around those unlikely to be word-internal)
  s/[\x{2010}-\x{2015}]/ - /g; # Some of these may actually be quotes!
  s/\&[nm]dash;/ - /g;        # HTML: like the match above, these may be quotes.
  s/\x{2027}/-/g;             # hyphenation point
  s/\x{2043}/-/g;             # hyphen bullet
  s/\x{2212}/-/g;             # Minus sign
  s/[\x{FFFC}\x{FFFD}]/-/g;   # replacement characters: have been used for -
  s/\&\#45\;/-/g;             # HTML -
  s/a\x{0302}\x{02C6}'/-/g;   # not clear why this occurs, but it does
  s/a\x{0302}\x{20AC} "/-/g;  # not clear why this occurs, but it does
  s/a\x{0302}\x{20AC}-/-/g;   # not clear why this occurs, but it does
  s/a\x{0302}\x{20AC}\x{00A6}/-/g;   # not clear why this occurs, but it does
  s/\-{2,}/ - /g;             # Merge multi -'s

  # Ellipses
  s/\x{2024}/./g;    # one dot leader!
  s/\x{2025}/../g;   # two dot leader!
  s/\x{2026}/.../g;  # horizontal ellipsis

  # Questions & exclamations
  s/\x{203C}/!!/g;  # Double exclamation
  s/\x{2047}/??/g;  # Double question
  s/[\x{203D}\x{2048}\x{2049}]/?!/g;  # interrobang, question-exclamation
  # TODO(arnab): inverted question & exclamation for Spanish

  # Slashes:
  s?\x{2215}?/?g;  # Division slash
  s?\x{2044}?/?g;  # Fraction slash

  # Other HTML symbols
  s/\&amp\;/&/g;   # HTML &

  # Spaces, etc.
  s/\p{Space}+/ /g;  # Convert all spaces to ASCII space
  s/[\x{2000}-\x{200F}]/ /g;	# uncommented by FRM
  s/[\x{2028}-\x{202F}]/ /g;	# uncommented by FRM
  s/\x{00A0}/ /g;    # No-break space
  s/\x{FEFF}/ /g;    # zero-width no-break space
  s/\x{00AD}/ /g;    # soft hyphen
  s/[\x{00B7}\x{2022}\x{2023}\x{25A0}\x{25CF}]//g;  # bullet
  s/\x{02DD}//g;     # double acute accent (but seems to be in error)
  s/\x{00B6}/ /g;    # pilcrow
  s/\x{2020}//g;     # dagger
  s/[\x{2605}\x{2606}]/ /g;    # star
  #s/[\x{2665}\x{2764}]/ /g;    # heart - may want context-dependent conversion
  s/\x{2666}/ /g;    # diamond
  s/\x{2122}/ /g;    # trade mark sign

  # Remove musical notes:
  s/[\x{2669}-\x{266C}]/ /g;

  # Handle ligatures: not strictly punctuations, but processed here
  s/\x{00C6}/Ae/g;   # uncommented by FRM, and others below added
  s/\x{00E6}/ae/g;
  s/\x{0152}/Oe/g;
  s/\x{0153}/oe/g;
  s/\x{FB00}/ff/g;
  s/\x{FB01}/fi/g;
  s/\x{FB02}/fl/g;
  s/\x{FB03}/ffi/g;
  s/\x{FB04}/ffl/g;
  s/\x{FB05}/ft/g;
  s/\x{FB06}/st/g;

  s/^\s*//;  s/\s*$//;  s/\s+/ /g;  # Normalize spaces
  print NFC($_), "\n";  # recompose & reorder canonically
}
