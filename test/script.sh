#!/bin/bash

wget  http://mirrors.vbi.vt.edu/mirrors/ftp.ncbi.nih.gov/blast/executables/release/2.2.22/blast-2.2.22-ia32-linux.tar.gz

tar xzf blast-2.2.22-ia32-linux.tar.gz

export PATH=${PATH}:${HOME}/blast-2.2.22/bin

./blaster -q test_japonica.fasta -s test_prot.fasta -n blastx -B test_japonica 

./matcher2.25  -q test_japonica.fasta -s TE_protein_db_121015.fasta -m test_japonica.align -b japonica_bx

awk 'NR > 1' japonica_bx.clean_match.tab | awk 'col="repeat", x="."{if ($9 > $8) s = "+"; else s = "-"; printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n",$1,col,substr($7,1,3),$2,$3,$14,s,x,$7}' |sort -k 1,1 -k 4,4 > japonica_bx.gff

echo "JEFF!"

