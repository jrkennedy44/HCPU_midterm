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


from pyRepetUnit.commons.coord.Match import Match


## Static methods for the manipulation of Match instances
#
class MatchUtils ( object ):
    
    ## Return a list with Match instances from the given file
    #
    # @param inFile name of a file in the Match format
    # @return a list of Match instances
    #
    def getMatchListFromFile( inFile ):
        lMatchInstances = []
        inFileHandler = open( inFile, "r" )
        while True:
            line = inFileHandler.readline()
            if line == "":
                break
            if line[0:10] == "query.name":
                continue
            m = Match()
            m.setFromString( line )
            lMatchInstances.append( m )
        inFileHandler.close()
        return lMatchInstances
    
    getMatchListFromFile = staticmethod( getMatchListFromFile )
    
    
    ##  Split a Match list in several Match lists according to the subject
    #
    #  @param lMatches a list of Match instances
    #  @return a dictionary which keys are subject names and values Match lists
    #
    def getDictOfListsWithSubjectAsKey( lMatches ):
        dSubject2MatchList = {}
        for iMatch in lMatches:
            if not dSubject2MatchList.has_key( iMatch.range_subject.seqname ):
                dSubject2MatchList[ iMatch.range_subject.seqname ] = []
            dSubject2MatchList[ iMatch.range_subject.seqname ].append( iMatch )
        return dSubject2MatchList
    
    getDictOfListsWithSubjectAsKey = staticmethod( getDictOfListsWithSubjectAsKey )
    
    
    ## Write Match instances contained in the given list
    #
    # @param lMatches a list of Match instances
    # @param fileName name of the file to write the Match instances
    # @param mode the open mode of the file ""w"" or ""a"" 
    #
    def writeListInFile( lMatches, fileName, mode="w", header=None ):
        fileHandler = open( fileName, mode )
        if header:
            fileHandler.write( header )
        for iMatch in lMatches:
            iMatch.write( fileHandler )
        fileHandler.close()
        
    writeListInFile = staticmethod( writeListInFile )

    ## Give path id list from a list of Match instances
    #
    # @param lMatch list of Match instances
    #
    # @return lId integer list
    #
    def getIdListFromMatchList(lMatch):
        lId = []
        for iMatch in lMatch:
            lId.append(iMatch.id)
        return lId
    
    getIdListFromMatchList = staticmethod(getIdListFromMatchList)