#!/usr/bin/perl
#usage: cat input.gff |  merge_conflicts_not_overlapping_AGI.pl lengthfile >output.gff


use strict;
use warnings;

#use lib "/newwing/wing2/users/kchougule/Dario_data/pipeline/simone/lib";
use lib "/wing2/users/kchougule/dario_rep_class/repipe/simone/lib";
use GFF3;

my $default_name = "Sequence_";


if ($#ARGV != 0) {
	die ("Length file for referernce lengths is needed\n");
}

open(FILE,$ARGV[0]) or die("Cannot open file ".$ARGV[0]."\n");

my %ref = ( );
my %len = ( );

my $default_value = "XXXX";

print STDERR "Preparing data structure\n";
while (my $line = <FILE>) {
	chomp($line);
	my @a = split(/\t/,$line);
	my $l = $a[1];
	@{$ref{$a[0]}} = ( );
	$len{$a[0]} = $l;
	for (my $i = 0; $i < $l; $i++) {
		${$ref{$a[0]}}[$i] = $default_value;
	}

}
close(FILE);

my $verbose = 0;
sub debug {
    print STDERR $_[0] . "\n" if $verbose;
}

print STDERR "Acquiring data\n";
#my $line;
#do {
#    $line = <STDIN>;
#    chomp($line);
#} while ($line =~ /^\#/);
#debug("[$line]");
#my $final = GFF3->new(line => $line);

my $temp;

while (my $line = <STDIN>) {
	chomp($line);
	if ($line =~ /^\#/) {
	debug("Skip comment");
	next;
	}
	debug("[$line]");
	$temp = GFF3->new(line => $line);
	my $t = $temp->get_type();
	my $t1 = substr($t,0,1);
	my $t2 = substr($t,1,1);
	my $t3 = substr($t,2,1);
	my $reference = $temp->get_reference();
	for (my $i = $temp->get_start()-1; $i < $temp->get_stop(); $i++) {
		my $f = ${$ref{$reference}}[$i];
		if (not defined $f) {
			print STDERR $line,"\n";
			print STDERR "$reference/$i/".$len{$reference}."\n";
			print STDERR "$t";
			print STDERR ${$ref{$reference}}[$i-1];
			die("argh\n");
		}
		
		my $f1 = substr($f,0,1);
		my $f2 = substr($f,1,1);
		my $f3 = substr($f,2,1);

		my $r1;
		my $r2;
		my $r3;
		if ($f1 eq $t1) {
		    $r1 = $f1;
		    if ($f2 eq $t2) {
		        $r2 = $f2;
		        if ($f3 eq $t3) {
		            $r3 = $f3;
		        } elsif ($f3 eq "X") {
		            $r3 = $t3;
		        } elsif ($t3 eq "X") {
		            $r3 = $f3;
		        } else {
		            $r3 = "_";
		        }
		    } else {
		        if ($f2 eq "X") {
		            $r2 = $t2;
		            $r3 = $t3;
		        } elsif ($t2 eq "X") {
		            $r2 = $f2;
		            $r3 = $f3;
		        } else {
		            $r2 = "_";
		            $r3 = "_";
		        }                        
		    }
		} else {
		    if ($f1 eq "X") {
		        $r1 = $t1;
		        $r2 = $t2;
		        $r3 = $t3;
		    } elsif ($t1 eq "X") {
		        $r1 = $f1;
		        $r2 = $f2;
		        $r3 = $f3;
		    } else {
		        $r1 = "_";
		        $r2 = "_";
		        $r3 = "_";
		    }                        
		}
		${$ref{$reference}}[$i] = $r1.$r2.$r3;
	}
}

print STDERR "Writing results\n";

my $final = GFF3->new();
$final->set_source("repeat");

print "##gff-version3\n";

my $count = 0;
foreach my $reference (sort keys %ref) {
	$final->set_reference($reference);
	my $l = $len{$reference};
	my $last = $default_value;
	for (my $i = 0; $i < $l; $i++) {
		my $type = ${$ref{$reference}}[$i];
		if ($type eq $default_value) {
			# space
			if ($last ne $default_value) {
				$final->set_data("Name","$default_name$count");
				print $final->return_line() ."\n";
				$count++;
				$last = $default_value;
			}
		} else {
			$type =~ s/_/X/g;
			if ($last eq $default_value) {
				$final->set_start($i+1);
				$final->set_stop($i+1);
				$final->set_type($type);
				$last = $type;
			} else {
				if ($type eq $last) {
					$final->set_stop($i+1);
				} else {
					$final->set_data("Name","$default_name$count");
					print $final->return_line() ."\n";
					$count++;
					$last = $type;
					$final->set_start($i+1);
					$final->set_stop($i+1);
					$final->set_type($type);
				}
			}
		}
	}
	if ($last ne $default_value) {
		$final->set_data("Name","$default_name$count");
		print $final->return_line() ."\n";
		$count++;
		$last = $default_value;
	}
}


