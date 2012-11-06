##==========================================##
## R script for masking (e.g., ATC to atc)  ##
## the nucleotide and protein repeats in    ##
## genome.fasta.                            ##
##==========================================##

## This script requires the Bioconductor "package"
## to be installed

require(Biostrings)
## Load genome.fasta
gen <- readBStringSet("genome.fasta")

## Load protein and nucleotide gff files
## these are prot_us_merged.gff and nuc_us_merged.gff
## from the previous find_repeats.txt file
prot <- read.table("prot_us_merged.gff", as.is=T)
nuc <- read.table("nuc_us_merged.gff", as.is=T)


### These for loops work, but are not the best
### optimization probably wouldn't be too tough
## Mask proteins
for(i in 1:nrow(prot)){
  i1 <- prot[i, 4] # get start index of region
  i2 <- prot[i, 5] # get end index of region
  masking <- tolower(subseq(gen, i1, i2)) # mask the region
  subseq(gen, i1, i2) <- masking # update the genome
}

### This for loop is slightly redundant. It may be remasking
### regions from above. Could use some optimization.
## Mask nucleotides
for(i in 1:nrow(nuc)){
  i1 <- nuc[i, 4] # get start index of region
  i2 <- nuc[i, 5] # get end index of region
  masking <- tolower(subseq(gen, i1, i2)) # mask the region
  subseq(gen, i1, i2) <- masking # update the genome
}

## Write out the masked genome
writeXStringSet(gen, "masked_genome.fasta", format="fasta")
