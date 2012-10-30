#!/usr/bin/perl
# takes a file with kmers and extract number of bp covered by at least one unique kmer

use strict;
use warnings;

my $kmer_length = $ARGV[0];

my $remainder = $kmer_length; # bases left before exausting last unique kmer
while (my $line = <STDIN>) {
	my $counter = 0; # final value to be produced for each sequence
	chomp $line;
	my @fields = split(/\t/, $line);
	my $index = 1;
	while ($index <= $#fields) {
		if ($fields[$index] == 1) {
			$remainder = $kmer_length;
		}
		else {
			$remainder--;
		}
		if ($remainder > 0) { $counter++;}
		$index++;
	}
	print $fields[0]."\t".$#fields."\t".$counter."\n"; # sequence, all bases, uniquely projected bases
}
