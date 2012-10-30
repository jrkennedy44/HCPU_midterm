#!/usr/local/bin/perl
# Merges different tracks (in GFF format)
# usage:
# cat *.gff | gffsort.pl | /home/brunello/delfabbro/svn/reas/analisys/merge_gff_protein_classes.pl >output.gff

use strict;
use warnings;
use List::Util qw[min max];
use Getopt::Long;
use Pod::Usage;

use lib "/home/brunello/delfabbro/svn/reas/modules";
use GFF;

my $default_method = "Proteins";
my $default_source = "Clusterized_Proteins";
my $default_class  = "Clusterized_Proteins";
my $default_name   = "Protein_";
my $conflicts_file = "";
my $noconflicts_file = "";
my $evalue = "1e10";
my $hits = "1";
my $verbose = 0;
my $help = 0;

GetOptions(
    'conflicts-file=s' => \$conflicts_file,
	'remove-conflicts=s' => \$noconflicts_file,
	'evalue=s' => \$evalue,
    'verbose' => \$verbose,
    'help|?' => \$help) or pod2usage(2);
pod2usage(1) if ($help);

open ERROR, ">&STDERR";  # redirect error to STDERR

if ($conflicts_file ne "") {
    open CONFLICTS, ">$conflicts_file" or die("Could not open \"$conflicts_file\" for writing\n");
}

if ($noconflicts_file ne "") {
    open NOCONFLICTS, ">$noconflicts_file" or die("Could not open \"$noconflicts_file\" for writing\n");
}

sub debug {
    print ERROR $_[0] . "\n" if $verbose;
}
my $overlap = 0;

# Prepare datas

my $count = 0;

my $final;
my @data = ( );

sub write_noconflicts() {
	debug("Write noconflicts");
	#my %number;
	my %e;
	foreach my $line (@data) {
		my $gff = GFF->new(line =>$line);
		my $name = $gff->get_group();
		if (exists $e{$name}) {
			#$number{$name}++;
			$e{$name} = min($e{$name}, $gff->get_evalue());
		} else {
			#$number{$name} = 1;
			$e{$name} = $gff->get_evalue();
		}
	}
	my $min_evalue = -1;
	#my $name_evalue = "";
	foreach my $key ( keys %e ) {
		if ($min_evalue < 0) {
			#$name = $key;
			$min_evalue = $e{$key};
		} else {
			#$name_evalue = $e{$key} < $min_evalue ? $key : $name_evalue;
			$min_evalue = min($e{$key},$min_evalue);
		}
	}

	foreach my $key ( keys %e ) {
		if ($e{$key} > $min_evalue * $evalue) {
			delete $e{$key}
		}
	}

	foreach my $line (@data) {
		my $gff = GFF->new(line =>$line);
		if (exists $e{$gff->get_group()}) {
			print NOCONFLICTS $line . "\n";
		}
	}
	@data = ( );
}

sub writeLine { # write line
    my $group = $final->get_group();
    $group =~ s/_/X/g;
	$final->set_group($group);
    $final->set_type($group);
    $final->set_feature("$default_name$count");
    $count++;
    $final->set_strand(".");
    $final->set_phase(".");
    $final->unset_f_start();
    $final->unset_f_stop();
    $final->unset_comment();
	print $final->return_line() . "\n";
}
my $line;
do {
    $line = <STDIN>;
    chomp($line);
} while ($line =~ /^\#/);
debug("[$line]");
$final = GFF->new(line => $line);
my $temp;


while ($line = <STDIN>) {
    chomp($line);
	if ($noconflicts_file ne "") {
		push (@data,$line);
	}
    if ($line =~ /^\#/) {
        debug("Skip comment");
        next;
    }
    debug("[$line]");
    $temp = GFF->new(line => $line);
	if ($temp->get_reference() ne $final->get_reference()) { # changed scaffold
		debug("changed scaffold");
		if ($noconflicts_file ne "") {
			write_noconflicts();
		}
		writeLine();
		$final = $temp;
	} else { # same scaffold
		if ($temp->get_start() <= ($final->get_stop() + $overlap)) { # overlap
			debug("overlap");
			$final->set_stop(max($final->get_stop(),$temp->get_stop()));
			if ($temp->get_group() ne $final->get_group()) { # different class
				debug("changed class");
				my $t = $temp->get_group();
				my $f = $final->get_group();


                my $t1 = substr($t,0,1);
                my $t2 = substr($t,1,1);
                my $t3 = substr($t,2,1);
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
                if ($conflicts_file ne "") {
                    $temp->set_comment("; $f,$t->$r1$r2$r3");
                    print CONFLICTS $temp->return_line() . "\n";
                }
                $final->set_group("$r1$r2$r3");
				debug("Changed from $f to " . $final->get_group());
			}
		} else { # not overlapping
			debug("not overlapping");
			if ($noconflicts_file ne "") {
				write_noconflicts();
			}
			writeLine();
			$final = $temp;
		}
	}
}
if ($noconflicts_file ne "") {
	write_noconflicts();
}
writeLine();
debug("FINISHED!!");

if ($conflicts_file ne "") {
    close CONFLICTS;
}
if ($noconflicts_file ne "") {
    close NOCONFLICTS;
}


__END__

=head1 GFF Statistics

gffStatistics.pl - Using this script

=head1 SYNOPSIS

TODO ...
