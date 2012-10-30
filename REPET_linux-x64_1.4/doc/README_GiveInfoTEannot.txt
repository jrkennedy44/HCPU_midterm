=============================
README for GiveInfoTEannot.py
=============================


Give some statistics about transposable elements (TE) annotation. It is necessary to have launch first the Teannot pipeline with a TEs library.
Different analysis types are available :
- 1 = stats per TE. The output file contains one line per TE with alignment statistics between TE copies and genome
- 2 = stats per cluster. The blastclust program clusterize the TEs (group them by cluster, using blastclust default parameters).

Note :  fragment refers to annotated fragment obtained before the “long join procedure” (TEannot step 7)
		copy refers to annotated linked fragments obtained after the “long join procedure” (TEannot step 7)


------------------------------------------------------
----------------- Output file fields -----------------
------------------------------------------------------

	<analysis type> 	TE or Cluster
	maxLength	TE length (max length if it's a group of TEs)
	meanLength	TE length (mean length if it's a group of TEs)
	covg	cumulative coverage (in bps) of all the fragments of a TE or group of TEs
	frags	number of fragments
	fullLgthFrags	number of full length fragments (+/- 5% difference with "maxLength" field)
	copies	number of copies
	fullLgthCopies	number of full length copies (+/- 5% difference with "maxLength" field)

The following fields give information about divergence (% of identity) between genome copies and their reference consensus, which is the most representative of the ancestor :

	meanId	mean identity calculated on the percentage of identities between each copy with it’s TE or a group of TEs
			Note: copy being a fragments chain, identity is weighted by fragments lengths
	sdId	standard deviation calculated on the percentages of identities
	minId	minimal percentage of identity of all copies of a TE or group of TEs
	q25Id	first quartile percentage of identity of all copies of a TE or group of TEs (i.e. 25% of copies have a percentage of identity < of this value)
	medId	median percentage of identity of all copies of a TE or group of TEs (i.e. 50% of copies have a percentage of identity < of this value)
	q75Id	third quartile percentage of identity of all copies of a TE or group of TEs (i.e. 75% of copies have a percentage of identity < of this value)
	maxId	maximal percentage of identity of all copies of a TE or group of TEs

The following fields give information about genome copies length :

	meanLgth	mean length of all copies of a TE or group of TEs
	sdLgth	standard deviation of length of all copies of a TE or group of TEs
	minLgth	minimal length of all copies of a TE or group of TEs
	q25Lgth	first quartile of length of all copies of a TE or group of TEs
	medLgth	median of length of all copies of a TE or group of TEs
	q75Lgth	third quartile of length of all copies of a TE or group of TEs
	maxLgth	maximal length of all copies of a TE or group of TEs

The following fields give information about percentage of consensus coverage by genome copies :
		
	meanLgthPerc	mean of coverage percentage of copies versus TE length ("maxLength" field)
			Note: copies mean coverage of the TE
	sdLgthPerc	standard deviation on TE coverage by genome copies (percent)
	minLgthPerc	minimal TE coverage by genome copies (percent)
	q25LgthPerc	first quartile, i.e. 25% of genome copies have a coverage < this value  (percent)
	medLgthPerc	median, i.e. 50% of genome copies have a coverage < this value  (percent)
	q75LgthPerc	third quartile, i.e. 75% of genome copies have a coverage < this value  (percent)
	maxLgthPerc	maximal TE coverage by genome copies (percent)
	