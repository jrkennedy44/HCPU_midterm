#!/usr/bin/perl
#usage: calculate_bp.pl <gff file> <tag list file>
#the output has a .count and .bp extension for number of hits and basepairs, respectively

use strict;

if(!defined($ARGV[0]) || !defined($ARGV[1])){
          print <<EOF;
          usage: ./calculate.pl <gff file> <tag list file> 
EOF
exit -1
}

my $gff=$ARGV[0];
my $list=$ARGV[1];

open(GFF, $gff) or die("Unable to open file");
open(LIST, $list) or die("Unable to open file");
open(OUT, ">$gff.count") or die("Unable to open file");
my @msf= <MSF>;
my $exe;
my $line;
$exe=`cut -f 3,4,5 $gff | awk '{print \$1,(\$3-\$2+1)}' | sort > temp.txt`;
$exe= `awk '{print \$1}' temp.txt|uniq -c > $gff.num`;

while ($line=<LIST>){
   chomp ($line);
   $exe=`grep '$line' temp.txt | awk '{sum+=\$2} END { print \$1"\t",sum}'`;
   if ($exe ne ''){
      print OUT $exe;
   }
   else{
     
      print OUT "$line\t0";
   }   


}

$exe=`strings $gff.count > $gff.bp`;
$exe=`rm -f $gff.count`;
$exe=`rm -f temp.txt`;

exit (0);	
