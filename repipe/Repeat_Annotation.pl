#!/usr/bin/perl
#usage: col3_mod.pl <gff file> 
#the output has a modified gff file having the the codes in column 3.
# Get options from command line



if(!defined($ARGV[0])){
          print <<EOF;
         usage: Repeat_Annotation.pl <gff file>  <length_file> <Blast_Inputfile>(optional)
EOF
exit -1
}

$gff=$ARGV[0];
$lengthfile=$ARGV[1];
$blastfile=$ARGV[2];
#$listfile=$ARGV[3];

#print"$gff\n";
@base_gff_name = split("\\.",$gff);
#push(@x,@base_gff_name);
#print"$base_gff_name[0]\n";

if( -e $blastfile)
{
#---------------------Manipulating gff file--------------------------------------------------------------------------------------------------------------------------------------------------------------
$exec =`sed 's/:AT_rich"/:SSL_AT_rich/g' $gff | sed 's/:GC_rich"/:SSL_GC_rich/g' | sed 's/[(]/SSS_(/g' | sed  's/SUBTEL_sat/SRS_SUBTEL_sat/g'| sed 's/Target\\s"Motif://g' |sed 's/RepeatMasker/repeat/g' | sed 's/"//g' | awk '{print\$1"\t"\$2"\t"substr(\$9,1,3)"\t"\$4"\t"\$5"\t"\$6"\t"\$7"\t"\$8"\t"\$9}'| awk '{ if (FNR > 3) print(\$0) }' > outys.gff`;
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#---------------------Manipulating output of blast2gff File-------------------------------------------------------------------------------------

$exec = `awk '{print\$1"\t"\$2"\t"substr(\$9,1,3)"\t"\$4"\t"\$5"\t"\$6"\t"\$7"\t"\$8"\t"\$9}' $blastfile > interim_blast_tab_manipulate.gff` ;

@blast2col = `awk '{print \$2}' interim_blast_tab_manipulate.gff`;
chomp(@blast2col);
$seccol = $blast2col[0];
$exec = `awk '{ gsub(/$seccol/,"repeat"); print }' interim_blast_tab_manipulate.gff > blast_tab_manipulate.gff`;
$exec= `rm -f interim_blast_tab_manipulate.gff`;
#-----------------------------------------------------------------------------------------------------------------------------------------------


#------------------------Concatenate and sort the two files-------------------------------------------------------------------
$exec= `cat outys.gff blast_tab_manipulate.gff | sort > sorted_file.gff `;
#-----------------------------------------------------------------------------------------------------------------------------



#$exec= `rm -f temp.txt temp.gff`;

#--------------------for Merge conflict------------------------------------------------------
$exec= `cat sorted_file.gff | /wing2/users/kchougule/dario_rep_class/repipe/merge_conflicts_not_overlapping_AGI.pl $lengthfile > out.gff `;

$exec= `awk '{ gsub(/Sequence/,\$3); print }' out.gff | awk 'NR>1' > $base_gff_name[0].cons.gff`;

$exec= `rm -f out.gff sorted_file.gff `;
#-------------------------------------------------------------------------------------------------

#----------------run calculate.pl-----------------------------------------------------------------
$exec= `/wing2/users/kchougule/dario_rep_class/repipe/calculate_bp.pl $base_gff_name[0].cons.gff /wing2/users/kchougule/dario_rep_class/repipe/list`;
#-------------------------------------------------------------------------------------------------

#----------------separate into a table------------------------------------------------------------
$exec =`paste $base_gff_name[0].cons.gff.bp $base_gff_name[0].cons.gff.num | awk '{ \$1=\$1; print }' | awk '{ gsub(/ /,"\t"); print }' | cut -f 1-3 > $base_gff_name[0].txt`;
$exec= `rm -f outys.gff blast_tab_manipulate.gff $base_gff_name[0].cons.gff.bp $base_gff_name[0].cons.gff.num`;

#-------------------------------------------------------------------------------------------------
#print"$exec\n";
#print"$colsec\n";
#print"$code\n";
#-----------------
}
else{

#---------------------Manipulating gff file--------------------------------------------------------------------------------------------------------------------------------------------------------------
$exec =`sed 's/:AT_rich"/:SSL_AT_rich/g' $gff | sed 's/:GC_rich"/:SSL_GC_rich/g' | sed 's/[(]/SSS_(/g' | sed  's/SUBTEL_sat/SRS_SUBTEL_sat/g'| sed 's/Target\\s"Motif://g' |sed 's/RepeatMasker/repeat/g' | sed 's/"//g' | awk '{print\$1"\t"\$2"\t"substr(\$9,1,3)"\t"\$4"\t"\$5"\t"\$6"\t"\$7"\t"\$8"\t"\$9}'| awk '{ if (FNR > 3) print(\$0) }' > outys.gff`;
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#------------------------sort the gff file-------------------------------------------------------------------
$exec= `sort outys.gff > sorted_file.gff `;
#-----------------------------------------------------------------------------------------------------------------------------

#--------------------for Merge conflict------------------------------------------------------
$exec= `cat sorted_file.gff | /wing2/users/kchougule/dario_rep_class/repipe/merge_conflicts_not_overlapping_AGI.pl $lengthfile > out.gff `;

$exec= `awk '{ gsub(/Sequence/,\$3); print }' out.gff | awk 'NR>1' > $base_gff_name[0].cons.gff`;

$exec= `rm -f out.gff sorted_file.gff `;
#-------------------------------------------------------------------------------------------------

#----------------run calculate.pl-----------------------------------------------------------------
$exec= `/wing2/users/kchougule/dario_rep_class/repipe/calculate_bp.pl $base_gff_name[0].cons.gff /wing2/users/kchougule/dario_rep_class/repipe/list`;
#-------------------------------------------------------------------------------------------------

#----------------separate into a table------------------------------------------------------------
$exec =`paste $base_gff_name[0].cons.gff.bp $base_gff_name[0].cons.gff.num | awk '{ \$1=\$1; print }' | awk '{ gsub(/ /,"\t"); print }' | cut -f 1-3 > $base_gff_name[0].txt`;
$exec= `rm -f outys.gff blast_tab_manipulate.gff $base_gff_name[0].cons.gff.bp $base_gff_name[0].cons.gff.num`;

#-------------------------------------------------------------------------------------------------

}
