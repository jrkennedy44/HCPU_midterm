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


import sys
from pyRepetUnit.commons.sql.TableAdaptator import TableAdaptator
from pyRepetUnit.commons.sql.ITableSeqAdaptator import ITableSeqAdaptator
from pyRepetUnit.commons.coord.SetUtils import SetUtils
from pyRepetUnit.commons.seq.Bioseq import Bioseq


## Adaptator for a Seq table
#
class TableSeqAdaptator( TableAdaptator, ITableSeqAdaptator ):
    
    ## Retrieve all the distinct accession names in a list.
    #
    # @return lAccessions list of accessions
    #
    def getAccessionsList( self ):
        sqlCmd = "SELECT DISTINCT accession FROM %s;" % ( self._table )
        lAccessions = self._getStringListWithSQLCmd(sqlCmd)
        return lAccessions
    
    ## Save sequences in a fasta file from a list of accession names.
    # 
    # @param lAccessions list of accessions
    # @param outFileName string Fasta file
    #
    def saveAccessionsListInFastaFile( self, lAccessions, outFileName ):
        outFile = open( outFileName, "w" )
        for ac in lAccessions:
            bs = self.getBioseqFromHeader( ac )
            bs.write(outFile)
        outFile.close()
    
    ## Get a bioseq instance given its header
    #
    # @param header string name of the sequence ('accession' field in the 'seq' table) 
    # @return bioseq instance
    #
    def getBioseqFromHeader( self, header ):
        sqlCmd = "SELECT * FROM %s WHERE accession='%s';" % ( self._table, header )
        self._iDb.execute( sqlCmd )
        res = self._iDb.fetchall()
        return Bioseq( res[0][0], res[0][1] )
        
    ## Retrieve the length of a sequence given its name.
    #
    # @param accession name of the sequence
    # @return seqLength integer length of the sequence
    # 
    def getSeqLengthFromAccession( self, accession ):
        sqlCmd = 'SELECT length FROM %s WHERE accession="%s"' % ( self._table, accession )
        seqLength = self._iDb.getIntegerWithSQLCmd(sqlCmd)
        return seqLength
    
    ## get subsequence according to given parameters
    #
    # @param accession 
    # @param start integer 
    # @param end integer
    # @return bioseq.sequence string
    #
    def getSubSequence( self, accession, start, end ):
        bs = Bioseq()
        if start <= 0 or end <= 0:
            print "ERROR with coordinates start=%i or end=%i" % ( start, end )
            sys.exit(1)
            
        if accession not in self.getAccessionsList():
            print "ERROR: accession '%s' absent from table '%s'" % ( accession, self._table )
            sys.exit(1)
            
        lengthAccession = self.getSeqLengthFromAccession( accession )
        if start > lengthAccession or end > lengthAccession:
            print "ERROR: coordinates start=%i end=%i out of sequence '%s' range (%i bp)" % ( start, end, accession, lengthAccession )
            sys.exit(1)
            
        sqlCmd = "SELECT SUBSTRING(sequence,%i,%i) FROM %s WHERE accession='%s'" % ( min(start,end), abs(end-start)+ 1, self._table, accession )
        self._iDb.execute( sqlCmd )
        res = self._iDb.fetchall()
        bs.setSequence( res[0][0] )
        if start > end:
            bs.reverseComplement()
        return bs.sequence
    
    ## get bioseq from given set list
    #
    # @param lSets set list of sets 
    # @return bioseq instance
    #
    def getBioseqFromSetList( self, lSets ):
        header = "%s::%i %s " % ( lSets[0].name, lSets[0].id, lSets[0].seqname )
        sequence = ""
        lSortedSets = SetUtils.getSetListSortedByIncreasingMinThenMax( lSets )
        if not lSets[0].isOnDirectStrand():
            lSortedSets.reverse()
        for iSet in lSortedSets:
            header += "%i..%i," % ( iSet.getStart(), iSet.getEnd() )
            sequence += self.getSubSequence( iSet.seqname, iSet.getStart(), iSet.getEnd() )
        return Bioseq( header[:-1], sequence )
    
    ## Return True if the given accession is present in the table
    #
    def isAccessionInTable( self, name ):
        sqlCmd = "SELECT accession FROM %s WHERE accession='%s'" % ( self._table, name )
        self._iDb.execute( sqlCmd )
        res = self._iDb.fetchall()
        return bool(res)
    
    ## Retrieve all the distinct accession names in a fasta file.
    #
    # @param outFileName string Fasta file
    # 
    def exportInFastaFile(self, outFileName ):
        lAccessions = self.getAccessionsList()
        self.saveAccessionsListInFastaFile( lAccessions, outFileName )
        
    def _getStringListWithSQLCmd( self, sqlCmd ):
        self._iDb.execute(sqlCmd)
        res = self._iDb.fetchall()
        lString = []
        for i in res:
            lString.append(i[0])
        return lString
   
    def _getTypeAndAttr2Insert(self, bs):
        type2Insert =  ( "'%s'", "'%s'", "'%s'", "'%i'" ) 
        attr2Insert =  (bs.header.split()[0], bs.sequence, bs.header, bs.getLength())
        return type2Insert, attr2Insert
    
    def _escapeAntislash(self, obj):
        pass

