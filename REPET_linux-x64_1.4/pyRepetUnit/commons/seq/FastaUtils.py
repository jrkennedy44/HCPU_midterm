# Copyright INRA (Institut National de la Recherche Agronomique)
# http://www.inra.fr
# http://urgi.versailles.inra.fr
#
# This software is governed by the CeCILL license under French law and
# abiding by the rules of distribution of free software.  You can  use, 
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# "http://www.cecill.info". 
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability. 
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or 
# data to be ensured and,  more generally, to use and operate it in the 
# same conditions as regards security. 
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.


import os
import sys
import string
import math
import shutil
import re
import glob
from pyRepetUnit.commons.seq.BioseqDB import BioseqDB
from pyRepetUnit.commons.seq.Bioseq import Bioseq
from pyRepetUnit.commons.coord.MapUtils import MapUtils
from repet_base.ConvCoord import ConvCoord
from pyRepetUnit.commons.coord.Range import Range
from pyRepetUnit.commons.checker.CheckerUtils import CheckerUtils


## Static methods for fasta file manipulation
#
class FastaUtils( object ):
    
    ## Count the number of sequences in the input fasta file
    #
    # @param inFile name of the input fasta file
    #
    # @return integer number of sequences in the input fasta file
    #
    def dbSize( inFile ):
        nbSeq = 0
        
        inFileHandler = open( inFile, "r" )
        line = inFileHandler.readline()
        while True:
            if line == "":
                break
            if line[0] == ">":
                nbSeq = nbSeq + 1
            line = inFileHandler.readline()
        inFileHandler.close()
        
        return nbSeq
    
    dbSize = staticmethod( dbSize )
    
    
    ## Compute the cumulative sequence length in the input fasta file
    #
    # @param inFile handler of the input fasta file
    #
    def dbCumLength( inFile ):
        cumLength = 0
        while True:
            line = inFile.readline()
            if line == "":
                break
            if line[0] != ">":
                cumLength += len(string.rstrip(line))
    
        return cumLength
    
    dbCumLength = staticmethod(dbCumLength)
    
    
    ## Return a list with the length of each sequence in the input fasta file
    #
    # @param inFile string name of the input fasta file
    #
    def dbLengths( inFile ):
        lLengths = []
        inFileHandler = open( inFile, "r" )
        currentLength = 0
        while True:
            line = inFileHandler.readline()
            if line == "":
                break
            if line[0] == ">":
                if currentLength != 0:
                    lLengths.append( currentLength )
                currentLength = 0
            else:
                currentLength += len(line[:-1])
        lLengths.append( currentLength )
        inFileHandler.close()
        return lLengths
    
    dbLengths = staticmethod( dbLengths )
    
    
    ## Retrieve the sequence headers present in the input fasta file
    #
    # @param inFile string name of the input fasta file
    # @param verbose integer level of verbosity
    #
    # @return list of sequence headers
    #
    def dbHeaders( inFile, verbose=0 ):
        lHeaders = []
        
        inFileHandler = open( inFile, "r" )
        while True:
            line = inFileHandler.readline()
            if line == "":
                break
            if line[0] == ">":
                lHeaders.append( string.rstrip(line[1:]) )
                if verbose > 0:
                    print string.rstrip(line[1:])
        inFileHandler.close()
        
        return lHeaders
    
    dbHeaders = staticmethod( dbHeaders )
    
    
    ## Cut a data bank into chunks according to the input parameters
    # If a sequence is shorter than the threshold, it is only renamed (not cut)
    #
    # @param inFileName string name of the input fasta file
    # @param chkLgth string chunk length (in bp, default=200000)
    # @param chkOver string chunk overlap (in bp, default=10000)
    # @param wordN string N stretch word length (default=11, 0 for no detection)
    # @param outFilePrefix string prefix of the output files (default=inFileName + '_chunks.fa' and '_chunks.map')
    # @param clean boolean remove 'cut' and 'Nstretch' files
    # @param verbose integer (default = 0)
    #
    def dbChunks( inFileName, chkLgth="200000", chkOver="10000", wordN="11", outFilePrefix="", clean=False, verbose=0 ):
        nbSeq = FastaUtils.dbSize( inFileName )
        if verbose > 0:
            print "cut the %i input sequences with cutterDB..." % ( nbSeq )
            sys.stdout.flush()
            
        prg = "cutterDB"
        cmd = prg
        cmd += " -l %s" % ( chkLgth )
        cmd += " -o %s"  %( chkOver )
        cmd += " -w %s" % ( wordN )
        cmd += " %s" % ( inFileName )
        returnStatus = os.system( cmd )
        if returnStatus != 0:
            msg = "ERROR: '%s' returned '%i'" % ( prg, returnStatus )
            sys.stderr.write( "%s\n" % ( msg ) )
            sys.exit(1)
            
        nbChunks = FastaUtils.dbSize( "%s_cut" % ( inFileName ) )
        if verbose > 0:
            print "done (%i chunks)" % ( nbChunks )
            sys.stdout.flush()
            
        if verbose > 0:
            print "rename the headers..."
            sys.stdout.flush()
            
        if outFilePrefix == "":
            outFastaName = inFileName + "_chunks.fa"
            outMapName = inFileName + "_chunks.map"
        else:
            outFastaName = outFilePrefix + ".fa"
            outMapName = outFilePrefix + ".map"
            
        inFile = open( "%s_cut" % ( inFileName ), "r" )
        line = inFile.readline()
        
        outFasta = open( outFastaName, "w" )
        outMap = open( outMapName, "w" )
        
        # read line after line (no need for big RAM) and change the sequence headers
        while True:
            
            if line == "":
                break
            
            if line[0] == ">":
                if verbose > 1:
                    print "rename '%s'" % ( line[:-1] ); sys.stdout.flush()
                data = line[:-1].split(" ")
                seqID = data[0].split(">")[1]
                newHeader = "chunk%s" % ( str(seqID).zfill( len(str(nbChunks)) ) )
                oldHeader = data[2]
                seqStart = data[4].split("..")[0]
                seqEnd = data[4].split("..")[1]
                outMap.write( "%s\t%s\t%s\t%s\n" % ( newHeader, oldHeader, seqStart, seqEnd ) )
                outFasta.write( ">%s\n" % ( newHeader ) )
                
            else:
                outFasta.write( line.upper() )
                
            line = inFile.readline()
            
        inFile.close()
        outFasta.close()
        outMap.close()
        
        if clean == True:
            os.remove(inFileName + "_cut")
            os.remove(inFileName + ".Nstretch.map")
            
    dbChunks = staticmethod( dbChunks )
    
    
    ## Split the input fasta file in several output files
    #
    # @param inFile string name of the input fasta file
    # @param nbSeqPerBatch integer number of sequences per output file
    # @param newDir boolean put the sequences in a new directory called 'batches'
    # @param useSeqHeader boolean use sequence header (only if 'nbSeqPerBatch=1')
    # @param prefix prefix in output file name 
    # @param verbose integer verbosity level (default = 0)
    #
    def dbSplit( inFile, nbSeqPerBatch, newDir, useSeqHeader=False, prefix="batch", verbose=0 ):
        if not os.path.exists( inFile ):
            msg = "ERROR: file '%s' doesn't exist" % ( inFile )
            sys.stderr.write( "%s\n" % ( msg ) )
            sys.exit(1)
            
        nbSeq = FastaUtils.dbSize( inFile )
        
        nbBatches = int( math.ceil( nbSeq / float(nbSeqPerBatch) ) )
        if verbose > 0:
            print "save the %i input sequences into %i batches" % ( nbSeq, nbBatches )
            sys.stdout.flush()
            
        if nbSeqPerBatch > 1 and useSeqHeader:
            useSeqHeader = False
            
        if newDir == True:
            if os.path.exists( "batches" ):
                shutil.rmtree( "batches" )
            os.mkdir( "batches" )
            os.chdir( "batches" )
            os.system( "ln -s ../%s ." % ( inFile ) )
            
        inFileHandler = open( inFile, "r" )
        inFileHandler.seek( 0, 0 )
        countBatch = 0
        countSeq = 0
        while True:
            line = inFileHandler.readline()
            if line == "":
                break
            if line[0] == ">":
                countSeq += 1
                if nbSeqPerBatch == 1 or countSeq % nbSeqPerBatch == 1:
                    if "outFile" in locals():
                        outFile.close()
                    countBatch += 1
                    if nbSeqPerBatch == 1 and useSeqHeader:
                        outFileName = "%s.fa" % ( line[1:-1].replace(" ","_") )
                    else:
                        outFileName = "%s_%s.fa" % ( prefix, str(countBatch).zfill( len(str(nbBatches)) ) )
                    outFile = open( outFileName, "w" )
                if verbose > 1:
                    print "saving seq '%s' in file '%s'..." % ( line[1:40][:-1], outFileName )
                    sys.stdout.flush()
            outFile.write( line )
        inFileHandler.close()
        
        if newDir == True:
            os.remove( os.path.basename( inFile ) )
            os.chdir( ".." )
            
    dbSplit = staticmethod( dbSplit )
    
    
    ## Split the input fasta file in several output files according to their cluster identifier
    #
    # @param inFileName string  name of the input fasta file
    # @param clusteringMethod string name of the clustering method (Grouper, Recon, Piler, Blastclust)
    # @param simplifyHeader boolean simplify the headers
    # @param createDir boolean put the sequences in different directories
    # @param outPrefix string prefix of the output files (default='seqCluster')
    # @param verbose integer (default = 0)
    #
    def splitSeqPerCluster( inFileName, clusteringMethod, simplifyHeader, createDir, outPrefix="seqCluster", verbose=0 ):
        if not os.path.exists( inFileName ):
            print "ERROR: %s doesn't exist" % ( inFileName )
            sys.exit(1)
    
        inFile = open( inFileName, "r" )
    
        line = inFile.readline()
        name = line.split(" ")[0]
        if "Cluster" in name:
            clusterID = name.split("Cluster")[1].split("Mb")[0]
            seqID = name.split("Mb")[1]
        else:
            clusterID = name.split("Cl")[0].split("Gr")[1]   # the notion of 'group' in Grouper corresponds to 'cluster' in Piler, Recon and Blastclust
            if "Q" in name.split("Gr")[0]:
                seqID = name.split("Gr")[0].split("MbQ")[1]
            elif "S" in name:
                seqID = name.split("Gr")[0].split("MbS")[1]
        sClusterIDs = set( [ clusterID ] )
        if simplifyHeader == True:
            header = "%s_Cluster%s_Seq%s" % ( clusteringMethod, clusterID, seqID )
        else:
            header = line[1:-1]
        if createDir == True:
            if not os.path.exists( "%s_cluster_%s" % ( inFileName, clusterID )  ):
                os.mkdir( "%s_cluster_%s" % ( inFileName, clusterID )  )
            os.chdir( "%s_cluster_%s" % ( inFileName, clusterID )  )
        outFileName = "%s%s.fa" % ( outPrefix, clusterID )
        outFile = open( outFileName, "w" )
        outFile.write( ">%s\n" % ( header ) )
        prevClusterID = clusterID
    
        line = inFile.readline()
        while True:
            if line == "":
                break
    
            if line[0] == ">":
                name = line.split(" ")[0]
                if "Cluster" in name:
                    clusterID = name.split("Cluster")[1].split("Mb")[0]
                    seqID = name.split("Mb")[1]
                else:
                    clusterID = name.split("Cl")[0].split("Gr")[1]
                    if "Q" in name.split("Gr")[0]:
                        seqID = name.split("Gr")[0].split("MbQ")[1]
                    elif "S" in name:
                        seqID = name.split("Gr")[0].split("MbS")[1]
    
                if clusterID != prevClusterID:
                    outFile.close()
    
                if simplifyHeader == True:
                    header = "%s_Cluster%s_Seq%s" % ( clusteringMethod, clusterID, seqID )
                else:
                    header = line[1:-1]
    
                if createDir == True:
                    os.chdir( ".." )
                    if not os.path.exists( "%s_cluster_%s" % ( inFileName, clusterID )  ):
                        os.mkdir( "%s_cluster_%s" % ( inFileName, clusterID )  )
                    os.chdir( "%s_cluster_%s" % ( inFileName, clusterID )  )
    
                outFileName = "%s%s.fa" % ( outPrefix, clusterID )
                if not os.path.exists( outFileName ):
                    outFile = open( outFileName, "w" )
                else:
                    if clusterID != prevClusterID:
                        outFile.close()
                        outFile = open( outFileName, "a" )
                outFile.write( ">%s\n" % ( header ) )
                prevClusterID = clusterID
                sClusterIDs.add( clusterID )
    
            else:
                outFile.write( line )
    
            line = inFile.readline()
    
        outFile.close()
        if verbose > 0:
            print "number of clusters: %i" % ( len(sClusterIDs) ); sys.stdout.flush()
            
        if createDir == True:
            os.chdir("..")
                
    splitSeqPerCluster = staticmethod( splitSeqPerCluster )
    
    
    ## Filter a fasta file in two fasta files using the length of each sequence as a criteron
    #
    # @param len_min integer    length sequence criterion to filter
    # @param inFileName string  name of the input fasta file
    # @param verbose integer (default = 0)      
    #
    def dbLengthFilter( len_min, inFileName, verbose=0 ):
        file_db = open( inFileName, "r" )
        file_dbInf = open( inFileName+".Inf"+str(len_min), "w" )
        file_dbSup = open( inFileName+".Sup"+str(len_min), "w" )
        seq = Bioseq()
        numseq = 0
        nbsave = 0
        
        while True:
            seq.read( file_db )
            if seq.sequence == None:
                break
            l = seq.getLength()
            numseq = numseq + 1
            if l >= len_min:
                seq.write( file_dbSup )
                if verbose > 0:
                        print 'sequence #',numseq,'=',l,'[',seq.header[0:40],'...] Sup !!'
                        nbsave=nbsave+1
            else:
                seq.write( file_dbInf )
                if verbose > 0:
                        print 'sequence #',numseq,'=',l,'[',seq.header[0:40],'...] Inf !!'
                        nbsave=nbsave+1
                        
        file_db.close()
        file_dbInf.close()
        file_dbSup.close()
        if verbose > 0:
            print nbsave,'saved sequences in ',inFileName+".Inf"+str(len_min)," and ", inFileName+".Sup"+str(len_min)
            
    dbLengthFilter = staticmethod( dbLengthFilter )
    
    
    ## Extract the longest sequences from a fasta file
    #
    # @param num integer maximum number of sequences in the output file
    # @param inFileName string name of the input fasta file
    # @param outFileName string name of the output fasta file
    # @param minThresh integer minimum length threshold (default=0)
    # @param verbose integer (default = 0)
    #
    def dbLongestSequences( num, inFileName, outFileName="", verbose=0, minThresh=0 ):
        bsDB = BioseqDB( inFileName )
        if verbose > 0:
            print "nb of input sequences: %i" % ( bsDB.getSize() )
    
        if outFileName == "":
            outFileName = inFileName + ".best" + str(num)
        outFile = open( outFileName, "w" )
        
        if bsDB.getSize()==0:
            return 0
        
        num = int(num)
        if verbose > 0:
            print "keep the %i longest sequences" % ( num )
            if minThresh > 0:
                print "with length > %i bp" % ( minThresh )
            sys.stdout.flush()
            
        # retrieve the length of each input sequence
        tmpLSeqLgth = []
        seqNum = 0
        for bs in bsDB.db:
            seqNum += 1
            tmpLSeqLgth.append( bs.getLength() )
            if verbose > 1:
                print "%d seq %s : %d bp" % ( seqNum, bs.header[0:40], bs.getLength() )
            sys.stdout.flush()
    
        # sort the lengths
        tmpLSeqLgth.sort()
        tmpLSeqLgth.reverse()
    
        # select the longest
        lSeqLgth = []
        for i in xrange( 0, min(num,len(tmpLSeqLgth)) ):
            if tmpLSeqLgth[i] >= minThresh:
                lSeqLgth.append( tmpLSeqLgth[i] )
        if verbose > 0:
            print "selected max length: %i" % ( max(lSeqLgth) )
            print "selected min length: %i" % ( min(lSeqLgth) )
            sys.stdout.flush()
    
        # save the longest
        inFile = open( inFileName )
        seqNum = 0
        nbSave = 0
        for bs in bsDB.db:
            seqNum += 1
            if bs.getLength() >= min(lSeqLgth) and bs.getLength() >= minThresh:
                bs.write( outFile )
                if verbose > 1:
                    print "%d seq %s : saved !" % ( seqNum, bs.header[0:40] )
                    sys.stdout.flush()
                nbSave += 1
            if nbSave == num:
                break
        inFile.close()
        outFile.close()
        if verbose > 0:
            print nbSave, "saved sequences in ", outFileName
            sys.stdout.flush()
            
        return 0
    
    dbLongestSequences = staticmethod( dbLongestSequences )
    
    
    ## Extract all the sequence headers from a fasta file and write them in a new fasta file
    #
    # @param inFileName string name of the input fasta file
    # @param outFileName string name of the output file recording the headers (default = inFileName + '.headers')
    #
    def dbExtractSeqHeaders( inFileName, outFileName="" ):
        lHeaders = FastaUtils.dbHeaders( inFileName )
        
        if outFileName == "":
            outFileName = inFileName + ".headers"
            
        outFile = open( outFileName, "w" )
        for i in lHeaders:
            outFile.write( i + "\n" )
        outFile.close()
    
        return 0
    
    dbExtractSeqHeaders = staticmethod( dbExtractSeqHeaders )
    
    
    ## Extract sequences and their headers selected by a given pattern from a fasta file and write them in a new fasta file
    #
    # @param pattern regular expression to search in headers
    # @param inFileName string name of the input fasta file
    # @param outFileName string name of the output file recording the selected bioseq (default = inFileName + '.extracted')
    # @param verbose integer verbosity level (default = 0)
    #
    def dbExtractByPattern( pattern, inFileName, outFileName="", verbose=0 ):
    
        if pattern == "":
            return
        
        if outFileName == "":
            outFileName = inFileName + '.extracted'
        outFile = open( outFileName, 'w' )
        
        patternTosearch = re.compile( pattern )
        bioseq = Bioseq()
        bioseqNb = 0
        savedBioseqNb = 0
        inFile = open( inFileName, "r" )
        while True:
            bioseq.read( inFile )
            if bioseq.sequence == None:
                break
            bioseqNb = bioseqNb + 1
            m = patternTosearch.search( bioseq.header )
            if m:
                bioseq.write( outFile )
                if verbose > 1:
                    print 'sequence num',bioseqNb,'matched on',m.group(),'[',bioseq.header[0:40],'...] saved !!'
                savedBioseqNb = savedBioseqNb + 1
        inFile.close()
        
        outFile.close()
        
        if verbose > 0:
            print "%i sequences saved in file '%s'" % ( savedBioseqNb, outFileName )
            
    dbExtractByPattern = staticmethod( dbExtractByPattern )
    
    
    ## Extract sequences and their headers selected by patterns contained in a file, from a fasta file and write them in a new fasta file
    #
    # @param patternFileName string file containing regular expression to search in headers
    # @param inFileName string name of the input fasta file
    # @param outFileName string name of the output file recording the selected bioseq (default = inFileName + '.extracted')
    # @param verbose integer verbosity level (default = 0)
    #
    def dbExtractByFilePattern( patternFileName, inFileName, outFileName="", verbose=0 ):
    
        if patternFileName == "":
            print "ERROR: no file of pattern"
            sys.exit(1)
    
        bioseq = Bioseq()
        bioseqNb = 0
        savedBioseqNb = 0
        lHeaders = []

        inFile = open( inFileName, "r" )
        while True:
            bioseq.read( inFile )
            if bioseq.sequence == None:
                break
            lHeaders.append( bioseq.header )
        inFile.close()
    
        lHeadersToKeep = []
        patternFile = open( patternFileName, "r" )
        for pattern in patternFile:
            if verbose > 0:
                print "pattern: ",pattern[:-1]; sys.stdout.flush()
                
            patternToSearch = re.compile(pattern[:-1])
            for h in lHeaders:
                if patternToSearch.search(h):
                    lHeadersToKeep.append(h)
        patternFile.close()
    
        if outFileName == "":
            outFileName = inFileName + ".extracted"
        outFile=open( outFileName, "w" )
    
        inFile = open( inFileName, "r" )
        while True:
            bioseq.read(inFile)
            if bioseq.sequence == None:
                break
            bioseqNb += 1
            if bioseq.header in lHeadersToKeep:
                bioseq.write(outFile)
                if verbose > 1:
                    print 'sequence num',bioseqNb,'[',bioseq.header[0:40],'...] saved !!'; sys.stdout.flush()
                savedBioseqNb += 1
        inFile.close()
    
        outFile.close()
        
        if verbose > 0:
            print "%i sequences saved in file '%s'" % ( savedBioseqNb, outFileName )
            
    dbExtractByFilePattern = staticmethod( dbExtractByFilePattern )
    
    
    ## Extract sequences and their headers not selected by a given pattern from a fasta file and write them in a new fasta file
    #
    # @param pattern regular expression to search in headers
    # @param inFileName string name of the input fasta file
    # @param outFileName string name of the output file recording the selected bioseq (default = inFileName + '.extracted')
    # @param verbose integer verbosity level (default = 0)
    #
    def dbCleanByPattern( pattern, inFileName, outFileName="", verbose=0 ):
        if pattern == "":
            return
        
        patternToSearch = re.compile(pattern)
        
        if outFileName == "":
            outFileName = inFileName + '.cleaned'
        outFile = open(outFileName,'w')
        
        bioseq = Bioseq()
        bioseqNb = 0
        savedBioseqNb = 0
        inFile = open(inFileName)
        while True:
            bioseq.read(inFile)
            if bioseq.sequence == None:
                break
            bioseqNb += 1
            if not patternToSearch.search(bioseq.header):
                bioseq.write(outFile)
                if verbose > 1:
                    print 'sequence num',bioseqNb,'[',bioseq.header[0:40],'...] saved !!'
                savedBioseqNb += 1
        inFile.close()
        
        outFile.close()
        
        if verbose > 0:
            print "%i sequences saved in file '%s'" % ( savedBioseqNb, outFileName )
            
    dbCleanByPattern = staticmethod( dbCleanByPattern )
    
    
    ## Extract sequences and their headers not selected by patterns contained in a file, from a fasta file and write them in a new fasta file
    #
    # @param patternFileName string file containing regular expression to search in headers
    # @param inFileName string name of the input fasta file
    # @param outFileName string name of the output file recording the selected bioseq (default = inFileName + '.extracted')
    # @param verbose integer verbosity level (default = 0)
    #
    def dbCleanByFilePattern( patternFileName, inFileName, outFileName="", verbose=0 ):
        if patternFileName == "":
            print "ERROR: no file of pattern"
            sys.exit(1)
            
        bioseq = Bioseq()
        bioseqNb = 0
        savedBioseqNb = 0
        lHeaders = []
        inFile = open( inFileName, "r" )
        while True:
            bioseq.read( inFile )
            if bioseq.sequence == None:
                break
            bioseqNb += 1
            lHeaders.append( bioseq.header )
        inFile.close()
        
        patternFile = open( patternFileName, "r")
        lHeadersToRemove = []
        for pattern in patternFile:
            if verbose > 0:
                print "pattern: ",pattern[:-1]; sys.stdout.flush()
                
            patternToSearch = re.compile( pattern[:-1] )
            for h in lHeaders:
                if patternToSearch.search(h):
                    lHeadersToRemove.append(h)
        patternFile.close()
        
        if outFileName == "":
            outFileName = inFileName + '.cleaned'
        outFile = open( outFileName, 'w' )
    
        bioseqNum = 0
        inFile=open( inFileName )
        while True:
            bioseq.read( inFile )
            bioseqNum += 1
            if bioseq.sequence == None:
                break
            if bioseq.header not in lHeadersToRemove:
                bioseq.write( outFile )
                if verbose > 1:
                    print 'sequence num',bioseqNum,'/',bioseqNb,'[',bioseq.header[0:40],'...] saved !!'; sys.stdout.flush()
                savedBioseqNb += 1
        inFile.close()
        
        outFile.close()
        
        if verbose > 0:
            print "%i sequences saved in file '%s'" % ( savedBioseqNb, outFileName )
            
    dbCleanByFilePattern = staticmethod( dbCleanByFilePattern )
    
    
    ## Find sequence's ORFs from a fasta file and write them in a tab file 
    # 
    # @param inFileName string name of the input fasta file
    # @param orfMaxNb integer Select orfMaxNb best ORFs
    # @param orfMinLength integer Keep ORFs with length > orfMinLength 
    # @param outFileName string name of the output fasta file (default = inFileName + '.orf.map')
    # @param verbose integer verbosity level (default = 0)
    #
    def dbORF( inFileName, orfMaxNb = 0, orfMinLength = 0, outFileName = "", verbose=0 ):
        if outFileName == "":
            outFileName = inFileName + ".orf.map"
        outFile = open( outFileName, "w" )
    
        bioseq = Bioseq()
        bioseqNb = 0
    
        inFile = open( inFileName )
        while True:
            bioseq.read( inFile )
            if bioseq.sequence == None:
                break
            bioseq.upCase() 
            bioseqNb += 1
            if verbose > 0:
                print 'sequence num',bioseqNb,'=',bioseq.getLength(),'[',bioseq.header[0:40],'...]'
                
            orf = bioseq.findORF()
            bestOrf = []
            for i in orf.keys():
                orfLen = len(orf[i])
                for j in xrange(1, orfLen):
                    start = orf[i][j-1] + 4
                    end = orf[i][j] + 3
                    if end - start >= orfMinLength:
                        bestOrf.append( ( end-start, i+1, start, end ) )
    
            bioseq.complement()
            
            orf = bioseq.findORF()
            seqLen = bioseq.getLength()
            for i in orf.keys():
                orfLen = len(orf[i])
                for j in xrange(1, orfLen):
                    start = seqLen - orf[i][j-1] - 3
                    end = seqLen - orf[i][j] - 2
                    if start - end >= orfMinLength:
                        bestOrf.append( ( start-end, (i+1)*-1, start, end ) )
    
            bestOrf.sort()
            bestOrf.reverse()
            bestOrfNb = len(bestOrf)
            if orfMaxNb > bestOrfNb or orfMaxNb == 0 :
                orfMaxNb = bestOrfNb
            for i in xrange(0, orfMaxNb):
                if verbose > 0:
                    print bestOrf[i]
                outFile.write("%s\t%s\t%d\t%d\n"%("ORF|"+str(bestOrf[i][1])+\
                                   "|"+str(bestOrf[i][0]),bioseq.header,
                                   bestOrf[i][2],bestOrf[i][3]))
    
        inFile.close()
        outFile.close()
    
        return 0

    dbORF = staticmethod( dbORF )
    
    ## Copy the input fasta file with shorter sequence headers
    #
    # @param inFileName string name of the input fasta file
    # @param outFileName string name of the output fasta file
    # @param verbose integer verbosity level   
    #
    def sortSequencesByIncreasingLength(inFileName, outFileName, verbose=0):
        if verbose > 0:
            print "sort sequences by increasing length"
            sys.stdout.flush()
        if not os.path.exists( inFileName ):
            print "ERROR: file '%s' doesn't exist" % ( inFileName )
            sys.exit(1)
            
        # read each seq one by one
        # save them in distinct temporary files
        # with their length in the name
        inFileHandler = open( inFileName, "r" )
        bs = Bioseq()
        countSeq = 0
        while True:
            bs.read( inFileHandler )
            if bs.header == None:
                break
            countSeq += 1
            tmpFile = "%ibp_%inb" % ( bs.getLength(), countSeq )
            bs.appendBioseqInFile( tmpFile )
            if verbose > 1:
                print "%s (%i bp) saved in '%s'" % ( bs.header, bs.getLength(), tmpFile )
            bs.header = ""
            bs.sequence = ""
        inFileHandler.close()
        
        # sort temporary file names
        # concatenate them into the output file
        if os.path.exists( outFileName ):
            os.remove( outFileName )
        lFiles = glob.glob( "*bp_*nb" )
        lFiles.sort( key=lambda s:int(s.split("bp_")[0]) )
        for fileName in lFiles:
            cmd = "cat %s >> %s" % ( fileName, outFileName )
            returnValue = os.system( cmd )
            if returnValue != 0:
                print "ERROR while concatenating '%s' with '%s'" % ( fileName, outFileName )
                sys.exit(1)
            os.remove( fileName )
            
        return 0

    sortSequencesByIncreasingLength = staticmethod(sortSequencesByIncreasingLength) 
    
    
    ## Return a dictionary which keys are the headers and values the length of the sequences
    #
    # @param inFile string name of the input fasta file
    # @param verbose integer verbosity level   
    #
    def getLengthPerHeader( inFile, verbose=0 ):
        dHeader2Length = {}
        
        inFileHandler = open( inFile, "r" )
        currentSeqHeader = ""
        currentSeqLength = 0
        while True:
            line = inFileHandler.readline()
            if line == "":
                break
            if line[0] == ">":
                if currentSeqHeader != "":
                    dHeader2Length[ currentSeqHeader ] = currentSeqLength
                    currentSeqLength = 0
                currentSeqHeader = line[1:-1]
                if verbose > 0:
                    print "current header: %s" % ( currentSeqHeader )
                    sys.stdout.flush()
            else:
                currentSeqLength += len( line.replace("\n","") )
        dHeader2Length[ currentSeqHeader ] = currentSeqLength
        inFileHandler.close()
        
        return dHeader2Length
    
    getLengthPerHeader = staticmethod( getLengthPerHeader )
    
    
    ## Convert headers from a fasta file having chunk coordinates
    #
    # @param inFile string name of the input fasta file
    # @param mapFile string name of the map file with the coordinates of the chunks on the chromosomes
    # @param outFile string name of the output file
    #
    def convertFastaHeadersFromChkToChr( inFile, mapFile, outFile ):
        inFileHandler = open( inFile, "r" )
        outFileHandler = open( outFile, "w" )
        dChunk2Map = MapUtils.getDictPerNameFromMapFile( mapFile )
        iConvCoord = ConvCoord()
        while True:
            line = inFileHandler.readline()
            if line == "":
                break
            if line[0] == ">":
                if "{Fragment}" not in line:
                    outFileHandler.write( line )
                    continue
                chkName = line.split(" ")[1]
                chrName = dChunk2Map[ chkName ].seqname
                lCoordPairs = line.split(" ")[3].split(",")
                lRangesOnChk = []
                for i in lCoordPairs:
                    iRange = Range( chkName, int(i.split("..")[0]), int(i.split("..")[1]) )
                    lRangesOnChk.append( iRange )
                lRangesOnChr = []
                for iRange in lRangesOnChk:
                    lRangesOnChr.append( iConvCoord.getRangeOnChromosome( iRange, dChunk2Map ) )
                newHeader = line[1:-1].split(" ")[0]
                newHeader += " %s" % ( chrName )
                newHeader += " {Fragment}"
                newHeader += " %i..%i" % ( lRangesOnChr[0].start, lRangesOnChr[0].end )
                for iRange in lRangesOnChr[1:]:
                    newHeader += ",%i..%i" % ( iRange.start, iRange.end )
                outFileHandler.write( ">%s\n" % ( newHeader ) )
            else:
                outFileHandler.write( line )
        inFileHandler.close()
        outFileHandler.close()
        
    convertFastaHeadersFromChkToChr = staticmethod( convertFastaHeadersFromChkToChr )

    
    ## Splice an input fasta file using coordinates in a Map file
    #
    # @note the coordinates should be merged beforehand!
    #
    def spliceFromCoords( genomeFile, coordFile, obsFile ):
        genomeFileHandler = open( genomeFile, "r" )
        obsFileHandler = open( obsFile, "w" )
        dChr2Maps = MapUtils.getDictPerSeqNameFromMapFile( coordFile )
        
        while True:
            bs = Bioseq()
            bs.read( genomeFileHandler )
            if bs.sequence == None:
                break
            if dChr2Maps.has_key( bs.header ):
                lCoords = MapUtils.getMapListSortedByIncreasingMinThenMax( dChr2Maps[ bs.header ] )
                splicedSeq = ""
                currentSite = 0
                for iMap in lCoords:
                    minSplice = iMap.getMin() - 1
                    if minSplice > currentSite:
                        splicedSeq += bs.sequence[ currentSite : minSplice ]
                    currentSite = iMap.getMax()
                splicedSeq += bs.sequence[ currentSite : ]
                bs.sequence = splicedSeq
            bs.write( obsFileHandler )
            
        genomeFileHandler.close()
        obsFileHandler.close()
        
    spliceFromCoords = staticmethod( spliceFromCoords )
    
    
    ## Shuffle input sequences (single file or files in a directory)
    #
    def dbShuffle( inData, outData, verbose=0 ):
        if CheckerUtils.isExecutableInUserPath("esl-shuffle"):
            prg = "esl-shuffle"
        else : prg = "shuffle"
        genericCmd = prg + " -d INPUT > OUTPUT"
        if os.path.isfile( inData ):
            if verbose > 0:
                print "shuffle input file '%s'" % inData
            cmd = genericCmd.replace("INPUT",inData).replace("OUTPUT",outData)
            print cmd
            returnStatus = os.system( cmd )
            if returnStatus != 0:
                sys.stderr.write( "ERROR: 'shuffle' returned '%i'\n" % returnStatus )
                sys.exit(1)
                
        elif os.path.isdir( inData ):
            if verbose > 0:
                print "shuffle files in input directory '%s'" % inData
            if os.path.exists( outData ):
                shutil.rmtree( outData )
            os.mkdir( outData )
            lInputFiles = glob.glob( "%s/*.fa" %( inData ) )
            nbFastaFiles = 0
            for inputFile in lInputFiles:
                nbFastaFiles += 1
                if verbose > 1:
                    print "%3i / %3i" % ( nbFastaFiles, len(lInputFiles) )
                fastaBaseName = os.path.basename( inputFile )
                prefix, extension = os.path.splitext( fastaBaseName )
                cmd = genericCmd.replace("INPUT",inputFile).replace("OUTPUT","%s/%s_shuffle.fa"%(outData,prefix))
                returnStatus = os.system( cmd )
                if returnStatus != 0:
                    sys.stderr.write( "ERROR: 'shuffle' returned '%i'\n" % returnStatus )
                    sys.exit(1)
                    
    dbShuffle = staticmethod( dbShuffle )
