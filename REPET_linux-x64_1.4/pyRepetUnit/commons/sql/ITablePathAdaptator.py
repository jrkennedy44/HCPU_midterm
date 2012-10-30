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


## Interface for TablePathAdaptator
#
class ITablePathAdaptator (object):

    ## Give the data contained in the table as a list of Path instances
    #
    # @return lPaths list of path instances
    #
    def getListOfAllPaths( self ):
        pass
    
    ## Give a list of Path instances having the same identifier
    #
    # @param id integer identifier number
    # @return lPath a list of Path instances
    #
    # @warning old name was getPathList_from_num
    #
    def getPathListFromId( self, id ):
        pass

    ## Give a list of Path instances according to the given list of identifier numbers
    #
    # @param lId integer list 
    # @return lPath a list of Path instances
    #
    # @warning old name was getPathList_from_numlist
    #
    def getPathListFromIdList( self, lId ):
        pass
        
    ## Give a list of Path instances having the same given query name
    #
    # @param query string name of the query 
    # @return lPath a list of Path instances
    #
    # @warning old name was getPathList_from_query
    #
    def getPathListFromQuery( self, query ):
        pass
    
    ## Give a list with all the distinct identifiers corresponding to the query
    #
    # @param query string name of the query 
    # @return lId a list of integer
    #
    # @warning old name was getPathList_from_query
    #
    def getIdListFromQuery( self, query ):
        pass
    
    ## Give a list with all the distinct identifiers corresponding to the subject
    #
    # @param subject string name of the subject 
    # @return lId a list of integer
    #
    # @warning old name was getPathList_from_subject
    #
    def getIdListFromSubject( self, subject ):
        pass
    
    ## Insert a path instance
    #
    # @param obj a path instance
    # @param delayed boolean indicating if the insert must be delayed
    #
    # @note data are inserted such that the query is always on the direct strand
    #
    # @warning old name was insAPath
    #
    def insert(self, obj, delayed = False):
        pass
    
    ## Insert a list of Path instances
    #
    # @param l a list of Path instances
    # @param delayed boolean
    #
    # @warning old name was insPathList
    #
    def insertList(self, l, delayed = False):
        pass
    
    ## Give a list of the identifier number contained in the table
    #
    # @return l integer list
    #
    # @warning old name was getPath_num
    #
    def getIdList(self):
        pass
    
    ## Give a list of Path instances having the same given subject name
    #
    # @param subject string name of the subject 
    # @return lPath a list of Path instances
    #
    # @warning old name was getPath_num
    #
    def getPathListFromSubject( self, subject ):
        pass
    
    ## Give a list of the distinct subject names present in the table
    #
    # @return lDistinctTypeNames string list
    #
    # @warning old name was getListDistinctSubjectName
    #
    def getSubjectList(self):
        pass
    
    ## Give a list of the distinct query names present in the table
    #
    # @return lDistinctQueryNames string list
    #
    # @warning old name was getListDistinctQueryName
    #
    def getQueryList(self):
        pass
    
    ## Give a list of Set instance list from the path contained on a query name
    #
    # @param queryName string query name
    # @return lSet list of set instance 
    #
    def getSubjectListFromQuery (self, queryName):
        pass
    
    ## Give a list of Path instances with the given query and subject, both on direct strand
    #
    # @param query string query name
    # @param subject string subject name
    # @return lPaths list of path instances
    #
    # @warning old name was getListPathsWithDirectQueryDirectSubjectPerQuerySubject
    #
    def getPathListWithDirectQueryDirectSubjectFromQuerySubject( self, query, subject ):
        pass
    
    ## Give a list of Path instances with the given query on direct strand and the given subject on reverse strand
    #
    # @param query string query name
    # @param subject string subject name
    # @return lPaths list of path instances
    #
    # @warning old name was getListPathsWithDirectQueryReverseSubjectPerQuerySubject
    #
    def getPathListWithDirectQueryReverseSubjectFromQuerySubject( self, query, subject ):
        pass
    
    ## Give the number of Path instances with the given query name
    #
    # @param query string query name
    # @return pathNb integer the number of Path instances
    #
    # @warning old name was getNbPaths_from_query
    #
    def getNbPathsFromQuery( self, query ):
        pass
    
    ## Give the number of Path instances with the given subject name
    #
    # @param subject string subject name
    # @return pathNb integer the number of Path instances
    #
    # @warning old name was getNbPaths_from_subject
    #
    def getNbPathsFromSubject( self, subject ):
        pass
    
    ## Give the number of distinct path identifiers
    #
    # @return idNb integer the number of Path instances
    #
    # @warning old name was getNbAllPathsnums
    #
    def getNbIds( self ):
        pass
    
    ## Give the number of distinct path identifiers for a given subject
    #
    # subjectName string subject name
    # @return idNb integer the number of Path instances
    #
    # @warning old name was getNbPathsnums_from_subject
    #
    def getNbIdsFromSubject( self, subjectName ):
        pass
    
    ## Give the number of distinct path identifiers for a given query
    #
    # @param queryName string query name
    # @return idNb integer the number of Path instances
    #
    # @warning old name was getNbPathsnums_from_query
    #
    def getNbIdsFromQuery( self, queryName ):
        pass
    
    ## Give a list of Path instances overlapping a given region
    #
    # @param query string query name
    # @param start integer start coordinate
    # @param end integer end coordinate
    # @return lPath list of Path instances
    #
    def getPathListOverlappingQueryCoord( self, query, start, end ):
        pass
    
    ## Give a list of Set instances overlapping a given region
    #
    # @param query string query name
    # @param start integer start coordinate
    # @param end integer end coordinate
    # @return lSet list of Set instances
    #
    # @warning old name was getSetList_from_qcoord
    #
    def getSetListOverlappingQueryCoord(self, query, start, end):
        pass

    ## Give a list of Path instances included in a given query region
    #
    # @param query string query name
    # @param start integer start coordinate
    # @param end integer end coordinate
    # @return lPaths list of Path instances
    #
    # @warning old name was getIncludedPathList_from_qcoord
    #
    def getPathListIncludedInQueryCoord( self, query, start, end ):
        pass
    
    ## Give a list of Set instances included in a given region
    #
    # @param query string query name
    # @param start integer start coordinate
    # @param end integer end coordinate
    # @return lSet list of Set instances
    #
    # @warning old name was getInSetList_from_qcoord
    #
    def getSetListIncludedInQueryCoord(self, query, start, end):
        pass
    
    ## Give a a list of Path instances sorted by query coordinates
    #
    # @return lPaths list of Path instances
    #
    # @warning old name was getListOfPathsSortedByQueryCoord
    #
    def getPathListSortedByQueryCoord( self ):
        pass
    
    ## Give a a list of Path instances sorted by query coordinates for a given query
    #
    # @param queryName string query name
    # @return lPaths list of Path instances
    #
    def getPathListSortedByQueryCoordFromQuery( self, queryName ):
        pass
    
    ## Give a list of path instances sorted by increasing E-value
    #
    # queryName string query name
    # @return lPaths list of path instances
    #
    def getPathListSortedByIncreasingEvalueFromQuery( self, queryName ):
        pass

    ## Give a cumulative length of all paths (fragments) for a given subject name
    #
    # @param subjectName string subject name
    # @return nb Cumulative length for all path
    # @warning doesn't take into account the overlaps !!
    # @warning old name was getCumulPathLength_from_subject
    #  
    def getCumulLengthFromSubject( self, subjectName ):
        pass
    
    ## Give a list of the length of all chains of paths for a given subject name
    #
    # @param subjectName string  name of the subject
    # @return lChainLengths list of lengths per chain of paths
    # @warning doesn't take into account the overlaps !!
    # @warning old name was getListChainLength_from_subject
    #
    def getChainLengthListFromSubject( self, subjectName ):
        pass

    ## Give a list of identity of all chains of paths for a given subject name
    #
    # @param subjectName string name of the subject
    # @return lChainIdentities list of identities per chain of paths
    # @warning doesn't take into account the overlaps !!
    # @warning old name was getListChainIdentity_from_subject
    # 
    def getChainIdentityListFromSubject( self, subjectName ):
        pass
    
    ## Give a list of Path lists sorted by weighted identity.
    #
    # @param qry query name
    # @return lChains list of chains
    #
    def getListOfChainsSortedByAscIdentityFromQuery( self, qry ):
        pass
    
    ## Give a list of the length of all paths for a given subject name
    #
    # @param subjectName string name of the subject
    # @return lPathLengths list of lengths per path
    # @warning doesn't take into account the overlaps !!
    # @warning old name was getListPathLength_from_subject
    #
    def getPathLengthListFromSubject( self, subjectName ):
        pass
    
    ## Give a a list with all distinct identifiers for a given subject sorted in decreasing order according to the length of the chains
    #    
    # @return lPathNums a list of paths Id
    #
    # @warning old name was getPathNumListSortedByDecreasingChainLengthFromSubject
    #
    def getIdListSortedByDecreasingChainLengthFromSubject( self, subjectName ):
        pass
    
    ## Give a list of Set instance list from the path contained on a query name
    #
    # @param query string query name
    # @return lSet list of set instance 
    #
    # @warning old name was getSetList_from_contig
    #
    def getSetListFromQuery(self, query):
        pass
    
    ## Delete path corresponding to a given identifier number
    #
    # @param id integer identifier number
    #
    # @warning old name was delPath_from_num
    #
    def deleteFromId(self,id):
        pass
    
    ## Delete path corresponding to a given list of identifier number
    #
    # @param lId list of identifier number
    #
    # @warning old name was delPath_from_numlist
    #
    def deleteFromIdList(self,lId):
        pass

    ## Join two path by changing id number of id1 and id2 path to the least of id1 and id2
    #
    # @param id1 integer path number
    # @param id2 integer path number
    # @return newId integer id used to join
    #
    # @warning old name was joinPath
    #
    def joinTwoPaths(self,id1,id2):
        pass
    
    ## Get a new id number
    #
    # @return newId integer new id
    #
    def getNewId(self):
        pass
    
    ## Test if table is empty
    #    
    def isEmpty( self ):
        pass
    
    ## Create a 'pathRange' table from a 'path' table. 
    # The output table summarizes the information per identifier. 
    # The min and max value are taken. 
    # The identity is averaged over the fragments. 
    # It may overwrite an existing table.
    #
    # @param outTable string name of the output table
    # @return outTable string Table which summarizes the information per identifier
    #
    def path2PathRange( self, outTable="" ):
        pass
    
    ## Return the number of times a given instance is present in the table
    # The identifier is not considered,
    # only coordinates, score, E-value and identity.
    #
    # @return nbOcc integer
    #
    def getNbOccurrences( self, iPath ):
        pass
