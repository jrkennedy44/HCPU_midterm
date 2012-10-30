#!/usr/bin/env python

###@file
# Read a file recording matches in the 'tab' format (output from Matcher) and return the number of matches between queries and subjects being CC, CI, IC and II.
# A match is said to be CC (for complete-complete) when both query and subject match over x% of their entire respective length. By default, x=95.
#
# usage: tabFileReader.py [ options ]
# options:
#      -h: this help
#      -m: name of the file recording the matches (format='tab', output from Matcher)
#      -q: name of the fasta file recording the queries
#      -s: name of the fasta file recording the subjects
#      -t: threshold over which the match is 'complete', in % of the seq length (default=95)
#      -i: identity below which matches are ignored (default=0)
#      -l: length below which matches are ignored (default=0)
#      -o: overlap on query and subject below which matches are ignored (default=0)
#      -v: verbose (default=0/1)

import sys
import getopt
from string import *

import pyRepet.seq.BioseqDB
import pyRepet.util.Stat

#----------------------------------------------------------------------------

def help():
    print
    print "usage: %s [ options ]" % ( sys.argv[0].split("/")[-1] )
    print "options:"
    print "     -h: this help"
    print "     -m: name of the file recording the matches (format='tab', output from Matcher)"
    print "     -q: name of the fasta file recording the queries"
    print "     -s: name of the fasta file recording the subjects"
    print "     -t: coverage threshold over which the match is 'complete' (in %% of the seq length, default=95)"
    print "     -i: identity below which matches are ignored (default=0)"
    print "     -l: length below which matches are ignored (default=0)"
    print "     -o: overlap on query and subject below which matches are ignored (default=0)"
    print "     -I: identity threshold for 'CC' matches (default=90)"
    print "     -E: E-value threshold for 'CC' matches (default=1e-10)"
    print "     -T: coverage threshold for match length on query compare to subject length (default=90)"
    print "     -v: verbose (default=0/1)"
    print

#----------------------------------------------------------------------------

#here are the fields of a '.tab' file:
#[0]: query sequence name
#[1]: whole match start coordinate on the query sequence
#[2]: whole match end coordinate on the query sequence
#[3]: length on the query sequence
#[4]: length in percentage of the query sequence
#[5]: length on the query relative to the subject length in percentage
#[6]: subject sequence name
#[7]: whole match start coordinate on the subject sequence
#[8]: whole match end coordinate on the subject sequence
#[9]: length on the subject sequence
#[10]: length in percentage of the subject sequence
#[11]: BLAST E-value
#[12]: BLAST score
#[13]: identity percentage
#[14]: path

class tabFileReader( object ):

    def __init__( self, line ):

        columns = line.split("\t")

        self.name_sbj = (columns[6])
        self.length_sbj = int(round(int(columns[9])/float(columns[10]),0))  #length of the subject
        self.prct_sbj = float(columns[10]) * 100  #prct_sbj = length of the match on the subject divided by the length of the subject * 100
        if int(columns[7]) < int(columns[8]):
            self.start_sbj = int(columns[7])                        #start of the match on the subject
            self.end_sbj = int(columns[8])                          #end of the match on the subject
        else:
            self.start_sbj = int(columns[8])
            self.end_sbj = int(columns[7])
        self.sbj_dist_ends = int(columns[9])                    #length on the subject that matches with the query

        self.name_qry = columns[0]
        self.length_qry = int(round(int(columns[3])/float(columns[4]),0))  #length of the query
        self.prct_qry = float(columns[4]) * 100   #prct_qry = length of the match on the query divided by the length of the query * 100
        if int(columns[1]) < int(columns[2]):
            self.start_qry = int(columns[1])                        #start of the match on the query
            self.end_qry = int(columns[2])                          #end of the match on the query
        else:
            self.start_qry = int(columns[2])
            self.end_qry = int(columns[1])
        self.qry_dist_ends = int(columns[3])                    #length on the query that matches with the subject

        self.length_match = int(columns[3])
        self.prct_matchQryOverSbj = float(columns[5]) * 100   #length on the query relative to the subject length in percentage
        self.identity = float(columns[13])
        self.score = int(columns[12])
        self.evalue = float(columns[11])

        self.sbj2qry = [self.length_sbj,self.prct_sbj,self.start_sbj,self.end_sbj,self.name_qry,self.length_sbj,self.prct_qry,self.start_qry,self.end_qry,self.identity,self.score]
        
        self.qry2sbj = [self.length_qry,self.prct_qry,self.start_qry,self.end_qry,self.name_sbj,self.length_sbj,self.prct_sbj,self.start_sbj,self.end_sbj,self.identity,self.score]

#----------------------------------------------------------------------------

def make_dico( lMatches ):
    """
    Record the matches in two dictionaries which keys are the queries or the subjects.
    """

    Sbj2Qry = {}
    Qry2Sbj = {}

    for match in lMatches:
        if Sbj2Qry.has_key( match.name_sbj ):
            Sbj2Qry[match.name_sbj].append( match )
        else:
            Sbj2Qry[match.name_sbj] = [ match ]
        if Qry2Sbj.has_key( match.name_qry ):
            Qry2Sbj[match.name_qry].append( match )
        else:
            Qry2Sbj[match.name_qry] = [ match ]

    return [ Sbj2Qry, Qry2Sbj ]

#----------------------------------------------------------------------------

def find_UniqRedun( list_matchs ):

    list_total_sbj = [];list_total_qry = []
    list_uniq_sbj = [];list_redun_sbj = []
    list_uniq_qry = [];list_redun_qry = []

    for match in list_matchs:
        list_total_sbj.append(match.name_sbj)
        list_total_qry.append(match.name_qry)

    for name_sbj in list_total_sbj:
        if list_total_sbj.count(name_sbj) == 1:
            list_uniq_sbj.append(name_sbj)
        else:
            if name_sbj not in list_redun_sbj:
                list_redun_sbj.append(name_sbj)

    for name_qry in list_total_qry:
        if list_total_qry.count(name_qry) == 1:
            list_uniq_qry.append(name_qry)
        else:
            if name_qry not in list_redun_qry:
                list_redun_qry.append(name_qry)

    return [ list_uniq_sbj, list_redun_sbj, list_uniq_qry, list_redun_qry ]

#----------------------------------------------------------------------------

def remove( all, sup_sbjqry, sup_sbj, sup_qry, inf_sbjqry ):

    for name_sbj in all.keys():

        if sup_sbjqry.has_key( name_sbj ) and sup_sbj.has_key( name_sbj ):
            del sup_sbj[ name_sbj ]

        if sup_sbjqry.has_key( name_sbj ) and sup_qry.has_key( name_sbj ):
            del sup_qry[ name_sbj ]

        if sup_sbjqry.has_key( name_sbj ) and inf_sbjqry.has_key( name_sbj ):
            del inf_sbjqry[ name_sbj ]

        if sup_sbj.has_key( name_sbj ) and sup_qry.has_key( name_sbj ):
            del sup_qry[ name_sbj ]

        if sup_sbj.has_key( name_sbj ) and inf_sbjqry.has_key( name_sbj ):
            del inf_sbjqry[ name_sbj ]

        if sup_qry.has_key( name_sbj ) and inf_sbjqry.has_key( name_sbj ):
            del inf_sbjqry[ name_sbj ]

    return [ sup_sbj, sup_qry, inf_sbjqry ]

#----------------------------------------------------------------------------

def write_output( outFile, match_type, Sbj2Qry, dSbj2Cat, Qry2Sbj, dQry2Cat ):
    """
    Save the results (subjects in each category and its matches) in a human-readable way.
    """

    if match_type == 'CC':
        msg = "Matches with L >= %i%% for subject and query (CC)" % ( thresholdCoverage )
    elif match_type == 'CI':
        msg = "Matches with L >= %i%% for subject and L < %i%% for query (CI)" % ( thresholdCoverage, thresholdCoverage )
    elif match_type == 'IC':
        msg = "Matches with L < %i%% for subject and L >= %i%% for query (IC)" % ( thresholdCoverage, thresholdCoverage )
    elif match_type == 'II':
        msg ="Matches with L < %i%% for subject and query (II)" % ( thresholdCoverage )
    if verbose > 1:
        print "%s: %i subjects" % ( msg, len(Sbj2Qry.keys()) )
    outFile.write("\n%s\n" % ( msg ) )

    for name_sbj in Sbj2Qry.keys():
        matchs = Sbj2Qry[name_sbj]
        if len(matchs) == 1:
            outFile.write("-> subject %s (%s: %s,%s) matches with query %s (%s: %s,%s): prct_sbj %.3f & prct_qry %.3f (id=%.3f,Eval=%g)\n" % (name_sbj,matchs[0].length_sbj,matchs[0].start_sbj,matchs[0].end_sbj,matchs[0].name_qry,matchs[0].length_qry,matchs[0].start_qry,matchs[0].end_qry,matchs[0].prct_sbj,matchs[0].prct_qry,matchs[0].identity,matchs[0].evalue))
        else:
            outFile.write("-> subject %s (%s: %s,%s) matches with %s queries:\n" % (name_sbj,matchs[0].length_sbj,matchs[0].start_sbj,matchs[0].end_sbj,len(matchs)))
            for match in matchs:
                outFile.write("%s versus %s (%s: %s,%s): prct_sbj %.3f & prct_qry %.3f (id=%.3f,Eval=%g)\n"%(name_sbj,match.name_qry,match.length_qry,match.start_qry,match.end_qry,match.prct_sbj,match.prct_qry,match.identity,match.evalue))

    tmpList = []
    for name_sbj in Sbj2Qry.keys():
        tmpList.append( name_sbj.split(" ")[0].lower() )
    tmpList.sort()
    for name_sbj in tmpList:
        outFile.write( name_sbj+"\n" )
        dSbj2Cat[ name_sbj ] = match_type

    tmpList = []
    for name_qry in Qry2Sbj.keys():
        tmpList.append( name_qry.split(" ")[0].lower() )
    tmpList.sort()
    for name_qry in tmpList:
        outFile.write( name_qry+"\n" )
        dQry2Cat[ name_qry ] = match_type

#----------------------------------------------------------------------------

def writeSubjectCategory( dSbj2Cat ):
    """
    Save the category (CC/CI/IC/II/NA) in which each subject has been found.

    @param dSbj2Cat: dictionary which keys are subject names and values the category of that subject
    @type dSbj2Cat: dictionary
    """

    # sort the subject names in alphabetical order
    lSbjSorted = dSbj2Cat.keys()
    lSbjSorted.sort()

    catFile = open( tabFileName + "_sbjCategories.txt", "w" )
    for sbj in lSbjSorted:
        string = "%s\t%s\n" % ( sbj, dSbj2Cat[ sbj ] )
        catFile.write( string )
    catFile.close()

#----------------------------------------------------------------------------

def writeQueryCategory( dQry2Cat ):
    """
    Save the category (CC/CI/IC/II/NA) in which each query has been found.

    @param dQry2Cat: dictionary which keys are query names and values the category of that query
    @type dQry2Cat: dictionary
    """

    # sort the query names in alphabetical order
    lQrySorted = dQry2Cat.keys()
    lQrySorted.sort()

    catFile = open( tabFileName + "_qryCategories.txt", "w" )
    for qry in lQrySorted:
        string = "%s\t%s\n" % ( qry, dQry2Cat[ qry ] )
        catFile.write( string )
    catFile.close()
    
#----------------------------------------------------------------------------

def main():

    global tabFileName
    tabFileName = ""
    qryFileName = ""
    sbjFileName = ""
    global thresholdCoverage
    thresholdCoverage = 95
    minIdentity = 0
    minLength = 0
    minOverlap = 0
    global thresholdIdentity
    thresholdIdentity = 90
    global thresholdEvalue
    thresholdEvalue = 1e-10
    global thresholdCoverageMatch
    thresholdCoverageMatch = 90
    global verbose
    verbose = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hm:q:s:t:i:l:I:E:T:o:v:")
    except getopt.GetoptError, err:
        print str(err); help(); sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-m":
            tabFileName = a
        elif o == "-q":
            qryFileName = a
        elif o == "-s":
            sbjFileName = a
        elif o == "-t":
            thresholdCoverage = int(a)
        elif o == "-i":
            minIdentity = float(a)
        elif o == "-l":
            minLength = int(a)
        elif o == "-o":
            minOverlap = float(a)
        elif o == "-I":
            thresholdIdentity = int(a)
        elif o == "-E":
            thresholdEvalue = float(a)
        elif o == "-T":
            thresholdCoverageMatch = int(a)
        elif o == "-v":
            verbose = int(a)

    if tabFileName == "":
        msg = "ERROR: missing 'tab' file (-m)"
        sys.stderr.write( "%s\n" % msg )
        help()
        sys.exit(1)
    if qryFileName == "" or sbjFileName == "":
        msg = "ERROR: missing 'fasta' files (-q or -s)"
        sys.stderr.write( "%s\n" % msg )
        help()
        sys.exit(1)

    if verbose > 0:
        print "START %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    # 4 categories of matchs:
    # type 1 (CC): the length of the match on the subject is >= 95% of the total length of the subject, idem for the query
    # type 2 (CI): sbj >= 95% & qry < 95%
    # type 3 (IC): sbj < 95% & qry >= 95%
    # type 4 (II): sbj & qry < 95%
    ListMatches_all = []
    ListMatches_sup_sbjqry = []
    ListMatches_sup_sbj = []
    ListMatches_sup_qry = []
    ListMatches_inf_sbjqry = []

    qryDB = pyRepet.seq.BioseqDB.BioseqDB( qryFileName )
    nbQry = qryDB.getSize()
    if verbose > 0:
        print "nb of queries in '%s': %i" % ( qryFileName, nbQry )
    dQry2Cat = {}
    for bs in qryDB.db:
        dQry2Cat[ bs.header.split(" ")[0].lower() ] = "NA"

    sbjDB = pyRepet.seq.BioseqDB.BioseqDB( sbjFileName )
    nbSbj = sbjDB.getSize()
    if verbose > 0:
        print "nb of subjects in '%s': %i" % ( sbjFileName, nbSbj )
    dSbj2Cat = {}
    for bs in sbjDB.db:
        dSbj2Cat[ bs.header.split(" ")[0].lower() ] = "NA"

    tabFile = open( tabFileName )
    nbMatchesInTab = 0
    dSubject2DistinctQueries = {}
    dQuery2DistinctSubjects = {}

    # For each match, create a 'tabFileReader' object and record it in a list according to the type of the match
    if verbose > 0:
        print "parse the 'tab' file..."; sys.stdout.flush()
    while True:
        line = tabFile.readline()
        if line == "":
            break
        if line[0:10] == "query.name":
            continue
        nbMatchesInTab += 1

        match = tabFileReader( line )
        if match.identity < minIdentity:
            line = tabFile.readline()
            continue
        if match.length_match < minLength:
            line = tabFile.readline()
            continue
        if match.prct_qry < minOverlap or match.prct_sbj < minOverlap:
            line = tabFile.readline()
            continue
        ListMatches_all.append( match )

        # type 1: sbj C & qry C
        if match.prct_sbj >= thresholdCoverage and match.prct_qry >= thresholdCoverage:
            qsLengthRatio = 100 * match.length_qry / float(match.length_sbj)
            if match.identity >= thresholdIdentity \
            and match.evalue <= thresholdEvalue \
            and qsLengthRatio >= thresholdCoverage - 2 \
            and qsLengthRatio <= 100 + (100-thresholdCoverage) + 2 \
            and match.prct_matchQryOverSbj >= thresholdCoverageMatch:
                ListMatches_sup_sbjqry.append( match )
            else:
                ListMatches_inf_sbjqry.append( match )

        # type 2: sbj C & qry I
        elif match.prct_sbj >= thresholdCoverage and match.prct_qry < thresholdCoverage:
            ListMatches_sup_sbj.append( match )

        # type 3: sbj I & qry C
        elif match.prct_qry >= thresholdCoverage and match.prct_sbj < thresholdCoverage:
            ListMatches_sup_qry.append( match )

        # type 4: sbj I & qry I
        elif match.prct_qry < thresholdCoverage and match.prct_sbj < thresholdCoverage:
            ListMatches_inf_sbjqry.append( match )

        if not dSubject2DistinctQueries.has_key( match.name_sbj ):
            dSubject2DistinctQueries[ match.name_sbj ] = []
        if not match.name_qry in dSubject2DistinctQueries[ match.name_sbj ]:
            dSubject2DistinctQueries[ match.name_sbj ].append( match.name_qry )
        if not dQuery2DistinctSubjects.has_key( match.name_qry ):
            dQuery2DistinctSubjects[ match.name_qry ] = []
        if not match.name_sbj in dQuery2DistinctSubjects[ match.name_qry ]:
            dQuery2DistinctSubjects[ match.name_qry ].append( match.name_sbj )

    if verbose > 0:
        print "parsing done !"; sys.stdout.flush()
        print "nb matches in '%s': %i" % ( tabFileName, nbMatchesInTab )
        print "nb matches 'CC': %i" % ( len(ListMatches_sup_sbjqry) )
        if verbose > 1:
            for match in ListMatches_sup_sbjqry:
                print "\t%s (%.2f%%) - %s (%.2f%%) id=%.2f" % ( match.name_sbj, match.prct_sbj, match.name_qry, match.prct_qry, match.identity )
        print "nb matches 'CI': %i" % ( len(ListMatches_sup_sbj) )
        if verbose > 1:
            for match in ListMatches_sup_sbj:
                print "\t%s (%.2f%%) - %s (%.2f%%) id=%.2f" % ( match.name_sbj, match.prct_sbj, match.name_qry, match.prct_qry, match.identity )
        print "nb matches 'IC': %i" % ( len(ListMatches_sup_qry) )
        print "nb matches 'II': %i" % ( len(ListMatches_inf_sbjqry) )

    if nbMatchesInTab == 0:
        print "nothing to do"
        sys.exit(0)

    # For each type of matchs, record them in 2 dictionaries: Sbj2Qry and Qry2Sbj
    D_all = make_dico( ListMatches_all )
    Sbj2Qry_all = D_all[0]
    Qry2Sbj_all = D_all[1]

    D_sup_sbjqry = make_dico(ListMatches_sup_sbjqry)
    Sbj2Qry_sup_sbjqry = D_sup_sbjqry[0]
    Qry2Sbj_sup_sbjqry = D_sup_sbjqry[1]

    D_sup_sbj = make_dico(ListMatches_sup_sbj)
    Sbj2Qry_sup_sbj = D_sup_sbj[0]
    Qry2Sbj_sup_sbj = D_sup_sbj[1]

    D_sup_qry = make_dico(ListMatches_sup_qry)
    Sbj2Qry_sup_qry = D_sup_qry[0]
    Qry2Sbj_sup_qry = D_sup_qry[1]

    D_inf_sbjqry = make_dico(ListMatches_inf_sbjqry)
    Sbj2Qry_inf_sbjqry = D_inf_sbjqry[0]
    Qry2Sbj_inf_sbjqry = D_inf_sbjqry[1]


    # For each type of matches, find the subjects/queries that are involve in one or several match
    list_all = find_UniqRedun(ListMatches_all)
    UniqSbj_all = list_all[0]
    RedunSbj_all = list_all[1]
    UniqQry_all = list_all[2]
    RedunQry_all = list_all[3]

    list1 = find_UniqRedun(ListMatches_sup_sbjqry)
    UniqSbj_sup_sbjqry = list1[0]
    RedunSbj_sup_sbjqry = list1[1]
    UniqQry_sup_sbjqry = list1[2]
    RedunQry_sup_sbjqry = list1[3]

    list2 = find_UniqRedun(ListMatches_sup_sbj)
    UniqSbj_sup_sbj = list2[0]
    RedunSbj_sup_sbj = list2[1]
    UniqQry_sup_sbj = list2[2]
    RedunQry_sup_sbj = list2[3]
    
    list3 = find_UniqRedun(ListMatches_sup_qry)
    UniqSbj_sup_qry = list3[0]
    RedunSbj_sup_qry = list3[1]
    UniqQry_sup_qry = list3[2]
    RedunQry_sup_qry = list3[3]
    
    list4 = find_UniqRedun(ListMatches_inf_sbjqry)
    UniqSbj_inf_sbjqry = list4[0]
    RedunSbj_inf_sbjqry = list4[1]
    UniqQry_inf_sbjqry = list4[2]
    RedunQry_inf_sbjqry = list4[3]
    
    iStatSbj = pyRepet.util.Stat.Stat()
    for subject in dSubject2DistinctQueries.keys():
        iStatSbj.add( len( dSubject2DistinctQueries[ subject ] ) )
    iStatQry = pyRepet.util.Stat.Stat()
    for query in dQuery2DistinctSubjects.keys():
        iStatQry.add( len( dQuery2DistinctSubjects[ query ] ) )


    # Write the review of the '.tab' file
    outFile = open( tabFileName + "_tabFileReader.txt", "w" )
    outFile.write( "Input: %s\n" % ( tabFileName ) )

    outFile.write( "\n# Number of subjects in '%s': %i\n" % ( sbjFileName, nbSbj ) )
    outFile.write( "# Number of queries in '%s': %i\n" % ( qryFileName, nbQry ) )

    outFile.write( "\nNumber of matches: %s\n" % (len(ListMatches_all)))
    outFile.write( "    # Number of different subjects that match: %s (Sn*=%.2f%%)\n" % ( len(Sbj2Qry_all.keys()), 100 * len(Sbj2Qry_all.keys()) / float(nbSbj) ) )
    outFile.write( "        Among them, number of different subjects having exactly one match: %s (%.2f%%)\n" % ( len(UniqSbj_all), 100 * len(UniqSbj_all) / float(len(Sbj2Qry_all.keys())) ) )
    outFile.write( "        Among them, number of different subjects having more than one match: %s\n" % (len(RedunSbj_all)))
    outFile.write( "        Different queries per subject: mean=%.2f sd=%.2f min=%.2f q25=%.2f med=%.2f q75=%.2f max=%.2f\n" % ( iStatSbj.mean(), iStatSbj.sd(), iStatSbj.min, iStatSbj.quantile(0.25), iStatSbj.median(), iStatSbj.quantile(0.75), iStatSbj.max ) )
    outFile.write( "    # Number of different queries that match: %s (Sp*=%.2f%%)\n" % ( len(Qry2Sbj_all.keys()), 100 * len(Qry2Sbj_all.keys()) / float(nbQry) ) )
    outFile.write( "        Among them, number of different queries having exactly one match: %s (%.2f%%)\n" % ( len(UniqQry_all), 100 * len(UniqQry_all) / float(len(Qry2Sbj_all.keys())) ) )
    outFile.write( "        Among them, number of different queries having more than one match: %s\n" % (len(RedunQry_all)) )
    outFile.write( "        Different subjects per query: mean=%.2f sd=%.2f min=%.2f q25=%.2f med=%.2f q75=%.2f max=%.2f\n" % ( iStatQry.mean(), iStatQry.sd(), iStatQry.min, iStatQry.quantile(0.25), iStatQry.median(), iStatQry.quantile(0.75), iStatQry.max ) )

    outFile.write( "\nNumber of matches with L >= %i%% for subject & query: %i\n" % ( thresholdCoverage, len(ListMatches_sup_sbjqry) ) )
    outFile.write( "    # Number of different subjects in the 'CC' case: %s (%.2f%%)\n" % ( len(Sbj2Qry_sup_sbjqry), 100 *  len(Sbj2Qry_sup_sbjqry) / float(nbSbj) ) )
    outFile.write( "        Among them, number of different subjects having exactly one match: %s\n" % (len(UniqSbj_sup_sbjqry)))
    outFile.write( "        Among them, number of different subjects having more than one match: %s\n" % (len(RedunSbj_sup_sbjqry)))
    outFile.write( "    # Number of different queries in the 'CC' case: %s (%.2f%%)\n" % ( len(Qry2Sbj_sup_sbjqry), 100 * len(Qry2Sbj_sup_sbjqry) / float(nbQry) ) )
    outFile.write( "        Among them, number of different queries having exactly one match: %s\n" % (len(UniqQry_sup_sbjqry)))
    outFile.write( "        Among them, number of different queries having more than one match: %s\n" % (len(RedunQry_sup_sbjqry)))

    outFile.write( "\nNumber of matches with L >= %i%% for subject and L < %i%% for query: %i\n" % ( thresholdCoverage, thresholdCoverage, len(ListMatches_sup_sbj) ) )
    outFile.write( "    Number of different subjects in that case: %s\n" % (len(Sbj2Qry_sup_sbj)))
    outFile.write( "        Among them, number of different subjects having exactly one match: %s\n" % (len(UniqSbj_sup_sbj)))
    outFile.write( "        Among them, number of different subjects having more than one match: %s\n" % (len(RedunSbj_sup_sbj)))
    outFile.write( "    Number of different queries in that case: %s\n" % (len(Qry2Sbj_sup_sbj)))
    outFile.write( "        Among them, number of different queries having exactly one match: %s\n" % (len(UniqQry_sup_sbj)))
    outFile.write( "        Among them, number of different queries having more than one match: %s\n" % (len(RedunQry_sup_sbj)))

    outFile.write( "\nNumber of matches with L < %i%% for subject and L >= %i%% for query: %i\n" % ( thresholdCoverage, thresholdCoverage, len(ListMatches_sup_qry) ) )
    outFile.write( "    Number of different subjects in that case: %s\n" % (len(Sbj2Qry_sup_qry)))
    outFile.write( "        Among them, number of different subjects having exactly one match: %s\n" % (len(UniqSbj_sup_qry)))
    outFile.write( "        Among them, number of different subjects having more than one match: %s\n" % (len(RedunSbj_sup_qry)))
    outFile.write( "    Number of different queries in that case: %s\n" % (len(Qry2Sbj_sup_qry)))
    outFile.write( "        Among them, number of different queries having exactly one match: %s\n" % (len(UniqQry_sup_qry)))
    outFile.write( "        Among them, number of different queries having more than one match: %s\n" % (len(RedunQry_sup_qry)))

    outFile.write( "\nNumber of matches with L < %i%% for subject & query: %i\n" % ( thresholdCoverage, len(ListMatches_inf_sbjqry) ) )
    outFile.write( "    Number of different subjects in that case: %s\n" % (len(Sbj2Qry_inf_sbjqry)))
    outFile.write( "        Among them, number of different subjects having exactly one match: %s\n" % (len(UniqSbj_inf_sbjqry)))
    outFile.write( "        Among them, number of different subjects having more than one match: %s\n" % (len(RedunSbj_inf_sbjqry)))
    outFile.write( "    Number of different queries in that case: %s\n" % (len(Qry2Sbj_inf_sbjqry)))
    outFile.write( "        Among them, number of different queries having exactly one match: %s\n" % (len(UniqQry_inf_sbjqry)))
    outFile.write( "        Among them, number of different queries having more than one match: %s\n" % (len(RedunQry_inf_sbjqry)))
    
    
    # For the elements already counted in the matches with L >= 95% for subject & query, remove them from the other dictionnaries
    rmv_Sbj2Qry = remove( Sbj2Qry_all, Sbj2Qry_sup_sbjqry, Sbj2Qry_sup_sbj, Sbj2Qry_sup_qry, Sbj2Qry_inf_sbjqry )
    rmv_Qry2Sbj = remove( Qry2Sbj_all, Qry2Sbj_sup_sbjqry, Qry2Sbj_sup_sbj, Qry2Sbj_sup_qry, Qry2Sbj_inf_sbjqry )
    
    outFile.write("\n\nAfter removal of the subjects/queries already counted in the matches with L >= %i%% for them:\n" % ( thresholdCoverage ) )
    
    outFile.write( "\nMatches with L >= %i%% for subject and L < %i%% for query:\n" % ( thresholdCoverage, thresholdCoverage ) )
    outFile.write( "    # Number of different subjects in the 'CI' case: %s (%.2f%%)\n" % ( len(rmv_Sbj2Qry[0]), 100*len(rmv_Sbj2Qry[0])/float(nbSbj) ) )
    outFile.write( "    # Number of different queries in the 'CI' case: %s (%.2f%%)\n" % ( len(rmv_Qry2Sbj[0]), 100*len(rmv_Qry2Sbj[0])/float(nbQry) ) )
    
    outFile.write( "\nMatches with L < %i%% for subject and L >= %i%% for query:\n" % ( thresholdCoverage, thresholdCoverage ) )
    outFile.write( "    # Number of different subjects in the 'IC' case: %s (%.2f%%)\n" % (len(rmv_Sbj2Qry[1]), 100*len(rmv_Sbj2Qry[1])/float(nbSbj) ) )
    outFile.write( "    # Number of different queries in the 'IC' case: %s (%.2f%%)\n" % (len(rmv_Qry2Sbj[1]), 100*len(rmv_Qry2Sbj[1])/float(nbQry) ) )
    
    outFile.write( "\nMatches with L < %i%% for subject & query:\n" % ( thresholdCoverage ) )
    outFile.write( "    # Number of different subjects in the 'II' case: %s (%.2f%%)\n" % (len(rmv_Sbj2Qry[2]), 100*len(rmv_Sbj2Qry[2])/float(nbSbj) ) )
    outFile.write( "    # Number of different queries in the 'II' case: %s (%.2f%%)\n" % (len(rmv_Qry2Sbj[2]), 100*len(rmv_Qry2Sbj[2])/float(nbQry) ) )
    
    outFile.write("\n==========================================================================\n")
    
    write_output( outFile, 'CC', Sbj2Qry_sup_sbjqry, dSbj2Cat, Qry2Sbj_sup_sbjqry, dQry2Cat )
    
    outFile.write("\n==========================================================================\n")
    
    write_output( outFile, 'CI', rmv_Sbj2Qry[0], dSbj2Cat, rmv_Qry2Sbj[0], dQry2Cat )
    
    outFile.write("\n==========================================================================\n")
    
    write_output( outFile, 'IC', rmv_Sbj2Qry[1], dSbj2Cat, rmv_Qry2Sbj[1], dQry2Cat )
    
    outFile.write("\n==========================================================================\n")
    
    write_output( outFile, 'II', rmv_Sbj2Qry[2], dSbj2Cat, rmv_Qry2Sbj[2], dQry2Cat )
    
    outFile.write("\n==========================================================================\n")
    
    outFile.close()
    
    writeSubjectCategory( dSbj2Cat )
    writeQueryCategory( dQry2Cat )
    
    if verbose > 0:
        print "END %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()
        
    return 0

#-----------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
