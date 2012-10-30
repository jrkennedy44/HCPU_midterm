#!/usr/bin/perl

use warnings;
use strict;

use Getopt::Long;
use Pod::Usage;
use Bio::SeqIO;

use lib "/home/brunello/delfabbro/svn/reas/modules";
use GFF;

###################################################
# Description of chr.agp file
###################################################
#
# see http://www.ncbi.nlm.nih.gov/projects/genome/guide/Assembly/AGP_Specification.html
#
###################################################

my $agp = "";
my $gff = "";
my $out = "";
my $verbose = 0;
my $solid = 0;
my $help = 0;
my $original = 0;
my $reverse = 0;

GetOptions(
    'agp=s' => \$agp,
    'gff=s' => \$gff,
    'solid' => \$solid,
    'out=s' => \$out,
    'verbose' => \$verbose,
    'reverse' => \$reverse,
    'original-to-comment' => \$original,
    'help|?' => \$help) or pod2usage(2);
pod2usage(1) if $help;
pod2usage(1) if ($agp eq "");
pod2usage(1) if ($gff eq "");

open ERROR, ">&STDERR";  # redirect error to STDERR

sub debug {
    print ERROR $_[0] . "\n" if $verbose;
}

if ($out eq "") {
	open OUT, ">&STDOUT";
} else {
	open(OUT, ">$out") or die "Cannot open file $out for writing\n";
}

my %references_start;
my %references_stop;
my %references_strand;
my %references_chr;

my %reverse_map;

open FILE, $gff or die "Could not open gff file $gff\n";
open AGP, $agp or die ("Could not open agp file \"$agp\".\n");

debug("Acquiring agp informations");
while (my $line = <AGP> ) {
    chomp($line);
	my @data = split(/\t/,$line);
	if ($data[4] eq "F" or $data[4] eq "W") {
		my $id = $data[5];
		$references_chr{$id} = $data[0];
		$references_start{$id} = $data[1];
		$references_stop{$id} = $data[2];
		$references_strand{$id} = $data[8];
		if ($reverse) {
			$reverse_map{$data[0]}{$data[1]}{"stop"} = $data[2];
			$reverse_map{$data[0]}{$data[1]}{"scaffold"} = $id;
		
		}
	} # else is a gap: do nothing
}

my $count = 0;
my $skipped = 0;

debug("Processing gff file");
while (my $line = <FILE> ) { # for each line
	chomp($line); # remove \n from input
    if ( $line =~ /^\#/ or $line eq "") { # if a comment
        debug("Skip comment line");
    } else { # $line is not a comment
		$count++;
        print ERROR "Processed $count record for file \"$gff\"\n" if ($verbose and ($count % 5000 == 0) );  
        my $obj = GFF->new( line => $line );

		my $id = $obj->get_reference();
		my $start = $obj->get_start();
		my $stop = $obj->get_stop();
		my $strand = $obj->get_strand();

		my $found = 0;
		my $found_id = "";
		if ($reverse) {
			if (exists $reverse_map{$id}) {
				foreach my $ref_start (keys %{$reverse_map{$id}}) {
					#print OUT $id," ",$ref_start," ",$reverse_map{$id}{$ref_start}{"stop"}," ",$reverse_map{$id}{$ref_start}{"scaffold"},"\n";
					if ($ref_start <= $start and $reverse_map{$id}{$ref_start}{"stop"} >= $stop) {
						$found = 1;
						$found_id = $reverse_map{$id}{$ref_start}{"scaffold"};
						last;
					}
				}
				if ($found) {
					$id = $found_id;
				}
			}
		} else {
			$found = 1 if (exists $references_chr{$id});
		}
		

		if ( $found ) {
			if ($original) {
				my $old_comment = $obj->get_comment();
				if (length($old_comment) != 0) {
					$old_comment .= " ";
				}
				$obj->set_comment($old_comment . "; Coordinates ".$obj->get_reference() . ":" . $obj->get_start() . ".." . $obj->get_stop() . " strand " . $obj->get_strand());
			}
			if ($reverse) {
				$obj->set_reference($id);
			} else {
				$obj->set_reference($references_chr{$id});
			}
			if ($references_strand{$id} eq "-") {
				if ($reverse) {
					$obj->set_start($references_stop{$id} - $stop + 1);
					$obj->set_stop($references_stop{$id} - $start + 1);
				} else {
					$obj->set_start($references_stop{$id} - $stop + 1);
					$obj->set_stop($references_stop{$id} - $start + 1);
				}
				if ($strand ne ".") {
					$obj->set_strand($strand eq "-" ? "+" : "-");
				}
				if ($solid) {
					my $t = $obj->get_feature();
					my $g = $obj->get_group();
					if ($t =~ /FOR/) {
						$t =~ s/FOR/REV/;
						$g =~ s/FOR/REV/;
						$obj->set_feature($t);
						$obj->set_group($g);
					} elsif ($t =~ /REV/) {
						$t =~ s/REV/FOR/;
						$g =~ s/REV/FOR/;
						$obj->set_feature($t);
						$obj->set_group($g);
					}
				}
			} else {
				if ($reverse) {
					$obj->set_start($start - $references_start{$id} + 1);
					$obj->set_stop($stop - $references_start{$id} + 1);
				} else {
					$obj->set_start($references_start{$id} + $start - 1);
					$obj->set_stop($references_start{$id} + $stop - 1);
				}
			}
			print OUT $obj->return_line() . "\n";
		} else {
			$skipped++;
			debug("Warning: $id not found in agp file");
		}
	}
}
debug("\nDone");
debug("Processed $count record, $skipped skipped.");
close AGP;
close OUT;

__END__

=head1 Convert GFF to chromosomes

convert_gff_to_chromosomes.pl - Using this script

=head1 SYNOPSIS

perl convert_gff_to_chromosomes.pl --gff <gffname> --agp <agpname> [--out <filename>] [--reverse] [--solid] [--original-to-comment] [--verbose]
perl convert_gff_to_chromosomes.pl --help

  Options:
    --agp <agpname>          use <agpname> to get gff information (required)
    --gff <gffname>          use <gffname> to get fasta information (required)
    --out <filename>         write output to <filename>
    --reverse                reverse coordinates (from chr to scaffold)
    --solid                  convert solid FOR/REV name
    --original-to-comment    Add a comment with original coordinates
    --verbose                verbose output
    --help                   print this help message

Convert a gff from local (scaffold/contig) coordinates to chromosomes coordinate in relation with information in agp file. The output is redirected to STDOUT.

