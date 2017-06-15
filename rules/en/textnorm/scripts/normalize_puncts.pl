#!/usr/bin/perl -w

# Copyright 2012  Arnab Ghoshal
# Modified 2013 by Fergus McInnes (FRM)

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
#   - when a ' at the end of a word is preceeded by an s (may be possessive)
# These need to be handled in a later processing stage.

use strict;
use Unicode::Normalize;
use open ':encoding(utf8)';
# use feature 'unicode_strings';

# Make sure we are reading and writing in UTF-8. 
binmode(STDIN, ":encoding(utf8)");
binmode(STDOUT, ":encoding(utf8)");
binmode(STDERR, ":encoding(utf8)");

my $help_message="USAGE: normalize_puncts.pl abbrevs tlds < in > out\n";
die "$help_message" if (scalar(@ARGV) != 2);

my $abbrev_file = $ARGV[0];
my $tld_file = $ARGV[1];
my %is_abbrev = ();  # List of all abbreviations
my %is_tld = ();     # List of all top-level domain names

&load_abbrevs($abbrev_file, \%is_abbrev);
&load_tlds($tld_file, \%is_tld);

while (<STDIN>) {
  chomp;
  $_ = NFD($_);   # UTF8 decompose

  clean_quoted_ellipses($_);  # Remove any ellipses in quoted segments

  s/\!+/ ! /g;
  s/\?+/ ? /g;
  s/\x{00A1}+/ \x{00A1} /g;  # Inverted exclamation
  s/\x{00BF}+/ \x{00BF} /g;  # Inverted question
  s/\;/ ; /g;
  s/(AA|BB)\-\s/$1 minus /g;
  s/-([ \,\.])/ $1/g;
  s/ -([^\p{N}])/ $1/g;
  s/(\p{N}) -(\p{N})/$1-$2/g;  # often a range with an accidental space
  # Sometimes single quotes seem to be rendered as =
  s/s=(\W)/s'$1/g;
  s/(\w)=s(\W)/$1's$2/g;
  s/ = / equals /g;
  s/(\w)\s*=\s*([0-9])/$1 equals $2/g;
  s/(\W)e=mc\^?2(\W)/$1E equals m c squared$2/gi; 
  s/(\W)e=mc squared/$1E equals m c squared/gi; 
  s/[\<\>\=\_]/ /g;

  # commented out by FRM: done later in final_cleanup.pl
  #s?(\p{L})/?$1 ?g;   # remove word-internal or word-ending /
  #s? /(\p{L})? $1?g;  # remove word beginning /

  # Some specific dates and patterns (refined by FRM):
  s/(^| |\-)(9)[-\/](11)(\D)/ $2 $3 !!$4/g;
  s/(^| |\-)(7|24)[-\/](7)(\D)/ $2 $3 !!$4/g;
  s/(^| |\-)(50)[-\/](50)(\D)/ $2 $3 !!$4/g;
  s/(^| |\-)(20|80)[-\/](20)(\D)/ $2 $3 !!$4/g;
  s/(^| |\-)(90)[-\/](10)(\D)/ $2 $3 !!$4/g;
  #s?(9|7|24|50|80|90|26|20)[-\/](11|7|50|20|10)?$1 $2?g;
  s/\!\![-\/]?//g;
  #s? /(\p{N}+)? $1?g;  # may want this back if numproc is affected

  s/^\s*\.+//;    # dots at the beginning; generally errors: remove
  next if /^$/;
  s/\.{2,}\s*$/ ./;  # convert dots at end to a single period
  s/(\d)\.(a|p)\.?m[ .]/$1 $2.m. /g;  # Normalize a.m./p.m.
  s/(\d)\.(A|P)\.?M[ .]/$1 $2.M. /g;  # Normalize A.M./P.M.
  s/ Ph\.D([\Ws])/ Ph.D.$1/g;
  s/ Ph\.D\.\./ Ph\.D\./g;

  # Ellipses before capitalized words converted to periods
  s/\.{2,}\s*(\p{Lu}\p{L}+)/ . $1/g;
  s/\.{2,}/ ... /g;  # Separate out all other ellipses

  # Separate out , and : except when within numbers (e.g. 1,500 or 09:30)
  # (now done before separate_periods so that abbreviations followed by
  # a comma or colon are found - FRM)
  s/([^\p{N}])\,([^\p{N}])/$1 , $2/g;
  s/([\p{N}])\,([^\p{N}])/$1 , $2/g;
  s/([^\p{N}])\,([\p{N}])/$1 , $2/g;
  s/(\P{N})\:(\P{N})/$1 : $2/g;
  s/(\p{N})\:(\P{N})/$1 : $2/g;
  s/(\P{N})\:(\p{N})/$1 : $2/g;

  # Deal with common cases of pronoun "I" at end of sentence:
  s/ (is|was|were|and|but|than|(so|as|nor|neither) \p{L}+) I\.( |$)/ $1 I . /g;

  $_ = &separate_periods(\%is_abbrev, \%is_tld, $_);

  s/[\"\']\s*[\"\']/ /g;  # Remove empty quotes
#  s/ //g;  # Remove ' in front of numbers
  # Separate quotes from words:
  s/\"/ " /g;
  s/^\s*\'/' /;
  # NOTE: following only valid for English!
  s/(\p{Alnum}+)\' s /$1's /g;  # recombine possessive 's or those for 1980' s
  s/\s*\. \'\s*s /.'s /g;  # recombine possessive 's after abbreviation
  s/\.(\p{L}+) \'s /.$1's /g;  # recombine possessive 's after tld
  s/n\' t /n't /g;              # recombine n' t as in don' t
  s/(\p{L}+)\' (m|d|re|ll|ve) /$1'$2 /g;  # Other contractions
  # TODO: join contractions like D' Augustino
  s/ \'\s*/ ' /g;
  s/([^s])' /$1 ' /g;  # Separate all word-ending ' except when following s
  s/([^s])'\s*$/$1 ' /g;  # Separate all word-ending ' except when following s

  # Removing dangling dashes for a second time since they may have been 
  # followed by stuff that's removed now.
  s/- / /g;

  s/^\s*//;  s/\s*$//;  s/\s+/ /g;  # Normalize spaces
  next if /^$/;  # Skip empty lines
  print NFC($_), "\n";  # UTF8 recompose & reorder canonically
}


# Romove multiple instances of ellipses inside quoted text
sub clean_quoted_ellipses {
  if ($_ =~ s/(['"].*?)\.{2,}(.*?['"])/$1 $2/g) {
    clean_quoted_ellipses($_);
  }
}


sub load_abbrevs {
  my ($abbrev_file, $abbrev_ref) = @_;
  die "Wrong arguments: '@_'" unless (defined($abbrev_file) and 
                                      defined($abbrev_ref));
  open(FH, $abbrev_file) or die "Cannot read from '$abbrev_file': $!";
  while (<FH>) {
    chomp;
    next if ($_ =~ /^\#/ or $_ =~ /^$/);  # skip empty lines & comments
    $_ = NFD($_);   # UTF8 decompose
    if ($_ !~ /\#/) {  # Not comments, but indicate context-specific behavior
      $abbrev_ref->{$_} = 1;
    } elsif ($_ =~ /(\S+)\s+\#\s*number/) {  # e.g. No. 9 or pp. 42-45
      $abbrev_ref->{$1} = 2;
    } else {
      warn "Ignoring unexpected line format: '$_'";
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


sub separate_periods {
  # edited by FRM to avoid losing apostrophes and to correct some other bugs
  my ($abbrev_ref, $tld_ref, $line) = @_;
  $line =~ s/\.-/. /g;
  $line =~ s/\.\'/. '/g;

  # Correct typos and anomalies not dealt with below:
  $line =~ s/(^|\P{L})(\p{L}) +\.(\p{L})\./$1$2.$3./g;
  $line =~ s/(^| )\.(\p{L}\P{L})/ . $2/g;

  # Protect abbreviations from splitting:
  my @words = split(/\s+/, $line);
  for my $i (0..$#words) {
#   print STDERR "$words[$i] ";
    if (defined($abbrev_ref->{$words[$i]})
     && ($abbrev_ref->{$words[$i]} != 2)) {
      $words[$i] =~ s/\./__dot__/g;
#     print STDERR "$words[$i] ";
    } elsif ($words[$i] =~ s/(s\.?)$//) {
      my $back = $1;
#     print STDERR "[back $back] ";
      if (defined($abbrev_ref->{$words[$i]})
       && ($abbrev_ref->{$words[$i]} != 2)) {
        $words[$i] =~ s/\./__dot__/g;
#       print STDERR "$words[$i] ";
      }
      $words[$i] =~ s/$/$back/;
#     print STDERR "$words[$i] ";
    } elsif ($words[$i] =~ s/\.$//) {
      if (defined($abbrev_ref->{$words[$i]})
       && ($abbrev_ref->{$words[$i]} != 2)) {
        $words[$i] =~ s/\./__dot__/g;
        $words[$i] .= " .";
#       print STDERR "$words[$i] ";
      } else {
        $words[$i] .= ".";
      }
    }
  }
  $line = join(" ", @words);

  # Separate out top-level domain names
  $line =~ s{\.([\p{L}]{2,})}[defined($tld_ref->{$1})? " .$1" : ". $1"]eg;
# print STDERR "1: $line\n";
  # Separate out . around numbers (will be wrong for things like $.90), except
  # when within numbers (e.g. $1.50) or at start of word (e.g. .50)
  $line =~ s/([^\p{N} ])\.([\p{N}])/$1. $2/g;
  $line =~ s/([\p{N}])\.([^\p{N}])/$1 . $2/g;
# print STDERR "2: $line\n";

  # Convert protected abbreviations back to normal form:
  $line =~ s/__dot__/./g;

  @words = split(/\s+/, $line);

  for my $i (0..$#words-1) {
    my $word = $words[$i];
#   print STDERR "0: $words[$i];\t";
    my $abbr_ref = (defined($abbrev_ref->{$word}) ? $abbrev_ref->{$word} : 1);
    if (defined($abbrev_ref->{$word}) ||
     $word =~ /\d\-?(lb|oz|[km]?g|ft|[ckm]?m|in)\.$/)
     { # abbrev: leave unchanged ...
#     print STDERR "ref: $abbrev_ref->{$word};\t";
      if (($abbr_ref == 2) && ($words[$i+1] !~ /\p{N}+/)) {
        # ... but treat as ordinary word if not abbrev in current context
        $words[$i] =~ s/(\p{Ll})\.(\p{Lu})/$1 . $2/g;
        $words[$i] =~ s/\.$/ ./;
#       print STDERR "3: $words[$i];\t";
      }
    } elsif ($words[$i] =~ s/\.(s\.?)$/\./) { # possible plural abbrev
      my $back = $1;
#     print STDERR "[back $back] ";
      if (defined($abbrev_ref->{$words[$i]})
       && ($abbrev_ref->{$words[$i]} != 2)) { # plural abbrev
#       print STDERR "ref: $abbrev_ref->{$word};\t";
        $words[$i] =~ s/$/$back/;
        $words[$i] =~ s/\.$/ ./;
      } else { # other word ending ".s" or ".s.": treat as normal
        $words[$i] =~ s/$/$back/;
        if ($word !~ /\.\&?\p{L}\./) {
          $words[$i] =~ s/(\p{Ll})\.(\p{Lu})/$1 . $2/g;
          # no need to separate final dot here as it can't be present
        }
      }
#     print STDERR "4: $words[$i];\t";
    } elsif ($word !~ /\.\&?\p{L}\./) {  # other words that are not abbrevs
      $words[$i] =~ s/(\p{Ll})\.(\p{Lu})/$1 . $2/g;
      $words[$i] =~ s/([^\.])\.$/$1 ./;
#     print STDERR "5: $words[$i];\t";
    }
  }
# print STDERR "0: $words[$#words];\t";
  my $word = $words[$#words];
  if (defined($abbrev_ref->{$word}) && $abbrev_ref->{$word} != 2) {
    # abbrev at end of line: add period
    $words[$#words] .= " .";
#   print STDERR "6: $words[$#words];\t";
  } elsif ($words[$#words] =~ s/\.(s\.?)$/\./) { # possible plural abbrev
    my $back = $1;
#   print STDERR "[back $back] ";
    if (defined($abbrev_ref->{$words[$#words]})
     && ($abbrev_ref->{$words[$#words]} != 2)) { # plural abbrev
#     print STDERR "ref: $abbrev_ref->{$word};\t";
      $words[$#words] =~ s/$/$back/;
      $words[$#words] =~ s/\.$/ ./;
    } else { # other word ending ".s" or ".s.": treat as normal
      $words[$#words] =~ s/$/$back/;
      if ($word !~ /\.\&?\p{L}\./) {
        $words[$#words] =~ s/(\p{Ll})\.(\p{Lu})/$1 . $2/g;
      }
      $words[$#words] =~ s/\.$/. ./;
    }
#   print STDERR "7s: $words[$#words];\t";
  } elsif ($word =~ /\.\&?\p{L}\./) { # unlisted abbrev: add period if needed
    $words[$#words] =~ s/\.$/. ./;
#   print STDERR "7a: $words[$#words];\t";
  } else { # non-abbrev
    $words[$#words] =~ s/(\p{Ll})\.(\p{Lu})/$1 . $2/g;
    $words[$#words] =~ s/([^\.])\.$/$1 ./;
#   print STDERR "7: $words[$#words];\t";
  }
#  print STDERR "\n";

  return join(" ", @words);
}
