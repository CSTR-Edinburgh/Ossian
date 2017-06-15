#!/usr/bin/perl -w

use strict;
# use open ':encoding(utf8)';
# use feature 'unicode_strings';

# Make sure we are reading and writing in UTF-8. 
binmode(STDIN, ":encoding(utf8)");
binmode(STDOUT, ":encoding(utf8)");
binmode(STDERR, ":encoding(utf8)");

my %seen_lines = ();

while (<STDIN>) {
  if (!defined($seen_lines{$_})) {
    $seen_lines{$_} = 1;
    print;
  }
}
