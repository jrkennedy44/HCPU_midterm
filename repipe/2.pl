#!/usr/bin/perl
#usage: col3_mod.pl <gff file> 
#the output has a modified gff file having the the codes in column 3.
# Get options from command line

if(!defined($ARGV[0])){
          print <<EOF;
         usage: Repeat_annotation.pl <gff file>  <length_file> <Blast2gff_outputfile>(optional)
EOF
exit -1
}

$gff=$ARGV[0];
$lengthfile=$ARGV[1];
$blastfile=$ARGV[2];
#$listfile=$ARGV[3];

if( -e $blastfile)
{
#---------------------Manipulating gff file--------------------------------------------------------------------------------------------------------------------------------------------------------------
$exec =`sed 's/:AT_rich"/:SSL_AT_rich/g' $gff | sed 's/:GC_rich"/:SSL_GC_rich/g' | sed 's/[(]/SSS_(/g' | sed 's/Target\\s"Motif://g' |sed 's/RepeatMasker/repeat/g' | sed 's/"//g' | awk '{print\$1"\t"\$2"\t"substr(\$9,1,3)"\t"\$4"\t"\$5"\t"\$6"\t"\$7"\t"\$8"\t"\$9}'| awk '{ if (FNR > 3) print(\$0) }' > outys.gff`;
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
$exec= `cat sorted_file.gff | /opt/repipe/merge_conflicts_not_overlapping_AGI.pl $lengthfile > out.gff `;

$exec= `awk '{ gsub(/Sequence/,\$3); print }' out.gff | awk 'NR>1' > result_merge_conflict.gff`;

$exec= `rm -f out.gff sorted_file.gff `;
#-------------------------------------------------------------------------------------------------

#----------------run calculate.pl-----------------------------------------------------------------
$exec= `/opt/repipe/calculate_bp.pl result_merge_conflict.gff /opt/repipe/list`;
#-------------------------------------------------------------------------------------------------

#----------------separate into a table------------------------------------------------------------
$exec =`paste result_merge_conflict.gff.bp result_merge_conflict.gff.num | awk '{ \$1=\$1; print }' | awk '{ gsub(/ /,"\t"); print }' | cut -f 1-3 > final_table_result.txt`;
$exec= `rm -f outys.gff blast_tab_manipulate.gff result_merge_conflict.gff.bp result_merge_conflict.gff.num`;

#-------------------------------------------------------------------------------------------------
#print"$exec\n";
#print"$colsec\n";
#print"$code\n";
#-----------------
}
else{

#---------------------Manipulating gff file--------------------------------------------------------------------------------------------------------------------------------------------------------------
$exec =`sed 's/:AT_rich"/:SSL_AT_rich/g' $gff | sed 's/:GC_rich"/:SSL_GC_rich/g' | sed 's/[(]/SSS_(/g' | sed 's/Target\\s"Motif://g' |sed 's/RepeatMasker/repeat/g' | sed 's/"//g' | awk '{print\$1"\t"\$2"\t"substr(\$9,1,3)"\t"\$4"\t"\$5"\t"\$6"\t"\$7"\t"\$8"\t"\$9}'| awk '{ if (FNR > 3) print(\$0) }' > outys.gff`;
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#------------------------sort the gff file-------------------------------------------------------------------
$exec= `sort outys.gff > sorted_file.gff `;
#-----------------------------------------------------------------------------------------------------------------------------

#--------------------for Merge conflict------------------------------------------------------
$exec= `cat sorted_file.gff | /opt/repipe/merge_conflicts_not_overlapping_AGI.pl $lengthfile > out.gff `;

$exec= `awk '{ gsub(/Sequence/,\$3); print }' out.gff | awk 'NR>1' > result_merge_conflict.gff`;

$exec= `rm -f out.gff sorted_file.gff `;
#-------------------------------------------------------------------------------------------------

#----------------run calculate.pl-----------------------------------------------------------------
$exec= `/opt/repipe/calculate_bp.pl result_merge_conflict.gff /opt/repipe/list`;
#-------------------------------------------------------------------------------------------------

#----------------separate into a table------------------------------------------------------------
$exec =`paste result_merge_conflict.gff.bp result_merge_conflict.gff.num | awk '{ \$1=\$1; print }' | awk '{ gsub(/ /,"\t"); print }' | cut -f 1-3 > final_table_result.txt`;
$exec= `rm -f outys.gff blast_tab_manipulate.gff result_merge_conflict.gff.bp result_merge_conflict.gff.num`;

#-------------------------------------------------------------------------------------------------

}
