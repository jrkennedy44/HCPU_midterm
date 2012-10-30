"""
Set of functions to be used on a fasta file.
"""

import os
import sys
import re
import math
import time
import glob

from pyRepet.seq.BioseqDB import *
from pyRepet.seq.Bioseq import *
from pyRepet.util.Stat import *
from pyRepet.launcher.programLauncher import *
from pyRepet.parser.Parser import *

#------------------------------------------------------------------------------

def dbSize( inFileName ):

	"""
	Count the number of sequences in the input fasta file.

	@param inFileName: name of the input fasta file
	@type inFileName: string

	@return: number of sequences in the input fata file
	@rtype: integer
	"""

	if not os.path.exists( inFileName ):
		print "*** Error: file '%s' doesn't exist" % ( inFileName )
		sys.exit(1)

	inFile = open( inFileName, "r" )
	line = inFile.readline()
	nbSeq = 0

	while True:
		if line == "":
			break
		if line[0] == ">":
			nbSeq = nbSeq + 1
		line = inFile.readline()
	inFile.close()

	return nbSeq

#------------------------------------------------------------------------------

def dbCumLength( inFileName ):

	"""
	Compute the cumulative sequence length in the input fasta file.

	@param inFileName: name of the input fasta file
	@type inFileName: string
	"""

	if not os.path.exists( inFileName ):
		print "*** Error: file '%s' doesn't exist" % ( inFileName )
		sys.exit(1)

	bsDB = BioseqDB( inFileName )

	return bsDB.getLength()

#------------------------------------------------------------------------------

def dbHeaders( inFileName, verbose=0 ):

	"""
	Retrieve the sequence headers present in the input fasta file.

	@param inFileName: name of the input fasta file
	@type inFileName: string

	@param verbose: level of verbosity
	@type verbose: integer

	@return: list of sequence headers
	@rtype: list of strings
	"""

	if not os.path.exists( inFileName ):
		print "*** Error: file '%s' doesn't exist" % ( inFileName )
		sys.exit(1)

	inFile = open( inFileName, "r" )
	lHeaders = []
	while True:
		line = inFile.readline()
		if line == "":
			break
		if line[0] == ">":
			lHeaders.append( line[1:-1] )
			if verbose > 0: print line[1:-1]
	inFile.close()

	return lHeaders

#------------------------------------------------------------------------------

def renameSeqHeaders( inFileName, pattern="seq", upper=True, outFilePrefix="", verbose=0 ):

	"""
	Rename the sequence headers according to the pattern (seq1, seq2, seq3...).

	@param inFileName: name of the input fasta file
	@type inFileName: string

	@param pattern: generic pattern to rename the headers (default=seq)
	@type pattern: string

	@param upper: turn sequence into upper case, AnTCnG -> ANTCNG (default=True)
	@type upper: boolean

	@param outFilePrefix: prefix of the output files (default=inFileName + '.fa' and '.map')
	@type outFileName: string

	@param verbose: verbose (default=0/1)
	@type verbose: integer
	"""

	if not os.path.exists( inFileName ):
		print "*** Error: file '%s' doesn't exist" % ( inFileName )
		sys.exit(1)

	inFile = open( inFileName, "r" )
	line = inFile.readline()

	if outFilePrefix == "":
		outFastaName = "%s_chunks.fa" % ( inFileName )
		outMapName = "%s_chunks.map" % ( inFileName )
	else:
		outFastaName = "%s.fa" % ( outFilePrefix )
		outMapName = "%s.map" % ( outFilePrefix )
	outFasta = open( outFastaName, "w" )
	outMap = open( outMapName, "w" )

	seqID = 1
	seqLength = 1
	while True:

		if line == "":
			outMap.write( "%i\n" % ( seqLength ) )
			break

		if line[0] == ">":
			if seqID != 0:
				outMap.write( "%i\n" % ( seqLength ) )
				seqLength = 0
			oldHeader = line.split(">")[1].split("\n")[0]
			newHeader = "%s%i" % ( pattern, seqID )
			outMap.write( "%s\t%s\t%i\t" % ( newHeader, oldHeader, seqLength ) )
			outFasta.write( ">%s\n" % ( newHeader ) )

		else:
			if upper == True:
				outFasta.write( line.upper() )
			else:
				outFasta.write( line )
			seqLength += len( line.split("\n")[0] )

		line = inFile.readline()

	inFile.close()
	outFasta.close()
	outMap.close()

#------------------------------------------------------------------------------

def dbChunks( inFileName, chkLgth="200000", chkOver="10000", wordN="11", outFilePrefix="", clean=False, verbose=0 ):

	"""
	Cut a data bank into chunks according to the input parameters.
	If a sequence is shorter than the threshold, it is only renamed (not cut).

	@param inFileName: name of the input fasta file
	@type inFileName: string

	@param chkLgth: chunk length (in bp, default=200000)
	@type chkLgth: string

	@param chkOver: chunk overlap (in bp, default=10000)
	@type chkOver: string

	@param wordN: N stretch word length (default=11, 0 for no detection)
	@type wordN: string

	@param outFilePrefix: prefix of the output files (default=inFileName + '_chunks.fa' or '_chunks.map')
	@type outFileName: string

	@param clean: clean (remove 'cut' and 'Nstretch' files
	@type clean: boolean

	@param verbose: verbose (default=0/1)
	@type verbose: integer
	"""

	if verbose > 0:
		nbSeq = dbSize( inFileName )
		print "cut the %i input sequences with cutterDB..." % ( nbSeq )
		sys.stdout.flush()
	pL = programLauncher( inFileName )
	pL.launchCutterDB( length=chkLgth, overlap=chkOver, wordN=wordN, verbose=verbose-1 )
	nbChunks = dbSize( "%s_cut" % ( inFileName ) )
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

	# clean
	if clean == True:
		cmd = "rm -f %s_cut %s.Nstretch.map" % ( inFileName, inFileName )
		log = os.system( cmd )
		if log != 0:
			print "*** Error: rm returned %i" % ( log )
			sys.exit(1)

#------------------------------------------------------------------------------

def dbSplit( inFileName, nbSeqPerBatch, newDir, verbose=0 ):

	"""
	split the input fasta file in several output files

	@param inFileName: name of the input fasta file
	@type inFileName: string

	@param nbSeqPerBatch: number of sequences per output file
	@type nbSeqPerBatch: string

	@param newDir: put the sequences in a new directory called 'batches'
	@type newDir: boolean

	@param verbose: verbose (default=0/1)
	@type verbose: integer
	"""

	if not os.path.exists( inFileName ):
		print "*** Error: %s doesn't exist" % ( inFileName )
		sys.exit(1)
		
	nbSeqPerBatch = int(nbSeqPerBatch)
	nbSeq = dbSize( inFileName )
	nbBatches = int( math.ceil( nbSeq / float(nbSeqPerBatch) ) )
	if verbose > 0:
		print "save the %i input sequences into %i batches" % ( nbSeq, nbBatches )
		sys.stdout.flush()

	if newDir == True:
		if os.path.exists( "batches" ):
			os.system( "rm -rf batches" )
		os.mkdir( "batches" )
		os.chdir( "batches" )
		os.system( "ln -s ../%s ." % ( inFileName ) )

	inFile = open( inFileName, "r" )

	line = inFile.readline()

	countBatch = 1
	outFileName = "batch_%s.fa" % ( str(countBatch).zfill( len(str(nbBatches)) ) )
	outFile = open( outFileName, "w" )
	countSeq = 0

	while True:
		if line == "":
			break
		if line[0] == ">":
			countSeq += 1
			if verbose > 1:
				print "saving seq '%s' in file '%s'..." % ( line[1:40][:-1], outFileName )
				sys.stdout.flush()
		if countSeq == nbSeqPerBatch + 1:
			outFile.close()
			countBatch += 1
			outFileName = "batch_%s.fa" % ( str(countBatch).zfill( len(str(nbBatches)) ) )
			outFile = open( outFileName, "w" )
			countSeq = 1
		outFile.write( line )
		line = inFile.readline()

	inFile.close()
	outFile.close()
	# delete symbolic links
	inFilePath, prefix = os.path.split( inFileName )
	if newDir == True:
		os.remove( prefix )
		os.chdir( ".." )

#------------------------------------------------------------------------------

def splitSeqPerCluster( inFileName, clusteringMethod, simplifyHeader, createDir, outPrefix="seqCluster", verbose=0 ):

	"""
	Split the input fasta file in several output files according to their cluster identifier

	@param inFileName: name of the input fasta file
	@type inFileName: string

	@param clusteringMethod: name of the clustering method (Grouper, Recon, Piler, Blastclust)
	@type clusteringMethod: string

	@param simplifyHeader: simplify the headers
	@type simplifyHeader: boolean

	@param createDir: put the sequences in different directories
	@type createDir: boolean
	
	@param outPrefix: prefix of the output files (default='seqCluster')
	@type outPrefix: string

	@param verbose: verbose (default=0/1)
	@type verbose: integer
	"""

	if not os.path.exists( inFileName ):
		print "*** Error: %s doesn't exist" % ( inFileName )
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
	prevSeqID = seqID

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
			prevSeqID = seqID
			sClusterIDs.add( clusterID )

		else:
			outFile.write( line )

		line = inFile.readline()

	outFile.close()
	if verbose > 0:
		print "number of clusters: %i" % ( len(sClusterIDs) ); sys.stdout.flush()
	os.chdir("..")

#------------------------------------------------------------------------------

def dbLength( inFileName ):

	"""
	return the length of each sequence in the input fasta file

	@param inFileName: name of the input fasta file
	@type inFileName: string
	"""

	if not os.path.exists( inFileName ):
		print "*** Error: %s doesn't exist" % ( inFileName )
		sys.exit(1)

	vec_len = []
	stat = Quantile()
	inFile = open( inFileName, "r" )
	seq = Bioseq()
	numseq = 0

	while 1:
		seq.read( inFile )
		if seq.sequence == None:
			break
		l = seq.getLength()
		stat.add( l )

		numseq = numseq + 1
		print "sequence #",numseq,"=",l,"[",seq.header[0:40],"...]"
		vec_len.append( ( l, numseq, seq.header[0:40] ) )
	inFile.close()

	vec_len.sort()
	for s in vec_len:
		print "len=",s[0],"=> #",s[1], s[2]
	print stat.string()
	print "total length=",stat.sum
	return vec_len

#------------------------------------------------------------------------------

def db2map( inFileName, map_filename="" ):

	file_db = open( inFileName , "r" )
	if map_filename == "":
		map_filename = inFileName + ".map"
	file_map = open( map_filename, "w" )
	seq = Bioseq()
	numseq = 0
	while 1:
		seq.read( file_db )
		if seq.sequence == None:
			break
		numseq = numseq + 1
		line='sequence'+str(numseq)+'\t'+seq.header+'\t1'+'\t'+str(seq.getLength())
		print line
		file_map.write( line + "\n" )

	file_db.close()
	file_map.close()
	print "saved in ",map_filename

#------------------------------------------------------------------------------

def dbLengthFilter(len_min,inFileName, verbose=0):
	file_db=open(inFileName)
	file_dbInf=open(inFileName+".Inf"+str(len_min),'w')
	file_dbSup=open(inFileName+".Sup"+str(len_min),'w')
	seq=Bioseq()
	numseq=0
	nbsave=0
	while 1:
		seq.read(file_db)
		if seq.sequence==None:
			break
		l=seq.getLength()
		numseq=numseq+1
		if l>=len_min:
		   seq.write(file_dbSup)
		   if verbose > 0:
		   	  print 'sequence #',numseq,'=',l,'[',seq.header[0:40],'...] Sup !!'
		   nbsave=nbsave+1
		else:
		   seq.write(file_dbInf)
		   if verbose > 0:
		   	  print 'sequence #',numseq,'=',l,'[',seq.header[0:40],'...] Inf !!'
		   nbsave=nbsave+1


	file_db.close()
	file_dbInf.close()
	file_dbSup.close()
	if verbose > 0:
		print nbsave,'saved sequences in ',inFileName+".Inf"+str(len_min)," and ", inFileName+".Sup"+str(len_min)

#------------------------------------------------------------------------------

def dbBestLength( num, inFileName, outFileName="", verbose=0, minThresh=0 ):

	"""
	extract the longest sequences from a fasta file

	@param num: maximum number of sequences in the output file
	@type num: integer

	@param inFileName: name of the input fasta file
	@type inFileName: string

	@param outFileName: name of the output fasta file
	@type outFileName: string
	
	@param minThresh: minimum length threshold (default=0)
	@type minThresh: integer
	"""

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

#---------------------------------------------------------------------------------

def dbExtractSeqHeaders( inFileName, outFileName="" ):

	"""
	extract all the sequence headers from a fasta file

	@param inFileName: name of the input fasta file
	@type inFileName: string

	@param outFileName: name of the output file recording the headers (default=inFileName+'.headers')
	@type outFileName: string
	"""

	if not os.path.exists( inFileName ):
		print "*** Error: %s doesn't exist" % ( inFileName )
		sys.exit(1)

	bsDB = BioseqDB( inFileName )
	log, lHeaders = bsDB.getSeqHeaders()
	if log != 0:
		print "*** Error: getSeqHeaders() returned %i" % ( log )
		sys.exit(1)

	if outFileName == "":
		outFileName = inFileName + ".headers"
	outFile = open( outFileName, "w" )
	for i in lHeaders:
		outFile.write( i + "\n" )
	outFile.close()

	return 0

#---------------------------------------------------------------------------------

def dbExtractByPattern( pattern, inFileName, outFileName="" ):

	if pattern == "":
		return
	srch = re.compile( pattern )
	file_db = open( inFileName )
	if outFileName == "":
		outFileName = inFileName + '.extracted'

	file_db2 = open( outFileName, 'w' )
	seq = Bioseq()
	numseq = 0
	nbsave = 0
	while 1:
		seq.read( file_db )
		if seq.sequence == None:
			break
		numseq = numseq + 1
		m = srch.search( seq.header )
		if m:
		   seq.write( file_db2 )
		   print 'seq #',numseq,'matched on',m.group(),'[',seq.header[0:40],'...] saved !!'
	           nbsave = nbsave + 1

	file_db.close()
	file_db2.close()
	print nbsave,'saved sequences in',outFileName

#---------------------------------------------------------------------------------

def dbExtractByFilePattern( patternFileName, inFileName, outFileName="", verbose=0 ):

	if patternFileName=="":
		print "*** Error: no file of pattern"
		sys.exit(1)

	seq = Bioseq()

	numseq = 0
	nbsave = 0
	header = []
	inFile = open( inFileName )
	while True:
		seq.read( inFile )
		if seq.sequence == None:
			break
		numseq = numseq + 1
		header.append( seq.header )
	inFile.close()

	to_keep = []
	patternFile = open( patternFileName )
	for pattern in patternFile:
		if verbose > 0:
			print "pattern: ",pattern[:-1]; sys.stdout.flush()
		srch = re.compile(pattern[:-1])
		for h in header:
			if srch.search(h):
				to_keep.append(h)
	patternFile.close()

	if outFileName == "":
		outFileName = inFileName + ".extracted"
	file_db2=open( outFileName, "w" )

	inFile = open( inFileName )
	while 1:
		seq.read(inFile)
		if seq.sequence==None:
			break
		if seq.header in to_keep:
			seq.write(file_db2)
			print 'sequence #',numseq,'[',seq.header[0:40],'...] saved !!'; sys.stdout.flush()
			nbsave=nbsave+1
	inFile.close()

	file_db2.close()

	print nbsave,'saved sequences in',outFileName

#------------------------------------------------------------------------------

def dbCleanByPattern(pattern,inFileName,db2_filename=""):

	if pattern=="":
		return
	srch=re.compile(pattern)
	file_db=open(inFileName)
	if db2_filename=="":
		db2_filename=inFileName+'.cleaned'
	
	file_db2=open(db2_filename,'w')
	seq=Bioseq()
	numseq=0
	nbsave=0
	while 1:
		seq.read(file_db)
		if seq.sequence==None:
			break
		numseq=numseq+1
		if not srch.search(seq.header):
		   seq.write(file_db2)
		   print 'sequence #',numseq,'[',seq.header[0:40],'...] saved !!'
	           nbsave=nbsave+1

	file_db.close()
	file_db2.close()
	print nbsave,'saved sequences in',db2_filename

#------------------------------------------------------------------------------

def dbCleanByFilePattern( file, inFileName, db2_filename="", verbose=0 ):

	if file == "":
		print "*** Error: no file of pattern"
		sys.exit(1)

	seq = Bioseq()

	numseq=0
	nbsave=0
	header=[]
	file_db = open( inFileName )
	while True:
		seq.read( file_db )
		if seq.sequence==None:
			break
		numseq=numseq+1
		header.append( seq.header )
	file_db.close()
	
	f=open(file)
	to_remove=[]
	for pattern in f:
		if verbose > 0:
			print "Pattern: ",pattern[:-1]; sys.stdout.flush()
		srch=re.compile(pattern[:-1])
		for h in header:
			if srch.search(h):
				to_remove.append(h)
	f.close()
	
	if db2_filename == "":
		db2_filename = inFileName + '.cleaned'
	file_db2 = open( db2_filename, 'w' )

	file_db=open( inFileName )
	num = 0
	while True:
		seq.read( file_db )
		num += 1
		if seq.sequence==None:
			break
		if seq.header not in to_remove:
			seq.write( file_db2 )
			print 'sequence #',num,'/',numseq,'[',seq.header[0:40],'...] saved !!'; sys.stdout.flush()
			nbsave=nbsave+1
	file_db.close()
				
	file_db2.close()

	print nbsave,'saved sequences in',db2_filename

#------------------------------------------------------------------------------

def dbExtractByNumber(num,inFileName,db2_filename=""):
	file_db=open(inFileName)
	if db2_filename=="":
		db2_filename=inFileName+'.extracted'
	
	file_db2=open(db2_filename,'w')
	seq=Bioseq()
	numseq=0
	while 1:
		seq.read(file_db)
		if seq.sequence==None:
			break
		numseq=numseq+1
		if numseq==num:
		   seq.write(file_db2)
		   print 'sequence #',numseq,'[',seq.header[0:40],'...] saved !!'
		   break	

	file_db.close()
	file_db2.close()

#------------------------------------------------------------------------------

def dbExtractByNumberList(numlist,inFileName,db2_filename=""):
	file_db=open(inFileName)
	if db2_filename=="":
		db2_filename=inFileName+'.extracted'
	
	file_db2=open(db2_filename,'w')
	seq=Bioseq()
	numseq=0
	nbsave=0
	while 1:
		seq.read(file_db)
		if seq.sequence==None:
			break
		numseq=numseq+1
		if numseq in numlist:
		   seq.write(file_db2)
		   print 'sequence #',numseq,'[',seq.header[0:40],'...] saved !!'
	           nbsave=nbsave+1


	file_db.close()
	file_db2.close()
	print nbsave,'saved sequences in ',db2_filename

#------------------------------------------------------------------------------

def dbExtractNumGroups( inFileName ):

    """
    extract the group list from the output fasta file from Grouper

    @param inFileName: name of output fasta file from Grouper
    @type inFileName: string
    """

    lGroups = []

    print "reading %s..." % ( inFileName )
    inFile = open( inFileName )
    line = "start"
    srchGrp = re.compile('Gr\d+')
    seq = Bioseq()
    while 1:
        seq.read( inFile )
        if seq.sequence == None:
            break
        m = srchGrp.search( seq.header )
        gr = int(m.string[m.start(0)+2:m.end(0)])	
        if gr not in lGroups:
            lGroups.append( gr )
    print "reading done !"
    inFile.close()

    return lGroups

#------------------------------------------------------------------------------

def dbExtractSeqGroups(inFileName,list_group,filename_out=""):
    print "reading ",inFileName, "..."
    file=open(inFileName)
    line="start"
    srchGrp=re.compile('Gr\d+')
    seq=Bioseq()
    if filename_out=="":
	    filename_out=inFileName+".extracted_group"
    fout=open(filename_out,"w")
    count=0
    while 1:
        seq.read(file)
        if seq.sequence==None:
            break
        m=srchGrp.search(seq.header)
        gr=int(m.string[m.start(0)+2:m.end(0)])	
        if gr in list_group:
		count=count+1
		seq.write(fout)
    file.close()
    fout.close()
    print count,"sequences saved in ",filename_out

#------------------------------------------------------------------------------

def dbCleanSeqGroups(filename,list_group,filename_out=""):
    print "reading ",filename, "..."
    file=open(filename)
    line="start"
    srchGrp=re.compile('Gr\d+')
    seq=Bioseq()
    if filename_out=="":
	    filename_out=filename+".cleaned_group"
    fout=open(filename_out,"w")
    count=0
    while 1:
        seq.read(file)
        if seq.sequence==None:
            break
        m=srchGrp.search(seq.header)
        gr=int(m.string[m.start(0)+2:m.end(0)])	
        if gr not in list_group:
		count=count+1
		seq.write(fout)
    file.close()
    fout.close()
    print count,"sequences saved in ",filename_out
    
#------------------------------------------------------------------------------

def dbExtractNumClusters(filename):
    clusters=[]
    print "reading ",filename, "..."
    file=open(filename)
    line="start"
    srchCl=re.compile('Cl\d+')
    seq=Bioseq()
    while 1:
        seq.read(file)
        if seq.sequence==None:
            break
        m=srchCl.search(seq.header)
        gr=int(m.string[m.start(0)+2:m.end(0)])	
        if gr not in clusters:
            clusters.append(gr)
    print "reading done!"
    file.close()
    return clusters            

#------------------------------------------------------------------------------

def dbExtractSeqCluster(filename,list_cluster,filename_out=""):
    print "reading ",filename, "..."
    file=open(filename)
    line="start"
    srchCl=re.compile('Cl\d+')
    seq=Bioseq()
    if filename_out=="":
	    filename_out=filename+".extracted_group"
    fout=open(filename_out,"w")
    count=0
    while 1:
        seq.read(file)
        if seq.sequence==None:
            break
        m=srchCl.search(seq.header)
        gr=int(m.string[m.start(0)+2:m.end(0)])	
        if gr in list_cluster:
		count=count+1
		seq.write(fout)
    file.close()
    fout.close()
    print count,"sequences saved in ",filename_out

#------------------------------------------------------------------------------

def dbCleanSeqCluster(filename,list_cluster,filename_out=""):
    print "reading ",filename, "..."
    file=open(filename)
    line="start"
    srchCl=re.compile('Cl\d+')
    seq=Bioseq()
    if filename_out=="":
	    filename_out=filename+".cleaned_cluster"
    fout=open(filename_out,"w")
    count=0
    while 1:
        seq.read(file)
        if seq.sequence==None:
            break
        m=srchCl.search(seq.header)
        gr=int(m.string[m.start(0)+2:m.end(0)])	
        if gr not in list_cluster:
		count=count+1
		seq.write(fout)
    file.close()
    fout.close()
    print count,"sequences saved in ",filename_out

#------------------------------------------------------------------------------

def filterClassifConsensus( inFileName, outFileName, filterSSRs, maxLengthToFilterSSRs, filterHostGenes, filterConfused, filterNoCat, nbAlignSeqNoCat, verbose=0 ):

	"""
	Filter each consensus according to the classification in its header.

	@param inFileName: name of the input fasta file
	@type inFileName: string

	@param outFileName: name of the output fasta file
	@type outFileName: string

	@param filterSSRs: filter the consensus classified as SSR
	@type filterSSRs: boolean
	
	@param maxLengthToFilterSSRs: length below which a SSR is filtered
	@type maxLengthToFilterSSRs: integer

	@param filterSSRs: filter the consensus classified as HostGene
	@type filterSSRs: boolean

	@param filterConfused: filter the consensus classified as confused
	@type filterConfused: boolean

	@param filterNoCat: filter the consensus classified as NoCat
	@type filterNoCat: boolean

	@param nbAlignSeqNoCat: minimum number of sequences in the MSA from which the NoCat consensus as been built
	@type nbAlignSeqNoCat: string

	@param verbose: verbosity level
	@type verbose: integer
	"""

	if outFileName == "":
		outFileName = "%s.filtered" % ( inFileName )
	nbAlignSeqNoCat = int( nbAlignSeqNoCat )

	if verbose > 0:
		print "input file: %s" % ( inFileName )
		print "output file: %s" % ( outFileName )
		if filterSSRs:
			if maxLengthToFilterSSRs == 0:
				print "filter SSRs"
			else:
				print "filter SSRs (<%ibp)" % ( maxLengthToFilterSSRs )
		if filterHostGenes:
			print "filter host's genes"
		if filterNoCat:
			print "filter NoCat"
		if filterConfused:
			print "filter confused"
		sys.stdout.flush()
	inFile = open( inFileName, "r" )
	outFile = open( outFileName, "w" )
	bs = Bioseq()
	nbInSeq = 0
	nbRmv = 0

	while True:
		bs.read( inFile )
		if bs.header == None:
			break
		nbInSeq += 1
		if verbose > 1: print bs.header
		if filterSSRs == True and "SSR" in bs.header and ( maxLengthToFilterSSRs == 0 or bs.getLength() <= maxLengthToFilterSSRs ):
			nbRmv += 1
			if verbose > 1: print "filtered !"
		elif filterHostGenes == True and "HostGene" in bs.header:
			nbRmv += 1
			if verbose > 1: print "filtered !"
		elif filterConfused == True and "confusedness=yes" in bs.header:
			nbRmv += 1
			if verbose > 1: print "filtered !"
		elif filterNoCat == True and "NoCat" in bs.header:
			algoMSA = ""
			for i in ["Map","MAP","Malign","Mafft","Prank","Clustalw","Muscle","Tcoffee"]:
				if i in bs.header:
					algoMSA = i
			regexp = ".*" + algoMSA + "_(\d*)\|.*"
			header = re.match(regexp, bs.header)
			nb = header.group(1)
			nbAlignSeq = int( nb )
			if nbAlignSeq <= nbAlignSeqNoCat:
				nbRmv += 1
				if verbose > 1: print "filtered !"
			else:
				bs.write( outFile )
		else:
			bs.write( outFile )

	inFile.close()
	outFile.close()

	if verbose > 0:
		print "nb of input seq: %i" % ( nbInSeq )
		print "nb of filtered seq: %i" % ( nbRmv )
		sys.stdout.flush()

#------------------------------------------------------------------------------

def dbWord(inFileName,wordsize):
	"""
	deprecated
	"""
	vec_len=[]
	file_db=open(inFileName)
	seq=Bioseq()
	numseq=0
	nb_word=0
	statCount={}
	while 1:
		seq.read(file_db)
		if seq.sequence==None:
			break
		numseq=numseq+1
		print 'sequence #',numseq,'=',seq.getLength(),'[',seq.header[0:40],'...]'
		occ,nb=seq.occ_word(wordsize)
		nb_word=nb_word+nb
		for i in occ.keys():
			if i not in statCount.keys():
				statCount[i]=occ[i]
			else:
				statCount[i]=statCount[i]+occ[i]

	file_db.close()
	vec_sort=[]
	for i in statCount.keys():
		vec_sort.append((-float(statCount[i])/nb_word,i))
	vec_sort.sort()
	for i in vec_sort:
		print i[1],"=",-i[0]

#------------------------------------------------------------------------------

def dbGCperc(inFileName):
	"""
	deprecated
	"""
	file_db=open(inFileName)
	seq=Bioseq()
	numseq=0
	sum_count=0
	sum_nb=0
	while 1:
		seq.read(file_db)
		if seq.sequence==None:
			break
		numseq=numseq+1
		occ,nb=seq.occ_word(1)
		count=0
		for i in occ.keys():
			if i == "G" or i=="C":
				count+=occ[i]
		if nb!=0 :
			print 'sequence #',numseq,'=','[',seq.header[0:20],'...]',float(count)/nb
			sum_count+=count
			sum_nb+=nb

	print "Total:",float(sum_count)/sum_nb, sum_count

	file_db.close()

#------------------------------------------------------------------------------

def dbCpG(inFileName):
	"""
	deprecated
	"""
	vec_len=[]
	file_db=open(inFileName)
	seq=Bioseq()
	numseq=0
	while 1:
		seq.read(file_db)
		if seq.sequence==None:
			break
		numseq=numseq+1
		lr,cg,c,g=seq.countCpG()
		print 'sequence #',numseq,'=',seq.header[0:40],'...]',lr,cg,c,g
	file_db.close()

#------------------------------------------------------------------------------

def dbEntropy(inFileName,wordsize):
	"""
	deprecated
	"""
	vec_len=[]
	stat=Stat()
	file_db=open(inFileName)
	seq=Bioseq()
	numseq=0
	while 1:
		seq.read(file_db)
		if seq.sequence==None:
			break
		i=seq.entropy(wordsize)
		stat.add(i)

		numseq=numseq+1
		print 'sequence #',numseq,'=',seq.getLength(),'[',seq.header[0:40],'...] entropy',i
		vec_len.append((-i,numseq,seq.header))

	file_db.close()
	vec_len.sort()
	for s in vec_len:
		print 'I=',-s[0],'=> #',s[1], s[2]
	print stat.string()
	return vec_len

#------------------------------------------------------------------------------

def dbRelEntropy(inFileName,wordsize):
	"""
	deprecated
	"""
	file_db=open(inFileName)
	seq=Bioseq()
	refocc={}
	sumlen=0
	while 1:
		seq.read(file_db)
		if seq.sequence==None:
			break
		sumlen=sumlen+seq.getLength()-wordsize
		occ=seq.occ_word(wordsize)
		if(len(refocc)==0):
			refocc=occ
		else:
			for w in occ.keys():
				if refocc.has_key(w):
					refocc[w]=refocc[w]+occ[w]
				else:
					refocc[w]=occ[w]
       	file_db.close()
	reffreq={}
	for w in refocc.keys():
		reffreq[w]=float(refocc[w]+1)/sumlen


	vec_len=[]
	stat=Stat()

	file_db=open(inFileName)
	numseq=0
	while 1:
		seq.read(file_db)
		if seq.sequence==None:
			break
		i=seq.rel_entropy(reffreq)
		stat.add(i)
		numseq=numseq+1
		print 'sequence #',numseq,'=',seq.getLength(),'[',seq.header[0:40],'...] entropy',i
		vec_len.append((i,numseq,seq.header))

	file_db.close()
	vec_len.sort()
	for s in vec_len:
		print 'H=',s[0],'=> #',s[1], s[2]
	print stat.string()
	return vec_len

#------------------------------------------------------------------------------

def dbSumRep(inFileName):
	"""
	deprecated
	"""
	import reputer
	stat={"F":Stat(),"R":Stat(),"C":Stat(),"P":Stat()}
	file_db=open(inFileName)
	seq=Bioseq()
	numseq=0
	while 1:
		seq.read(file_db)
		if seq.sequence==None:
			break
		hist=reputer.dist(seq,"-allmax -f -r -c -p -l 3")
		sumL={"F":0,"R":0,"C":0,"P":0}
		sumN={"F":0,"R":0,"C":0,"P":0}
		for i in hist:
			sumL[i[0]]=sumL[i[0]]+(i[1]*i[2])
			sumN[i[0]]=sumN[i[0]]+i[2]
		for i in sumL.keys():		
			sumL[i]=-(math.log(float(sumL[i])/sumN[i])-math.log(seq.getLength()))
			stat[i].add(sumL[i])

		numseq=numseq+1
		print 'sequence #',numseq,'=',seq.getLength(),'[',\
		      seq.header[0:40],'...]'
		print "\tF=%5.3f R=%5.3f C=%5.3f P=%5.3f" % \
		      (sumL["F"],sumL["R"],sumL["C"],sumL["P"])

	file_db.close()
	for i in stat.keys():
		print i,"=>",stat[i].string()
		

#------------------------------------------------------------------------------

def dbITRsearch(inFileName,len_min,mismatch,skip_len=20000):
	"""
	deprecated
	"""
	import reputer
	n=0
	s=0
	file_db=open(inFileName)
	file_out=open(inFileName+".stree_itr",'w')
	seq=Bioseq()
	numseq=0
	while 1:
		seq.read(file_db)
		if seq.sequence==None:
			break
		numseq=numseq+1
		print 'sequence #',numseq,'=',\
		      seq.getLength(),'[',\
		      seq.header[0:40],'...]'
		if seq.getLength()<skip_len:			
			rep=reputer.find(seq,"-p -l "+str(len_min)+\
					 " -e "+str(mismatch))
			for i in rep.rep_list:
				if i.pos1 < 5 \
				   and i.pos2+i.length2>seq.getLength()-5:
					i.view()
					n=n+1
					seq.write(file_out)
					break
		else:
			s=s+1
			print ' too long, skipped'

	print n,"found ", s, "skipped"
				
	file_db.close()
	file_out.close()

#------------------------------------------------------------------------------

def dbRepShow(inFileName,reputer_param="-allmax -f -r -c -p -l 10"):
	"""
	deprecated
	"""
	import reputer
	import Gnuplot
	tmpname=os.tmpnam();
	g = Gnuplot.Gnuplot(debug=1)
	g('set data style lines')
	g('set terminal postscript landscape color')
	g('set output "'+inFileName+'.ps"')
	allsum=0
	n=0
	max=0
	min=0
	file_db=open(inFileName)
	seq=Bioseq()
	numseq=0
	while 1:
		seq.read(file_db)
		if seq.sequence==None:
			break
		n=n+1
		replist=reputer.find(seq,reputer_param)
		fileEmpty=open(tmpname+"E","w")
		fileF=open(tmpname+"F","w")
		fileR=open(tmpname+"R","w")
		fileC=open(tmpname+"C","w")
		fileP=open(tmpname+"P","w")
		F=0
		R=0
		C=0
		P=0
		fileEmpty.write("%d\t%d"%(seq.getLength(),seq.getLength()))
		for i in replist.rep_list:
			if i.type=="F":
				F=1
				fileF.write(str(i.pos1)\
					    +"\t"+str(i.pos2)\
					    +"\n"+str(i.pos1+i.length1)\
					    +"\t"+\
					    str(i.pos2+i.length2)+"\n\n")
			elif i.type=="R":
				R=1
				fileR.write(str(i.pos1)\
					    +"\t"+str(i.pos2)\
					    +"\n"+str(i.pos1+i.length1)\
					    +"\t"+\
					    str(i.pos2+i.length2)+"\n\n")
			elif i.type=="C":
				C=1
				fileC.write(str(i.pos1)\
					    +"\t"+str(i.pos2)\
					    +"\n"+str(i.pos1+i.length1)\
					    +"\t"+\
					    str(i.pos2+i.length2)+"\n\n")
			elif i.type=="P":
				P=1
				fileP.write(str(i.pos1)\
					    +"\t"+str(i.pos2)\
					    +"\n"+str(i.pos1+i.length1)\
					    +"\t"+\
					    str(i.pos2+i.length2)+"\n\n")
		fileF.close()
		fileR.close()
		fileC.close()
		fileP.close()
		fileEmpty.close()
		
		g.title(seq.header)
		cmd='l='+str(seq.getLength())+\
		     '\nset xrange [0:l]\nset yrange [0:l]\nplot "'+\
		     tmpname+'E" notitle with dots'

		if F:
			cmd=cmd+', "'+tmpname+'F" title "F" with lines 1 1'
		if R:
			cmd=cmd+', "'+tmpname+'R" title "R" with lines 2 1'
		if C:
			cmd=cmd+', "'+tmpname+'C" title "C" with lines 3 1'
		if P:
			cmd=cmd+', "'+tmpname+'P" title "P" with lines 4 1'

		g(cmd)
			
					    
		numseq=numseq+1

	file_db.close()
	os.system("gv "+inFileName+".ps")
	os.system("rm "+tmpname+"*")		   

#------------------------------------------------------------------------------

def dbConsensus(filename,consensus_filename,max_set_size=20,max_len=20000,min_len=50,min_base_nb=1):
	"""
	deprecated
	"""

	os.system("orienter "+filename)
	tmp_consensus_filename=filename+".oriented.consensus.tmp"
	size_db=dbSize(filename+".oriented")
	file_in=open(filename+".oriented")
	file_out=open(consensus_filename,'w')
	seq=Bioseq()
    
	if size_db==1:
		seq.read(file_in)
		seq.header="not a consensus"
		seq.write(file_out)
		file_out.close()
		file_in.close()
		os.system("cp "+filename+".oriented"+
			  " "+filename+
			  ".malign.fa")
		os.system("cp "+filename+".oriented"+
			  " "+filename+
			  ".malign.fa.cons")
		sys.exit(1)

	seq_in_set=0
	nb_consensus=0
	count_set=0

	set_size=size_db
	while set_size>max_set_size:
		set_size=set_size/2

	tmp_file_out=open(tmp_consensus_filename,'w')
	last_seq=0
	while 1:
		#read subset of sequence
		seq.read(file_in)
		if seq.sequence!=None:
			if seq.getLength() < max_len and seq.getLength() > min_len:
				seq.write(tmp_file_out)
				seq_in_set=seq_in_set+1
			else:
				if seq.getLength() > max_len:
					print seq.header+" too long!!"
					if not seq.header.find(" too long, not aligned"):
						seq.header=seq.header+" too long, not aligned"
						seq.write(file_out)
				if seq.getLength() < min_len:
					print seq.header+" too short!!"
				
		else:
			last_seq=1
			if seq_in_set==0:
				return count_set
				

		# aligne subset
		if seq_in_set==set_size or last_seq:
			count_set=count_set+1
			print "aligning the set #",count_set," of ",seq_in_set," sequences"
			tmp_file_out.close()
			if seq_in_set>1:
				os.system("nice malign "+tmp_consensus_filename
					  +" 20 -8 16 4 > "
					  +tmp_consensus_filename+".malign"
					  +str(count_set)+".fa")
				os.system("nice consensusFastaAli.py -n "
					  +str(min_base_nb)+" "
					  +tmp_consensus_filename
					  +".malign"+str(count_set)+".fa ")
				os.system("cp "+tmp_consensus_filename+
					  ".malign"+str(count_set)+".fa "
					  +filename+
					  ".malign"+str(count_set)+".fa")

			else:
				os.system("cp "+tmp_consensus_filename+
					  " "+filename+
					  ".malign"+str(count_set)+".fa")
				os.system("cp "+tmp_consensus_filename+
					  " "+tmp_consensus_filename+
					  ".malign"+str(count_set)+".fa.cons")

			
			os.system("cat "+tmp_consensus_filename+
				  ".malign"+str(count_set)+\
				  ".fa.cons >> "+consensus_filename)
			seq_in_set=0
			tmp_file_out=open(tmp_consensus_filename,'w')
			if set_size==size_db or last_seq: break               
	tmp_file_out.close()
	file_out.close()
	file_in.close()
	os.system("rm "+tmp_consensus_filename+"* "+filename+".oriented" )
	return count_set

#------------------------------------------------------------------------------

def dbComplement(inFileName,comp_filename=""):
	"""
	deprecated
	"""
	file_db=open(inFileName)
	if comp_filename=="":
		comp_filename=inFileName+'.comp'
	file_comp=open(comp_filename,'w')
	seq=Bioseq()
	numseq=0
	while 1:
		seq.read(file_db)
		if seq.sequence==None:
			break
		numseq=numseq+1
		print 'sequence #',numseq,'=',seq.getLength(),'[',seq.header[0:40],'...]'
		seq.sequence=seq.complement()
		seq.header=seq.header+" (complement!)"
		seq.write(file_comp)

	file_db.close()
	file_comp.close()

#------------------------------------------------------------------------------

def dbTraduit(inFileName,phase=0,complement='T',pep_filename=""):
	"""
	deprecated
	"""
	file_db=open(inFileName)
	if pep_filename=="":
		pep_filename=inFileName+'.pep'
	file_pep=open(pep_filename,'w')
	seq=Bioseq()
	seq_out=Bioseq()
	numseq=0
	while 1:
		seq.read(file_db)
		if seq.sequence==None:
			break
		numseq=numseq+1
		print 'sequence #',numseq,'=',seq.getLength(),\
		      '[',seq.header[0:40],'...]'
		
		if phase>=0 :
			if phase==1 or phase==0 :
				seq_out.sequence=seq.traduit(1)
				seq_out.header=seq.header+" (phase 1)"
				seq_out.write(file_pep)

			if phase==2 or phase==0 :
				seq_out.sequence=seq.traduit(2)
				seq_out.header=seq.header+" (phase 2)"
				seq_out.write(file_pep)

			if phase==3 or phase==0 :
				seq_out.sequence=seq.traduit(3)
				seq_out.header=seq.header+" (phase 3)"
				seq_out.write(file_pep)

		if complement=='T' or phase<0 :
			seq.sequence=seq.complement()

			if phase==-1 or phase==0 :
				seq_out.sequence=seq.traduit(1)
				seq_out.header=seq.header+" (phase -1)"
				seq_out.write(file_pep)

			if phase==-2 or phase==0 :
				seq_out.sequence=seq.traduit(2)
				seq_out.header=seq.header+" (phase -2)"
				seq_out.write(file_pep)

			if phase==-3 or phase==0 :
				seq_out.sequence=seq.traduit(3)
				seq_out.header=seq.header+" (phase -3)"
				seq_out.write(file_pep)

	file_db.close()
	file_pep.close()

#------------------------------------------------------------------------------

def dbORF( inFileName, nb=0, size=0, outFileName="" ):

	inFile = open( inFileName )
	if outFileName == "":
		outFileName = inFileName + ".orf.map"
	outFile = open( outFileName, "w" )

	seq = Bioseq()
	seq_out = Bioseq()
	numseq = 0

	while 1:
		seq.read( inFile )
		if seq.sequence == None:
			break
		seq.upCase() 
		numseq = numseq + 1
		print 'sequence #',numseq,'=',seq.getLength(),'[',seq.header[0:40],'...]'

		orf = seq.findORF()

		best_orf = []
		for i in orf.keys():
			l = len(orf[i])
			for j in xrange(1,l):
				start = orf[i][j-1] + 4
				end = orf[i][j] + 3
				if end - start >= size:
					best_orf.append( ( end-start, i+1, start, end ) )

		seq.sequence = seq.complement()

		orf = seq.findORF()
		seqlen = seq.getLength()
		for i in orf.keys():
			l = len(orf[i])
			for j in xrange(1,l):
				start = seqlen - orf[i][j-1] - 3
				end = seqlen - orf[i][j] - 2
				if start - end >= size:
					best_orf.append( ( start-end, (i+1)*-1, start, end ) )

		best_orf.sort()
		best_orf.reverse()
		l = len(best_orf)
		if nb > l or nb == 0 :
			nb = l
		for i in xrange(0,nb):
			print best_orf[i]
			outFile.write("%s\t%s\t%d\t%d\n"%("ORF|"+str(best_orf[i][1])+\
							   "|"+str(best_orf[i][0]),seq.header,
							   best_orf[i][2],best_orf[i][3]))

	inFile.close()
	outFile.close()

	return 0

#------------------------------------------------------------------------------

def shortenSeqHeaders( inFileName, maxHeaderLgth="10", pattern="seq", outFileName="", linkFileName="" ):

	"""
	copy the input fasta file with shorter sequence headers

	@param inFileName: name of the input fasta file
	@type inFileName: string

	@param maxHeaderLgth: maximum size of sequence headers (default=10)
	@type maxHeaderLgth: string

	@param pattern: default='seq'
	@type pattern: string

	@param outFileName: name of the output fasta file (default=inFileName+'.shortH')
	@type outFileName: string

	@param linkFileName: name of the file recording the link old header - new header (default=inFileName+'.shortHlink')
	@type linkFileName: string
	"""

	if not os.path.exists( inFileName ):
		print "*** Error: %s doesn't exist" % ( inFileName )
		sys.exit(1)

	maxHeaderLgth = int( maxHeaderLgth )

	bsDB = BioseqDB( inFileName )

	if outFileName == "":
		outFileName = inFileName + ".shortH"
	if os.path.exists( outFileName ):
		os.system( "rm -f " + outFileName )
	outFile = open( outFileName, "w" )

	if linkFileName == "":
		linkFileName = inFileName + ".shortHlink"
	if os.path.exists( linkFileName ):
		os.system( "rm -f " + linkFileName )
	linkFile = open( linkFileName, "w" )

	i = 1
	for bs in bsDB.db:
		if len(bs.header) > maxHeaderLgth:
			bs.writeWithOtherHeader( outFile, "%s%i" % ( pattern, i ) )
			linkFile.write( "%s\t%s\t%i\t%i\n" % ( "%s%i" % ( pattern, i ), bs.header, 1, bs.getLength() ) )
		else:
			bs.write( outFile )
			linkFile.write( "%s\t%s\t%i\t%i\n" % ( bs.header, bs.header, 1, bs.getLength() ) )
		i += 1

	outFile.close()
	linkFile.close()

	return 0

#------------------------------------------------------------------------------

def retrieveLinksNewInitialHeaders( linkFileName ):
	dNew2Init = {}
	linkFile = open( linkFileName,"r" )
	line = linkFile.readline()
	while True:
		if line == "":
			break
		data = line.split("\t")
		dNew2Init[ data[0] ] = data[1]
		line = linkFile.readline()
	linkFile.close()
	return dNew2Init

#------------------------------------------------------------------------------

def retrieveInitSeqHeaders( inFileName, linkFileName, outFileName, verbose=0 ):
	"""
	!!!!! MIGRATION: use RetrieveInitialSequenceHeaders in the directory 'repet_base' !!!!!!!
	"""
	
	"""
	To be used after the function 'shortenSeqHeaders'.
	"""

	if not os.path.exists( inFileName ):
		print "*** Error: %s doesn't exist" % ( inFileName )
		sys.exit(1)

	if outFileName == "":
		print "*** Error: output file name requested"
		sys.exit(1)

	# retrieve the link between initial header (e.g. Dmel_Blaster_Grouper_12_MAP_3) and new header (e.g. seq15)
	if verbose > 0: print "retrieve the links initial <-> new headers"; sys.stdout.flush()
	dNew2Init = retrieveLinksNewInitialHeaders( linkFileName )
	if verbose > 0: print "nb of links: %i" % ( len(dNew2Init.keys()) ); sys.stdout.flush()

	# save the data bank with the initial headers
	if verbose > 0: print "load the fasta file with the new headers"; sys.stdout.flush()
	bsDB = BioseqDB( inFileName )
	if verbose > 0: print "save it with the initial headers"; sys.stdout.flush()
	for bs in bsDB.db:
		i = 0
		stop = False
		while stop == False:
			headerToBeReplaced = dNew2Init.keys()[i]
			if bs.header == headerToBeReplaced:
				bs.header = dNew2Init[ headerToBeReplaced ]
				stop = True
			if i == len( dNew2Init.keys() ):
				stop = True
			else:
				i += 1

	if os.path.exists( outFileName ):
		os.system( "rm -f %s" % outFileName )
	bsDB.save( outFileName )

	return 0

#------------------------------------------------------------------------------

def sortSequencesByIncreasingLength( inFile, outFile, verbose=0 ):
	"""
	Save sequences in 'inFile' into 'outFile' sorted by their length in increasing order.
	"""
	if verbose > 0:
		print "sort sequences by increasing length"
		sys.stdout.flush()
	if not os.path.exists( inFile ):
		print "ERROR: file '%s' doesn't exist" % ( inFile )
		sys.exit(1)
		
	# read each seq one by one
	# save them in distinct temporary files
	# with their length in the name
	inFileHandler = open( inFile, "r" )
	bs = Bioseq()
	countSeq = 0
	while True:
		bs.read( inFileHandler )
		if bs.header == None:
			break
		countSeq += 1
		tmpFile = "%ibp_%inb" % ( bs.getLength(), countSeq )
		bs.save( tmpFile )
		if verbose > 1:
			print "%s (%i bp) saved in '%s'" % ( bs.header, bs.getLength(), tmpFile )
		bs.header = ""
		bs.sequence = ""
	inFileHandler.close()
	
	# sort temporary file names
	# concatenate them into the output file
	if os.path.exists( outFile ):
		os.remove( outFile )
	lFiles = glob.glob( "*bp_*nb" )
	lFiles.sort( key=lambda s:int(s.split("bp_")[0]) )
	for fileName in lFiles:
		cmd = "cat %s >> %s" % ( fileName, outFile )
		returnValue = os.system( cmd )
		if returnValue != 0:
			print "ERROR while concatenating '%s' with '%s'" % ( fileName, outFile )
			sys.exit(1)
		os.remove( fileName )
		
	return 0
