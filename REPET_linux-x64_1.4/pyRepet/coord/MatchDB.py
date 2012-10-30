import sys, math, copy

import pyRepet.coord.Match

#------------------------------------------------------------------------------

class MatchDB:

    """
    This class manages a databank recording matches in the 'tab' format (output from Matcher).
    """

    #--------------------------------------------------------------------------

    def __init__( self, name="" ):

        """
        Constructor
        """

        self.db = []
        self.dQry2Matches = {}
        self.dSbj2Matches = {}
        self.name = name
        if name != "":
            tabFile = open( name )
            self.read( tabFile )
            tabFile.close()

    #--------------------------------------------------------------------------

    def read( self, tabFile, thresIdentity=0.0, thresLength=0.0, verbose=0 ):

        """
        Record each match of the input file as Match object.

        @param thresIdentity: load the match if the query is identical to >= x% of the subject
        @type thresIdentity: float

        @param thresLength: and if the length of the match is >= x% of the query length
        @type thresLength: float

        @param verbose: level of verbosity
        @type verbose: integer
        """

        thresIdentityPerc = math.floor( thresIdentity*100 )

        if verbose > 0:
            print "reading match file..."; sys.stdout.flush()
        line = tabFile.readline()
        countLine = 1

        while True:
            if line == "":
                break
            if verbose > 0:
                if countLine % 10000 == 0:
                    print "line %10i" % ( countLine ); sys.stdout.flush()
            if verbose > 1:
                print line[:-1]
            match = pyRepet.coord.Match.Match()
            if not line[0:10] == "query.name":
                data = line[:-1].split("\t")
                match.set_from_tuple( data )
                if match.identity >= thresIdentityPerc and match.query_length_perc >= thresLength:
                    self.add( match )
                    if verbose > 1:
                        print "keep"
                else:
                    if verbose > 1:
                        print "remove"
            line = tabFile.readline()
            countLine += 1

        if verbose > 0:
            print "done !"; sys.stdout.flush()

    #--------------------------------------------------------------------------

    def add( self, match ):

        """
        Add the match in the object's attributes.
        """

        self.db.append( match )

        if not self.dQry2Matches.has_key( match.range_query.seqname ):
            self.dQry2Matches[ match.range_query.seqname ] = [ match ]
        else:
            self.dQry2Matches[ match.range_query.seqname ].append( match )

        if not self.dSbj2Matches.has_key( match.range_subject.seqname ):
            self.dSbj2Matches[ match.range_subject.seqname ] = [ match ]
        else:
            self.dSbj2Matches[ match.range_subject.seqname ].append( match )

    #--------------------------------------------------------------------------

    def getNbMatches( self ):

        """
        Return the number of matches.
        """

        return len( self.db )

    #--------------------------------------------------------------------------

    def getNbMatchesWithThres( self, thresIdentity, thresLength ):

        """
        Return the number of matches above the thresholds.
        """

        thresIdentityPerc = math.floor( thresIdentity*100 )
        countMatch = 0

        for match in self.db:
            if match.identity >= thresIdentityPerc and match.query_length_perc >= thresLength:
                countMatch += 1

        return countMatch

    #--------------------------------------------------------------------------

    def getNbDistinctQry( self ):

        """
        Return the number of distinct queries involved in the matches.
        """

        return len( self.dQry2Matches.keys() )

    #--------------------------------------------------------------------------

    def getNbDistinctSbj( self ):

        """
        Return the number of distinct subjects involved in the matches.
        """

        return len( self.dSbj2Matches.keys() )

    #--------------------------------------------------------------------------

    def getNbDistinctQryWithThres( self, thresIdentity, thresLength ):

        """
        Count the number of distinct queries involved in at least one match above the thresholds.
        """

        thresIdentityPerc = math.floor( thresIdentity*100 )
        countQry = 0

        for qry in self.dQry2Matches.keys():
            countMatch = 0
            for match in self.dQry2Matches[ qry ]:
                if match.identity >= thresIdentityPerc and match.query_length_perc >= thresLength:
                    countMatch += 1
            if countMatch > 0:
                countQry += 1

        return countQry

    #--------------------------------------------------------------------------

    def getNbDistinctSbjWithThres( self, thresIdentity, thresLength ):

        """
        Count the number of distinct subjects involved in at least one match above the thresholds.
        """

        thresIdentityPerc = math.floor( thresIdentity*100 )
        countSbj = 0

        for qry in self.dSbj2Matches.keys():
            countMatch = 0
            for match in self.dSbj2Matches[ qry ]:
                if match.identity >= thresIdentityPerc and match.query_length_perc >= thresLength:
                    countMatch += 1
            if countMatch > 0:
                countSbj += 1

        return countSbj

    #--------------------------------------------------------------------------

    def showNbMatchesPerQuery( self ):

        """

        """

        for qry in self.dQry2Matches.keys():
            print "%s: %i matches as query" % ( qry, len(self.dQry2Matches[qry]) )
        sys.stdout.flush()

    #--------------------------------------------------------------------------

    def showNbMatchesPerQueryWithThres( self, thresIdentity, thresLength ):

        """

        """

        thresIdentityPerc = math.floor( thresIdentity*100 )

        for qry in self.dQry2Matches.keys():
            countMatch = 0
            for match in self.dQry2Matches[ qry ]:
                if match.identity >= thresIdentityPerc and match.query_length_perc >= thresLength:
                    countMatch += 1
            if countMatch > 0:
                print "%s: %i matches as query (id>=%.2f,qlgth>=%.2f)" % ( qry, countMatch, thresIdentity, thresLength )
        sys.stdout.flush()

    #--------------------------------------------------------------------------

    def rmvDoublons( self, verbose=0 ):

        """
        Remove match doublons.
        """

        if verbose > 0:
            print "nb of matches (with doublons): %i" % ( self.getNbMatches() )

        # fill a list of non-redundant matches
        lMatchesUniq = []
        for match in self.db:
            if len(lMatchesUniq) == 0:
                lMatchesUniq.append( match )
            else:
                nbDoublons = 0
                for m in lMatchesUniq:
                    if match.isDoublonWith( m ):
                        nbDoublons += 1
                if nbDoublons == 0:
                    lMatchesUniq.append( match )

        # check it is really non-redundant
        for match1 in lMatchesUniq:
            for match2 in lMatchesUniq:
                if match1.id != match2.id:
                    if match1.isDoublonWith( match2 ):
                        print "*** Error: doublon not removed"
                        sys.exit(1)

        # update the attributes
        self.db = []
        self.dQry2Matches = {}
        self.dSbj2Matches = {}
        for match in lMatchesUniq:
            self.add( match )

        if verbose > 0:
            print "nb of matches (without doublons): %i" % ( self.getNbMatches() )

    #--------------------------------------------------------------------------

    def filterDiffQrySbj( self, qryDB, thresIdentity, thresLength, verbose=0 ):

        """
        Return the list of queries 'included' in subjects when two different databanks are used.

        @param qryDB: databank of all the queries
        @type qryDB: BioseqDB object

        @param thresIdentity: remove the seq if it is identical to >= 95% of another seq
        @type thresIdentity: float

        @param thresLength: and if the length of the match is >= 98% of its length
        @type thresLength: float

        @return: list of query name to keep
        @rtype: list of strings

        @return: dictionary whose keys are query name and values the match because of which the queri will be removed
        @rtype: list of strings
        """

        if verbose > 0:
            print "filtering matches (id>=%.2f,qlgth>=%.2f)..." % ( thresIdentity, thresLength ); sys.stdout.flush()

        thresIdentityPerc = math.floor( thresIdentity*100 )
        dQryToRmv2Matches = {}
        lQryToKeep = []
        nbSeqWithoutMatch = 0
        nbSeqWithMatchBelow = 0
        nbSeqWithMatchAbove = 0
        nbSeqToRmv = 0

        # for each sequence given in input as query
        for seqH in qryDB.idx.keys():

            # keep it if it has no match
            if not self.dQry2Matches.has_key( seqH ):
                nbSeqWithoutMatch += 1
                if seqH not in lQryToKeep:
                    lQryToKeep.append( seqH )

            # otherwise
            else:
                nbMatchAboveThresh = 0
                queryIsShorter = False

                # for each of its matches
                for match in self.dQry2Matches[ seqH ]:

                    # check if they are above the thresholds
                    if match.identity >= thresIdentityPerc and match.query_length_perc >= thresLength:
                        nbMatchAboveThresh += 1

                    # keep the match because of which this query will be removed
                    else:
                        dQryToRmv2Matches[ seqH ] = match

                # keep the query if it has only matches below the thresholds
                if nbMatchAboveThresh == 0:
                    nbSeqWithMatchBelow += 1
                    if seqH not in lQryToKeep:
                        lQryToKeep.append( seqH )
                else:
                    nbSeqToRmv += 1

        if verbose > 0:
            print "nb of sequences without any match: %i" % ( nbSeqWithoutMatch )
            print "nb of sequences to remove (matches above the threshold): %i" % ( nbSeqToRmv )
            print "done !"; sys.stdout.flush()

        return lQryToKeep, dQryToRmv2Matches

    #--------------------------------------------------------------------------

    def filterSameQrySbj( self, qryDB, thresIdentity, thresLength, verbose=0 ):

        """
        Return the list of queries 'included' in subjects when the same databank is used for both.

        @param qryDB: databank of all the queries
        @type qryDB: BioseqDB object

        @param thresIdentity: remove the seq if it is identical to >= 95% of another seq
        @type thresIdentity: float

        @param thresLength: and if the length of the match is >= 98% of its length
        @type thresLength: float

        @return: list of query headers to keep
        @rtype: list of strings

        @return: dictionary whose keys are query name and values the match because of which the queri will be removed
        @rtype: list of strings
        """

        if verbose > 0:
            print "filtering matches (id>=%.2f,qlgth>=%.2f)..." % ( thresIdentity, thresLength ); sys.stdout.flush()

        dQryToRmv2Matches = {}
        dContained = {}   # the keys of this dico are the sequences CONTAINED in other sequences
        dMatchLgth100 = {}   # keys are queries in matches with matchLgthPerc = 100%
        dQry2countOverThresh = {}

        thresIdentityPerc = math.floor( thresIdentity*100 )

        # for each match
        for match in self.db:

            # if it is above the thresholds
            if match.identity >= thresIdentityPerc and match.query_length_perc >= thresLength:

                if not dQry2countOverThresh.has_key( match.range_query.seqname ):
                    dQry2countOverThresh[ match.range_query.seqname ] = 1
                else:
                    dQry2countOverThresh[ match.range_query.seqname ] += 1

                if match.match_length_perc < 1.0 and match.query_length_perc >= match.match_length_perc:
                    string = "query %s (%d bp) is contained in subject %s (%d bp)   (%f - %f - %f)" %\
                          ( match.range_query.seqname, match.query_length, match.range_subject.seqname,
                            match.subject_length, match.identity,
                            match.query_length_perc, match.match_length_perc )
                    if verbose > 1: print string; sys.stdout.flush()
                    if dContained.has_key( match.range_subject.seqname ) and dContained[ match.range_subject.seqname ] == [ match.range_query.seqname ]:
                        continue
                    if dContained.has_key( match.range_query.seqname ):
                        dContained[ match.range_query.seqname ].append( match.range_subject.seqname )
                    else:
                        dContained[ match.range_query.seqname ] = [ match.range_subject.seqname ]
                    dQryToRmv2Matches[ match.range_query.seqname ] = match

                elif match.match_length_perc == 1.0:
                    if dMatchLgth100.has_key( match.range_subject.seqname ) and match.range_query.seqname in dMatchLgth100[ match.range_subject.seqname ]:
                        string = "query %s (%d bp) is contained in subject %s (%d bp)   (%f - %f - %f)" %\
                              ( match.range_query.seqname, match.query_length, match.range_subject.seqname,
                                match.subject_length, match.identity,
                                match.query_length_perc, match.match_length_perc )
                        if verbose > 1: print string; sys.stdout.flush()
                        if dContained.has_key( match.range_query.seqname ):
                            dContained[ match.range_query.seqname ].append( match.range_subject.seqname )
                        else:
                            dContained[ match.range_query.seqname ] = [ match.range_subject.seqname ]
                        dQryToRmv2Matches[ match.range_query.seqname ] = match
                    if dMatchLgth100.has_key( match.range_subject.seqname ) and match.range_query.seqname not in dMatchLgth100[ match.range_subject.seqname ]:
                        dMatchLgth100[ match.range_subject.seqname ].append( match.range_query.seqname )
                    if not dMatchLgth100.has_key( match.range_subject.seqname ):
                        dMatchLgth100[ match.range_query.seqname ] = [ match.range_subject.seqname ]

        lSeqToRmv = dContained.keys()

        lQryToKeep = []
        for bs in qryDB.db:
            if bs.header not in lSeqToRmv:
                lQryToKeep.append( bs.header )

        if verbose > 0:
            print "nb of sequences to remove (matches above the threshold): %i" % ( len(lSeqToRmv) )
            print "done !"; sys.stdout.flush()

        return lQryToKeep, dQryToRmv2Matches
