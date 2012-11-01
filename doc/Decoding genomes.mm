<map version="0.9.0">
<!-- To view this file, download free mind mapping software FreeMind from http://freemind.sourceforge.net -->
<node CREATED="1351784298255" ID="ID_1350092895" MODIFIED="1351784612550" TEXT="Decoding genomes">
<node CREATED="1351784394329" ID="ID_1833021382" LINK="http://www.repeatmasker.org/" MODIFIED="1351802411938" POSITION="right" TEXT="Repeat masker">
<icon BUILTIN="full-2"/>
<node CREATED="1351789109619" ID="ID_670757721" MODIFIED="1351789109619" TEXT=""/>
</node>
<node CREATED="1351784425447" FOLDED="true" ID="ID_405879752" MODIFIED="1351802421504" POSITION="right" TEXT="Blaster suite">
<node CREATED="1351784703011" FOLDED="true" ID="ID_707108288" MODIFIED="1351802404617" TEXT="Blaster">
<arrowlink DESTINATION="ID_896548935" ENDARROW="Default" ENDINCLINATION="92;0;" ID="Arrow_ID_636061436" STARTARROW="None" STARTINCLINATION="92;0;"/>
<icon BUILTIN="full-1"/>
<node CREATED="1351784935538" ID="ID_9218490" LINK="http://urgi.versailles.inra.fr/content/download/892/6830/file/Blaster_documentation.pdf" MODIFIED="1351784977226" TEXT="Documentation"/>
<node CREATED="1351785367636" ID="ID_123651242" MODIFIED="1351785372606" TEXT="blaster -q ./sequences/Genomes/test_japonica.fasta -s ./sequences/TE_protein_db_121015.fasta -n blastx -b ./japonica"/>
<node CREATED="1351785468829" ID="ID_1496865510" MODIFIED="1351785585588" TEXT="30 minutes on HPC"/>
<node CREATED="1351786220840" ID="ID_605044798" MODIFIED="1351786237353" TEXT="operates on test_japonica.fasta"/>
<node CREATED="1351786246068" ID="ID_1652749062" MODIFIED="1351786263981" TEXT="references TE_protein_db_121015.fasta"/>
<node CREATED="1351789721503" ID="ID_1476536784" MODIFIED="1351789729424" TEXT="compares two sets of sequences"/>
</node>
<node CREATED="1351784713805" ID="ID_294253610" MODIFIED="1351787336681" TEXT="Matcher">
<node CREATED="1351785410651" ID="ID_625403790" MODIFIED="1351787284784" TEXT="matcher2.25  -q ./sequences/Genomes/test_japonica.fasta -s ./sequences/TE_protein_db_121015.fasta -m ./japonica-308227504.align -b "/>
</node>
<node CREATED="1351784822767" ID="ID_1099836326" MODIFIED="1351784825091" TEXT="Grouper"/>
<node CREATED="1351784908118" ID="ID_961055248" LINK="http://urgi.versailles.inra.fr/Tools/REPET" MODIFIED="1351784927291" TEXT="Part of the REPET package"/>
</node>
<node CREATED="1351785596535" FOLDED="true" ID="ID_694736924" MODIFIED="1351790386624" POSITION="left" TEXT="Blat">
<node CREATED="1351786492049" ID="ID_1727948407" LINK="http://genome.ucsc.edu/cgi-bin/hgBlat" MODIFIED="1351786511308" TEXT="web interface"/>
<node CREATED="1351786635494" ID="ID_122042754" MODIFIED="1351786665114" TEXT="&quot;Blat is an alignment tool like BLAST, but it is structured differently. On DNA, Blat works by keeping an index of an entire genome in memory. Thus, the target database of BLAT is not a set of GenBank sequences, but instead an index derived from the assembly of the entire genome. The index -- which uses less than a gigabyte of RAM -- consists of all non-overlapping 11-mers except for those heavily involved in repeats. This smaller size means that Blat is far more easily mirrored. Blat of DNA is designed to quickly find sequences of 95% and greater similarity of length 40 bases or more. It may miss more divergent or short sequence alignments.&quot;"/>
<node CREATED="1351787124437" ID="ID_48551414" LINK="http://genome.ucsc.edu/FAQ/FAQblat.html#blat6" MODIFIED="1351787133876" TEXT="Speeding up with -ooc flag"/>
<node CREATED="1351786963046" ID="ID_1314717523" LINK="http://hgdownload.cse.ucsc.edu/admin/exe/" MODIFIED="1351787041822" TEXT="For HPC, need to download executable"/>
</node>
<node CREATED="1351786802459" FOLDED="true" ID="ID_896548935" LINK="http://blast.ncbi.nlm.nih.gov/" MODIFIED="1351802417421" POSITION="right" TEXT="Blast">
<arrowlink DESTINATION="ID_1833021382" ENDARROW="None" ENDINCLINATION="243;0;" ID="Arrow_ID_822621177" STARTARROW="Default" STARTINCLINATION="243;0;"/>
<node CREATED="1351787237286" ID="ID_706465069" MODIFIED="1351787237286" TEXT=""/>
<node CREATED="1351787258974" ID="ID_1922250967" MODIFIED="1351787270732" TEXT="Not called directly, called by blaster"/>
<node CREATED="1351788648404" ID="ID_93781806" LINK="http://blast.ncbi.nlm.nih.gov/Blast.cgi?CMD=Web&amp;PAGE_TYPE=BlastDocs&amp;DOC_TYPE=ProgSelectionGuide" MODIFIED="1351789865772" TEXT="Very lengthy description of choosing among different blast programs"/>
</node>
<node CREATED="1351788884549" FOLDED="true" ID="ID_1302762206" MODIFIED="1351802289269" POSITION="left" TEXT="Process flowcharts">
<node CREATED="1351788895206" ID="ID_66878628" MODIFIED="1351789118106">
<richcontent TYPE="NODE"><html>
  <head>
    
  </head>
  <body>
    <img src="GitHub/HCPU_midterm/doc/flowchart_1.PNG" />
  </body>
</html>
</richcontent>
</node>
<node CREATED="1351788922387" ID="ID_855488947" MODIFIED="1351788940476">
<richcontent TYPE="NODE"><html>
  <head>
    
  </head>
  <body>
    <img src="GitHub/HCPU_midterm/doc/flowchart_2.PNG" />
  </body>
</html>
</richcontent>
</node>
</node>
<node CREATED="1351789165179" ID="ID_241065602" MODIFIED="1351789388924" POSITION="right" TEXT="Repeat annotation">
<icon BUILTIN="full-3"/>
</node>
<node CREATED="1351789232576" FOLDED="true" ID="ID_819545990" MODIFIED="1351802427211" POSITION="left" TEXT="Summary of probem">
<node CREATED="1351789241750" ID="ID_1375109841" MODIFIED="1351789303324" TEXT="We have a long string of letters collected by a DNA sequencing machine."/>
<node CREATED="1351789306236" ID="ID_1746838136" MODIFIED="1351789332073" TEXT="We want to analyze that data, but it&apos;s really big and there&apos;s a lot of it we&apos;re not interested in."/>
<node CREATED="1351789336243" ID="ID_1776854725" MODIFIED="1351790457997" TEXT="The first step is to mask out all of the data we&apos;re not interested in, by comparing our new data to a reference database."/>
<node CREATED="1351802324450" ID="ID_1056079198" MODIFIED="1351802355866" TEXT="The overall question is to identify which parts of the process are bottlenecks, and how can we improve them."/>
<node CREATED="1351786292789" ID="ID_159963014" MODIFIED="1351786298588" TEXT="When to hard mask vs soft mask?"/>
</node>
<node CREATED="1351789396713" FOLDED="true" ID="ID_1553338723" MODIFIED="1351802297482" POSITION="right" TEXT="Files">
<node CREATED="1351787532182" ID="ID_1662815240" MODIFIED="1351787543318" TEXT="test_japonica.fasta">
<node CREATED="1351787548603" ID="ID_700248524" MODIFIED="1351787664805" TEXT="&gt;Chr1 NNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNCTAAACCCTAAACCCTAAAC CCTAAACCCTAAACCCTAAACCCTAAACCCTAAACCCTAACCCTAAACCCTAACCCTAAA CCCTAAACCCTAAACCCTAAACCCTAAACCCTAAACAGCTGACAGTACGATAGATCCACG CGAGAGGAACCGGAGAGACAACGGGATCCAGGCGCCAGCGACGGATCCGGGCGAGAGGGG AGTGGAGATCATGGATCCGTGCGGGAGGGGAAGAAGTCGCCGAATCCGACCCTCCCATCG"/>
</node>
<node CREATED="1351789405503" ID="ID_159057742" MODIFIED="1351789425638" TEXT="TE_protein_db_121015.fasta">
<node CREATED="1351789427733" ID="ID_1231996999" MODIFIED="1351789503311" TEXT="&gt;RIT_GmRTE-a01 MDQLRNNVNARSLPGSNALYGS... &gt;RIT_MtRTE-a01 KERVVLGLDSQSKTLSN... &gt;RIT_AhRTE-a01 RRYCTKVRSFPGS...."/>
</node>
<node CREATED="1351790272863" ID="ID_1283468273" MODIFIED="1351790285960" TEXT="indica_genome.fa">
<node CREATED="1351790287769" ID="ID_26245886" MODIFIED="1351790292820" TEXT="&gt;Chr01  2003-08-01 BGI GCGCGGGGAAGGGCCGATGGGCCGCGGGGGAGAGGAGAGAGAGGGAGGGG ACTGGGCCGAGCCGGCCCAAGAAGGGAAGGGGGTGGAAAGAAGACTTTTT AGCGGTTTTTCTTTTTATAAAACCGTTTTTAACGTTTGGTTTATTTCGTT..."/>
</node>
</node>
</node>
</map>
