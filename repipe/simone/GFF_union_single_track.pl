#!/usr/bin/perl
# takes a list of scaffold (in one column)
# and a GFF file with segments (from-to coordinates)
# and removes duplications merging hits (union)

use strict;
use warnings;
use Set::Infinite qw($inf);

my $list_of_scaffolds = $ARGV[0];
open(LIST, $list_of_scaffolds) or die("Cannot open file $list_of_scaffolds\n");
# set with intervals
my %set;
while (my $line = <LIST>) {
	chomp $line;
	# initialize empty set for each scaffold
	$set{$line} = Set::Infinite->new;
}

my $file1 = $ARGV[1];

foreach my $key (keys (%set)) {
	open(FILE1, $file1) or die("Cannot open input file $file1\n");
	while (my $line = <FILE1>) {
		chomp $line;
		my @fields = split(/\t/, $line);
		my $scaffold = $fields[0];
		if ($scaffold eq $key) {
			my $start = $fields[3];
			my $stop  = $fields[4];
			$set{$scaffold} = $set{$scaffold}->union($start, $stop);
		}
	}
	if ($set{$key}->count > 0) {
		$set{$key}->iterate(sub {print $key."\ttest\ttest\t".$_[0]->min."\t".$_[0]->max."\t.\t.\t.\tTarget\n";}, sub {}, );
	}
	close FILE1;
}
