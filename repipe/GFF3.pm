package GFF3;

use strict;
use warnings;
use Carp;

my $GFFreference = 0;
my $GFFsource = 1;
my $GFFtype = 2;
my $GFFstart = 3;
my $GFFstop = 4;
my $GFFscore = 5;
my $GFFstrand = 6;
my $GFFphase = 7;

my $GFFgroup = 8;
my $GFFfeature = 9;
my $GFFf_start = 10;
my $GFFf_stop = 11;
my $GFFcomment = 12;

my $gff2 = 0;

sub remove_spaces {
	my $value = $_[0];
	$value =~ s/^[[:space:]]*//;
	$value =~ s/[[:space:]]*$//;
	return $value;
}

sub intelligent_sort {
	my ($a,$b) = @_;
	
	if ($a =~ /^id$/i) {
		return -1;
	} elsif ($b =~ /^id$/i) {
		return 1;
	} elsif ($a =~ /^name$/i) {
		return -1;
	} elsif ($b =~ /^name$/i) {
		return 1;
	} elsif ($a =~ /^parent$/i) {
		return -1;
	} elsif ($b =~ /^parent$/i) {
		return 1;
	} elsif ($a =~ /^pacid$/i) {
		return -1;
	} elsif ($b =~ /^pacid$/i) {
		return 1;
	} else {
		return $a cmp $b;
	}
}

sub new {
    my ($class, %arg) = @_;
    my %data = ( );
    if (exists $arg{gff2}) {
    	$gff2 = 1;
    }
    if (exists $arg{new} or (not exists $arg{line})) {
        return bless {
            _reference => "none",
            _source => "none",
            _type => "none",
            _start => "0",
            _stop => "0",
            _score => ".",
            _strand => ".",
            _phase => ".",
            _group => "",
            _feature => "",
            _f_start => "",
            _f_stop => "",
            _comment => "",
            _gff2 => $gff2,
            _data => \%data
        }, $class;
    }
    my $line = $arg{line} || croak("no line");
    my $group_in_name = (exists $arg{group_in_name}) ? $arg{group_in_name} : 0 ;
    chomp($line);
	$line =~ tr/\r//d;
    my @a = split(/[\t]/,$line);
    my @reference = ( );
    if ( $#a <= 6 ) {
        croak("not enough data in line \"$line\"");
    }
    my $group = "";
    my $feature = "";
    my $fstart = "";
    my $fstop = "";
    my $comment = "";
    if ( $#a > 7 ) {
        my $tail = remove_spaces($a[8]);
        for (my $i=9; $i <= $#a ; $i++) {
            $tail .= " ".remove_spaces($a[$i]); 
        }
		$tail = remove_spaces($tail);
        my @comments = split(/;/,$tail);
        for (my $j = 0; $j <= $#comments; $j++) {
            $comments[$j] = remove_spaces($comments[$j]);
            if ($gff2) { # <=== legacy GFF2
		    if ($comments[$j] =~ /^Target/) { # target, not comment
		        my @f = split(/[\ ]+/,$comments[$j]);
				if ( $#f >= 1 ) {
			        $f[1] =~ s/^\"//;
		      	    $f[1] =~ s/\"$//;
		            if ($f[1] =~ /:/ ) {
		               ($group,$feature) = split(/:/,$f[1]);
		            } else {
				$feature = $f[1];
			    }
		            if ($group_in_name and $feature =~ /_/) {
		                $feature =~ /^([^_]*)_.*$/;
		                $group = $1;
		            }
				}
		        if ( ($#f >= 3) and (not $f[2] =~ /[^0123456789]+/) and (not $f[3] =~ /[^0123456789]+/ ) ) {
		            $fstart = $f[2];
		            $fstop = $f[3];
		            if ($#f >= 4) {
		                $comment .= ";Note=\"";
		                for (my $i = 4 ; $i <= $#f; $i++) {
		                    $comment .= " " . $f[$i];
		                }
		                $comment .= "\"";
		            }
		        } else {
		            if ($#f >= 2) {
		                $comment .= ";Note=\"";
		                for (my $i = 2 ; $i <= $#f; $i++) {
		                    $comment .= " " . $f[$i];
		                }
		                $comment .= "\"";
		            }
		        }
		    } else { # is a comment
		    	$comment .= ";" if (length($comment) != 0);
		    	$comments[$j] =~ s/ /="/;
		    	$comments[$j] =~ s/$/"/;
	    		$comment .= $comments[$j];
		    }
            } else { # <==== GFF3
            	$comments[$j] =~ /^(.*)="*([^"]*)"*$/;
            	if (exists $data{$1}) {
            		$data{$1} .= ";$1=$2";
            	} else {
	            	$data{$1} = $2;
	        }
            }
        }
    }
    return bless {
        _reference => remove_spaces($a[0]),
        _source => remove_spaces($a[1]),
        _type => remove_spaces($a[2]),
        _start => remove_spaces($a[3]),
        _stop => remove_spaces($a[4]),
        _score => remove_spaces($a[5]),
        _strand => remove_spaces($a[6]),
        _phase => remove_spaces($a[7]),
        _group => $group,
        _feature => $feature,
        _f_start => $fstart,
        _f_stop => $fstop,
        _comment => $comment,
        _gff2 => $gff2,
        _data => \%data
    }, $class;
}

sub return_line {
    my $line = $_[0] -> {_reference};
    $line .= "\t" . $_[0] -> {_source};
    $line .= "\t" . $_[0] -> {_type};
    $line .= "\t" . $_[0] -> {_start};
    $line .= "\t" . $_[0] -> {_stop};
    $line .= "\t" . $_[0] -> {_score};
    $line .= "\t" . $_[0] -> {_strand};
    $line .= "\t" . $_[0] -> {_phase};
    if ($_[0] -> {_gff2} == 1) { # <==== legacy gff2
    	    my $bah = 0;
	    if ( $_[0] -> {_feature} ne "" ) {
		$line .= "\tName=\"";
		if ( $_[0] -> {_group} ne "" ) {
		    $line .= $_[0] -> {_group} . ":" . $_[0] -> {_feature};
		} else {
		    $line .= $_[0] -> {_feature};
		}
		$line .= "\"";
		if ( $_[0] -> {_f_start} ne "" ) {
		    $line .= ";Original_coordinates=\"" . $_[0] -> {_feature} . ":" . $_[0] -> {_f_start} . ".." . $_[0] -> {_f_stop} . "\"";
		}
		$bah = 1;
	    }
	    if ( $_[0] -> {_comment} ne "" ) {
	    	if ($bah) {
	    		$line .= ";";
	    	} else {
	    		$line .= "\t";
	    	}
		$line .= $_[0] -> {_comment};
	    }
    } else { # <==== GFF3
    	my $ref = \%{$_[0] -> {_data}};
    	my $something = 0;
    	foreach my $key (sort { intelligent_sort($a,$b) } keys %{$ref}) {
    		if ($something) {
    			$line .= ";";
    		} else {
    			$line .= "\t";
    			$something = 1;
    		}
		$line .= $key . "=" . $$ref{$key};
	}
    }
    return $line;
}

sub check_version {
	my ($self, $line) = @_;
	if ($line =~ /^##gff-version 3/i) {
		return 3;
	} else {
		return 2;
	}
}

sub get_reference { $_[0] -> {_reference} }
sub get_source    { $_[0] -> {_source} }
sub get_type      { $_[0] -> {_type} }
sub get_start     { $_[0] -> {_start} }
sub get_stop      { $_[0] -> {_stop} }
sub get_score     { $_[0] -> {_score} }
sub get_strand    { $_[0] -> {_strand} }
sub get_phase     { $_[0] -> {_phase} }
sub get_group     { $_[0] -> {_group} }
sub get_feature   { $_[0] -> {_feature} }
sub get_f_start   { $_[0] -> {_f_start} }
sub get_f_stop    { $_[0] -> {_f_stop} }
sub get_comment   { $_[0] -> {_comment} }
sub get_gff2      { $_[0] -> {_gff2} }
sub get_data      {
	my ($self, $key) = @_;
	my $ref = \%{$self -> {_data}};
	if ($self -> {_gff2}) {
		if ($key =~ /name/i) {
			return $self->{feature};
		}
	} else {
		if (exists $$ref{$key}) {
			return $$ref{$key};
		} else {
			return "";
		}
	}
}

sub get_evalue {
	$_[0] -> {_comment} =~ /[Ee][_-]*[vV][aA][lL][uU][eE] ([0-9\-eE]*)/ ;
	return $1;
}

sub set_reference {
    my ($self, $reference) = @_;
    $self -> {_reference} = $reference if $reference;
}

sub set_source {
    my ($self, $source) = @_;
    $self -> {_source} = $source if $source;
}

sub set_start {
    my ($self, $start) = @_;
    $self -> {_start} = $start if $start;
}

sub set_stop {
    my ($self, $stop) = @_;
    $self -> {_stop} = $stop if $stop;
}

sub set_type {
    my ($self, $type) = @_;
    $self -> {_type} = $type if $type;
}

sub set_score {
    my ($self, $score) = @_;
    $self -> {_score} = $score;
}

sub set_strand {
    my ($self, $strand) = @_;
    $self -> {_strand} = $strand if $strand;
}

sub set_phase {
    my ($self, $phase) = @_;
    $self -> {_phase} = $phase if $phase;
}

sub set_group {
    my ($self, $group) = @_;
    $self -> {_group} = $group if $group;
}

sub set_feature {
    my ($self, $feature) = @_;
    $self -> {_feature} = $feature if $feature;
}

sub set_f_start {
    my ($self, $f_start) = @_;
    $self -> {_f_start} = $f_start if $f_start;
}

sub set_f_stop {
    my ($self, $f_stop) = @_;
    $self -> {_f_stop} = $f_stop if $f_stop;
}

sub set_comment {
    my ($self, $comment) = @_;
    $self -> {_comment} = $comment if $comment;
}

sub set_gff2 {
    my ($self, $gff2) = @_;
    $self -> {_gff2} = $gff2 if $gff2;
}

sub set_data {
    my ($self, $key, $value) = @_;
    my $ref = \%{$self -> {_data}};
    $$ref{$key} = $value;
}

sub unset_feature {
    my $self = $_[0];
    $self -> {_feature} = "";
}

sub unset_group {
    my $self = $_[0];
    $self -> {_group} = "";
}

sub unset_f_start {
    my $self = $_[0];
    $self -> {_f_start} = "";
}

sub unset_f_stop {
    my $self = $_[0];
    $self -> {_f_stop} = "";
}

sub unset_comment {
    my $self = $_[0];
    $self -> {_comment} = "";
}

sub unset_data {
    my ($self, $key) = @_;
    my $ref = \%{$self -> {_data}};
    delete($$ref{$key});
}

sub unset_all_data {
    my ($self) = @_;
    my $ref = \%{$self -> {_data}};
    foreach my $key (keys %$ref) {
	    delete($$ref{$key});
    }
}


1; # END
