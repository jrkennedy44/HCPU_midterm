#!/usr/bin/env python

##@file
# Detect TE features on sequences, classify them and remove redundancy.
#
# usage: TEclassifier.py [ options ]
# options:
#      -h: this help
#      -p: project name (<=15 characters, only alphanumeric or underscore)"
#      -c: configuration file
#      -i: input file name (format=fasta)
#      -s: step (1 to detect features; 2 to classify)
#      -v: verbose (default=0/1/2)


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
import getopt
import string
import ConfigParser
import glob
import logging
import re
import shutil

if not os.environ.has_key( "REPET_PATH" ):
    print "ERROR: no environment variable REPET_PATH"
    sys.exit(1)
sys.path.append( os.environ["REPET_PATH"] )

from pyRepetUnit.commons.LoggerFactory import LoggerFactory
from pyRepetUnit.commons.checker.CheckerUtils import CheckerUtils
from pyRepetUnit.commons.checker.CheckerException import CheckerException
from ConfigParser import NoOptionError

from pyRepetUnit.commons.sql.DbMySql import DbMySql
from pyRepetUnit.commons.sql.TablePathAdaptator import TablePathAdaptator
from pyRepetUnit.commons.sql.TableMatchAdaptator import TableMatchAdaptator
from pyRepetUnit.commons.sql.TableSetAdaptator import TableSetAdaptator
from pyRepetUnit.commons.sql.TableMapAdaptator import TableMapAdaptator
from pyRepetUnit.commons.sql.TableSeqAdaptator import TableSeqAdaptator

from pyRepetUnit.commons.seq.BioseqDB import BioseqDB
from pyRepetUnit.commons.seq.FastaUtils import FastaUtils
from pyRepetUnit.commons.utils.FileUtils import FileUtils
from pyRepetUnit.commons.coord.SetUtils import SetUtils
from pyRepetUnit.commons.coord.Match import Match
from pyRepetUnit.hmmer.profilsSearchInTEClassifier.ProfilesSearch import ProfilesSearch

from pyRepet.launcher.programLauncher import programLauncher
from pyRepetUnit.commons.launcher.Launcher import Launcher
from pyRepetUnit.commons.sql.RepetJob import RepetJob

#------------------------------------------------------------------------------

def help():
    """
    Give the list of the command-line options.
    """
    print
    print "usage: %s [ options ]" % ( sys.argv[0].split("/")[-1] )
    print "options:"
    print "     -h: this help"
    print "     -p: project name (<=15 characters, only alphanumeric or underscore)"
    print "     -c: configuration file"
    print "     -i: name of the input file (format='fasta')"
    print "     -s: step (1 to detect features; 2 to classify)"
    print "     -n: use hmmer3 (default is hmmer2)"
    print "     -v: verbose (default=0/1/2/3)"
    print

#------------------------------------------------------------------------------

def setup_env( config ):
    """
    Setup the required environment (variables, libraries).
    @param config: configuration file
    @type config: file handling
    """
    os.environ["REPET_HOST"] = config.get("repet_env","repet_host")
    os.environ["REPET_USER"] = config.get("repet_env","repet_user")
    os.environ["REPET_PW"] = config.get("repet_env","repet_pw")
    os.environ["REPET_DB"] = config.get("repet_env","repet_db")
    os.environ["REPET_PORT"] = config.get("repet_env","repet_port")

#------------------------------------------------------------------------------

class Consensus:
    """
    This class allows to classify a consensus obtained via the TEdenovo pipeline.
    """

    order2class = {}
    for k in ["LTR","LARD","LINE","SINE"]:
        order2class[k] = "classI"
    for k in ["TIR","MITE","Helitron","Polinton"]:
        order2class[k] = "classII"

    structfeat2order = {}
    structfeat2order["LTR"] = "LTR"
    structfeat2order["TIR"] = "TIR"
    structfeat2order["polyA_tail"] = "LINE"
    structfeat2order["SSR_tail"] = "LINE"

    #--------------------------------------------------------------------------

    def __init__( self, n, l, c ):
        """
        @param n: name of the consensus
        @type n: string
        @param l: length of the consensus
        @type l: integer
        @param c: configuration file
        @type c: file handling
        """

        self.project = project

        self.name = n
        self.length = int(l)
        self.strand = "?"

        header = n.split("_")
        self.nb_align = header[ len(header)-1 ]

        # record the parameters from the configuration file
        # tables, max/min length
        self.param = c

        # record the features
        # possible keys: LTR, TIR, polyA_tail, SSR_tail, TE_BLRtx, TE_BLRx, HG_BLRn
        self.features = {}
        self.bestMatch = {}
        self.bestMatch[ "TE_BLRtx" ] = None
        self.bestMatch[ "TE_BLRx" ] = None
        self.bestMatch[ "HG_BLRn" ] = None
        self.bestMatch[ "TE_BLRn" ] = None

        # record the classification
        # category (class I;class II;SSR;HostGene;confused;NoCat), order (only for the TEs), completeness (comp;incomp) and comments
        self.classif = {}
        self.classif["structFeat"] = None
        self.classif["codingFeat"] = None
        self.classif["final"] = None
        self.confused = None

    #--------------------------------------------------------------------------

    def search_TR( self ):
        """
        Retrieve the terminal repeats (TIR or LTR) of the sequence (if any).
        """

        if not db.doesTableExist( self.project + "_TR_set" ):
            return
        
        if verbose > 2:
            print "search terminal repeats..."; sys.stdout.flush()

        tr_set = TableSetAdaptator( db, self.project + "_TR_set" )
        list_set = tr_set.getSetListFromSeqName( self.name )
        dPath2TermTIR = {}
        dPath2TermLTR = {}
        list_tir = []
        list_ltr = []
        maxLength_TIR = 0
        maxLength_LTR = 0

        # size up to which a TIR is still considered as a terminal TIR
        threshold_termTIR = 10

        # size up to which a LTR is still considered as a terminal LTR
        threshold_termLTR = 20

        # for each sequence detected by TRsearch
        for i_set in list_set:
            i_tr = TR( i_set )
            if verbose > 3:
                i_tr.view()

            # select the terminal TIRs (if any) 
            if "TIR" in i_set.name:
                minTIR = min( i_tr.start, i_tr.end )
                maxTIR = max( i_tr.start, i_tr.end )
                if minTIR <= threshold_termTIR or maxTIR >= self.length - threshold_termTIR:
                    if dPath2TermTIR.has_key( i_tr.id ):
                        dPath2TermTIR[ i_tr.id ].append( i_tr )
                    else:
                        dPath2TermTIR[ i_tr.id ] = [ i_tr ]

            # select the terminal LTRs (if any)
            elif "LTR" in i_set.name:
                minLTR = min( i_tr.start, i_tr.end )
                maxLTR = max( i_tr.start, i_tr.end )
                if minLTR <= threshold_termLTR or maxLTR >= self.length - threshold_termLTR:
                    if dPath2TermLTR.has_key( i_tr.id ):
                        dPath2TermLTR[ i_tr.id ].append( i_tr )
                    else:
                        dPath2TermLTR[ i_tr.id ] = [ i_tr ]

        # remove the paths where only one of the TR is terminal
        for p in dPath2TermTIR.keys():
            if len( dPath2TermTIR[ p ] ) < 2:
                del dPath2TermTIR[ p ]
        for p in dPath2TermLTR.keys():
            if len( dPath2TermLTR[ p ] ) < 2:
                del dPath2TermLTR[ p ]

        # select the longest TR
        for p in dPath2TermTIR.keys():
            i_tr = dPath2TermTIR[ p ][0]
            if i_tr.getLength() > maxLength_TIR:
                maxLength_TIR = i_tr.getLength()
                list_tir.append( i_tr )
                list_tir.append( dPath2TermTIR[ p ][1] )
        for p in dPath2TermLTR.keys():
            i_tr = dPath2TermLTR[ p ][0]
            if i_tr.getLength() > maxLength_LTR:
                maxLength_LTR = i_tr.getLength()
                list_ltr.append( i_tr )
                list_ltr.append( dPath2TermLTR[ p ][1] )

        # if the sequence has only TIRs
        if len(list_tir) != 0 and len(list_ltr) == 0:
            if verbose > 2:
                print "TIR feature"
            self.features["TIR"] = list_tir

        # if the sequence has only LTRs
        elif len(list_tir) == 0 and len(list_ltr) != 0:
            if verbose > 2:
                print "LTR feature"
            self.features["LTR"] = list_ltr

        # if the sequence has TIRs and LTRs, keep the LTRs
        elif len(list_tir) != 0 and len(list_ltr) != 0:
            if verbose > 2:
                print "LTR and TIR, keep LTR feature"
            self.features["LTR"] = list_ltr
            
        else:
            if verbose > 2:
                print "no terminal repeat was found"; sys.stdout.flush()

    #--------------------------------------------------------------------------

    def search_tail( self ):
        """
        Retrieve the polyA or SSR tail (if any).
        """

        if db.doesTableExist( self.project + "_polyA_set" ):
            self.search_tail_polyA()

        if db.doesTableExist( self.project + "_SSRtrf_set" ):
            if self.bestMatch["TE_BLRtx"] != None:
                if self.bestMatch["TE_BLRtx"].sbj_order == "LINE":
                    self.search_tail_ssr()
            elif self.bestMatch["TE_BLRx"] != None:
                if self.bestMatch["TE_BLRx"].sbj_order == "LINE":
                    self.search_tail_ssr()

    #--------------------------------------------------------------------------

    def search_tail_polyA( self ):
        """
        Retrieve the polyA tail (if any).
        """

        if verbose > 2:
            print "search poly-A tail..."; sys.stdout.flush()

        table_polyA_set = TableSetAdaptator( db, self.project + "_polyA_set" )
        list_polyA_set = table_polyA_set.getSetListFromSeqName( self.name )

        nbTails = 0

        for i in list_polyA_set:
            if "term" in i.name and "non-" not in i.name:
                nbTails += 1
                if not self.features.has_key("polyA_tail"):
                    self.features["polyA_tail"]=[i]
                else:
                    self.features["polyA_tail"].append(i)

        if verbose > 2:
            if nbTails == 0:
                print "no tail was found"
            else:
                print "found a tail"
            sys.stdout.flush()

    #--------------------------------------------------------------------------

    def search_tail_ssr( self ):
        """
        Retrieve the SSR tail (if any).
        """
        
        if verbose > 2:
            print "search SSR-like tail..."; sys.stdout.flush()

        table_ssr_set = TableSetAdaptator( db, self.project + "_SSRtrf_set" )
        list_ssr_set = table_ssr_set.getSetListFromSeqName( self.name )

        minLength = 10
        nbTails = 0

        for i in list_ssr_set:
            if abs( int(i.end) - int(i.start) ) + 1 > minLength:
                if i.end > self.length - 5 or i.start < 5:      #msat at the beginning or at the end of the sequence
                    nbTails += 1
                    if not self.features.has_key("SSR_tail"):
                        self.features["SSR_tail"]=[i]
                    else:
                        self.features["SSR_tail"].append(i)

        if verbose > 2:
            if nbTails == 0:
                print "no tail was found"
            else:
                print "found a tail"
            sys.stdout.flush()

    #--------------------------------------------------------------------------

    def search_SSR( self ):
        """
        Retrieve the simple short repeats (if any).
        """
        
        if not db.doesTableExist( self.project + "_SSRtrf_set" ):
            return

        if verbose > 2:
            print "search SSRs..."; sys.stdout.flush()
        table_ssr_set = TableSetAdaptator( db, self.project + "_SSRtrf_set" )
        lSets = table_ssr_set.getSetListFromSeqName(self.name)

        for iSet in lSets:
            if not self.features.has_key("SSR"):
                self.features["SSR"] = [ iSet ]
            else:
                self.features["SSR"].append( iSet )
                
        if verbose > 2:
            if not self.features.has_key("SSR"):
                print "no SSR was found"
            else:
                print "%i SSRs were found" % ( len(self.features["SSR"]) )
            sys.stdout.flush()

    #--------------------------------------------------------------------------

    def search_ORF( self ):
        """
        Retrieve the ORFs of the sequence (if any).
        """
        if not db.doesTableExist( self.project + "_ORF_map" ):
            return
        if verbose > 2:
            print "search ORFs..."; sys.stdout.flush()
        orf_map = TableMapAdaptator( db, self.project + "_ORF_map")
        list_map = orf_map.getMapListFromChr( self.name )
        list_orf = []
        for i in list_map:
            list_orf.append( ORF(i) )
            self.features["ORF"] = list_orf
        if verbose > 2 and len(self.features["ORF"]) > 0:
            print "ORF=%i" % ( len(self.features["ORF"]) )
            
    #--------------------------------------------------------------------------

    def search_TElib( self ):
        """
        Retrieve the matches (if any) between the sequence and TElib via tblastx, blastx and blastn.
        """

        if db.doesTableExist( self.project + "_TE_BLRtx_path" ):
            if verbose > 2:
                print "search results from TE library via tblastx..."; sys.stdout.flush()
            self.search_TElib_BLR( "tx" )

        if db.doesTableExist( self.project + "_TE_BLRx_path" ):
            if verbose > 2:
                print "search results from TE library via blastx..."; sys.stdout.flush()
            self.search_TElib_BLR( "x" )

        if db.doesTableExist( self.project + "_TE_BLRn_path" ):
            if verbose > 2:
                print "search results from TE library via blastn..."; sys.stdout.flush()
            self.search_TElib_BLR( "n" )

    #--------------------------------------------------------------------------

    def search_TElib_BLR( self, blast ):
        """
        Launch search_TElib_matchs().
        @param blast: 'tx' or 'x' or 'n'
        @type blast: string
        """

        if blast == "n":
            tma = TableMatchAdaptator( db, self.project + "_TE_BLR" + blast + "_match" )
            lMatches = tma.getMatchListFromQuery( self.name )
            lPaths = []
            for m in lMatches:
                if m.getLengthPercOnSubject() >= 0.5:
                    lPaths.append( m.getPathInstance() )
        else:
            tpa = TablePathAdaptator( db, self.project + "_TE_BLR" + blast + "_path" )
            lPaths = tpa.getPathListFromQuery( self.name )
        if verbose > 2:
            if len(lPaths) > 0:
                print "BLR%s: %i matches" % ( blast, len(lPaths) ); sys.stdout.flush()
            else:
                print "no match"; sys.stdout.flush()

        # get the two best matches
        [ list_blast, bestMatch1, bestMatch2 ] = self.search_TElib_matchs( lPaths )

        # record them and their strand
        if len( list_blast ) > 0:
            self.features["TE_BLR"+blast] = [ bestMatch1, bestMatch2 ]
            self.findStrandFromMatches( bestMatch1, bestMatch2 )
            self.bestMatch[ "TE_BLR" + blast ] = bestMatch1

    #--------------------------------------------------------------------------

    def search_TElib_matchs( self, list_blast_path ):
        """
        Record the 2 best matches (if any) between the consensus and known sequences from TElib.
        @param list_blast_path: list of all the matches
        @type list_blast_path: list of Path objects
        """

        list_blast = []
        bestMatch1 = ""
        bestMatch2 = ""

        # if there is no match, pass
        if len( list_blast_path ) == 0:
            return [ list_blast, bestMatch1, bestMatch2 ]

        # if there is at least one match
        elif len( list_blast_path ) != 0:

            # for each match, parse it
            for match_path in list_blast_path:
                match_repb = TElib( match_path )
                list_blast.append( match_repb )

            # initialize the match with the highest score
            bestMatch1 = list_blast[0]
            bestMatch2 = list_blast[0]
            max_score1 = list_blast[0].score
            max_score2 = list_blast[0].score

            # for each match
            for match in list_blast:

                # record the 1st best match
                if match.score > max_score1:
                    max_score1 = match.score
                    bestMatch1 = match

                # record the 2nd best match
                elif match.score > max_score2 and match.score < max_score1:
                    max_score2 = match.score
                    bestMatch2 = match

        return [ list_blast, bestMatch1, bestMatch2 ]

    #--------------------------------------------------------------------------

    def findStrandFromMatches( self, bestMatch1, bestMatch2 ):
        """
        Retrieve the strand of the sequence knowing the strand of its two best matches with known sequences.
        """

        if bestMatch1.sbj_strand == "+" and bestMatch2.sbj_strand == "+":
            self.strand = "+"
        elif bestMatch1.sbj_strand == "-" and bestMatch2.sbj_strand == "-":
            self.strand = "-"
        else:
            self.strand = "?"

    #--------------------------------------------------------------------------

    def search_HostGenes( self ):
        """
        Retrieve the matches (if any) between the sequence and host genes via blastn.
        """
        table = "%s_HG_BLRn_match" % ( self.project )
        if not db.doesTableExist( table ):
            return
        if self.param.get("classif_consensus","filter_host_genes") != "yes":
            return
        if verbose > 2:
            print "search results from host's genes via blastn..."; sys.stdout.flush()

        iTable = TableMatchAdaptator( db, table )
        lMatches = iTable.getMatchListFromQuery( self.name )
        if len(lMatches) != 0:
            if verbose > 2:
                if len(lMatches) == 1:
                    print "BLRn: %i match" % ( len(lMatches) )
                else:
                    print "BLRn: %i matches" % ( len(lMatches) )
            bestMatch = lMatches[0]
            maxScore = lMatches[0].score
            for iMatch in lMatches:
                if iMatch.score > maxScore:
                    maxScore = iMatch.score
                    bestMatch = iMatch
            self.features["HG_BLRn"] = [ bestMatch ]
        else:
            if verbose > 2:
                print "no match"

    #--------------------------------------------------------------------------
    
    def search_TEprofiles_OLD( self ):
        
        """
        Retrieve the two best matches (if any) between the sequence and profiles via HMMER.
        """
        
        if not db.doesTableExist( self.project + "_Profiles_path" ):
            return
        
        if verbose > 2:
            print "search results from TE profiles via hmmer..."; sys.stdout.flush()
            
        tableProfiles = TablePathAdaptator( db, self.project + "_Profiles_path" )
        lPaths = tableProfiles.getPathListSortedByIncreasingEvalueFromQuery( self.name )
        
        if len(lPaths) > 0:
            if verbose > 2:
                print "HMMER: %i matches" % ( len(lPaths) ); sys.stdout.flush()
            self.features["TE_HMMER"] = [ lPaths[0] ]
            if len(lPaths) > 1:
                self.features["TE_HMMER"].append( lPaths[1] )
        else:
            if verbose > 2:
                print "no match"; sys.stdout.flush()
                
    #--------------------------------------------------------------------------
    
    def search_TEprofiles( self ):
        """
        Retrieve the best matches (if any) between the sequence and profiles via HMMER, for each kind of profile (INT, Tase, RT...).
        """
        if not db.doesTableExist( self.project + "_Profiles_path" ):
            return
        if verbose > 2:
            print "search results from TE profiles via hmmer..."; sys.stdout.flush()
            
        # retrieve the list of paths
        tableProfiles = TablePathAdaptator( db, self.project + "_Profiles_path" )
        lPaths = tableProfiles.getPathListFromQuery( self.name )
        if len(lPaths) > 0:
            if verbose > 2  and len(lPaths) == 1:
                print "HMMER: 1 match"
            elif verbose > 2  and len(lPaths) > 1:
                print "HMMER: %i matches" % ( len(lPaths) ); sys.stdout.flush()
        else:
            if verbose > 2: print "no match"; sys.stdout.flush()
            return
        
        # gather the paths per type of profile
        threshold = float( config.get("detect_features","TE_HMMER_evalue") )
        dProfileTypes2Paths = {}
        for p in lPaths:
            if p.e_value > threshold:
                continue
            profileType = p.range_subject.seqname.split("_")[-2]
            if not dProfileTypes2Paths.has_key( profileType ):
                dProfileTypes2Paths[ profileType ] = []
            dProfileTypes2Paths[ profileType ].append( p )
        if len( dProfileTypes2Paths.keys() ) == 0:
            if verbose > 2:
                print "no match above threshold (E-value=%g)" % ( threshold )
            return
        
        # keep the best path per type of profile
        self.features["TE_HMMER"] = []
        for profileType in dProfileTypes2Paths.keys():
            if len( dProfileTypes2Paths[ profileType ] ) == 1:
                self.features["TE_HMMER"].append( dProfileTypes2Paths[ profileType ][0] )
                if verbose > 2:
                    print "match: %s (E-value=%g)"  % ( dProfileTypes2Paths[ profileType ][0].range_subject.seqname,
                                                         dProfileTypes2Paths[ profileType ][0].e_value )
            else:
                bestPath = dProfileTypes2Paths[ profileType ][0]
                for p in dProfileTypes2Paths[ profileType ]:
                    if p.e_value < bestPath.e_value:
                        bestPath = p
                self.features["TE_HMMER"].append( bestPath )
                if verbose > 2:
                    print "best match: %s (E-value=%g)"  % ( bestPath.range_subject.seqname,
                                                              bestPath.e_value )
                    
    #--------------------------------------------------------------------------
    
    def search_TEclass( self ):
        """
        Retrieve the ORFs of the sequence (if any).
        """
        if not db.doesTableExist( self.project + "_TEclass_map" ):
            return
        if verbose > 2:
            print "search TEclass results..."; sys.stdout.flush()
        iAdapt = TableMapAdaptator( db, self.project + "_TEclass_map")
        lMaps = iAdapt.getMapListFromChr( self.name )
        if len(lMaps) > 0:
            self.features["TEclass"] = lMaps[0].name
            if verbose > 2:
                print "TEclass=%s" % ( self.features["TEclass"] )
                
    #--------------------------------------------------------------------------

    def search_hRep( self ):
        """
        Retrieves the repeats within the sequence (if any).
        """
        if not db.doesTableExist( self.project + "_hrepeat_set" ):
            return
        hrep_set = TableSetAdaptator( db, self.project + "_hrepeat_set")
        list_set = hrep_set.getSetListFromSeqName(self.name)
        list_hrep = []
        for i in list_set:
            list_hrep.append( hRep(i) )
            self.features["hRep"] = list_hrep

    #--------------------------------------------------------------------------

    def saveFeatures( self, countSetID, setFile ):
        """
        Save the features (terminal repeats, tail, matches, if any) in a set file.
        @param countSetID: current ID in the set file
        @type countSetID: integer
        @param setFile: file with format 'set'
        @type setFile: file handling
        @return: current ID in the set file
        @rtype: integer
        """

        for typeTermRep in ["LTR","TIR"]:
            if self.features.has_key( typeTermRep ):
                string = ""
                countSetID += 1
                for termRep in self.features[ typeTermRep ]:
                    string += "%i\t%s\t%s\t%i\t%i\n" % ( countSetID, typeTermRep, self.name, termRep.start, termRep.end )
                setFile.write( string )

        for typeTail in ["polyA_tail","SSR_tail"]:
            if self.features.has_key( typeTail ):
                string = ""
                for tail in self.features[ typeTail ]:
                    countSetID += 1
                    string += "%i\t%s\t%s\t%i\t%i\n" % ( countSetID, typeTail, tail.seqname, tail.start, tail.end )
                setFile.write( string )

        for typeMatch in ["TE_BLRn","TE_BLRtx","TE_BLRx"]:
            if self.features.has_key( typeMatch ):
                string = ""
                for match in self.features[ typeMatch ]:
                    countSetID += 1
                    string += "%i\t%s_%i-%i-%s\t%s\t%i\t%i\n" % ( countSetID, match.sbj_name, match.sbj_start, match.sbj_end, typeMatch, match.qry_name, match.qry_start, match.qry_end )
                setFile.write( string )
                
        if self.features.has_key( "HG_BLRn" ):
            string = ""
            for iMatch in self.features[ "HG_BLRn" ]:
                countSetID += 1
                string += "%i\t%s_%i-%i-%s\t%s\t%i\t%i\n" % ( countSetID, iMatch.range_subject.seqname, iMatch.range_subject.start, iMatch.range_subject.end, "HG_BLRn", iMatch.range_query.seqname, iMatch.range_query.start, iMatch.range_query.end )
            setFile.write( string )
            
        if self.features.has_key( "TE_HMMER" ):
            string = ""
            for p in self.features["TE_HMMER"]:
                countSetID += 1
                string += "%i\t%s_%i-%i-%s\t%s\t%i\t%i\n" % ( countSetID, p.range_subject.seqname, p.range_subject.start, p.range_subject.end, "TE_HMMER", p.range_query.seqname, p.range_query.start, p.range_query.end )
            setFile.write( string )

        return countSetID

    #--------------------------------------------------------------------------

    def filter_SSR( self ):
        """
        Filter the consensus corresponding to SSRs.
        """

        # if the consensus is too short
        min_length = self.param.getint("classif_consensus","SSR_min_total_length")
        if self.length < min_length:
            category = "SSR"
            order = "NA"
            superfam = "NA"
            comments = "length < %i bp" % ( min_length )
            completeness = "NA"
            self.classif["final"] = Classif( category, order, superfam, comments, completeness )
            self.confused = False
            if verbose > 2:
                print "classified as SSR (%i<%ibp)" % ( self.length, min_length )
                sys.stdout.flush()


        if self.classif["final"] == None:

            # if the consensus contains some SSR
            if self.features.has_key("SSR"):
                # calculate the coverage
                lMergedSets = SetUtils.mergeSetsInList( self.features["SSR"] )
                ssr_cumul = SetUtils.getCumulLength( lMergedSets )

                # if the coverage is too high
                ssr_coverage = ssr_cumul / float(self.length)
                max_coverage = float(self.param.get("classif_consensus","SSR_max_coverage"))
                if verbose > 2:
                    print "SSR coverage: %.2f" % ( ssr_coverage )
                    sys.stdout.flush()
                if ssr_coverage >= max_coverage:
                    category = "SSR"
                    order = "NA"
                    superfam = "NA"
                    comments = "SSRs=(coverage=%.2f>%.2f)" % ( ssr_coverage, max_coverage )
                    completeness = "NA"
                    self.classif["final"] = Classif( category, order, superfam, comments, completeness )
                    self.confused = False

                else:
                    # if the consensus only contains some SSR
                    if (len(self.features.keys()) == 1) or ( len(self.features.keys()) == 2 and self.features.has_key("ORF") ):
                        category = "NoCat"
                        order = "?"
                        superfam = "?"
                        comments = "SSRs=(coverage=%.2f<%.2f)" % ( ssr_coverage, max_coverage )
                        completeness = "?"
                        self.classif["final"] = Classif( category, order, superfam, comments, completeness )
                        self.confused = False


        if self.classif["final"] == None:

            # if the consensus has a SSR tail
            if self.features.has_key("SSR_tail"):

                # if it has also LTR
                if self.features.has_key("LTR"):
                    del_ssr = 0
                    length_ltr = self.features["LTR"][0].end - self.features["LTR"][0].start
                    for i in self.features["SSR_tail"]:
                        if (i.end - i.start + 1) < length_ltr:
                            del_ssr = 1

                    # if the LTR is bigger than the SSR tail
                    if del_ssr == 1:
                        del self.features["SSR_tail"]

                    # if the LTR is included in the SSR tail
                    else:
                        category = "?"
                        order = "?"
                        superfam = "?"
                        comments = "LTR within a SSR"
                        completeness = "?"
                        self.classif["final"] = Classif( category, order, superfam, comments, completeness )
                        self.confused = True

                # if it has also TIR
                elif self.features.has_key("TIR"):
                    del_ssr = 0
                    length_tir = self.features["TIR"][0].end - self.features["TIR"][0].start
                    for i in self.features["SSR_tail"]:
                        if (i.end - i.start + 1) < length_tir:
                            del_ssr = 1

                    # if the TIR is bigger than the SSR tail
                    if del_ssr == 1:
                        del self.features["SSR_tail"]

                    # if the TIR is included in the SSR tail
                    else:
                        category = "?"
                        order = "?"
                        superfam = "?"
                        comments = "TIR within a SSR"
                        completeness = "?"
                        self.classif["final"] = Classif( category, order, superfam, comments, completeness )
                        self.confused = True

                # if it has also a polyA tail
                elif self.features.has_key("polyA_tail"):
                    del self.features["SSR_tail"]

                # if it has also some SSR
                elif self.features.has_key("SSR"):
                    del self.features["SSR"]
                    
        if self.classif["final"] != None:
            if self.features.has_key( "TE_BLRtx" ):
                comments += ";%s" % ( self.getCommentsAboutTeBlastAsString( "TE_BLRtx" ) )
            if self.features.has_key( "TE_BLRx" ):
                comments += ";%s" % ( self.getCommentsAboutTeBlastAsString( "TE_BLRx" ) )
            if self.features.has_key( "TE_BLRn" ):
                comments += ";%s" % ( self.getCommentsAboutTeBlastAsString( "TE_BLRn" ) )
            if self.features.has_key( "TE_HMMER" ):
                comments += ";%s" % ( self.getCommentsAboutProfilesAsString() )
                
    #--------------------------------------------------------------------------

    def filter_HostGenes( self ):
        """
        Filter the consensus matching with host gene(s) depending on the identity and coverage of the matches.
        """
        
        if self.classif["final"] == None and self.features.has_key("HG_BLRn"):
            iMatch = self.features["HG_BLRn"][0]
            sbjName = iMatch.range_subject.seqname
            matchId = iMatch.identity
            qryCoverage = iMatch.getLengthPercOnQuery()
            
            minIdentity = self.param.getfloat("classif_consensus","host_genes_threshold_identity")
            minCoverage = self.param.getfloat("classif_consensus","host_genes_threshold_coverage")
            if matchId >= 100 * minIdentity and qryCoverage >= minCoverage:
                category = "HostGene"
                order = "NA"
                superfam = "NA"
                comments = "match=(%s;%s;id=%.2f;cov=%.2f)" % ( "HG_BLRn", sbjName, matchId, qryCoverage )
                completeness = "NA"
                self.classif["final"] = Classif( category, order, superfam, comments, completeness )
                self.confused = False
                
    #--------------------------------------------------------------------------

    def classify( self ):
        """
        Classify the sequence according to its features.
        """

        # check if the sequence has been classified previously (as SSR or host gene)
        if self.classif["final"] != None:
            return


        # if the sequence has at least one feature
        if len( self.features.keys() ) > 0:


            # if the sequence has at least 2 structural features (among LTR, TIR, polyA tail and SSR tail)
            if self.features.has_key("LTR") \
                   and ( self.features.has_key("TIR") \
                         or self.features.has_key("polyA_tail") \
                         or self.features.has_key("SSR_tail") ):
                category = "?"
                order = "?"
                superfam = "?"
                comments = "contradictory structural features:LTR"
                if self.features.has_key("TIR"):
                    comments += "-TIR"
                if self.features.has_key("polyA_tail"):
                    comments += "-polyA_tail"
                if self.features.has_key("SSR_tail"):
                    comments += "-SSR_tail"
                if self.features.has_key( "TE_HMMER" ):
                    comments += ";%s" % ( self.getCommentsAboutProfilesAsString() )
                if self.features.has_key( "TE_BLRn" ):
                    comments += ";%s" % ( self.getCommentsAboutTeBlastAsString( "TE_BLRn" ) )
                if self.features.has_key("TEclass"):
                    comments += " TEclass=%s" % ( self.features["TEclass"] )
                completeness = "?"
                self.classif["final"] = Classif( category, order, superfam, comments, completeness )
                self.confused = True
                
            elif self.features.has_key("TIR") and ( self.features.has_key("polyA_tail") or self.features.has_key("SSR_tail") ):
                category = "?"
                order = "?"
                superfam = "?"
                comments = "contradictory structural features:TIR"
                if self.features.has_key("polyA_tail"):
                    comments += "-polyA_tail"
                if self.features.has_key("SSR_tail"):
                    comments += "-SSR_tail"
                if self.features.has_key( "TE_HMMER" ):
                    comments += ";%s" % ( self.getCommentsAboutProfilesAsString() )
                if self.features.has_key( "TE_BLRn" ):
                    comments += ";%s" % ( self.getCommentsAboutTeBlastAsString( "TE_BLRn" ) )
                if self.features.has_key("TEclass"):
                    comments += ";TEclass=%s" % ( self.features["TEclass"] )
                completeness = "?"
                self.classif["final"] = Classif( category, order, superfam, comments, completeness )
                self.confused = True
                
            elif self.features.has_key("polyA_tail") and self.features.has_key("SSR_tail"):
                category = "?"
                order = "?"
                superfam = "?"
                comments = "contradictory structural features:polyA_tail-SSR_tail"
                if self.features.has_key( "TE_HMMER" ):
                    comments += ";%s" % ( self.getCommentsAboutProfilesAsString() )
                if self.features.has_key( "TE_BLRn" ):
                    comments += ";%s" % ( self.getCommentsAboutTeBlastAsString( "TE_BLRn" ) )
                if self.features.has_key("TEclass"):
                    comments += ";TEclass=%s" % ( self.features["TEclass"] )
                completeness = "?"
                self.classif["final"] = Classif( category, order, superfam, comments, completeness )
                self.confused = True
                
                
            # if the sequence has no structural features
            elif "LTR" not in self.features.keys() and "TIR" not in self.features.keys() \
                     and "polyA_tail" not in self.features.keys() and "SSR_tail" not in self.features.keys():
                
                # if it has coding feature(s) (i.e. matches with known TEs via tblastx and/or blastx)
                if self.features.has_key( "TE_BLRtx" ) or self.features.has_key( "TE_BLRx" ):
                    self.classifPartialFromCodingFeatures()
                    self.classifShortCopiesWithoutStructFeat()
                    if self.classif["final"] == None:
                        self.classifFinalWithOnlyOneKindOfFeatures( "coding" )
                        if self.features.has_key( "TE_HMMER" ):
                            self.classif["final"].comments += ";%s" % ( self.getCommentsAboutProfilesAsString() )
                        if self.features.has_key( "TE_BLRn" ):
                            self.classif["final"].comments += ";%s" % ( self.getCommentsAboutTeBlastAsString( "TE_BLRn" ) )
                        if self.features.has_key("TEclass"):
                            self.classif["final"].comments += ";TEclass=%s" % ( self.features["TEclass"] )
                            
                # if it has no coding feature
                elif not self.features.has_key( "TE_BLRtx" ) and not self.features.has_key( "TE_BLRx" ):
                    # if it has matches with BLRn, it can be classified at least as incomplete (and may be confused)
                    if self.features.has_key( "TE_BLRn" ):
                        lClassif = self.getClassifFromMatch( "TE_BLRn" )
                        if self.features.has_key( "TE_HMMER" ):
                            if lClassif[3] == "":
                                lClassif[3] = self.getCommentsAboutProfilesAsString()
                            else:
                                lClassif[3] += ";%s" % ( self.getCommentsAboutProfilesAsString() )
                        if self.features.has_key("TEclass"):
                            lClassif[3] += ";TEclass=%s" % ( self.features["TEclass"] )
                        lClassif[4] = "incomp"
                        self.classif["final"] = Classif( lClassif=lClassif )
                        if lClassif[1] != "?":
                            self.confused = False
                        else:
                            self.confused = True
                    # if it has no match with BLRn (but possibly with HMMER), it is a NoCat
                    else:
                        category = "NoCat"
                        order = "?"
                        superfam = "?"
                        comments = "no structural features neither matches with known TEs"
                        if self.features.has_key( "TE_HMMER" ):
                            comments += ";%s" % ( self.getCommentsAboutProfilesAsString() )
                        if self.features.has_key("TEclass"):
                            comments += ";TEclass=%s" % ( self.features["TEclass"] )
                        completeness = "?"
                        self.classif["final"] = Classif( category, order, superfam, comments, completeness )
                        self.confused = False
                        
                        
            # if the sequence has only one structural feature
            else:
                
                # check if is a LARD, MITE or SINE
                self.classifShortCopiesWithStructFeat()

                # if not:
                if self.classif["final"] == None:

                    # classify according to the unique structural feature
                    self.classifPartialWithOneStructFeature()

                    # if it has coding features
                    if self.features.has_key( "TE_BLRtx" ) or self.features.has_key( "TE_BLRx" ):

                        # classify according to them
                        self.classifPartialFromCodingFeatures()

                        # and combine the two by taking into account the length parameters
                        self.classifFinalWithStructAndCodingFeatures()
                        if self.features.has_key( "TE_HMMER" ):
                            self.classif["final"].comments += ";%s" % ( self.getCommentsAboutProfilesAsString() )
                        if self.features.has_key( "TE_BLRn" ):
                            self.classif["final"].comments += ";%s" % ( self.getCommentsAboutTeBlastAsString( "TE_BLRn" ) )
                        if self.features.has_key("TEclass"):
                            self.classif["final"].comments += ";TEclass=%s" % ( self.features["TEclass"] )

                    # if it hasn't any coding feature
                    else:

                        # classify only according to the structural feature the length parameters
                        self.classifFinalWithOnlyOneKindOfFeatures( "struct" )
                        if self.features.has_key( "TE_HMMER" ):
                            self.classif["final"].comments += ";%s" % ( self.getCommentsAboutProfilesAsString() )
                        if self.features.has_key( "TE_BLRn" ):
                            self.classif["final"].comments += ";%s" % ( self.getCommentsAboutTeBlastAsString( "TE_BLRn" ) )
                        if self.features.has_key("TEclass"):
                            self.classif["final"].comments += ";TEclass=%s" % ( self.features["TEclass"] )


        # if the sequence has no feature
        else:
            category = "NoCat"
            order = "?"
            superfam = "?"
            comments = ""
            if self.features.has_key( "TE_BLRn" ):
                if comments == "":
                    comments = self.getCommentsAboutTeBlastAsString( "TE_BLRn" )
                else:
                    comments += ";%s" % ( self.getCommentsAboutTeBlastAsString( "TE_BLRn" ) )
            if self.features.has_key( "TE_HMMER" ):
                if comments == "":
                    comments = self.getCommentsAboutProfilesAsString()
                else:
                    comments += ";%s" % ( self.getCommentsAboutProfilesAsString() )
            if self.features.has_key("TEclass"):
                if comments == "":
                    comments = "TEclass=%s" % ( self.features["TEclass"] )
                else:
                    comments += ";TEclass=%s" % ( self.features["TEclass"] )
            if comments == "":
                comments = "not a single feature"
            completeness = "?"
            self.classif["final"] = Classif( category, order, superfam, comments, completeness )
            self.confused = False
            
    #--------------------------------------------------------------------------

    def classifPartialFromCodingFeatures( self ):
        """
        Classify according to coding features (if any), i.e. fill the dictionary 'classif' for key 'codingFeat'.
        """

        # if the sequence has matches with tBx AND with Bx
        if self.features.has_key( "TE_BLRtx" ) and self.features.has_key( "TE_BLRx" ):
            lBLRtx = self.getClassifFromMatch( "TE_BLRtx" )
            lBLRx = self.getClassifFromMatch( "TE_BLRx" )
            lComb = self.getCombineClassif_tBx_Bx( lBLRtx, lBLRx )
            self.classif["codingFeat"] = Classif( lClassif=lComb )

        # if the sequence has matches with tBx BUT NOT with Bx
        elif self.features.has_key( "TE_BLRtx" ) and not self.features.has_key( "TE_BLRx" ):
            lBLRtx = self.getClassifFromMatch( "TE_BLRtx" )
            self.classif["codingFeat"] = Classif( lClassif=lBLRtx )

        # if the sequence has matches with Bx BUT NOT with tBx
        elif not self.features.has_key( "TE_BLRtx" ) and self.features.has_key( "TE_BLRx" ):
            lBLRx = self.getClassifFromMatch( "TE_BLRx" )
            self.classif["codingFeat"] = Classif( lClassif=lBLRx )

    #--------------------------------------------------------------------------

    def getClassifFromMatch( self, method ):
        """
        Deduce the classification of the sequence based on its best match with the desired method.
        @param method: 'TE_BLRtx' or 'TE_BLRx' or 'TE_BLRn'
        @type method: string
        @return:  list of classification items ( category, order, superfam, comments, completeness )
        @rtype: list
        """
        category = self.features[method][0].sbj_class
        order = self.features[method][0].sbj_order
        superfam = self.features[method][0].sbj_superfam
        comments = self.getCommentsAboutTeBlastAsString( method )
        completeness = "NA"
        return [ category, order, superfam, comments, completeness ]

    #--------------------------------------------------------------------------

    def getCombineClassif_tBx_Bx( self, tBx, Bx ):
        """
        Deduce the classification of the sequence based on its two best matches, 1 with tBx and 1 with Bx.
        @param tBx: classification from tblastx
        @type tBx: list of strings
        @param Bx: classification from blastx
        @type Bx: list of strings
        @return:  list of classification items ( category, order, superfam, comments, completeness )
        @rtype: list
        """

        comments = "%s;%s" % ( tBx[3] , Bx[3] )

        # if same category
        if tBx[0] == Bx[0]:
            category = tBx[0]

            # if the category is unknown
            if tBx[0] == "?":
                order = "?"

            # if the category is known
            elif tBx[0] != "?":

                # if same order
                if tBx[1] == Bx[1]:
                    order = tBx[1]

                # if different orders
                else:

                    # one order is unknown
                    if tBx[1] == "?" or Bx[1] == "?":
                        if tBx[1] != "?" and Bx[1] == "?":
                            order = tBx[1]
                        elif tBx[1] == "?" and Bx[1] != "?":
                            order = Bx[1]

                    # the 2 orders are known but different
                    else:
                        order = "?"

        # if different categories
        else:

            # if one category is unknown (the other being known)
            if tBx[0] == "?" or Bx[0] == "?":

                # if category via tBx is known
                if tBx[0] != "?":
                    category = tBx[0]
                    order = tBx[1]

                # if category via Bx is known
                elif Bx[0] != "?":
                    category = Bx[0]
                    order = Bx[1]

            # if the 2 categories are known but different
            else:    # (tBx[0] == "I" and Bx[0] == "II") or (tBx[0] == "II" and Bx[0] == "I"):
                category = "?"
                order = "?"

        superfam ="?"
        if tBx[2] != "?" and Bx[2] != "?" and tBx[2] == Bx[2]:
            superfam = tBx[2]
        if tBx[2] != "?" and Bx[2] == "?":
            superfam = tBx[2]
        if tBx[2] == "?" and Bx[2] != "?":
            superfam = Bx[2]
        completeness = "NA"

        return [ category, order, superfam, comments, completeness ]

    #--------------------------------------------------------------------------

    def classifPartialWithOneStructFeature( self ):
        """
        Classify according to one structural feature, i.e. fill the dictionary 'classif' for key 'structFeat'.
        """

        if self.features.has_key( "LTR" ):
            category = "classI"
            order = "LTR"
            superfam = "?"
            comments = "struct=(LTRs;%int)" % ( self.features["LTR"][0].getLength() )
            completeness = "NA"
            self.classif["structFeat"] = Classif( category, order, superfam, comments, completeness )

        elif self.features.has_key( "TIR" ):
            category = "classII"
            order = "TIR"
            superfam = "?"
            comments = "struct=(TIRs;%int)" % ( self.features["TIR"][0].getLength() )
            completeness = "NA"
            self.classif["structFeat"] = Classif( category, order, superfam, comments, completeness )

        elif self.features.has_key( "polyA_tail" ):
            category = "classI"
            order = "LINE"
            superfam = "?"
            comments = "struct=(polyA_tail;%int)" % ( abs( self.features["polyA_tail"][0].end - self.features["polyA_tail"][0].start ) + 1 )
            completeness = "NA"
            self.classif["structFeat"] = Classif( category, order, superfam, comments, completeness )

        elif self.features.has_key( "SSR_tail" ):
            category = "classI"
            order = "LINE"
            superfam = "?"
            comments = "struct=(SSR_tail;%int)" % ( abs( self.features["SSR_tail"][0].end - self.features["SSR_tail"][0].start ) + 1 )
            completeness = "NA"
            self.classif["structFeat"] = Classif( category, order, superfam, comments, completeness )

    #--------------------------------------------------------------------------

    def classifFinalWithOnlyOneKindOfFeatures( self, kind ):
        """
        Finalize the classification when there are only one kind of features (structural xor coding).
        """

        if self.classif["final"] != None:
            print "ERROR: classification already finalized"
            sys.exit(1)

        if self.classif["codingFeat"] != None and self.classif["structFeat"] != None:
            print "ERROR: coding AND structural features instead of only one kind"
            sys.exit(1)

        completeness = "incomp"

        # if the category is unknown
        if self.classif[kind+"Feat"].category == "?":
            self.classif["final"] = self.classif[kind+"Feat"]
            self.classif["final"].completeness = completeness
            self.confused = True

        # if the category is known
        elif self.classif[kind+"Feat"].category != "?":

            # if the order is unknown
            if self.classif[kind+"Feat"].order == "?":
                self.classif["final"] = self.classif[kind+"Feat"]
                self.classif["final"].completeness = completeness
                self.confused = True

            # if the order is known
            elif self.classif[kind+"Feat"].order != "?":
                self.classif["final"] = self.classif[kind+"Feat"]
                if self.classif[kind+"Feat"].order not in ["Helitron","Polinton"]:
                    self.classif["final"].completeness = completeness
                else:
                    self.classif["final"].completeness = "NA"

                # check the sequence length compare to the parameters
                order = self.classif["final"].order
                self.checkLength( order, completeness )

    #--------------------------------------------------------------------------

    def classifFinalWithStructAndCodingFeatures( self ):
        """
        Finalize the classification when there are both structural and coding features.
        """

        if self.classif["final"] != None:
            print "ERROR: classification already finalized"
            sys.exit(1)

        if self.classif["codingFeat"] == None or self.classif["structFeat"] == None:
            print "ERROR: coding OR structural features instead of both kinds"
            sys.exit(1)

        completeness = "comp"

        # combine both kinds of features
        self.combineStructAndCodingFeatures()

        # check the sequence length compare to the parameters
        if self.confused == None:
            order = self.classif["final"].order
            self.checkLength( order, completeness )

    #--------------------------------------------------------------------------

    def combineStructAndCodingFeatures( self ):
        """
        Deduce a classification by combining 2 classifications from 'structural' and 'coding' features.
        """

        completeness = "comp"

        comments = self.classif["structFeat"].comments
        comments += ";" + self.classif["codingFeat"].comments

        # if same category
        if self.classif["structFeat"].category == self.classif["codingFeat"].category:
            category = self.classif["structFeat"].category

            # if the category is unknown
            if self.classif["structFeat"].category == "?":
                order = "?"
                self.confused = True

            # if the category is known
            elif self.classif["structFeat"].category != "?":

                # if same order
                if self.classif["structFeat"].order == self.classif["codingFeat"].order:
                    order = self.classif["structFeat"].order

                    # if the order is unknown
                    if order == "?":
                        self.confused = True

                # if different orders
                elif self.classif["structFeat"].order != self.classif["codingFeat"].order:

                    # if one order is unknown (the other being known)
                    if self.classif["structFeat"].order == "?" or self.classif["codingFeat"].order == "?":
                        if self.classif["structFeat"].order != "?":
                            order = self.classif["structFeat"].order
                        elif self.classif["codingFeat"].order != "?":
                            order = self.classif["codingFeat"].order

                    # if both orders are known (but different)
                    elif self.classif["structFeat"].order != "?" and self.classif["codingFeat"].order != "?":
                        order = "?"
                        self.confused = True

        # if different categories
        elif self.classif["structFeat"].category != self.classif["codingFeat"].category:

            # if one category is unknown (the other being known)
            if self.classif["structFeat"].category == "?" or self.classif["codingFeat"].category == "?":

                if self.classif["structFeat"].category != "?":
                    category = self.classif["structFeat"].category
                    order = self.classif["structFeat"].order
                    if order == "?":
                        self.confused = True

                elif self.classif["codingFeat"].category != "?":
                    category = self.classif["codingFeat"].category
                    order = self.classif["codingFeat"].order
                    if order == "?":
                        self.confused = True

            # if both categories are known but different
            elif self.classif["structFeat"].category != "?" or self.classif["codingFeat"].category != "?":
                category = "?"
                order = "?"
                self.confused = True

        superfam = self.classif["codingFeat"].superfam

        self.classif["final"] = Classif( category, order, superfam, comments, completeness )

    #--------------------------------------------------------------------------

    def checkLength( self, order, completeness ):
        """
        Take the length into account to classify the sequence.
        @param order: order of the classification
        @type order: string
        @param completeness: 'comp' or 'incomp'
        @type completeness: string
        """

        if order in ["Helitron","Polinton"]:
            self.confused = False
            return

        maxLength = self.param.getint("classif_consensus",order+"comp_max_length")

        # if the sequence is too long
        if self.length > maxLength:
            string = ";length=%i>%i" % ( self.length, maxLength )
            tmp = self.classif["final"].comments + string
            self.classif["final"].comments = tmp
            self.confused = True

        else:
            if self.classif["final"].order == "LINE":
                minLength = self.param.getint("classif_consensus","SINE_max_length")
                if self.length <= minLength:
                    string = ";length=%i<=%i" % ( self.length, minLength )
                    tmp = self.classif["final"].comments + string
                    self.classif["final"].comments = tmp
                    self.confused = True
                else:
                    self.confused = False
            elif self.classif["final"].order == "TIR":
                minLength = self.param.getint("classif_consensus","MITE_max_length")
                if self.length <= minLength:
                    string = ";length=%i<=%i" % ( self.length, minLength )
                    tmp = self.classif["final"].comments + string
                    self.classif["final"].comments = tmp
                    self.confused = True
                else:
                    self.confused = False
            else:
                self.confused = False

##        if completeness == "comp":
##            self.checkLengthForComp( order )

##        elif completeness == "incomp":
##            self.checkLengthForIncomp( order )

    #--------------------------------------------------------------------------

    def checkLengthForComp( self, order ):
        """
        Take the length into account to classify the sequence that has structural and coding features (i.e. complete).
        """

        maxLength = self.param.getint("classif_consensus",order+"comp_max_length")
        minLength = self.param.getint("classif_consensus",order+"comp_min_length")

        # if the sequence is too long
        if self.length > maxLength:
            string = ";length=%i>%i" % ( self.length, maxLength )
            tmp = self.classif["final"].comments + string
            self.classif["final"].comments = tmp
            self.confused = True

        # if the sequence is too short
        elif self.length < minLength:
            string = ";length=%i<%ip" % ( self.length, minLength )
            tmp = self.classif["final"].comments + string
            self.classif["final"].comments = tmp
            self.confused = True

        else:
            self.confused = False

    #--------------------------------------------------------------------------

    def checkLengthForIncomp( self, order ):
        """
        Take the length into account to classify the sequence that has structural or coding features (i.e. incomplete).
        """

        maxLength = self.param.getint("classif_consensus",order+"comp_min_length")

        # if the sequence is too long
        if self.length > maxLength:
            string = ";length=%i>%i" % ( self.length, maxLength )
            tmp = self.classif["final"].comments + string
            self.classif["final"].comments = tmp
            self.confused = True

        else:
            self.confused = False

    #--------------------------------------------------------------------------

    def classifShortCopiesWithStructFeat( self ):
        """
        Classify the LARDs, SINEs and MITEs when the consensus has one and only one structural feature.
        """

##        # if the sequence has LTRs
##        if self.features.has_key( "LTR" ):

##            # calculate its length without LTRs
##            length_without_LTR = self.length - 2 * (self.features["LTR"][0].end - self.features["LTR"][0].start + 1)
##            minLength = self.param.getint("classif_consensus","LTRcomp_min_length")

##            # if this length is below the parameter
##            if length_without_LTR < minLength:

##                # if it has no 'coding' match, then it is a LARD
##                if not self.features.has_key("TE_BLRtx") and not self.features.has_key("TE_BLRx"):
##                    category = "classI"
##                    order = "LARD"
##                    comments = "struct=(LTRs;%int);length=%i<%i" % ( self.features["LTR"][0].getLength(), length_without_LTR, minLength )
##                    completeness = "NA"
##                    self.classif["final"] = Classif( category, order, comments, completeness )
##                    self.confused = False

##                # else it is confused
##                else:
##                    category = "classI"
##                    order = "LARD"
##                    comments = "struct=(LTRs;%int);length=%i<%i;coding=" % ( self.features["LTR"][0].getLength(), length_without_LTR, minLength )
##                    if self.features.has_key("TE_BLRtx"):
##                        comments += "(TE_BLRtx;%s;%s;%s;%int)" % ( self.bestMatch["TE_BLRtx"].sbj_name, self.bestMatch["TE_BLRtx"].sbj_class, self.bestMatch["TE_BLRtx"].sbj_order, self.bestMatch["TE_BLRtx"].getLength() )
##                    elif self.features.has_key("TE_BLRx"):
##                        comments += "(TE_BLRx;%s;%s;%s;%int)" % ( self.bestMatch["TE_BLRx"].sbj_name, self.bestMatch["TE_BLRx"].sbj_class, self.bestMatch["TE_BLRx"].sbj_order, self.bestMatch["TE_BLRx"].getLength() )
##                    completeness = "NA"
##                    self.classif["final"] = Classif( category, order, comments, completeness )
##                    self.confused = True


        # if the sequence has TIRs
        if self.features.has_key( "TIR" ):
            maxLength = self.param.getint("classif_consensus","MITE_max_length")

            # if its length is below the parameter
            if self.length <= maxLength:

                # if it has no 'coding' match, then it is a MITE
                if not self.features.has_key("TE_BLRtx") and not self.features.has_key("TE_BLRx"):
                    category = "classII"
                    order = "MITE"
                    superfam = "NA"
                    comments = "struct=(TIRs;%int);length=%i<%i" % ( self.features["TIR"][0].getLength(), self.length, maxLength )
                    completeness = "NA"
                    self.classif["final"] = Classif( category, order, superfam, comments, completeness )
                    self.confused = False

                # else it is confused
                else:
                    category = "classII"
                    order = "MITE"
                    superfam = "NA"
                    comments = "struct=(TIRs;%int);length=%i<%i;match=" % ( self.features["TIR"][0].getLength(), self.length, maxLength )
                    if self.features.has_key("TE_BLRtx"):
                        comments += "(TE_BLRtx;%s;%s;%s;%int)" % ( self.bestMatch["TE_BLRtx"].sbj_name, self.bestMatch["TE_BLRtx"].sbj_class, self.bestMatch["TE_BLRtx"].sbj_order, self.bestMatch["TE_BLRtx"].getLength() )
                    elif self.features.has_key("TE_BLRx"):
                        comments += "(TE_BLRx;%s;%s;%s;%int)" % ( self.bestMatch["TE_BLRx"].sbj_name, self.bestMatch["TE_BLRx"].sbj_class, self.bestMatch["TE_BLRx"].sbj_order, self.bestMatch["TE_BLRx"].getLength() )
                    completeness = "NA"
                    self.classif["final"] = Classif( category, order, superfam, comments, completeness )
                    self.confused = True


        # if the sequence has a tail
        elif self.features.has_key( "polyA_tail" ) or self.features.has_key( "SSR_tail" ):
            maxLength = self.param.getint("classif_consensus","SINE_max_length")

            # if its length is below the parameter
            if self.length <= maxLength:

                #if it has no 'coding' match, then it is a SINE
                if not self.features.has_key("TE_BLRtx") and not self.features.has_key("TE_BLRx"):
                    category = "classI"
                    order = "SINE"
                    superfam = "NA"
                    if self.features.has_key( "polyA_tail" ):
                        comments = "struct=(polyA_tail;%int);length=%i<%i" % ( self.features["polyA_tail"][0].getLength(), self.length, maxLength )
                    elif self.features.has_key( "SSR_tail" ):
                        comments = "struct=(SSR_tail;%int);length=%i<%i" % ( self.features["SSR_tail"][0].getLength(), self.length, maxLength )
                    completeness = "NA"
                    self.classif["final"] = Classif( category, order, superfam, comments, completeness )
                    self.confused = False

                # else it is confused
                else:
                    category = "classI"
                    order = "SINE"
                    superfam = "NA"
                    if self.features.has_key( "polyA_tail" ):
                        comments = "struct=(polyA_tail;%int);length=%i<%i;match=" % ( self.features["polyA_tail"][0].getLength(), self.length, maxLength )
                    elif self.features.has_key( "SSR_tail" ):
                        comments = "struct=(SSR_tail;%int);length=%i<%i;match=" % ( self.features["SSR_tail"][0].getLength(), self.length, maxLength )
                    if self.features.has_key("TE_BLRtx"):
                        comments += "(TE_BLRtx;%s;%s;%s;%int)" % ( self.bestMatch["TE_BLRtx"].sbj_name, self.bestMatch["TE_BLRtx"].sbj_class, self.bestMatch["TE_BLRtx"].sbj_order, self.bestMatch["TE_BLRtx"].getLength() )
                    elif self.features.has_key("TE_BLRx"):
                        comments += "(TE_BLRx;%s;%s;%s;%int)" % ( self.bestMatch["TE_BLRx"].sbj_name, self.bestMatch["TE_BLRx"].sbj_class, self.bestMatch["TE_BLRx"].sbj_order, self.bestMatch["TE_BLRx"].getLength() )
                    completeness = "NA"
                    self.classif["final"] = Classif( category, order, superfam, comments, completeness )
                    self.confused = True

    #--------------------------------------------------------------------------

    def classifShortCopiesWithoutStructFeat( self ):
        """
        Classify the LARDs, SINEs and MITEs when the consensus has no structural feature, only coding feature(s).
        """

        # if the sequence is a 'classI' or 'classII' based on its coding features
        if self.classif["codingFeat"].category in ["classI","classII","class I","class II"]:
            category = self.classif["codingFeat"].category

            # if it has 'LARD' or 'SINE' or 'MITE' as order
            if self.classif["codingFeat"].order in ["LARD","SINE","MITE"]:
                order = self.classif["codingFeat"].order
                superfam = "?"

                if self.features.has_key( "TE_BLRtx" ):
                    method = "TE_BLRtx"
                    comments = "match=(%s;%s;%s;%s;%int);" % ( method, self.bestMatch[method].sbj_name, self.bestMatch[method].sbj_class, self.bestMatch[method].sbj_order, self.bestMatch[method].getLength() )
                if self.features.has_key( "TE_BLRx" ):
                    method = "TE_BLRx"
                    comments = "match=(%s;%s;%s;%s;%int);" % ( method, self.bestMatch[method].sbj_name, self.bestMatch[method].sbj_class, self.bestMatch[method].sbj_order, self.bestMatch[method].getLength() )

                if order == "LARD":
                    threshold = self.param.getint("classif_consensus","LTRcomp_min_length")
                else:
                    threshold = self.param.getint("classif_consensus",order+"_max_length")

                # if its length is below the threshold
                if self.length < threshold:
                    comments += "length=%i<%i" % ( self.length, threshold )
                    self.confused = False
                else:
                    comments += "length=%i>%i" % ( self.length, threshold )
                    self.confused = True

                completeness = "NA"
                self.classif["final"] = Classif( category, order, superfam, comments, completeness )

    #-------------------------------------------------------------------------
    
    def getCommentsAboutTeBlastAsString( self, method ):
        """
        Return string with data about matches between sequence and known TEs via one blast (tblastx, blastx, blastn).
        """
        comments = "match=(%s;%s;%s;%s;%s;%int;%g)" % ( method, self.bestMatch[method].sbj_name, self.bestMatch[method].sbj_class, self.bestMatch[method].sbj_order, self.bestMatch[method].sbj_superfam, self.bestMatch[method].getLength(), self.bestMatch[method].e_val )
        return comments

    #-------------------------------------------------------------------------
    
    def getCommentsAboutProfilesAsString( self ):
        """
        Return string with data about matches between sequence and HMM profiles.
        """
        comments = "profiles=(%s;%s;%int;%g)" % ( "HMMER", self.features["TE_HMMER"][0].range_subject.seqname, self.features["TE_HMMER"][0].range_subject.getLength(), self.features["TE_HMMER"][0].e_value )
        if len(self.features["TE_HMMER"]) > 1:
            comments += ";"
            comments += "profiles=(%s;%s;%int;%g)" % ( "HMMER", self.features["TE_HMMER"][1].range_subject.seqname, self.features["TE_HMMER"][1].range_subject.getLength(), self.features["TE_HMMER"][1].e_value )
        return comments
    
    #-------------------------------------------------------------------------
    
    def showClassif( self ):
        self.classif["final"].show()
        
#------------------------------------------------------------------------------

class Classif:
    """
    This class represents the classification of a sequence.
    """

    def __init__( self, category="", order="", superfam="", comments="", completeness="", lClassif=None ):
        if lClassif == None:
            self.category = category
            self.order = order
            self.superfam = superfam
            self.comments = comments
            self.completeness = completeness
        else:
            self.category = lClassif[0]
            self.order = lClassif[1]
            self.superfam = lClassif[2]
            self.comments = lClassif[3]
            self.completeness = lClassif[4]


    def show( self ):
        string = "category=%s; order=%s; superfam=%s; completeness=%s\ncomments=%s" % ( self.category, self.order, self.superfam, self.completeness, self.comments )
        print string; sys.stdout.flush()

#------------------------------------------------------------------------------

class TElib:
    """
    This class represents a match in the 'path' format and retrieve the class and order from the subject.
    """

    def __init__( self, path ):

        self.id = path.id

        self.qry_name = path.range_query.seqname
        self.qry_start = path.range_query.start
        self.qry_end = path.range_query.end

        sbj_name = path.range_subject.seqname.split(":")
        self.sbj_name = sbj_name[0]
        self.sbj_class = sbj_name[1]
        self.sbj_order = ""
        if "LTR" in sbj_name[2]:
            self.sbj_order = "LTR"
        elif "TIR" in sbj_name[2]:
            self.sbj_order = "TIR"
        elif "LINE" in sbj_name[2]:
            self.sbj_order = "LINE"
        elif "SINE" in sbj_name[2]:
            self.sbj_order = "SINE"
        elif "MITE" in sbj_name[2]:
            self.sbj_order = "MITE"
        elif "Helitron" in sbj_name[2]:
            self.sbj_order = "Helitron"
        elif "Polinton" in sbj_name[2]:
            self.sbj_order = "Polinton"
        elif "?" in sbj_name[2]:
            self.sbj_order = "?"
        if len(sbj_name) > 3:
            self.sbj_superfam = sbj_name[3]
        else:
            self.sbj_superfam = "?"
        self.sbj_start = path.range_subject.start
        self.sbj_end = path.range_subject.end
        if self.sbj_start < self.sbj_end:
            self.sbj_strand = "+"
        else:
            self.sbj_strand = "-"

        self.e_val = path.e_value
        self.identity = path.identity
        self.score = path.score

    def getLength( self ):
        return abs( int(self.qry_end) - int(self.qry_start) ) + 1

#------------------------------------------------------------------------------

class HostGene( Match ):
    def __init__( self, path ):
        Match.__init__( self )
#        if self.sbj_start < self.sbj_end:
#            self.sbj_strand = "+"
#        else:
#            self.sbj_strand = "-"

#------------------------------------------------------------------------------

class TR:
    
    def __init__( self, set ):
        self.id = set.id
        self.name = set.seqname
        data = set.name.split("|")
        rep_nb = re.search("[0-9]+",data[0]).group(0)
        termRep = data[0].split(rep_nb)[1]
        self.tr = termRep
        self.start = set.start
        self.end = set.end
        self.identity = data[2].split("=")[1]

    def view( self ):
        string = "%s\t%s\t%s\t%s\t%s\t%s" % ( self.id, self.name, self.tr, self.start, self.end, self.identity )
        print string

    def getLength( self ):
        if self.start < self.end:
            return self.end - self.start + 1
        else:
            return self.start - self.end + 1

#------------------------------------------------------------------------------

class ORF:
    
    def __init__(self,map):
        name = map.name.split("|")  #ex: name=["ORF","-3","266"]
        self.seqname = map.seqname  #ex: seqname="Juan"
        self.phase = name[1]        #ex: self.phase="-3"
        self.long = name[2]         #ex: self.long="266"
        self.start = map.start      #ex: self.start="3844L"
        self.end = map.end          #ex: self.end="3578L"

#------------------------------------------------------------------------------

class hRep:
    
    def __init__(self,set):
        self.name = set.seqname
        data = set.name.split("|")
        self.dir = data[0]
        self.size = data[1].split("=")[1]
        self.score = data[2].split("=")[1]
        self.lenTE = data[3].split("=")[1]
        self.start = set.start
        self.end = set.end

#------------------------------------------------------------------------------

def checkAttributes( ):
    """
    Check all necessary parameters are present.
    """
    if project == "":
        print "ERROR: missing project name (-p)"
        help(); sys.exit(1)
    if not CheckerUtils.isCharAlphanumOrUnderscore(project):
        print "ERROR: project name must contain only alphanumeric or underscore characters"
        help(); sys.exit(1)
    if configFileName == "":
        print "ERROR: missing configuration file (-c)"
        help(); sys.exit(1)
    if not os.path.exists( configFileName ):
        print "ERROR: can't find file '%s'" % ( configFileName )
        help(); sys.exit(1)
    if step == "":
        print "ERROR: missing step (-s)"
        help(); sys.exit(1)
    if "1" in step and inFileName == "":
        print "ERROR: missing input file (-i)"
        help(); sys.exit(1)
    if "1" in step and not os.path.exists( inFileName ):
        print "ERROR: can't find file '%s'" % ( inFileName )
        help(); sys.exit(1)
        
#------------------------------------------------------------------------------

def createSeqTable( inFileName ):
    """
    Create a table recording the input sequences.
    @param inFileName: name of the input fasta file
    @type inFileName: string
    """
    prg = os.environ["REPET_PATH"] + "/bin/srptCreateTable.py"
    cmd = prg
    cmd += " -n %s_seq" % ( project )
    cmd += " -f %s" % ( inFileName )
    cmd += " -t fasta"
    cmd += " -o"
    pL.launch( prg, cmd, verbose - 1 )

#------------------------------------------------------------------------------

def detectFeatures( inFileName, count, cDir, tmpDir ):
    """
    Launch programs to detect features on the sequences.
    @param inFileName: name of the input fasta file (absolute path)
    @type inFileName: string
    @param count: number of the job
    @type count: integer
    @param cDir: current directory (where to retrieve the result files)
    @ype cDir: string
    @param tmpDir: temporary directory (where the job will run)
    @type tmpDir: string
    """
    
    cL.job.jobname = "detectFeatures_%i" % ( count )
    prefix = os.path.basename( inFileName )
    cmd_start = ""
    cmd_start += "if not os.path.exists( \"" + prefix + "\" ):\n"
    cmd_start += "\tlog = os.system( \"cp %s .\" )\n" % ( inFileName )
    cmd_start += "\tif log != 0:\n"
    cmd_start += "\t\tprint \"ERROR: can't copy '%s' in temporary directory\"\n" % ( inFileName )
    cmd_start += "\t\tsys.stdout.flush()\n"
    cmd_start += "\t%s" % ( cL.cmd_test( cL.job, "error", loop=1 ) )
    cmd_start += "\t\tsys.exit(1)\n"
    cmd_finish = ""
    cmd_finish += "if os.path.exists( \"" + tmpDir + "/" + prefix + "\" ):\n"
    cmd_finish += "\tos.system( \"rm -f " + tmpDir + "/" + prefix + "\" )\n"
    
    # generic commands to launch a specific program and check its return values
    launch_1 = "log = os.system( \""
    launch_2 = "\" )\n"
    launch_2 += "if log != 0:\n"
    launch_2 += cL.cmd_test( cL.job, "error", loop=1 )
    launch_2 += "\tsys.exit(1)\n"
    
    if config.get("detect_features","term_rep") == "yes":
        cmd_start += detectTRsearch( prefix, launch_1, launch_2, cDir )
        
    if config.get("detect_features","polyA") == "yes":
        cmd_start += detectPolyA( prefix, launch_1, launch_2, cDir )
        
    if config.get("detect_features","tand_rep") == "yes":
        cmd_start += detectTRF( prefix, launch_1, launch_2, cDir )
        
    if config.get("detect_features","orf") == "yes":
        cmd_start += detectORFs( prefix, launch_1, launch_2, cDir )
        
    if config.get("detect_features","TE_BLRn") == "yes":
        cmd_start += detectBlaster( prefix, config.get("detect_features","TE_nucl_bank"), "blastn", "TE_BLRn", launch_1, launch_2, cDir, tmpDir )
        
    if config.get("detect_features","TE_BLRtx") == "yes":
        cmd_start += detectBlaster( prefix, config.get("detect_features","TE_nucl_bank"), "tblastx", "TE_BLRtx", launch_1, launch_2, cDir, tmpDir )
        
    if config.get("detect_features","TE_BLRx") == "yes":
        cmd_start += detectBlaster( prefix, config.get("detect_features","TE_prot_bank"), "blastx", "TE_BLRx", launch_1, launch_2, cDir, tmpDir )
        
    if config.get("detect_features","HG_BLRn") == "yes":
        cmd_start += detectBlaster( prefix, config.get("detect_features","HG_nucl_bank"), "blastn", "HG_BLRn", launch_1, launch_2, cDir, tmpDir )
        
    if config.get("detect_features","TE_HMMER") == "yes":
        if newHmmer:
            cmd_start += detectHmmProfilesNew( prefix, launch_1, launch_2, cDir, tmpDir )
        else:
            cmd_start += detectHmmProfiles( prefix, launch_1, launch_2, cDir, tmpDir )
            
    if config.get("detect_features","rDNA_BLRn") == "yes":
        cmd_start += detectBlaster( prefix, config.get("detect_features","rDNA_bank"), "blastn", "rDNA_BLRn", launch_1, launch_2, cDir, tmpDir )
        
    if CheckerUtils.isOptionInSectionInConfig( config, "detect_features", "TEclass" ) \
    and config.get("detect_features","TEclass") == "yes":
        cmd_start += detectTEclass( prefix, launch_1, launch_2, cDir )
        
    return cmd_start, cmd_finish

#------------------------------------------------------------------------------

def detectTRsearch( inFileName, launch_1, launch_2, cDir ):
    """
    Launch TRsearch to detect terminal repeats on the input sequences and record the results into a MySQL table.
    @param inFileName: name of the input fasta file
    @type inFileName: string
    @param launch_1: generic command at the beginning of a specific command
    @type launch_1: string
    @param launch_2: generic command at the end of a specific command
    @type launch_2: string
    @param cDir: current directory (where to retrieve the result files)
    @type cDir: string
    @return: all the commands to run the job
    @rtype: string
    """
    cmd = ""
    cmd += launch_1
    pL.reset( inFileName )
    cmd += pL.launchTRsearch( run="no" )
    cmd += launch_2
    cmd += "if not os.path.exists( \"%s/%s.TR.set\" ):\n" % ( cDir, inFileName )
    cmd += "\tos.system( \"mv %s.TR.set %s\" )\n" % ( inFileName, cDir )
    return cmd

#------------------------------------------------------------------------------

def detectPolyA( inFileName, launch_1, launch_2, cDir ):
    """
    Launch polyAtail to detect terminal repeats on the input sequences and record the results into a MySQL table.
    @param inFileName: name of the input fasta file
    @type inFileName: string
    @param launch_1: generic command at the beginning of a specific command
    @type launch_1: string
    @param launch_2: generic command at the end of a specific command
    @type launch_2: string
    @return: all the commands to run the job
    @rtype: string
    """
    cmd = ""
    cmd += launch_1
    pL.reset( inFileName )
    cmd += pL.launchPolyAtail( run="no" )
    cmd += launch_2
    cmd += "if not os.path.exists( \"%s/%s.polyA.set\" ):\n" % ( cDir, inFileName )
    cmd += "\tos.system( \"mv %s.polyA.set %s\" )\n" % ( inFileName, cDir )
    return cmd

#------------------------------------------------------------------------------

def detectTRF( inFileName, launch_1, launch_2, cDir ):
    """
    Launch TRF to detect tandem repeats on the input sequences and record the results into a MySQL table.
    @param inFileName: name of the input fasta file
    @type inFileName: string
    @param launch_1: generic command at the beginning of a specific command
    @type launch_1: string
    @param launch_2: generic command at the end of a specific command
    @type launch_2: string
    @return: all the commands to run the job
    @rtype: string
    """
    cmd = ""
    cmd += launch_1
    cmd += os.environ["REPET_PATH"] + "/bin/launchTRF.py"
    cmd += " -i %s" % ( inFileName )
    cmd += " -o %s.SSRtrf.set" % ( inFileName )
    cmd += " -c"
    cmd += " -v 1"
    cmd += launch_2
    cmd += "if not os.path.exists( \"%s/%s.SSRtrf.set\" ):\n" % ( cDir, inFileName )
    cmd += "\tos.system( \"mv %s.SSRtrf.set %s\" )\n" % ( inFileName, cDir )
    return cmd

#------------------------------------------------------------------------------

def detectORFs( inFileName, launch_1, launch_2, cDir ):
    """
    Launch 'dbORF.py' to detect open reading frames (ORFs) on the input sequences and record the results into a MySQL table.
    @param inFileName: name of the input fasta file
    @type inFileName: string
    @param launch_1: generic command at the beginning of a specific command
    @type launch_1: string
    @param launch_2: generic command at the end of a specific command
    @type launch_2: string
    @return: all the commands to run the job
    @rtype: string
    """
    cmd = ""
    cmd += launch_1
    cmd += os.environ["REPET_PATH"] + "/bin/dbORF.py"
    cmd += " -i %s" % ( inFileName )
    cmd += " -n 10"
    cmd += " -s 30"
    cmd += launch_2
    cmd += "if not os.path.exists( \"%s/%s.orf.map\" ):\n" % ( cDir, inFileName )
    cmd += "\tos.system( \"mv %s.orf.map %s\" )\n" % ( inFileName, cDir )    
    return cmd

#------------------------------------------------------------------------------

def detectBlaster( inFileName, bank, blast, acronym, launch_1, launch_2, cDir, tmpDir ):
    """
    Launch Blaster and then Matcher to compare the input sequences with a given bank and record the results into a MySQL table.
    @param inFileName: name of the input fasta file
    @type inFileName: string
    @param bank: name of the bank
    @type: string
    @param blast: name of the blast
    @type blast: string
    @param acronym: acronym of the command (TE_BLRn, TE_BLRtx, TE_BLRx, HG_BLRn)
    @param launch_1: generic command at the beginning of a specific command
    @type launch_1: string
    @param launch_2: generic command at the end of a specific command
    @type launch_2: string
    @return: all the commands to run the job
    @rtype: string
    """
    
    if not os.path.exists( "%s_cut" % ( bank ) ):
        if verbose > 0:
            print "prepare bank '%s'..." % ( bank ); sys.stdout.flush()
        prg = os.environ["REPET_PATH"] + "/bin/blaster"
        cmd = prg
        cmd += " -s %s" % ( bank )
        cmd += " -n %s" % ( blast )
        if config.get("detect_features","wublast") == "yes":
            cmd += " -W"
            cmd += " -p -cpus=1"
        cmd += " -r"
        cmd += " -P"
        pL.launch( prg, cmd )
        os.system( "rm %s-%s-*.param" % ( bank, blast ) )
        
    cmd = ""
    
    cmd += launch_1
    cmd += os.environ["REPET_PATH"] + "/bin/blaster"
    cmd += " -q %s" % ( inFileName )
    cmd += " -s %s/%s" % ( cDir, bank )
    cmd += " -B %s_%s_%s" % ( inFileName, acronym, bank )
    cmd += " -n %s" % ( blast )
    if config.get("detect_features","wublast") == "yes":
        cmd += " -W"
        cmd += " -p -cpus=1"
    cmd += " -r"
    cmd += " -v 1"
    cmd += launch_2
    
    cmd += "if not os.path.exists( \"%s/%s_%s_%s.param\" ):\n" % ( cDir, inFileName, acronym, bank )
    cmd += "\tos.system( \"mv %s_%s_%s.param %s\" )\n" % ( inFileName, acronym, bank, cDir )
    cmd += "if os.path.exists( \"%s_cut\" ):\n" % ( inFileName )
    cmd += "\tos.system( \"rm -f %s_cut*\" )\n" % ( inFileName )
    cmd += "if os.path.exists( \"%s.Nstretch.map\" ):\n" % ( inFileName )
    cmd += "\tos.remove( \"%s.Nstretch.map\" )\n" % ( inFileName )
    cmd += "if os.path.exists( \"%s_%s_%s.raw\" ):\n" % ( inFileName, acronym, bank )
    cmd += "\tos.remove( \"%s_%s_%s.raw\" )\n" % ( inFileName, acronym, bank )
    cmd += "if os.path.exists( \"%s_%s_%s.seq_treated\" ):\n" % ( inFileName, acronym, bank )
    cmd += "\tos.remove( \"%s_%s_%s.seq_treated\" )\n" % ( inFileName, acronym, bank )
    
    cmd += launch_1
    cmd += os.environ["REPET_PATH"] + "/bin/matcher"
    cmd += " -m %s_%s_%s.align" % ( inFileName, acronym, bank )
    cmd += " -q %s" % ( inFileName )
    cmd += " -s %s/%s" % ( cDir, bank )
    cmd += " -j"
    cmd += " -v 1"
    cmd += launch_2
    
    cmd += "if not os.path.exists( \"%s/%s_%s_%s.align.clean_match.path\" ):\n" % ( cDir, inFileName, acronym, bank )
    cmd += "\tos.system( \"mv %s_%s_%s.align.clean_match.path %s\" )\n" % ( inFileName, acronym, bank, cDir )
    cmd += "if not os.path.exists( \"%s/%s_%s_%s.align.clean_match.tab\" ):\n" % ( cDir, inFileName, acronym, bank )
    cmd += "\tos.system( \"mv %s_%s_%s.align.clean_match.tab %s\" )\n" % ( inFileName, acronym, bank, cDir )
    cmd += "if not os.path.exists( \"%s/%s_%s_%s.align.clean_match.param\" ):\n" % ( cDir, inFileName, acronym, bank )
    cmd += "\tos.system( \"mv %s_%s_%s.align.clean_match.param %s\" )\n" % ( inFileName, acronym, bank, cDir )
    cmd += "if os.path.exists( \"%s_%s_%s.align\" ):\n" % ( inFileName, acronym, bank )
    cmd += "\tos.remove( \"%s_%s_%s.align\" )\n" % ( inFileName, acronym, bank )
    cmd += "if os.path.exists( \"%s_%s_%s.align.clean_match.fa\" ):\n" % ( inFileName, acronym, bank )
    cmd += "\tos.remove( \"%s_%s_%s.align.clean_match.fa\" )\n" % ( inFileName, acronym, bank )
    cmd += "if os.path.exists( \"%s_%s_%s.align.clean_match.map\" ):\n" % ( inFileName, acronym, bank )
    cmd += "\tos.remove( \"%s_%s_%s.align.clean_match.map\" )\n" % ( inFileName, acronym, bank )
    
    if tmpDir != cDir:
        cmd += "if os.path.exists( \"%s\" ):\n" % ( bank )
        cmd += "\tos.remove( \"%s\" )\n" % ( bank )
        
    return cmd

#------------------------------------------------------------------------------

def detectHmmProfiles( inFileName, launch_1, launch_2, cDir, tmpDir ):
    """
    Translate into the 6 frames and replace stop codons by X,
    launch 'hmmpfam', convert the output into the 'align' format,
    transform the match coordinates from aa into nt on the consensus sequences,
    finally launch 'matcher' with 'join' option and get a 'path' file.
    @param inFileName: name of the input fasta file
    @type inFileName: string
    @param launch_1: generic command at the beginning of a specific command
    @type launch_1: string
    @param launch_2: generic command at the end of a specific command
    @type launch_2: string
    @return: all the commands to run the job
    @rtype: string
    """
    
    profilsHmmBank = config.get("detect_features","TE_HMM_profiles")
    bank = os.path.basename( profilsHmmBank )
    evalueMax = config.get("detect_features","TE_HMMER_evalue")
    
    cmd = ""
    
    cmd += launch_1
    cmd += os.environ["REPET_PATH"] + "/bin/translateAfastaFileInAllFrameAndReplaceStopsByX_script.py"
    cmd += " -i %s" % ( inFileName )
    cmd += " -o %s_translated" % ( inFileName )
    cmd += launch_2
    
    cmd += launch_1
    cmd += "hmmpfam"
    cmd += " --informat FASTA"
    cmd += " -E %s" % ( evalueMax )
    cmd += " %s/%s" % ( cDir, bank )
    cmd += " %s_translated" % ( inFileName )
    cmd += " > %s_tr.hmmPfamOut" % ( inFileName )
    cmd += launch_2
    
    cmd += "if os.path.exists( \"%s_translated\" ):\n" % ( inFileName )
    cmd += "\tos.remove( \"%s_translated\" )\n" % ( inFileName )
    
    cmd += launch_1
    cmd += os.environ["REPET_PATH"] + "/bin/HmmOutput2alignAndTransformCoordInNtAndFilterScores_script.py"
    cmd += " -i %s_tr.hmmPfamOut" % ( inFileName )
    cmd += " -o %s_profiles_%s.align" % ( inFileName, bank )
    cmd += " -T %s" % ( inFileName )
    cmd += " -c"
    cmd += launch_2
    
    cmd += launch_1
    cmd += os.environ["REPET_PATH"] + "/bin/matcher"
    cmd += " -m %s_profiles_%s.align" % ( inFileName, bank )
    cmd += " -j"
    cmd += " -E 10"
    cmd += " -L 0"
    cmd += " -v 1"
    cmd += launch_2
    
    cmd += "if not os.path.exists( \"%s/%s_profiles_%s.align.clean_match.path\" ):\n" % ( cDir, inFileName, bank )
    cmd += "\tos.system( \"mv %s_profiles_%s.align.clean_match.path %s\" )\n" % ( inFileName, bank, cDir )
    cmd += "if not os.path.exists( \"%s/%s_profiles_%s.align.clean_match.param\" ):\n" % ( cDir, inFileName, bank )
    cmd += "\tos.system( \"mv %s_profiles_%s.align.clean_match.param %s\" )\n" % ( inFileName, bank, cDir )
    cmd += "if os.path.exists( \"%s_profiles_%s.align\" ):\n" % ( inFileName, bank )
    cmd += "\tos.remove( \"%s_profiles_%s.align\" )\n" % ( inFileName, bank )
    cmd += "if os.path.exists( \"%s_profiles_%s.align.clean_match.map\" ):\n" % ( inFileName, bank )
    cmd += "\tos.remove( \"%s_profiles_%s.align.clean_match.map\" )\n" % ( inFileName, bank )
    
    if tmpDir != cDir:
        cmd += "if os.path.exists( \"%s\" ):\n" % ( bank )
        cmd += "\tos.remove( \"%s\" )\n" % ( bank )
        
    return cmd

#------------------------------------------------------------------------------

def detectHmmProfilesNew( inFileName, launch_1, launch_2, cDir, tmpDir ):
        iProfilesSearch = ProfilesSearch()
        profilsHmmBank = config.get("detect_features","TE_HMM_profiles")
        bank = os.path.basename( profilsHmmBank )
        cmd = ""
        if not ( os.path.exists(cDir + "/" + bank + ".h3m") \
            and os.path.exists(cDir + "/" + bank + ".h3i") \
            and os.path.exists(cDir + "/" + bank + ".h3f") \
            and os.path.exists(cDir + "/" + bank + ".h3p")) :
            iProfilesSearch.prepareProfilesBank(launch_1, launch_2, config, cDir, verbose)
        
        cmd += iProfilesSearch.detectHmmProfiles( inFileName, launch_1, launch_2, cDir, tmpDir, config )
        return cmd

#------------------------------------------------------------------------------

def detectTEclass( inFileName, launch_1, launch_2, cDir ):
    """
    Launch TEclass to classify the input sequences based on their composition.
    @param inFileName: name of the input fasta file
    @type inFileName: string
    @param launch_1: generic command at the beginning of a specific command
    @type launch_1: string
    @param launch_2: generic command at the end of a specific command
    @type launch_2: string
    @param cDir: current directory (where to retrieve the result files)
    @type cDir: string
    @return: all the commands to run the job
    @rtype: string
    """
    cmd = ""
    cmd += launch_1
    
    launch = os.environ["REPET_PATH"] + "/bin/launchTEclass.py"
    launch += " -i %s" % ( inFileName )
    launch += " -o %s.TEclass.map" % ( inFileName )
    launch += " -c"
    launch += " -v 1"
    
    cmd += launch
    cmd += launch_2
    cmd += "if not os.path.exists( \"%s/%s.TEclass.map\" ):\n" % ( cDir, inFileName )
    cmd += "\tos.system( \"mv %s.TEclass.map %s\" )\n" % ( inFileName, cDir )
    return cmd

#------------------------------------------------------------------------------
        
def createDirectory(dirName, message):
        logger.info( message )
        if verbose > 0:
            print message
            sys.stdout.flush()
        if os.path.exists(dirName):
            shutil.rmtree(dirName)
        os.mkdir(dirName)
        os.chdir(dirName)
        
def collectResults():
    """
    Collect the results of each job for each detection programs.
    """

    if config.get(sectionName, "term_rep") == "yes":
        message = "collect results from 'TRsearch'"
        createDirectory("TRsearch", message)
        collectTROrPolyAOrTRF("TR")
        
    if config.get(sectionName, "polyA") == "yes":
        message = "collect results from 'polyAtail'"
        createDirectory("polyA", message)
        collectTROrPolyAOrTRF("polyA")
        
    if config.get(sectionName, "tand_rep") == "yes":
        message = "collect results from 'TRF'"
        createDirectory("TRF", message)
        collectTROrPolyAOrTRF("SSRtrf")
        
    if config.get(sectionName, "orf") == "yes":
        message = "collect results from 'dbORF.py'"
        createDirectory("ORFs", message)
        collectORFOrTEclass("orf")

    if CheckerUtils.isOptionInSectionInConfig( config, sectionName, "TEclass" ) \
    and config.get(sectionName, "TEclass") == "yes":
        message = "collect results from 'TEclass'"
        createDirectory("TEclass", message)
        collectORFOrTEclass("TEclass")  
        
    if config.get(sectionName, "TE_BLRn") == "yes":
        bank = config.get(sectionName, "TE_nucl_bank")
        message = "collect results from 'blastn' on bank '%s'" % ( bank )
        createDirectory("TE_BLRn", message)
        collectBlaster("TE_BLRn", bank)
        
    if config.get(sectionName, "TE_BLRtx") == "yes":
        bank = config.get(sectionName, "TE_nucl_bank")
        message = "collect results from 'tblastx' on bank '%s'" % ( bank )
        createDirectory("TE_BLRtx", message)
        collectBlaster("TE_BLRtx", bank)

    if config.get(sectionName, "TE_BLRx") == "yes":
        bank = config.get(sectionName, "TE_prot_bank")
        message = "collect results from 'blastx' on bank '%s'" % ( bank )
        createDirectory("TE_BLRx", message)
        collectBlaster("TE_BLRx", bank)

    if config.get(sectionName, "HG_BLRn") == "yes":
        bank = config.get(sectionName, "HG_nucl_bank")
        message = "collect results from 'blastn' on bank '%s'" % ( bank )
        createDirectory("HG_BLRn", message)
        collectBlaster("HG_BLRn", bank)
               
    if config.get(sectionName, "rDNA_BLRn") == "yes":
        bank = config.get(sectionName, "rDNA_bank")
        message = "collect results from 'blastn' on bank '%s'" % ( bank )
        createDirectory("rDNA_BLRn", message)
        collectBlaster("rDNA_BLRn", bank)

    if config.get(sectionName, "TE_HMMER") == "yes":
        bank = config.get(sectionName, "TE_HMM_profiles")
        message = "collect results from 'hmmpfam' on bank '%s'" % ( bank )
        createDirectory("HmmProfiles", message)
        collectProfilesHmmer()            

#------------------------------------------------------------------------------
    
def collectTROrPolyAOrTRF(analysis):
    FileUtils.catFilesByPattern( "../batch_*.fa.%s.set" % ( analysis ), "%s.%s.set.tmp" % ( project, analysis ) )

    lCmds = []
    prg = os.environ["REPET_PATH"] + "/bin/setnum2id"
    cmd = prg
    cmd += " -i %s.%s.set.tmp" % ( project, analysis )
    cmd += " -o %s.%s.set" % ( project, analysis )
    cmd += " -v %i" % ( verbose - 1 )
    lCmds.append( cmd )

    prg = os.environ["REPET_PATH"] + "/bin/srptCreateTable.py"
    cmd = prg
    cmd += " -f %s.%s.set" % ( project, analysis )
    cmd += " -n %s_%s_set" % ( project, analysis )
    cmd += " -t set"
    cmd += " -o"
    cmd += " -c %s" % ( configFileName )
    lCmds.append( cmd )
    
    cDir = os.getcwd()
    if config.get(sectionName, "tmpDir" ) != "":
        tmpDir = config.get(sectionName, "tmpDir")
    else:
        tmpDir = cDir
            
    groupid = "%s_TEclassifier_CollectResults_%s" % ( project, analysis )
    acronym = "setnum2id_srptCreateTable"
    iJobDb = RepetJob( cfgFileName = "%s/%s" % (os.path.abspath("../"), configFileName) )
    cL = Launcher( iJobDb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
    cL.beginRun()
    cL.job.jobname = acronym
    cmd_start = ""
    cmd_start += "os.system( \"ln -s %s/%s.%s.set.tmp .\" )\n" % ( cDir, project, analysis )
    cmd_start += "os.system( \"cp %s/%s .\" )\n" % ( os.path.abspath("../"), configFileName )
    for c in lCmds:
        cmd_start += "log = os.system( \""
        cmd_start += c
        cmd_start += "\" )\n"
    cmd_finish = "os.system( \"mv %s.%s.set %s/.\" )\n" % ( project, analysis, cDir )
    cL.runSingleJob( cmd_start, cmd_finish )
    cL.endRun()
    if config.get(sectionName, "clean") == "yes":
        cL.clean( acronym )
    iJobDb.close()
    
    os.remove("%s.%s.set.tmp" % ( project, analysis ))
    os.chdir( ".." )
    cmd = "find -name \"batch_*.fa.%s.set\" -exec rm {} \;" % ( analysis )
    os.system(cmd)
    
#------------------------------------------------------------------------------
    
def collectORFOrTEclass(analysis):
    FileUtils.catFilesByPattern( "../batch_*.fa.%s.map" % ( analysis ), "%s.%s.map" % ( project, analysis ) )

    prg = os.environ["REPET_PATH"] + "/bin/srptCreateTable.py"
    cmd = prg
    cmd += " -f %s.%s.map" % ( project, analysis )
    cmd += " -n %s_%s_map" % ( project, analysis.replace("orf", "ORF") )
    cmd += " -t map"
    cmd += " -o"
    cmd += " -c %s" % ( configFileName )
    
    cDir = os.getcwd()
    if config.get(sectionName, "tmpDir" ) != "":
        tmpDir = config.get(sectionName, "tmpDir")
    else:
        tmpDir = cDir
            
    groupid = "%s_TEclassifier_CollectResults_%s" % ( project, analysis )
    acronym = "srptCreateTable"
    iJobDb = RepetJob( cfgFileName = "%s/%s" % (os.path.abspath("../"), configFileName) )
    cL = Launcher( iJobDb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
    cL.beginRun()
    cL.job.jobname = acronym
    cmd_start = ""
    cmd_start += "os.system( \"ln -s %s/%s.%s.map .\" )\n" % ( cDir, project, analysis )
    cmd_start += "os.system( \"cp %s/%s .\" )\n" % ( os.path.abspath("../"), configFileName ) 
    cmd_start += "log = os.system( \""
    cmd_start += cmd
    cmd_start += "\" )\n"
    cL.runSingleJob( cmd_start )
    cL.endRun()
    if config.get(sectionName, "clean") == "yes":
        cL.clean( acronym )
    iJobDb.close()
    
    os.chdir( ".." )
    cmd = "find -name \"batch_*.fa.%s.map\" -exec rm {} \;" % ( analysis )
    os.system(cmd)

#------------------------------------------------------------------------------

def collectBlaster( analysis, bank ):
    FileUtils.catFilesByPattern( "../batch_*.fa_%s_%s.align.clean_match.path" % ( analysis, bank ),
                                 "%s_%s_%s.align.clean_match.path.tmp" % ( project, analysis, bank ) )

    FileUtils.catFilesByPattern( "../batch_*.fa_%s_%s.align.clean_match.tab" % ( analysis, bank ),
                                 "%s_%s_%s.align.clean_match.tab.tmp" % ( project, analysis, bank ) )
    
    lCmds = []
    prg = os.environ["REPET_PATH"] + "/bin/pathnum2id"
    cmd = prg
    cmd += " -i %s_%s_%s.align.clean_match.path.tmp" % ( project, analysis, bank )
    cmd += " -o %s_%s_%s.align.clean_match.path" % ( project, analysis, bank )
    cmd += " -v %i" % ( verbose - 1 )
    lCmds.append( cmd )
    
    prg = os.environ["REPET_PATH"] + "/bin/Matchnum2id.py"
    cmd = prg
    cmd += " -i %s_%s_%s.align.clean_match.tab.tmp" % ( project, analysis, bank )
    cmd += " -o %s_%s_%s.align.clean_match.tab" % ( project, analysis, bank )
    cmd += " -v %i" % ( verbose - 1 )
    lCmds.append( cmd )
    
    prg = os.environ["REPET_PATH"] + "/bin/srptCreateTable.py"
    cmd = prg
    cmd += " -f %s_%s_%s.align.clean_match.path" % ( project, analysis, bank )
    cmd += " -n %s_%s_path" % ( project, analysis )
    cmd += " -t path"
    cmd += " -o"
    cmd += " -c %s" % ( configFileName )
    lCmds.append( cmd )
    
    prg = os.environ["REPET_PATH"] + "/bin/srptCreateTable.py"
    cmd = prg
    cmd += " -f %s_%s_%s.align.clean_match.tab" % ( project, analysis, bank )
    cmd += " -n %s_%s_match" % ( project, analysis )
    cmd += " -t match"
    cmd += " -o"
    cmd += " -c %s" % ( configFileName )
    lCmds.append( cmd )
        
    cDir = os.getcwd()
    if config.get(sectionName, "tmpDir" ) != "":
        tmpDir = config.get(sectionName, "tmpDir")
    else:
        tmpDir = cDir
            
    groupid = "%s_TEclassifier_CollectResults_%s" % ( project, analysis )
    acronym = "pathnum2id_Matchnum2id_srptCreateTable"
    iJobDb = RepetJob( cfgFileName = "%s/%s" % (os.path.abspath("../"), configFileName) )
    cL = Launcher( iJobDb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
    cL.beginRun()
    cL.job.jobname = acronym
    cmd_start = ""
    cmd_start += "os.system( \"ln -s %s/%s_%s_%s.align.clean_match.path.tmp .\" )\n" % ( cDir, project, analysis, bank )
    cmd_start += "os.system( \"ln -s %s/%s_%s_%s.align.clean_match.tab.tmp .\" )\n" % ( cDir, project, analysis, bank )
    cmd_start += "os.system( \"cp %s/%s .\" )\n" % ( os.path.abspath("../"), configFileName ) 
    for c in lCmds:
        cmd_start += "log = os.system( \""
        cmd_start += c
        cmd_start += "\" )\n"
    cmd_finish = "os.system( \"mv %s_%s_%s.align.clean_match.tab %s/.\" )\n" % ( project, analysis, bank, cDir )
    cmd_finish += "os.system( \"mv %s_%s_%s.align.clean_match.path %s/.\" )\n" % ( project, analysis, bank, cDir )
    cL.runSingleJob( cmd_start, cmd_finish )
    cL.endRun()
    if config.get(sectionName, "clean") == "yes":
        cL.clean( acronym )
    iJobDb.close()      
        
    os.remove("%s_%s_%s.align.clean_match.path.tmp" % ( project, analysis, bank ))
    os.remove("%s_%s_%s.align.clean_match.tab.tmp" % ( project, analysis, bank )) 
    os.chdir( ".." )
    cmd = "find -name \"batch_*.fa_%s_%s.*\" -exec rm {} \;" % ( analysis, bank )
    os.system(cmd)
    lCutFiles = glob.glob( "%s_cut*" % ( bank ) )
    if len( lCutFiles ) != 0:
        for f in lCutFiles:
            os.remove( f ) 
    if os.path.exists( "%s.Nstretch.map" % ( bank ) ):
        os.remove( "%s.Nstretch.map" % ( bank ) )

#------------------------------------------------------------------------------
    
def collectProfilesHmmer():
    bankFull = config.get(sectionName, "te_hmm_profiles")
    bank = os.path.basename( bankFull )
    FileUtils.catFilesByPattern( "../batch_*.fa_profiles_%s.align.clean_match.path" % ( bank ),
                                 "%s_profiles_%s.align.clean_match.path.tmp" % ( project, bank ) )

    lCmds = []
    prg = os.environ["REPET_PATH"] + "/bin/pathnum2id"
    cmd = prg
    cmd += " -i %s_profiles_%s.align.clean_match.path.tmp" % ( project, bank )
    cmd += " -o %s_profiles_%s.align.clean_match.path" % ( project, bank )
    cmd += " -v %i" % ( verbose - 1 )
    lCmds.append( cmd )
        
    prg = os.environ["REPET_PATH"] + "/bin/srptCreateTable.py"
    cmd = prg
    cmd += " -f %s_profiles_%s.align.clean_match.path" % ( project, bank )
    cmd += " -n %s_Profiles_path" % ( project )
    cmd += " -t path"
    cmd += " -o"
    cmd += " -c %s" % ( configFileName )
    lCmds.append( cmd )
    
    cDir = os.getcwd()
    if config.get(sectionName, "tmpDir" ) != "":
        tmpDir = config.get(sectionName, "tmpDir")
    else:
        tmpDir = cDir
            
    groupid = "%s_TEclassifier_CollectResults_TE_HMMER" % ( project )
    acronym = "pathnum2id_srptCreateTable"
    iJobDb = RepetJob( cfgFileName = "%s/%s" % (os.path.abspath("../"), configFileName) )
    cL = Launcher( iJobDb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
    cL.beginRun()
    cL.job.jobname = acronym
    cmd_start = ""
    cmd_start += "os.system( \"ln -s %s/%s_profiles_%s.align.clean_match.path.tmp .\" )\n" % ( cDir, project, bank )
    cmd_start += "os.system( \"cp %s/%s .\" )\n" % ( os.path.abspath("../"), configFileName )
    for c in lCmds:
        cmd_start += "log = os.system( \""
        cmd_start += c
        cmd_start += "\" )\n"
    cmd_finish = "os.system( \"mv %s_profiles_%s.align.clean_match.path %s/.\" )\n" % ( project, bank, cDir )
    cL.runSingleJob( cmd_start, cmd_finish )
    cL.endRun()
    if config.get(sectionName, "clean") == "yes":
        cL.clean( acronym )
    iJobDb.close()

    os.remove("%s_profiles_%s.align.clean_match.path.tmp" % ( project, bank ))
    os.chdir( ".." )
    cmd = "find -name \"batch_*.fa_profiles_%s.*\" -exec rm {} \;" % ( bank )
    os.system(cmd)
    
#------------------------------------------------------------------------------

def checkFeatureTables():
    """
    Check if the different tables recording sequence features (tandem repeats, matches with known TEs...) exist or not.
    """
    
    exist = 0
    tableSuffix = [ "_seq",
                   "_TR_set",
                   "_SSRtrf_set",
                   "_polyA_set",
                   "_ORF_map",
                   "_TE_BLRn_path",
                   "_TE_BLRn_match",
                   "_TE_BLRtx_path",
                   "_TE_BLRtx_match",
                   "_TE_BLRx_path",
                   "_TE_BLRx_match",
                   "_HG_BLRn_path",
                   "_HG_BLRn_match",
                   "_Profiles_path",
                   "_TEclass_map" ]
    iDb = DbMySql()
    for suffix in tableSuffix:
        if iDb.doesTableExist( project + suffix ):
            message = "table '%s%s' exists" % ( project, suffix )
            message += " (%i lines)" % ( iDb.getSize( project + suffix ) )
            logger.info( message )
            if verbose > 0:
                print message
                sys.stdout.flush()
            exist += 1
        else:
            message = "table '%s%s' doesn't exist" % ( project, suffix )
            logger.warning( message )
            if verbose > 0:
                print message
                sys.stdout.flush()
    iDb.close()
    return exist

#------------------------------------------------------------------------------

def keepClassifParamInLog():
    """
    Keep track of the parameters used for the classification in the log file.
    """

    string = "parameters used for the classification:"
    for option in [ "LTRcomp_max_length", "LTRcomp_min_length", "LINEcomp_max_length", "LINEcomp_min_length", "TIRcomp_max_length", "TIRcomp_min_length", "SINE_max_length", "MITE_max_length", "SSR_max_coverage", "SSR_min_total_length", "redundancy_threshold_identity", "redundancy_threshold_coverage", "filter_host_genes", "host_genes_threshold_identity", "host_genes_threshold_coverage" ]:
        string += "\n%s: %s" % ( option, config.get("classif_consensus",option) )
    logger.info( string )

#------------------------------------------------------------------------------

def classifyConsensus( elements, config, uniq, lClassifNames ):
    """
    Classify the input sequences according to their features and save the classification.
    @param elements: list containing a pair (accession,length) for each input sequence
    @type elements: list of 2-dim lists
    @param config: configuration file
    @type config: file handling
    @param uniq: '' or '_uniq'
    @type uniq: string
    @param lClassifNames: list containing all the possible classification names (LTRcomp...)
    @type lClassifNames: list of strings
    """

    # be sure to clean existing files
    for i in ["LTR","LARD","LINE","SINE","TIR","MITE","Helitron","Polinton","SSR","HostGene","confused","NoCat"]:
        for j in ["","comp","incomp"]:
            if os.path.exists( "%s_%s%s.fa" % ( project, i, j ) ):
                os.remove( "%s_%s%s.fa" % ( project, i, j ) )

    fileHeader = project + uniq + "_TEclassifier"

    classifFileName = "%s.classif" % ( fileHeader )
    classifFile = open( classifFileName, "w" )

    fastaAllFileName = "%s.fa" % ( fileHeader )
    fastaAllFile = open( fastaAllFileName, "w" )

    setFileName = "%s.set" % ( fileHeader )
    setFile = open( setFileName, "w" )
    countSetID = 0

    nbSeq = len(elements)
    tick = 500.0
    interval = int( nbSeq / tick )
    seqTreated = 1

    if verbose > 0:
        print "classify the %i input sequences of project '%s'..." % ( nbSeq, project )
        sys.stdout.flush()

    # for each sequence
    for element in elements:

        name = element[0].replace("\\","\\\\")
        length = int(element[1])
        if verbose > 1:
            print "%s (%i bp)" % ( name, length )
            sys.stdout.flush()
        if verbose > 1:
            if tick < nbSeq:
                if ( seqTreated % interval ) == 0:
                    print "%4i / %4i" % ( seqTreated, nbSeq ); sys.stdout.flush()
                    
        # retrieve its features
        global db
        db = DbMySql()
        consensus = Consensus( name, length, config )
        consensus.search_TElib()
        consensus.search_TR()
        consensus.search_tail()
        consensus.search_SSR()
        consensus.search_ORF()
        consensus.search_HostGenes()
        consensus.search_TEprofiles()
        consensus.search_TEclass()
        db.close()

        # fill a 'set' table with the features
        countSetID = consensus.saveFeatures( countSetID, setFile )

        # classify it according to its features
        consensus.filter_SSR()
        consensus.filter_HostGenes()
        consensus.classify()
        if verbose > 2:
            consensus.showClassif()
            
        # save the classification in a tabulated file
        saveClassif( consensus, classifFile )

        # save the sequence in a fasta file with all the other sequences
        iDb = DbMySql()
        iTableSeqAdaptator = TableSeqAdaptator(iDb, "%s_seq" % project)
        bs = iTableSeqAdaptator.getBioseqFromHeader(consensus.name)
        iDb.close()
        saveFasta( consensus, bs, fastaAllFile )

        # save the sequence in a fasta file with the other seq having the same classification
        ordercomp = ""
        if consensus.classif["final"].order in ["LTR","LINE","TIR"]:
            ordercomp += consensus.classif["final"].order
            if consensus.classif["final"].completeness == "comp":
                ordercomp += "comp"
            else:
                ordercomp += "incomp"
        elif consensus.classif["final"].order in ["LARD","SINE","MITE","Helitron","Polinton"]:
            ordercomp += consensus.classif["final"].order
        elif consensus.classif["final"].category in ["HostGene","SSR","NoCat"]:
            ordercomp += consensus.classif["final"].category
        elif consensus.confused == True:
            ordercomp += "confused"
        else:
            consensus.classif["final"].show()
            sys.exit(1)
        faFileName = "%s_%s.fa" % ( project, ordercomp )
        if not os.path.exists( faFileName ):
            faFile = open( faFileName, "w" )
        else:
            faFile = open( faFileName, "a" )
        bs.write( faFile )
        faFile.close()

        seqTreated += 1

    if verbose > 0:
        print "classification done !"; sys.stdout.flush()

    classifFile.close()
    fastaAllFile.close()
    setFile.close()

    # load the results into 2 MySQL tables
    lCmds = []
    
    prg = "%s/bin/srptCreateTable.py" % os.environ["REPET_PATH"]

    cmd = prg
    cmd += " -f %s"  % classifFileName
    cmd += " -n %s_classif" % fileHeader
    cmd += " -t TEclassif"
    cmd += " -o"
    lCmds.append(cmd)

    cmd = prg
    cmd += " -f %s" % setFileName
    cmd += " -n %s_set" % fileHeader
    cmd += " -t set"
    cmd += " -o"
    lCmds.append(cmd)
    
    sectionName = "classif_consensus"
    queue = config.get(sectionName, "resources")
    cDir = os.getcwd()
    if config.get(sectionName, "tmpDir" ) != "":
        tmpDir = config.get(sectionName, "tmpDir")
    else:
        tmpDir = cDir
    
    groupid = "%s_ClassifConsensus" % project
    acronym = "createTable"
    iJobDb = RepetJob( cfgFileName=configFileName )
    cLauncher = Launcher( iJobDb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
    cLauncher.beginRun()
    cLauncher.job.jobname = acronym
    cmd_start = ""
    cmd_start += "os.system( \"ln -s %s/%s .\" )\n" % ( cDir, classifFileName )
    cmd_start += "os.system( \"ln -s %s/%s .\" )\n" % ( cDir, setFileName )
    for c in lCmds:
        cmd_start += "log = os.system( \""
        cmd_start += c
        cmd_start += "\" )\n"
    cLauncher.runSingleJob( cmd_start )
    cLauncher.endRun()
    if config.get(sectionName,"clean") == "yes":
        cLauncher.clean( acronym )
    iJobDb.close()

#------------------------------------------------------------------------------

def saveClassif( consensus , classifFile ):
    """
    Write the results of the classification for each input sequence.
    @param consensus: consensus
    @type consensus: Consensus object
    @param classifFile: 'annot' file allowing to export the results into a MySQL table
    @type classifFile: file handling
    """

    string = "%s\t" % ( consensus.name )
    string += "%i\t" % ( consensus.length )
    string += "%s\t" % ( consensus.strand )
    if consensus.confused == True:
        string += "confused\t"
    else:
        string += "ok\t"
    string += "%s\t" % ( consensus.classif["final"].category )
    string += "%s\t" % ( consensus.classif["final"].order )
    string += "%s\t"  %( consensus.classif["final"].superfam )
    string += "%s\t" % ( consensus.classif["final"].completeness )
    string += "%s\n" % ( consensus.classif["final"].comments )

    classifFile.write( string )

#------------------------------------------------------------------------------

def saveFasta( consensus, bs, outFile ):
    """
    Save the classified sequence into the output fasta file with its classification in the header.
    @param consensus: consensus
    @type consensus: Consensus object
    @param bs: L{Bioseq>pyRepet.seq.Bioseq} instance
    @type bs: L{Bioseq>pyRepet.seq.Bioseq}
    @param outFile: output fasta file
    @type outFile: file handling
    """

    sep = "|"

    newHeader = "name=%s" % ( bs.header )
    newHeader += "%s" % ( sep )
    newHeader += "category=%s" % ( consensus.classif["final"].category )
    newHeader += "%s" % ( sep )
    newHeader += "order=%s" % ( consensus.classif["final"].order )
    newHeader += "%s" % ( sep )
    newHeader += "superfam=%s" % ( consensus.classif["final"].superfam )
    newHeader += "%s" % ( sep )
    newHeader += "completeness=%s" % ( consensus.classif["final"].completeness )
    newHeader += "%s" % ( sep )
    if consensus.confused == True:
        newHeader += "confusedness=yes"
    else:
        newHeader += "confusedness=no"
    bs.header = newHeader

    bs.write( outFile )

#------------------------------------------------------------------------------

def rmvRedundancyAmongTwoBanks( query, subject, output, logFile, config ):
    """
    Remove the redundant sequences between queries and subjects.
    @param query: name of the queries (e.g. LTRincomp)
    @type query: string
    @param subject: name of the subjects (e.g. LTRcomp)
    @type subject: string
    @param output: part of the output file
    @type output: string
    @param logFile: log file recording the number of removed sequences
    @type logFile: file handling
    @param config: configuration file
    @type config: file handling
    """

    if verbose > 1:
        if query == subject:
            print "remove redundancy among " + project + "_" + query
            sys.stdout.flush()
        else:
            print "remove redundancy between " + project + "_" + query + " and " +\
                  project + "_" + subject
        sys.stdout.flush()

    if not os.path.exists( project + "_" + query + ".fa" ):
        if verbose > 1:
            print "WARNING: query file doesn't exist\n"
            sys.stdout.flush()
        return
    if not os.path.exists( project + "_" + subject + ".fa" ):
        if verbose > 1:
            print "WARNING: subject file doesn't exist\n"
            sys.stdout.flush()
        return

    sectionName = "classif_consensus"

    prg = "%s/bin/rmvRedundancy.py" % os.environ["REPET_PATH"]
    cmd = prg
    cmd += " -q %s_%s.fa" % ( project, query )
    cmd += " -s %s_%s.fa" % ( project, subject )
    cmd += " -o %s_%s.fa" % ( project, output )
    if config.get(sectionName, "redundancy_threshold_identity") != "":
        cmd += " -i %s" % config.get(sectionName, "redundancy_threshold_identity")
    if config.get(sectionName, "redundancy_threshold_coverage") != "":
        cmd += " -l %s" % config.get(sectionName, "redundancy_threshold_coverage")
    cmd += " -Q '%s'" % config.get(sectionName, "resources")
    cmd += " -C %s" % configFileName
    cmd += " -c"
    cmd += " -v %i" % ( verbose - 1 )

    pL.launch( prg, cmd )

#------------------------------------------------------------------------------

def updateAfterRmvRedundancy( file_1, file_2 ):
    """
    After having removed the redundancy in file_1, remove file_1 and rename file_2 into file_1.
    @param file_1: input file to remove
    @type file_1: string
    @param file_2: output file to rename
    @type file_2: string
    """
    if os.path.exists( file_1 ) and os.path.exists( file_2 ):
        os.remove( file_1 )
        os.rename( file_2, file_1 )
        
#------------------------------------------------------------------------------

def rmvRedundancyBasedOnClassif( lClassifNames ):
    """
    Remove the redundancy among sequences based on their classification.
    @param lClassifNames: list containing all the possible classification names (LTRcomp...)
    @type lClassifNames: list of strings
    """
    redunLogFileName = "%s_redundancy.txt" % ( project )
    if os.path.exists( redunLogFileName ):
        os.remove( redunLogFileName )
        
    if os.path.exists( "rmvRedundancy" ):
        shutil.rmtree( "rmvRedundancy" )
    os.mkdir( "rmvRedundancy" )
    os.chdir( "rmvRedundancy" )
    os.system( "ln -s ../%s ." % ( configFileName ) )
    
    # start by removing the redundancy among each classification type
    for classifName in lClassifNames:
        if os.path.exists( "../%s_%s.fa" % ( project, classifName ) ):
            os.system( "ln -s ../%s_%s.fa ." % ( project, classifName ) )
            rmvRedundancyAmongTwoBanks( classifName, classifName, classifName + "_uniq", redunLogFileName, config )
            
    # for the LTR, LINE and TIR, remove the redundancy order by order
    # (e.g. remove the LTRincomp contained in LTRcomp)
    for orderName in ["LTR","LINE","TIR"]:
        rmvRedundancyAmongTwoBanks( orderName+"incomp_uniq", orderName+"comp_uniq", orderName+"incomp_uniq2", redunLogFileName, config )
        updateAfterRmvRedundancy( project+"_"+orderName+"incomp_uniq.fa", project+"_"+orderName+"incomp_uniq2.fa" )

    # remove the redundancy among the LARD compare to the LTR
    rmvRedundancyAmongTwoBanks( "LARD_uniq", "LTRincomp_uniq", "LARD_uniq2", redunLogFileName, config )
    updateAfterRmvRedundancy( project+"_LARD_uniq.fa", project+"_LARD_uniq2.fa" )
    rmvRedundancyAmongTwoBanks( "LARD_uniq", "LTRcomp_uniq", "LARD_uniq2", redunLogFileName, config )
    updateAfterRmvRedundancy( project+"_LARD_uniq.fa", project+"_LARD_uniq2.fa" )

    # remove the redundancy among the SINE compare to the LINE
    rmvRedundancyAmongTwoBanks( "SINE_uniq", "LINEincomp_uniq", "SINE_uniq2", redunLogFileName, config )
    updateAfterRmvRedundancy( project+"_SINE_uniq.fa", project+"_SINE_uniq2.fa" )
    rmvRedundancyAmongTwoBanks( "SINE_uniq", "LINEcomp_uniq", "SINE_uniq2", redunLogFileName, config )
    updateAfterRmvRedundancy( project+"_SINE_uniq.fa", project+"_SINE_uniq2.fa" )

    # remove the redundancy among the MITE compare to the TIR
    rmvRedundancyAmongTwoBanks( "MITE_uniq", "TIRincomp_uniq", "MITE_uniq2", redunLogFileName, config )
    updateAfterRmvRedundancy( project+"_MITE_uniq.fa", project+"_MITE_uniq2.fa" )
    rmvRedundancyAmongTwoBanks( "MITE_uniq", "TIRcomp_uniq", "MITE_uniq2", redunLogFileName, config )
    updateAfterRmvRedundancy( project+"_MITE_uniq.fa", project+"_MITE_uniq2.fa" )

    # remove the redundancy for the "confused" and the "NoCat"
    for query in ["confused","NoCat"]:
        for subject in ["LTRcomp","LTRincomp","LARD","LINEcomp","LINEincomp","SINE","TIRcomp","TIRincomp","MITE","Helitron","Polinton"]:
            rmvRedundancyAmongTwoBanks( query+"_uniq", subject+"_uniq", query+"_uniq2", redunLogFileName, config )
            updateAfterRmvRedundancy( project+"_"+query+"_uniq.fa", project+"_"+query+"_uniq2.fa" )

    # write the non-redundant sequences in a fasta file
    if os.path.exists( project + "_uniq_TEclassifier.fa" ):
        os.remove( project + "_uniq_TEclassifier.fa" )
    for i in lClassifNames:
        if os.path.exists( "%s_%s_uniq.fa" % ( project, i ) ):
            log = os.system( "cat "+project+"_"+i+"_uniq.fa >> "+project+"_uniq_TEclassifier.fa" )
            if log != 0:
                message = "ERROR while concatenating the fasta files"
                logger.error( message )
                if verbose > 0: print message; sys.stdout.flush()
                sys.exit(1)
                
    os.chdir( ".." )
    if os.path.exists( "%s_uniq_TEclassifier.fa" % ( project ) ):
        os.remove( "%s_uniq_TEclassifier.fa" % ( project ) )
    os.system( "ln -s rmvRedundancy/%s_uniq_TEclassifier.fa ." % ( project ) )
    os.system( "find . -name \"*.raw\" -exec rm {} \;" )
    os.system( "find . -name \"*.seq_treated\" -exec rm {} \;" )
    os.system( "find . -name \"*_cut*\" -exec rm {} \;" )
    os.system( "find . -name \"*.Nstretch.map\" -exec rm {} \;" )

#------------------------------------------------------------------------------

def main():
    """
    This program looks for TE features on the input sequences and classify them according to their features.
    A step of redundancy removal is also performed.
    """
    
    global project
    project = ""
    global configFileName
    configFileName = ""
    global inFileName
    inFileName = ""
    global step
    step = ""
    global verbose
    verbose = 0
    global newHmmer
    newHmmer = False

    try:
        opts, args = getopt.getopt( sys.argv[1:], "hp:c:i:s:nv:" )
    except getopt.GetoptError, err:
        print str(err)
        help()
        sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-p":
            project = a
        elif o == "-c":
            configFileName = a
        elif o == "-i":
            inFileName = a
        elif o == "-s":
            step = a
        elif o == "-n":
            newHmmer = True
        elif o == "-v":
            verbose = int(a)
            
    checkAttributes()
    
    global config
    config = ConfigParser.ConfigParser()
    config.readfp( open(configFileName) )
    setup_env( config )
    
    if step == "1":
        try:
            CheckerUtils.checkOptionInSectionInConfigFile( config, "detect_features", "clean" )
        except NoOptionError:
            print "ERROR: the option 'clean' must be define in section 'detect_features' in your config file"
            sys.exit(1)
    elif step == "2":
        try:
            CheckerUtils.checkOptionInSectionInConfigFile( config, "classif_consensus", "clean" )
        except NoOptionError:
            print "ERROR: the option 'clean' must be define in section 'classif_consensus' in your config file"
            sys.exit(1)
            
    global logger
    global logFileName
    logFileName = "%s_TEclassifier_s%s.log" % ( project, step )
    if verbose > 0:
        logger = LoggerFactory.createLogger( logFileName, logging.DEBUG, "%(asctime)s %(levelname)s: %(message)s" )
    else:
        logger = LoggerFactory.createLogger( logFileName, logging.INFO, "%(asctime)s %(levelname)s: %(message)s" )
    message = "START %s" % ( sys.argv[0].split("/")[-1] )
    logger.info( message )
    if verbose > 0: print message; sys.stdout.flush()
    
    global pL
    pL = programLauncher()
    
    global queue
    queue = ""
    global sectionName
    sectionName = ""
    
    #--------------------------------------------------------------------------

    # As a first step, detect TE features on the consensus
    # ONLY WITH A QUEUE NAME
    if step == "1":
        
        sectionName = "detect_features"
        if verbose > 0:
            message = "step 1: detect TE features on the input sequences"
            logger.info( message )
            if verbose > 0: print message; sys.stdout.flush()
            
        if config.get(sectionName, "TE_BLRtx") == "yes":
            if not os.path.exists( config.get(sectionName,"TE_nucl_bank") ):
                print "ERROR: nucleotide bank for tblastx is missing"
                sys.exit(1)
                
        if config.get(sectionName, "TE_BLRx") == "yes":
            if not os.path.exists( config.get(sectionName,"TE_prot_bank") ):
                print "ERROR: amino-acid bank for blastx is missing"
                sys.exit(1)
                
        if config.get(sectionName, "HG_BLRn") == "yes":
            if not os.path.exists( config.get(sectionName,"HG_nucl_bank") ):
                print "ERROR: nucleotide bank of host's genes is missing"
                sys.exit(1)
                
        if config.get(sectionName, "TE_HMMER") == "yes":
            if not os.path.exists( config.get(sectionName,"TE_HMM_profiles") ):
                print "ERROR: bank of TE HMM profiles is missing"
                sys.exit(1)
                
        if config.get(sectionName, "rDNA_BLRn") == "yes":
            if not os.path.exists( config.get(sectionName,"rDNA_bank") ):
                print "ERROR: nucleotide bank of rRNA genes is missing"
                sys.exit(1)
                
        if config.get(sectionName, "TE_BLRtx") == "yes" \
        or config.get(sectionName, "TE_BLRx") == "yes" \
        or config.get(sectionName, "HG_BLRn") == "yes" \
        or config.get(sectionName, "TE_BLRn") == "yes" \
        or config.get(sectionName, "rDNA_BLRn") == "yes":
            if config.get(sectionName, "wublast") == "yes":
                if not (CheckerUtils.isExecutableInUserPath("wu-blastall") or CheckerUtils.isExecutableInUserPath("wu-formatdb")):
                    print "ERROR: wu-blastall and wu-formatdb must be in your path"
                    sys.exit(1)
            else:
                if not (CheckerUtils.isExecutableInUserPath("blastall") or CheckerUtils.isExecutableInUserPath("formatdb")):
                    print "ERROR: 'blastall' and 'formatdb' from NCBI must be in your path"
                    sys.exit(1)
                    
        if config.get(sectionName, "tand_rep") == "yes" \
        and not CheckerUtils.isExecutableInUserPath("trf"):
            print "ERROR: 'trf' must be in your path"
            sys.exit(1)
            
        if config.get(sectionName, "TE_HMMER") == "yes" \
        and not CheckerUtils.isExecutableInUserPath("hmmpfam"):
            print "ERROR: 'hmmpfam' must be in your path"
            sys.exit(1)
            
        if config.get(sectionName, "TE_HMMER") == "yes" \
        and newHmmer:
            if not CheckerUtils.isExecutableInUserPath("hmmscan"):
                print "ERROR: 'hmmscan' must be in your path"
                sys.exit(1)
            if not CheckerUtils.isExecutableInUserPath("hmmpress"):
                print "ERROR: 'hmmpress' must be in your path"
                sys.exit(1)

        if CheckerUtils.isOptionInSectionInConfig( config, sectionName, "TEclass" ) \
        and config.get(sectionName, "TEclass") == "yes" \
        and not CheckerUtils.isExecutableInUserPath("test_consensi_2.1.pl"):
            print "ERROR: 'test_consensi_2.1.pl' must be in your path"
            sys.exit(1)
            
        FileUtils.fromWindowsToUnixEof( inFileName )
        inFileHandler = open(inFileName, "r")
        separator = "\n"
        try:
            CheckerUtils.checkHeaders( inFileHandler )
        except CheckerException, e:
            print "Wrong headers are:"
            print separator.join( e.messages )
            print "Authorized characters are: a-z A-Z 0-9 - . : _\n"
            inFileHandler.close()
            sys.exit(1)
        inFileHandler.close()
        
        createSeqTable( inFileName )
        
        message = "split the sequences in batches"
        logger.info( message )
        if verbose > 0:
            print message
            sys.stdout.flush()
        maxNbJobs = 1500
        minSeqPerJob = 2
        nbSeq = FastaUtils.dbSize( inFileName )
        message = "nb of sequences: %i" % ( nbSeq )
        logger.info( message )
        if verbose > 0:
            print message
            sys.stdout.flush()
        seqPerJob = nbSeq / float(maxNbJobs)
        
        queue = config.get(sectionName, "resources")
        cDir = os.getcwd()
        if config.get(sectionName, "tmpDir" ) != "":
            tmpDir = config.get(sectionName, "tmpDir")
        else:
            tmpDir = cDir
            
        prg = "%s/bin/dbSplit.py" % os.environ["REPET_PATH"]
        cmd = prg
        cmd += " -i %s" % inFileName
        if seqPerJob <= 1.0:
            cmd += " -n %i" % minSeqPerJob
        else:
            cmd += " -n %i" % ( seqPerJob + 1 )
        cmd += " -d"
        
        groupid = "%s_TEclassifier_DetectFeatures_dbSplit" % project
        acronym = "dbSplit"
        iJobDb = RepetJob( cfgFileName = configFileName )
        cLauncher = Launcher( iJobDb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
        cLauncher.beginRun()
        cLauncher.job.jobname = acronym
        cmd_start = ""
        cmd_start += "os.system( \"ln -s %s/%s .\" )\n" % ( cDir, inFileName )
        cmd_start += "log = os.system( \""
        cmd_start += cmd
        cmd_start += "\" )\n"
        cmd_finish = "if not os.path.exists( \"%s/batches\" ):\n" % cDir
        cmd_finish += "\tos.system( \"mv batches %s/.\" )\n" % cDir
        cLauncher.runSingleJob( cmd_start, cmd_finish )
        cLauncher.endRun()
        if config.get(sectionName,"clean") == "yes":
            cLauncher.clean( acronym )
        iJobDb.close()
        
        message = "launch the programs on each batch"
        logger.info( message )
        if verbose > 0:
            print message
            sys.stdout.flush()

        global cL
        groupid = "%s_TEclassifier_detectFeatures" % project
        acronym = "detectFeatures"
        iJobDb = RepetJob( cfgFileName = configFileName )
        cL = Launcher( iJobDb, "batches", "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
        cL.beginRun()
        lFiles = glob.glob( "%s/batches/*" % os.getcwd() )
        count = 0
        for inFileName in lFiles:
            count += 1
            cmd_start, cmd_finish = detectFeatures( inFileName, count, cDir, tmpDir )
            cL.runSingleJob( cmd_start, cmd_finish )
        cL.endRun()
        if config.get(sectionName,"clean") == "yes":
            cL.clean( "%s_*" % acronym)
        iJobDb.close()
        if os.path.exists( "formatdb.log" ):
            os.remove( "formatdb.log" )
        if os.path.exists( "last_time_stamp.log" ):
            os.remove( "last_time_stamp.log" )
        if config.get(sectionName,"TE_HMMER") == "yes" and newHmmer:
            bankProfiles = config.get(sectionName,"TE_HMM_profiles")
            if os.path.exists( "%s.h3f" % bankProfiles ):
                os.remove( "%s.h3f" % bankProfiles )
            if os.path.exists( "%s.h3i" % bankProfiles ):
                os.remove( "%s.h3i" % bankProfiles )
            if os.path.exists( "%s.h3m" % bankProfiles ):
                os.remove( "%s.h3m" % bankProfiles )
            if os.path.exists( "%s.h3p" % bankProfiles ):
                os.remove( "%s.h3p" % bankProfiles )

        message = "collect the results and load them into tables"
        logger.info( message )
        if verbose > 0:
            print message
            sys.stdout.flush()
        collectResults()
        
        if config.get(sectionName,"clean") == "yes":
            os.system( "rm -rf batches" )
        if checkFeatureTables() == 0:
            message = "ERROR: no table recording TE features exists"
            logger.error( message )
            if verbose > 0:
                print message
                sys.stdout.flush()
            sys.exit(1)
            
    #--------------------------------------------------------------------------
    
    # As a second step, begin by classifying the consensus based on their features
    if step == "2":
        
        sectionName = "classif_consensus"
        message = "step 2: classify the input sequences based on their TE features"
        logger.info( message )
        if verbose > 0:
            print message
            sys.stdout.flush()
        
        lClassifNames = ["LTRcomp","LTRincomp","LARD","LINEcomp","LINEincomp",
                         "SINE","TIRcomp","TIRincomp","MITE","Helitron","Polinton",
                         "SSR","confused","NoCat","HostGene"]
        
        if checkFeatureTables() == 0:
            message = "ERROR: no table recording TE features exists"
            logger.error( message )
            if verbose > 0:
                print message
                sys.stdout.flush()
            sys.exit(1)
        
        iDb = DbMySql()
        iDb.execute("SELECT accession,length FROM %s_seq;" % project)
        elements = iDb.fetchall()
        iDb.close()
        
        keepClassifParamInLog()
        
        #TODO: how to launch classifyConsensus method with runSingleJob ?
        classifyConsensus(elements, config, "", lClassifNames)
        
        queue = config.get(sectionName, "resources")
        cDir = os.getcwd()
        if config.get(sectionName,"tmpDir" ) != "":
            tmpDir = config.get(sectionName,"tmpDir")
        else:
            tmpDir = cDir
        
        prg = "%s/bin/giveInfoClassif.py" % os.environ["REPET_PATH"]
        cmd = prg
        cmd += " -i %s_TEclassifier.classif" % project
        cmd += " -v %i" % (verbose - 1)
        
        groupid = "%s_ClassifConsensus_giveInfoClassif" % project
        acronym = "giveInfoClassif"
        iJobDb = RepetJob(cfgFileName = configFileName)
        cLauncher = Launcher(iJobDb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym)
        cLauncher.beginRun()
        cLauncher.job.jobname = acronym
        cmd_start = ""
        cmd_start += "os.system( \"ln -s %s/%s_TEclassifier.classif .\" )\n" % (cDir, project)
        cmd_start += "log = os.system( \""
        cmd_start += cmd
        cmd_start += "\" )\n"
        cmd_finish = "if not os.path.exists( \"%s/%s_TEclassifier.classif_stats.txt\" ):\n" % (cDir, project)
        cmd_finish += "\tos.system( \"mv %s_TEclassifier.classif_stats.txt %s/.\" )\n" % (project, cDir)
        cLauncher.runSingleJob(cmd_start, cmd_finish)
        cLauncher.endRun()
        if config.get(sectionName, "clean") == "yes":
            cLauncher.clean(acronym)
        iJobDb.close()
        
        message = "start the redundancy removal procedure"
        logger.info(message)
        if verbose > 0:
            print message
            sys.stdout.flush()
        
        rmvRedundancyBasedOnClassif(lClassifNames)
        
        message = "the redundancy removal procedure is finished"
        logger.info( message )
        if verbose > 0:
            print message
            sys.stdout.flush()
        
        uniqDB = BioseqDB( "%s_uniq_TEclassifier.fa" % project )
        logger.info( "nb of classified, non-redundant sequences: %i" % uniqDB.getSize() )
    
        prg = "%s/bin/srptGetClassifUniq.py" % os.environ["REPET_PATH"]
        cmd = prg
        cmd += " -p %s" % project
        cmd += " -v %i" % verbose
        
        groupid = "%s_ClassifConsensus_srptGetClassifUniq" % project
        acronym = "srptGetClassifUniq"
        iJobDb = RepetJob(cfgFileName = configFileName)
        cLauncher = Launcher(iJobDb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym)
        cLauncher.beginRun()
        cLauncher.job.jobname = acronym
        cmd_start = ""
        cmd_start += "os.system( \"ln -s %s/%s_uniq_TEclassifier.fa .\" )\n" % (cDir, project)
        cmd_start += "os.system( \"ln -s %s/%s_TEclassifier.classif .\" )\n" % (cDir, project)
        cmd_start += "log = os.system( \""
        cmd_start += cmd
        cmd_start += "\" )\n"
        cmd_finish = "if not os.path.exists( \"%s/%s_uniq_TEclassifier.classif\" ):\n" % (cDir, project)
        cmd_finish += "\tos.system( \"mv %s_uniq_TEclassifier.classif %s/.\" )\n" % (project, cDir)
        cLauncher.runSingleJob(cmd_start, cmd_finish)
        cLauncher.endRun()
        if config.get(sectionName,"clean") == "yes":
            cLauncher.clean(acronym)
        iJobDb.close()
        
        prg = "%s/bin/giveInfoClassif.py" % os.environ["REPET_PATH"]
        cmd = prg
        cmd += " -i %s_uniq_TEclassifier.classif" % project
        cmd += " -v %i" % verbose
        
        groupid = "%s_ClassifConsensus_giveInfoClassif_uniq" % project
        acronym = "giveInfoClassif_uniq"
        iJobDb = RepetJob(cfgFileName = configFileName)
        cLauncher = Launcher(iJobDb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym)
        cLauncher.beginRun()
        cLauncher.job.jobname = acronym
        cmd_start = ""
        cmd_start += "os.system( \"ln -s %s/%s_uniq_TEclassifier.classif .\" )\n" % (cDir, project)
        cmd_start += "log = os.system( \""
        cmd_start += cmd
        cmd_start += "\" )\n"
        cmd_finish = "if not os.path.exists( \"%s/%s_uniq_TEclassifier.classif_stats.txt\" ):\n" % (cDir, project)
        cmd_finish += "\tos.system( \"mv %s_uniq_TEclassifier.classif_stats.txt %s/.\" )\n" % (project, cDir)
        cLauncher.runSingleJob(cmd_start, cmd_finish)
        cLauncher.endRun()
        if config.get(sectionName,"clean") == "yes":
            cLauncher.clean(acronym)
        iJobDb.close()

    #--------------------------------------------------------------------------
        
    if step == "2b":
        message = "step 2: classify the input sequences based on their TE features by using the multi-agent classification system"
        logger.info(message)
        if verbose > 0:
            print message
            sys.stdout.flush()
            
        if checkFeatureTables() == 0:
            message = "ERROR: no table recording TE features exists"
            logger.error( message )
            if verbose > 0:
                print message
                sys.stdout.flush()
            sys.exit(1)
            
        sectionName = "classif_consensus"
        queue = config.get(sectionName, "resources")
        cDir = os.getcwd()
        if config.get(sectionName, "tmpDir") != "":
            tmpDir = config.get(sectionName, "tmpDir")
        else:
            tmpDir = cDir
            
        repbase_nt = config.get("detect_features", "TE_nucl_bank")
        if config.get("detect_features", "TE_BLRn") == "yes":
            if not os.path.exists( repbase_nt ):
                sys.stderr.write("ERROR: can't find file '%s'\n" % repbase_nt)
                sys.exit(1)
        
        #insertion profiles bank in DB
        if config.get("detect_features","TE_HMMER") == "yes":
            profilesBank = config.get("detect_features", "te_hmm_profiles")
            if not os.path.exists(profilesBank):
                sys.stderr.write("ERROR: can't find file '%s'\n" % profilesBank)
                sys.exit(1)
            prg = "%s/bin/srptInsertProfilesBankInDBAndLaunchPASTEC.py" % os.environ["REPET_PATH"]
            cmd = prg
            cmd += " -p %s" % project
            cmd += " -i %s" % inFileName
            cmd += " -C %s" % configFileName
            cmd += " -S 1"
            cmd += " -v %i" % verbose
            
            groupid = "%s_ClassifConsensus_insertProfilesBankInDB" % project
            acronym = "srptInsertProfilesBankInDBAndLaunchPASTEC"
            iJobDb = RepetJob(cfgFileName = configFileName)
            cLauncher = Launcher(iJobDb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym)
            cLauncher.beginRun()
            cLauncher.job.jobname = acronym
            cmd_start = ""
            cmd_start += "os.system( \"ln -s %s/%s .\" )\n" % (cDir, profilesBank)
            cmd_start += "os.system( \"cp %s/%s .\" )\n" % (cDir, configFileName)
            cmd_start += "log = os.system( \""
            cmd_start += cmd
            cmd_start += "\" )\n"
            cLauncher.runSingleJob(cmd_start)
            cLauncher.endRun()
            if config.get(sectionName, "clean") == "yes":
                cLauncher.clean(acronym)
            iJobDb.close()
                
        #split consensus file
        prg = "%s/bin/dbSplit.py" % os.environ["REPET_PATH"]
        cmd = prg
        cmd += " -i %s" % inFileName
        cmd += " -n 100"
        cmd += " -d"
        
        groupid = "%s_TEclassifier_ClassifyConsensus_dbSplit" % project
        acronym = "dbSplit"
        iJobDb = RepetJob(cfgFileName = configFileName)
        cLauncher = Launcher(iJobDb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym)
        cLauncher.beginRun()
        cLauncher.job.jobname = acronym
        cmd_start = ""
        cmd_start += "os.system( \"ln -s %s/%s .\" )\n" % (cDir, inFileName)
        cmd_start += "log = os.system( \""
        cmd_start += cmd
        cmd_start += "\" )\n"
        cmd_finish = "if not os.path.exists( \"%s/batches\" ):\n" % cDir
        cmd_finish += "\tos.system( \"mv batches %s/.\" )\n" % cDir
        cLauncher.runSingleJob(cmd_start, cmd_finish)
        cLauncher.endRun()
        if config.get(sectionName, "clean") == "yes":
            cLauncher.clean( acronym )
        iJobDb.close()
        
        #launch PASTEC on each batch
        message = "launch PASTEC on each batch"
        logger.info( message )
        if verbose > 0:
            print message
            sys.stdout.flush()
            
        groupid = "%s_ClassifConsensus_launchSuperAgentLive" % project
        iJobDb = RepetJob(cfgFileName = configFileName)
        cLauncher = Launcher( iJobDb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, "SuperAgentLive" )
        cLauncher.beginRun()
        lFiles = glob.glob("%s/batches/*" % cDir)
        if len(lFiles) == 0:
            print "ERROR: directory 'batches' is empty"
            sys.exit(1)
        count = 0
        for file in lFiles:
            prg = "%s/bin/srptInsertProfilesBankInDBAndLaunchPASTEC.py" % os.environ["REPET_PATH"]
            cmd = prg
            cmd += " -p %s" % project
            cmd += " -i %s" % file
            cmd += " -C %s" % configFileName
            cmd += " -S 2"
            cmd += " -v %i" % verbose
            
            count += 1
            cLauncher.acronyme = "SuperAgentLive_%i" % count
            cLauncher.job.jobname = cLauncher.acronyme
            cmd_start = ""
            cmd_start += "os.system( \"ln -s %s/batches/%s .\" )\n" % (cDir, file)
            if config.get("detect_features","TE_BLRn") == "yes":
                cmd_start += "os.system( \"ln -s %s/%s .\" )\n" % (cDir, repbase_nt)
            cmd_start += "os.system( \"cp %s/%s .\" )\n" % (cDir, configFileName)
            cmd_start += "log = os.system( \""
            cmd_start += cmd
            cmd_start += "\" )\n"
            cmd_finish = ""
            cmd_finish += "if not os.path.exists( \"%s/%sTEclassifier.classif\" ):\n" % (cDir, project)
            cmd_finish += "\tos.system( \"mv %sTEclassifier.classif %s/%sTEclassifier.classif_%i\" )\n" % (project, cDir, project, count)
            cLauncher.runSingleJob(cmd_start, cmd_finish)
        cLauncher.acronyme = "SuperAgentLive"
        cLauncher.endRun()
        if config.get(sectionName, "clean") == "yes":
            cLauncher.clean("SuperAgentLive_*")
        iJobDb.close()
            
        FileUtils.catFilesByPattern("%sTEclassifier.classif_*" % project, "%sTEclassifier.classif" % project)
        FileUtils.removeFilesByPattern("%sTEclassifier.classif_*" % project)

    #--------------------------------------------------------------------------
        
    message = "END %s" % ( sys.argv[0].split("/")[-1] )
    logger.info( message )
    if verbose > 0:
        print message
        sys.stdout.flush()
    
    return 0

if __name__ == "__main__":
    main()
