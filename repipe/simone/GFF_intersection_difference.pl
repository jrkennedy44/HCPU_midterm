#!/usr/bin/perl
# takes a list of scaffold (in one column)
# and two GFF files with segments (from-to coordinates)
# and computes intersections and differences of tracks

use strict;
use warnings;
use Set::Infinite;

my $list_of_scaffolds = $ARGV[0];
my $file1 = $ARGV[1];
my $file2 = $ARGV[2];
open(LIST, $list_of_scaffolds) or die("Cannot open file $list_of_scaffolds\n");
# set with intervals
my %set1;
my %set2;
my %result;
while (my $line = <LIST>) {
	chomp $line;
	# initialize empty set for each scaffold
	$set1{$line} = Set::Infinite->new;
	$set2{$line} = Set::Infinite->new;
	$result{$line} = Set::Infinite->new;
}

foreach my $key (keys (%set1)) {
	open(FILE1, $file1) or die("Cannot open input file $file1\n");
	while (my $line = <FILE1>) {
		chomp $line;
		my @fields = split(/\t/, $line);
		my $scaffold = $fields[0];
		if ($scaffold eq $key) {
			my $start = $fields[3];
			my $stop  = $fields[4];
			$set1{$scaffold} = $set1{$scaffold}->union($start, $stop);
		}
	}
	close FILE1;

	open(FILE2, $file2) or die("Cannot open input file $file2\n");
	while (my $line = <FILE2>) {
		chomp $line;
		my @fields = split(/\t/, $line);
		my $scaffold = $fields[0];
		if ($scaffold eq $key) {
			my $start = $fields[3];
			my $stop  = $fields[4];
			$set2{$scaffold} = $set2{$scaffold}->union($start, $stop);
		}
	}
	close FILE2;

	$result{$key} = $set1{$key}->intersection($set2{$key});
	if ($result{$key}->count > 0) {
		$result{$key}->iterate(sub {print $key."\tIntersection\tIntersection\t".$_[0]->min."\t".$_[0]->max."\t.\t.\t.\tTarget\n";}, sub {}, );
	}

	$result{$key} = $set1{$key}->difference($set2{$key});
	if ($result{$key}->count > 0) {
		my ($min, $max);
		$result{$key}->iterate(sub { $min = $_[0]->min+1 ; $max = $_[0]->max-1; print $key."\tDifference1\tDifference1\t".$min."\t".$max."\t.\t.\t.\tTarget\n";}, sub {}, );
	}

	$result{$key} = $set2{$key}->difference($set1{$key});
	if ($result{$key}->count > 0) {
		my ($min, $max);
		$result{$key}->iterate(sub { $min = $_[0]->min+1 ; $max = $_[0]->max-1; print $key."\tDifference2\tDifference2\t".$min."\t".$max."\t.\t.\t.\tTarget\n";}, sub {}, );
	}
}
