import sys
from math import *
from pyRepet.seq.Bioseq import Bioseq
from pyRepet.seq.BioseqDB import BioseqDB
import pyRepet.util.Stat
import random

#------------------------------------------------------------------------------

class AlignedBioseqDB( BioseqDB ):

    #--------------------------------------------------------------------------

    def length( self ):

        """calculate the length of the MSA"""

        return self.db[0].getLength()

    #--------------------------------------------------------------------------

    def true_length( self, seq ):

        """calculate the true length of the sequence (without any gaps)"""

        count = 0
        for pos in xrange(0,len(seq)):
            if seq[pos] != '-':
                count += 1
        return count
    
    #--------------------------------------------------------------------------

    def getListOccPerSite( self ):

        """
        Record the occurrences of symbols (A, T, G, C, N, -, ...) at each site

        @return: list of dico whose keys are symbols and values are their occurrences
        @rtype: list of dico
        """

        lOccPerSite = []   # list of dictionaries, one per position on the sequence
        n = 0    # nb of sequences parsed from the input file
        firstSeq = True

        # for each sequence in the bank
        for bs in self.db:
            if bs.sequence == None:
                break
            n += 1

            # if it is the first to be parsed, create a dico at each site
            if firstSeq:
                for i in xrange(0,len(bs.sequence)):
                    lOccPerSite.append( {} )
                firstSeq = False

            # for each site, add its nucleotide
            for i in xrange(0,len(bs.sequence)):
                nuc = bs.sequence[i].upper()
                if lOccPerSite[i].has_key( nuc ):
                    lOccPerSite[i][nuc] += 1
                else:
                    lOccPerSite[i][nuc] = 1

        return lOccPerSite

    #--------------------------------------------------------------------------

    def getConsensus( self, minNbNt, minPropNt=0.0, verbose=0 ):

        """
        Make a consensus from the MSA

        @param minNbNt: minimum nb of nucleotides to edit a consensus
        @type minNbNt: integer

        @param minPropNt: minimum proportion for the major nucleotide to be used, otherwise add 'N' (default=0.0)
        @type minPropNt: float

        @param verbose: level of information sent to stdout (default=0/1)
        @type verbose: integer

        @return: consensus
        @rtype: Bioseq instance
        """

        maxPropN = 0.40  # discard consensus if more than 40% of N's

        nbInSeq = self.getSize()
        if verbose > 0:
            print "nb of aligned sequences: %i" % ( nbInSeq ); sys.stdout.flush()
        if nbInSeq < 2:
            print "ERROR: can't make a consensus with less than 2 sequences"
            sys.exit(1)
        if minNbNt >= nbInSeq:
            minNbNt = nbInSeq - 1
            print "minNbNt=%i" % ( minNbNt )
        if minPropNt >= 1.0:
            print "ERROR: minPropNt=%.2f should be a proportion (below 1.0)" % ( minPropNt )
            sys.exit(1)

        lOccPerSite = self.getListOccPerSite()
        nbSites = len(lOccPerSite)
        if verbose > 0:
            print "nb of sites: %i" % ( nbSites ); sys.stdout.flush()

        seqConsensus = ""
        stat = pyRepet.util.Stat.Stat()

        # for each site (i.e. each column of the MSA)
        nbRmvColumns = 0
        countSites = 0
        for dNt2Occ in lOccPerSite:
            countSites += 1
            if verbose > 1:
                print "site %s / %i" % ( str(countSites).zfill( len(str(nbSites)) ),
                                         nbSites )
                sys.stdout.flush()
            occMaxNt = 0   # occurrences of the predominant nucleotide at this site
            lBestNt = []
            nbNt = 0   # total nb of A, T, G and C (no gap)

            # for each distinct symbol at this site (A, T, G, C, N, -,...)
            for j in dNt2Occ.keys():
                if j != "-":
                    nbNt += dNt2Occ[j]
                    if verbose > 1:
                        print "%s: %i" % ( j, dNt2Occ[j] )
                    if dNt2Occ[j] > occMaxNt:
                        occMaxNt = dNt2Occ[j]
                        lBestNt = [ j ]
                    elif dNt2Occ[j] == occMaxNt:
                        lBestNt.append( j )
            if nbNt > 0:
                stat.add( float(occMaxNt)/float(nbNt) )
            else:   # some MSA programs can remove some sequences (e.g. Muscle after Recon) or when using Refalign (non-alignable TE fragments put together via a refseq)
                nbRmvColumns += 1

            if len( lBestNt ) == 1:
                bestNt = lBestNt[0]
            elif len( lBestNt ) > 1:
                bestNt = lBestNt[0]  #"N"

            # if the predominant nucleotide occurs in less than x% of the sequences, put a "N"
            if minPropNt > 0.0 and nbNt != 0 and float(occMaxNt)/float(nbNt) < minPropNt:
                bestNt = "N"

            if int(nbNt) >= int(minNbNt):
                seqConsensus += bestNt
                if verbose > 1:
                    print "-> %s" % ( bestNt )

        if nbRmvColumns:
            print "WARNING: %i sites were removed (%.2f%%)" % ( nbRmvColumns, nbRmvColumns / float(nbSites) * 100 )
            sys.stdout.flush()
            if seqConsensus == "":
                print "WARNING: no consensus can be built (no sequence left)"
                return

        propN = seqConsensus.count("N") / float(len(seqConsensus))
        if propN >= maxPropN:
            print "WARNING: no consensus can be built (%i%% of N's >= %i%%)" % ( propN * 100, maxPropN * 100 )
            return
        elif propN >= maxPropN * 0.5:
            print "WARNING: %i%% of N's" % ( propN * 100 )
            #lPropNs = self.getPropNtPerWindow( seqConsensus, "N", verbose-1 )
            #statsPropNs = pyRepet.util.Stat.Stat( lPropNs )
            #statsPropNs.view()
            #print statsPropNs.cv()
            #print statsPropNs.kurtosis()
            #statsPropNs.viewQuantiles()

        consensus = Bioseq()
        consensus.sequence = seqConsensus
        consensus.header = "consensus=%s length=%i nbAlign=%i" % ( self.name, len(seqConsensus), self.getSize() )

        if verbose > 0:
            #stat.viewQuantiles()
            #print "kurtosis: %.3f" % ( stat.kurtosis() )
            statEntropy = self.getEntropy( verbose - 1 )
            print "entropy: %s" % ( statEntropy.stringQuantiles() )
            sys.stdout.flush()

        return consensus

    #--------------------------------------------------------------------------

    def getPropNtPerWindow( self, sequence, nt, verbose=0 ):
        """
        Get a list with the proportion of a given nucleotide per 100-bp window
        """

        lPropNts = []

        windowSize = 100
        if len(sequence) <= windowSize:
            windowSize = 20
            if len(sequence) < 10:
                print "ERROR: sequence is too short"
                sys.exit(1)

        nbWindows = int( ceil( len(sequence) / float(windowSize) ) )
        start = 0
        end = windowSize - 1
        if windowSize < 100:
            overlap = 5
        else:
            overlap = 10
        for i in xrange(0,nbWindows):
            lPropNts.append( sequence[start:end].count(nt) / float(windowSize) )
            if verbose > 0:
                print sequence[start:end], lPropNts[-1]
            start = end - overlap + 1
            end = start + windowSize - 1
            if end > len(sequence) - 1:
                end = len(sequence) - 1

        return lPropNts

    #--------------------------------------------------------------------------

    def getMap( self ):

        """
        
        """

        dSeq2Maps = {}

        for bs in self.db:
            dSeq2Maps[ bs.header ] = bs.getMap()

        return dSeq2Maps

    #--------------------------------------------------------------------------

    def identity( self ):

        """calculate the identity percentage of the MSA"""

        datay = []

        # loop on the length of the alignment
        for posx in xrange (0,self.length()):
            nbOfIdNuc = 0
            nbOfPairs = 0
            # loop on the number of sequences
            for seq in xrange(0,self.getSize()):
               # one records the letter to compare
               ref=self.db[seq].sequence[posx]
               # llop on the next sequences
               for seq_suiv in xrange(seq+1,self.getSize()):
                   # comparison of the two sites: if identical and no gap, one increments
                   if (self.db[seq_suiv].sequence[posx]!='-' and ref !='-'):
                       nbOfPairs+=1
                       if (self.db[seq_suiv].sequence[posx]==ref):
                           nbOfIdNuc+=1

               if nbOfPairs!=0:
                   datay.append(nbOfIdNuc/nbOfPairs*100)
               else:
                   datay.append(0)
        return datay
    
    #--------------------------------------------------------------------------

    def clean( self ):

        """clean the MSA"""

        i2del = []

        # for each sequence in the MSA
        for seqi in xrange(0,self.getSize()):

            if seqi in i2del:
                continue

            #define it as the reference
            ref = self.db[seqi].sequence
            ref_header = self.db[seqi].header.split()[0]

            # for each following sequence
            for seq_next in xrange(seqi+1,self.getSize()):
                if seq_next in i2del:
                    continue

                keep = 0
                # for each position along the MSA
                for posx in xrange(0,self.length()):
                    seq = self.db[seq_next].sequence
                    if seq[posx] != '-' and ref[posx] != '-':
                        keep = 1
                        break

                # if there is at least one gap between the ref seq and the other seq
                # keep track of the shortest by recording it in "i2del"
                if keep == 0:
                    if self.true_length(ref) < self.true_length(seq):
                        if seqi not in i2del:
                            i2del.append( seqi )
                    else:
                        if seq_next not in i2del:
                            i2del.append( seq_next )

        # delete from the MSA each seq present in the list "i2del"
        for i in reversed(sorted(set(i2del))):
            del self.db[i]

        self.idx = {}
        count = 0
        for i in self.db:
            self.idx[i.header] = count
            count += 1

    #--------------------------------------------------------------------------

    def pairwise_identity(self):

        """calculate pairwise identity"""

        data = []
        for seqi in xrange(0,self.getSize()):
           ref=self.db[seqi].sequence
           ref_header=self.db[seqi].header.split()[0]
           for seq_next in xrange(seqi+1,self.getSize()):
               nbOfIdNuc=0.0
               nbOfPairs=0.0
               seq=self.db[seq_next].sequence
               for posx in xrange (0,self.length()):
                   if seq[posx]!='-' and ref[posx] !='-' and (seq[posx]!='N' and ref[posx] !='N'):
                       nbOfPairs+=1.0
                       if seq[posx]==ref[posx]:
                           nbOfIdNuc+=1.0

               if nbOfPairs!=0:
                   data.append((ref_header,self.db[seq_next].header.split()[0],\
                                nbOfIdNuc/nbOfPairs*100))
               else:
                   data.append((ref_header,self.db[seq_next].header.split()[0],0.0))
        return data
    
    #--------------------------------------------------------------------------

    def gap(self):
     #calculate pairwise identity
        data=[]
        for seq in xrange(0,self.getSize()):
           seq=self.db[seq]
           seq_header=seq.header.split()[0]
           start=-1
           end=-1
           lseg=[]
           for i in xrange(0,len(seq.sequence)):
                if seq.sequence[i]=='-':
                    end=i
                    if start==-1:
                        start=i
                else:
                    if start!=-1 and end!=-1:
                        lseg.append([start+1,end+1])
                    start=-1
                    end=-1

           if start!=-1 and end!=-1:
               lseg.append([start+1,end+1])
           data.append((seq_header,float(len(lseg))/len(seq.sequence),lseg))

        return data    

    #--------------------------------------------------------------------------

    def getATGCNFromIUPAC( self, nt ):

        """
        Return A, T, G, C or N from an IUPAC letter.
        IUPAC = ['A','T','G','C','U','R','Y','M','K','W','S','B','D','H','V','N']
        """

        subset = ["A","T","G","C","N"]

        if nt in subset:
            return nt
        elif nt == "U":
            return "T"
        elif nt == "R":
            return random.choice( "AG" )
        elif nt == "Y":
            return random.choice( "CT" )
        elif nt == "M":
            return random.choice( "CA" )
        elif nt == "K":
            return random.choice( "TG" )
        elif nt == "W":
            return random.choice( "TA" )
        elif nt == "S":
            return random.choice( "CG" )
        elif nt == "B":
            return random.choice( "CTG" )
        elif nt == "D":
            return random.choice( "ATG" )
        elif nt == "H":
            return random.choice( "ATC" )
        elif nt == "V":
            return random.choice( "ACG" )
        else:
            return "N"

    #--------------------------------------------------------------------------

    def __computeEntropy( self, nbOcc, nbNt ):

        """
        Compute the entropy based on the occurrences of a certain nucleotide and the total number of nucleotides.
        """

        if nbOcc == 0.0:
            return 0.0
        else:
            freq = nbOcc / float(nbNt)
            return - freq * log(freq) / log(2) 

    #--------------------------------------------------------------------------

    def getEntropy( self, verbose=0 ):

        """
        Get the entropy of the whole multiple alignment (only for A, T, G and C).

        @param verbose: level of verbosity
        @type verbose: integer

        @return: statistics about the entropy of the MSA
        @rtype: pyRepet.util.Stat
        """

        stats = pyRepet.util.Stat.Stat()

        # get the occurrences of symbols at each site
        lOccPerSite = self.getListOccPerSite()

        countSite = 0

        # for each site
        for dSymbol2Occ in lOccPerSite:
            countSite += 1

            # count the number of nucleotides (A, T, G and C, doesn't count gap '-')
            nbNt = 0
            dATGC2Occ = {}
            for base in ["A","T","G","C"]:
                dATGC2Occ[ base ] = 0.0
            for nt in dSymbol2Occ.keys():
                if nt != "-":
                    nbNt += dSymbol2Occ[ nt ]
                    checkedNt = self.getATGCNFromIUPAC( nt )
                    if checkedNt in ["A","T","G","C"] and dSymbol2Occ.has_key( checkedNt ):
                        dATGC2Occ[ checkedNt ] += 1 * dSymbol2Occ[ checkedNt ]
                    else:   # for 'N'
                        if dSymbol2Occ.has_key( checkedNt ):
                            dATGC2Occ[ "A" ] += 0.25 * dSymbol2Occ[ checkedNt ]
                            dATGC2Occ[ "T" ] += 0.25 * dSymbol2Occ[ checkedNt ]
                            dATGC2Occ[ "G" ] += 0.25 * dSymbol2Occ[ checkedNt ]
                            dATGC2Occ[ "C" ] += 0.25 * dSymbol2Occ[ checkedNt ]
            if verbose > 2:
                for base in dATGC2Occ.keys():
                    print "%s: %i" % ( base, dATGC2Occ[ base ] )

            # compute the entropy for the site
            entropySite = 0.0
            for nt in dATGC2Occ.keys():
                entropySite += self.__computeEntropy( dATGC2Occ[ nt ], nbNt )
            if verbose > 1:
                print "site %i (%i nt): entropy = %.3f" % ( countSite, nbNt, entropySite )
            stats.add( entropySite )

        return stats

    #--------------------------------------------------------------------------

    #liste des y pour l'entropie
    def entropy(self):
        datay=[]
        for posx in xrange(0,self.length()):
              nbTotal=0
              nbOfA=0
              nbOfC=0
              nbOfG=0
              nbOfT=0
              currentNuc=""
              for seq in xrange(0,float(self.getSize())):
                  currentNuc=self.db[seq].sequence[posx]
                 
                  if  currentNuc!="-":
                      nbTotal+=1  
                  if  currentNuc=="A" or currentNuc=="a":
                      nbOfA+=1
                  elif  currentNuc=="T" or currentNuc=="t":
                      nbOfT +=1
                  elif currentNuc=="G" or currentNuc=="g":
                      nbOfG+=1
                  elif  currentNuc=="C" or currentNuc=="c":
                      nbOfC+=1
                  elif currentNuc=="N" or currentNuc=="n":
                      nbOfA+=0.25
                      nbOfC+=0.25
                      nbOfG+=0.25

              datay.append(self.__computeEntropy(nbOfA,nbTotal)+self.__computeEntropy(nbOfT,nbTotal)+self.__computeEntropy(nbOfC,nbTotal)+self.__computeEntropy(nbOfG,nbTotal))

        return datay

    #--------------------------------------------------------------------------

    #liste des y pour le nombre de nucleotides a cette pos de l'alignement
    def nbNuc(self):
        datay=[]
        for posx in xrange(0,self.length()):
            nbnuc=0 
            for seq in xrange(0,float(self.getSize())):
                if self.db[seq].sequence[posx]!='-':
                    nbnuc+=1
            datay.append(float(nbnuc)/self.getSize())
        return datay
    
    #--------------------------------------------------------------------------

    def __lisse_curve(self,data,win):
        deb=win/2
        fin=len(data)-(win/2)
        liste_tmp=data[:]
        liste_tmp[:deb]=[ 0 ]*deb
        if win>0:
            liste_tmp[-fin:]=[ 0 ]*fin
        for i in xrange(deb,fin):
            for j in xrange(-win/2,win/2):
                liste_tmp[i]+=data[i+j]
            liste_tmp[i]/=float(win)
        return liste_tmp
