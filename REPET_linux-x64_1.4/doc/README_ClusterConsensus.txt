==============================
README for ClusterConsensus.py
==============================


At the end of the TEdenovo pipeline, it is useful, or even required, to investigate the relationships among the de novo consensus that have been built.
"ClusterConsensus.py" is used to facilitate the manual curation of TE consensus.
It starts by grouping them into clusters (i.e. "TE families") and then build a multiple alignment for each cluster.
These multiple alignments can be visualized with Jalview to ease the manual curation and the interpretation of TE family (cluster) diversification.

WARNING: if you want to launch "ClusterConsensus.py" through computer cluster at URGI, you have to wrap the command in a "qsub".
$ qsub -cwd -j y -V -N launchClusterConsensus <<EOF
> ClusterConsensns.py -i ...
> EOF
Or write your command in a text file (e.g. "ClusterCons.sh") and launch: 
$ qsub -cwd -V ClusterCons.sh

"ClusterConsensus.py" can work on whatever TE sequences you have.
However, it's better to use consensus from the TEdenovo pipeline.
Moreover, it's also convenient to launch the TEannot pipeline before.


------------------------------------------------------------
===================== Global options =======================
------------------------------------------------------------
	-h : Help page.
	-i <input file> (mandatory): Input fasta file name, containing TE consensus with short headers. This file could be the result of TEdenovo pipeline (e.g. "DmelChr4_denovoLib.fa").
	-v <verbosity> (optional): Verbosity level (default = 0, you can also choose 1 or 2)


------------------------------------------------------------
=================== options for step 1 =====================
------------------------------------------------------------

Clustering of consensus with BlastClust.
	-s 1 (mandatory)
	-I <identity_threshold> (optional): Identity threshold for clustering (default = 0).
	-c <coverage> (optional): Coverage for clustering (default = 0.8).
	-r <reference_sequence> (optional): well-known reference TE sequences file name (format = 'fasta'). It is useful when you want to curate manually consensus with well-known TE sequences (e.g. from Repbase, BDGP, TREP...).

Example :
ClusterConsensus.py -s 1 -i DmelChr4_denovoLibTEs.fa -r wellKnownTEs_for_DmelChr4.fa -v 2
--------------- Results (output files tree) ----------------
Blastclust
	DmelChr4_denovoLibTEs.fa_blastclust.fa
	GiveInfoBlastclust_DmelChr4_denovoLibTEs.fa_blastclust.fa.log
compRefTEs (only if "-r" option specified)
	DmelChr4_denovoLibTEs.fa_vs_wellKnownTEs_for_DmelChr4.fa.m2.align.merged.match.path
	DmelChr4_denovoLibTEs.fa_vs_wellKnownTEs_for_DmelChr4.fa.m2.align.merged.match.tab
	DmelChr4_denovoLibTEs.fa_vs_wellKnownTEs_for_DmelChr4.fa.m2.align.merged.match.tab_qryCategories.txt
	DmelChr4_denovoLibTEs.fa_vs_wellKnownTEs_for_DmelChr4.fa.m2.align.merged.match.tab_sbjCategories.txt
	DmelChr4_denovoLibTEs.fa_vs_wellKnownTEs_for_DmelChr4.fa.m2.align.merged.match.tab_tabFileReader.txt


------------------------------------------------------------
=================== options for step 2 =====================
------------------------------------------------------------

Create a directory by cluster (clusters from step 1) in data_per_family directory. A cluster can be considered as a TE family, so we use the term "family".
In each "family_..." directory, you can find :
* "family<id>.fa" : a fasta file containing all consensus of the family. The other files beginning by "family<id>.fa" have more information in the header of each consensus, such as their length, their number of TE copies.
* "<consensus name>_consensus.fa" : a fasta file containing a consensus
* "<consensus name>_AbaMatches.fa" : a fasta file containing all sequences from "aba matches". In TEdenovo pipeline, each consensus is built from sequences found by all-by-all ("aBa") alignments.
	WARNING : Only when TEdenovo and TEannot pipelines have been launched before.
	-s 2 (mandatory)
	-C <config_file> (mandatory): TEdenovo pipeline configuration file to find sequences used to build consensus (and to connect to database if -a option specified).
	-a <table_name> (optional): annotation table name (<projectName>_chr_allTEs_nr_noSSR_join_path) to add copies information. This table comes from TEannot pipeline.
	-r <reference_sequence_file_name> (optional): well-known reference TE sequences file name (format = 'fasta'). It is useful when you want to curate manually the consensus with well-known TE sequences (e.g. from Repbase, BDGP, TREP...).
	
Example :
ClusterConsensus.py -s 2 -i DmelChr4_denovoLibTEs.fa -a DmelChr4_chr_allTEs_nr_noSSR_join_path -C TEdenovo.cfg -v 2
--------------- Results (output files tree) ----------------
data_per_family
	family_001
	...
	family_007
		family7.fa.fullS.seqlen.copy.aBa
		family7.fa.fullS.seqlen.copy
		family7.fa.fullS.seqlen
		family7.fa.fullS
		family7.fa
		DmelChr4-B-R79-Map20_classI-LTR-incomp_consensus.fa
		DmelChr4-B-R79-Map20_classI-LTR-incomp_AbaMatches.fa
		DmelChr4-B-G677-Map3_classI-LTR-comp_consensus.fa
		DmelChr4-B-G677-Map3_classI-LTR-comp_AbaMatches.fa
		DmelChr4-B-G614-Map4_classI-LTR-comp_consensus.fa
		DmelChr4-B-G614-Map4_classI-LTR-comp_AbaMatches.fa
		DmelChr4-B-G328-Map5_classI-LTR-incomp_consensus.fa
		DmelChr4-B-G328-Map5_classI-LTR-incomp_AbaMatches.fa
		DmelChr4-B-G30-Map17_confused_consensus.fa
		DmelChr4-B-G30-Map17_confused_AbaMatches.fa
	...
	family_430


------------------------------------------------------------
=================== options for step 3 =====================
------------------------------------------------------------

This step offers different methods to build a phylogeny.
Choose one TE family at a time to build a multiple sequence alignment (aka "MSA") and a phylogeny.
To specify a family, give the family identifier with -F option (e.g. '7' for "BlastclustCluster7Mb1 DmelChr4-B-G601-Map4_classII-TIR-comp" consensus, find in Blastclust/DmelChr4_denovoLibTEs.fa_blastclust.fa).
Sometimes, it is possible to choose the multiple alignment program with -M option. In fact, according to the sequences to be aligned, some algorithms work better than others.
	WARNING: Installation of sreformat (in hmmer package) is necessary.
			 Installation of phyml is necessary.

=================== options for step 3a ====================
This option builds a multiple alignment and a phylogeny of all consensus in the chosen family. 
	WARNING: Installation of 'mummer' is required.
	-s 3a (mandatory)
	-F <family_id> (mandatory): family identifier
	-M <method> (optional): Multiple alignment method (default = 'Mafft', you can also choose 'Map' or 'Tcoffee').

Example :
ClusterConsensus.py -s 3a -i DmelChr4_denovoLibTEs.fa -F 7 -M Map -v 2
--------------- Results (output files tree) ----------------
data_per_family
	family_007
		family7.fa.fullS.seqlen.copy.oriented
		family7.fa.fullS.seqlen.copy.oriented_map.afa
		family7.fa.fullS.seqlen.copy.oriented_map.afa.shortHlink
		family7.fa.fullS.seqlen.copy.oriented_map.afa.shortH
		family7.fa.fullS.seqlen.copy.oriented_map.afa.shortH.phylip

=================== options for step 3b ====================
This option builds a multiple alignment and a phylogeny of all consensus and also for their all-by-all matches (from step 1 of the TEdenovo pipeline).
	WARNING: Installation of 'mummer' is required.
	-s 3b (mandatory)
	-F <family_id> (mandatory): family identifier
	-M <method> (optional): Multiple alignment method (default = 'Mafft', you can also choose 'Map' or 'Tcoffee').
			
Example :
ClusterConsensus.py -s 3b -i DmelChr4_denovoLibTEs.fa -F 7 -M Map -v 2
--------------- Results (output files tree) ----------------
data_per_family
	family_007
		family7.fa.fullS.seqlen.copy.aBa.oriented
		family7.fa.fullS.seqlen.copy.aBa.oriented_map.afa
		family7.fa.fullS.seqlen.copy.aBa.oriented_map.afa.shortHlink
		family7.fa.fullS.seqlen.copy.aBa.oriented_map.afa.shortH
		family7.fa.fullS.seqlen.copy.aBa.oriented_map.afa.shortH.phylip

=================== options for step 3c ====================
This option uses ms-msa to build a multiple alignment and phylogeny of consensus and all-by-all matches. "ms" means master-slave. It uses "refalign" too, taking a reference sequence as ancestor to orientate the indel events.
At first, each consensus is aligned with its all-by-all matches, and then "profile" alignment between previous alignments are made with "muscle" until all sequences are aligned.
	WARNING: Installation of 'muscle' is required.
	-s 3c (mandatory)
	-F <family_id> (mandatory): family identifier

Example :
ClusterConsensus.py -s 3c -i DmelChr4_denovoLibTEs.fa -F 7 -v 2
--------------- Results (output files tree) ----------------
data_per_family
	family_007 
		consensus_DmelChr4-B-G30-Map17_confused_withAbaMatches.fa
		consensus_DmelChr4-B-G30-Map17_confused_withAbaMatches.fa.oriented
		consensus_DmelChr4-B-G30-Map17_confused_withAbaMatches.fa.oriented.fa_aln
		consensus_DmelChr4-B-G328-Map5_classI-LTR-incomp_withAbaMatches.fa
		consensus_DmelChr4-B-G328-Map5_classI-LTR-incomp_withAbaMatches.fa.oriented
		consensus_DmelChr4-B-G328-Map5_classI-LTR-incomp_withAbaMatches.fa.oriented.fa_aln
		consensus_DmelChr4-B-G614-Map4_classI-LTR-comp_withAbaMatches.fa
		consensus_DmelChr4-B-G614-Map4_classI-LTR-comp_withAbaMatches.fa.oriented
		consensus_DmelChr4-B-G614-Map4_classI-LTR-comp_withAbaMatches.fa.oriented.fa_aln
		consensus_DmelChr4-B-G677-Map3_classI-LTR-comp_withAbaMatches.fa
		consensus_DmelChr4-B-G677-Map3_classI-LTR-comp_withAbaMatches.fa.oriented
		consensus_DmelChr4-B-G677-Map3_classI-LTR-comp_withAbaMatches.fa.oriented.fa_aln
		consensus_DmelChr4-B-R79-Map20_classI-LTR-incomp_withAbaMatches.fa
		consensus_DmelChr4-B-R79-Map20_classI-LTR-incomp_withAbaMatches.fa.oriented
		consensus_DmelChr4-B-R79-Map20_classI-LTR-incomp_withAbaMatches.fa.oriented.fa_aln 
		family7_profilesAba.afa
		family7_profilesAba.afa.shortH
		family7_profilesAba.afa.shortHlink
		family7_profilesAba.afa.shortH.phylip

=================== options for step 3d ====================
This option uses msa to build a multiple alignment and phylogeny of consensus and copies (consensus and copies sequences come from TEannot pipeline).
	WARNING: Installation of 'mummer' is required.
	-s 3d (mandatory)
	-F <family_id> (mandatory): family identifier
	-a <table_name> (mandatory): Name of the table (<projectName>_chr_allTEs_nr_noSSR_join_path), recording the annotations. This table comes from TEannot pipeline.
	-g <table_name> (mandatory): Genome sequences table name (<projectName>_chr_seq), to retrieve the sequence of each TE copy.
	-C <config_file> (mandatory): Configuration file from TEdenovo pipeline.
	-M <method> (optional): Multiple alignment method (default = 'Mafft', you can also choose 'Map' or 'Tcoffee').
	-l <length> (optional): TE copies' minimum length (in bp, default = 100).
	-n <number_longest_TE> (optional): Longest TE copies number (default = 20), these longest copies are taken for consensus construction.
	-p <min_proportion> (optional): Minimum proportion of copy compared to its consensus (default = 0.5).
    		
Example :
ClusterConsensus.py -s 3d -i DmelChr4_denovoLibTEs.fa -a DmelChr4_chr_allTEs_nr_noSSR_join_path -g DmelChr4_chr_seq -C TEdenovo.cfg -F 7 -M Map -v 2
--------------- Results (output files tree) ----------------
data_per_family
	family_007
		DmelChr4-B-G30-Map17_confused_20LongestCopies.fa
		DmelChr4-B-G328-Map5_classI-LTR-incomp_20LongestCopies.fa
		DmelChr4-B-G614-Map4_classI-LTR-comp_20LongestCopies.fa
		DmelChr4-B-G677-Map3_classI-LTR-comp_20LongestCopies.fa
		DmelChr4-B-R79-Map20_classI-LTR-incomp_20LongestCopies.fa
		family7_BestRefseqsConsensus20Copies.fa
		family7_BestRefseqsConsensus20Copies.fa.oriented
		family7_BestRefseqsConsensus20Copies.fa.oriented_map.afa
		family7_BestRefseqsConsensus20Copies.fa.oriented_map.afa.shortH
		family7_BestRefseqsConsensus20Copies.fa.oriented_map.afa.shortHlink
		family7_BestRefseqsConsensus20Copies.fa.oriented_map.afa.shortH.phylip
	
=================== options for step 3e ====================
This option uses ms-msa to build a multiple alignment and phylogney of consensus and copies. "ms" means master-slave.
	-s 3e (mandatory)
	-F <family_id> (mandatory): family identifier
	-n <number_longest_TE> (optional): Longest TE copies number (default = 20), these longest copies are taken for consensus construction.
    		
Example :
ClusterConsensus.py -s 3e -i DmelChr4_denovoLibTEs.fa -F 7 -v 2
--------------- Results (output files tree) ----------------
data_per_family
	family_007
		consensus_DmelChr4-B-G677-Map3_classI-LTR-comp_withCopies.fa
		consensus_DmelChr4-B-G677-Map3_classI-LTR-comp_withCopies.fa.oriented
		consensus_DmelChr4-B-G677-Map3_classI-LTR-comp_withCopies.fa.oriented.fa_aln
		consensus_DmelChr4-B-R79-Map20_classI-LTR-incomp_withCopies.fa
		consensus_DmelChr4-B-R79-Map20_classI-LTR-incomp_withCopies.fa.oriented
		consensus_DmelChr4-B-R79-Map20_classI-LTR-incomp_withCopies.fa.oriented.fa_aln
		family7_profilesCopies.afa
		family7_profilesCopies.afa.shortH
		family7_profilesCopies.afa.shortHlink
		family7_profilesCopies.afa.shortH.phylip
