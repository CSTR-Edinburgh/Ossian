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

# This script filters out bracketed segments and long-ish URLs
# It assumes punctuations have been convertd from UTF8 to ASCII.

use strict;
use Unicode::Normalize;
# use open ':encoding(utf8)';
# use feature 'unicode_strings';

# Make sure we are reading and writing in UTF-8. 
binmode(STDIN, ":encoding(utf8)");
binmode(STDOUT, ":encoding(utf8)");
binmode(STDERR, ":encoding(utf8)");

my $help_message="";

while (<STDIN>) {
  chomp;
  $_ = NFD($_);   # decompose

  next unless /[\.\?\!\"\']\s*$/;  # Unpunctuated endings => usually fragments
  # The following two patterns cover things like EU directive numbers
  # e.g. A4-0091/96 or 89/48/EEC or SEC 96/1426
  # (but dates are exempted - FRM)
  next if /\p{N}+[\/]+\p{N}+[\/]\p{L}+/;
  next if /\p{Lu}\p{N}+\_[\p{L}\p{N}]+/;
  next if /\p{L}+\p{N}+[-\/]+\p{L}*\p{N}+[-\/]+\p{L}*\p{N}+/;
  next if /\p{L}*\p{N}+[-\/]+\p{L}+\p{N}+[-\/]+\p{L}*\p{N}+/;
  next if /\p{L}*\p{N}+[-\/]+\p{L}*\p{N}+[-\/]+\p{L}+\p{N}+/;
  next if /\p{Lu}\p{N}*[-\/]+\p{L}*\p{N}+[-\/]+\p{Alnum}+/;
  next if /\p{Lu}\p{N}*[ -\/]+\p{L}*\p{N}+[\/]+\p{L}*\p{N}+/;

  # Convert superscripts:
  s/\{\+2\}(\W)/ squared$1/g;
  s/\{\+3\}(\W)/ cubed$1/g;

  # Remove newswire locations recognisable by source in parentheses
  # (not always removed by lines below, as location may not be in capitals):
  s/^.*\s\((AP|CNN|Reuters)\)\s*\-+\s*//;

  # Remove all bracketed segments
  clean_nested_paren($_);
  clean_nested_sqrbracket($_);
  clean_nested_angbracket($_);
  clean_nested_braces($_);
  # Sometimes bracketed segments are split between lines. No need to join them
  # back since we are removing the segments.
  s/\(.*$//;
  s/\[.*$//;
  s/^.*\)//;
  s/^.*\]//;

  # Remove newswire sources enclosed in slashes:
  s/^/ /;
  s/\s\/\S*Newswire\S*\// /g;

  # Filter out URLs
  filter_urls($_);

  s/^\s*//;  s/\s*$//;  s/\s+/ /g;  # Normalize spaces

  next unless /[\.\?\!\"\']\s*$/;  # Unpunctuated endings => usually fragments
                                   # May need 2nd time after removing brackets
  s/^[^\s]*\s*\:\s*//;  # Single "word" at beginning followed by : is fragment

  # Newswire style location: "LONDON - The financial ..."
  # - and variants, e.g. "LA PAZ", "ASH, England", "LITTLE ROCK, Ark.",
  # "NEW YORK/HONG KONG"
  s/^\p{Lu}[\p{Lu}\p{M}'-]{3,}(\/[\p{Lu}\p{M}' -]{3,})?\s*\-\s+//;
  s/^\p{Lu}[\p{Lu}\p{M}'-]{2,},(\s+\p{Lu}[\p{L}\.]+){1,3}\s*\-\s+//;
  s/^\p{Lu}[\p{Lu}\p{M}']+(\s+\p{Lu}[\p{Lu}\p{M}']+){1,2}(\/[\p{Lu}\p{M}' -]{3,})?\s*\-\s+//;
  s/^\p{Lu}[\p{Lu}\p{M}']+(\s+\p{Lu}[\p{Lu}\p{M}']+){1,3},(\s+\p{Lu}[\p{L}\.]+){1,3}\s*\-\s+//;
  # Newswire style location and date: "LONDON, Nov 25 - The financial ..."
  my $monthre = 'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|January|February|March|April|June|July|August|September|October|November|December';
  s/^\p{Lu}[\p{Lu}\p{M}'-]{3,},\s+($monthre)\.?\s*\d+(,?\s*\d{4})?\s*\-\s+//;
  s/^\p{Lu}[\p{Lu}\p{M}'-]{2,},(\s+\p{Lu}[\p{L}\.]+){1,3},\s+($monthre)\.?\s*\d+(,?\s*\d{4})?\s*\-\s+//;
  s/^\p{Lu}[\p{Lu}\p{M}']+(\s+\p{Lu}[\p{Lu}\p{M}']+){1,3},\s+($monthre)\.?\s*\d+(,?\s*\d{4})?\s*\-\s+//;
  s/^\p{Lu}[\p{Lu}\p{M}']+(\s+\p{Lu}[\p{Lu}\p{M}']+){1,3},(\s+\p{Lu}[\p{L}\.]+){1,3},\s+($monthre)\.?\s*\d+(,?\s*\d{4})?\s*\-\s+//;
  s/^\d+\s+\-\s+//;  # Day (fragment of newswire date) and dash

  # Remove bullets, etc. from the beginning (but not currency signs - FRM):
  s/^[^\p{L}\p{N}\"\'\$\x{00A3}\x{FFE1}\x{00A5}\x{20AC}]+//;
  s/^\x{00DE}\s+//;  # capital thorn sometimes used as a bullet
  next if /^[^\p{L}]*$/;    # Remove fragments without any letters

  s/^\s*//;  s/\s*$//;  s/\s+/ /g;  # Normalize spaces
  next if /^$/;  # Skip empty lines

  # Filter out suspected lists:
  next unless / /;  # Remove single word sentences
  my $separator_count = () = ($_ =~ /[\,\;\:\-]/g);
  my $space_count = () = ($_ =~ / /g);
  next if ($separator_count/$space_count > 0.3);

  print NFC($_), "\n";  # recompose & reorder canonically
}


# For nested parentheses this removes the innermost one, and then calls itself 
# recursively to remove the outer ones.
sub clean_nested_paren {
  if ($_ =~ s/[\(][^\(]*?[\)]//g) {
    clean_nested_paren($_);
  }
}

# For nested square brackets this removes the innermost one, and then calls 
# itself recursively to remove the outer ones.
sub clean_nested_sqrbracket {
  if ($_ =~ s/[\[][^\[]*?[\]]//g) {
    clean_nested_sqrbracket($_);
  }
}

# For nested angular brackets this removes the innermost one, and then calls 
# itself recursively to remove the outer ones.
sub clean_nested_angbracket {
  if ($_ =~ s/[\<][^\<]*?[\>]//g) {
    clean_nested_angbracket($_);
  }
}

# For nested segments in braces this removes the innermost one, and then calls 
# itself recursively to remove the outer ones.
sub clean_nested_braces {
  if ($_ =~ s/[\{][^\{]*?[\}]//g) {
    clean_nested_braces($_);
  }
}

# Filter out URLs
sub filter_urls {
  # Note that this only roughly does the job. The intention is not to remove 
  # every possible URLs at this point.
  s/http[^\s]+//ig;
  s/www[^\s]+//ig;
  s/[^\s]+\.htm[^\s]*//ig;
  s/[^\s]+\.sht[^\s]*//ig;  # Yes, some folks use '.sht': curse of TLAs
  s/[^\s]+\.txt//ig;
  s/[^\s]+\.asp[^\s]*//ig;
  s/[^\s]+\.jsp[^\s]*//ig;
  s/[^\s]+\.php[^\s]*//ig;
}
