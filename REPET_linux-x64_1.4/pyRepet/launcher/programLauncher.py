import os
import sys

if not os.environ.has_key("REPET_PATH"):
    print "ERROR: no environment variable REPET_PATH"
    sys.exit(1)
sys.path.append( os.environ["REPET_PATH"] )

from pyRepet.seq.fastaDB import *
from pyRepet.util.file.FileUtils import FileUtils
from pyRepet.seq.BioseqUtils import BioseqUtils
from pyRepetUnit.commons.checker.CheckerUtils import CheckerUtils


class programLauncher( object ):

    #--------------------------------------------------------------------------

    def __init__( self, inFileName="", outFileName = "" ):

            self.inFileName = inFileName
            self._OutputFile = outFileName
            self.fileUtils = FileUtils()

    #--------------------------------------------------------------------------

    def reset( self, inFileName ):

        self.inFileName = inFileName
        
     #--------------------------------------------------------------------------   
         
    def setOutputFileName( self, outFileName ):
            
        self._OutputFile = outFileName        
    
    #-------------------------------------------------------------------------- 
        
    def _checkFileExistsAndNotEmpty(self, fileName):
        
        if self.fileUtils.isRessourceExists(fileName) and not self.fileUtils.isFileEmpty(fileName):
            return 1
        return 0

    #--------------------------------------------------------------------------

    def launch( self, prg, cmd, verbose=0 ):

        # slowly switch from yes/no to 0/1/2/...
        if verbose == "yes":
            verbose = 1
        if verbose == "no":
            verbose = 0

        if verbose > 0:
            print "beginning of %s" % ( prg ); sys.stdout.flush()

        log = os.system( cmd )

        if log == 0:
            if verbose > 0:
                print "%s finished successfully" % ( prg ); sys.stdout.flush()
            return 0

        else:
            print "*** Error: %s returned %i" % ( prg, log )
            print "time: %s" % ( time.strftime("%Y-%m-%d %H:%M:%S") )
            sys.exit(1)

    #--------------------------------------------------------------------------

    def launchBlaster( self, subjectBankName="", allByAll="no", blastVersion="NCBI", blastAlgo="blastn", blastOpt="", cutLgth="50000", cutOver="100", cutWord="11", cutExt="_cut", sensitiv="0", evalFilter="1e-10", idFilter="0", lgthFilter="20", outPrefix="", reRunAll="no", prepareOnly="no", run="yes", verbose="no" ):

        prg = os.environ["REPET_PATH"] + "/bin/blaster"
        cmd = prg
        cmd += " -q " + self.inFileName
        if subjectBankName != "":
            cmd += " -s " + subjectBankName
        if allByAll == "yes":
            cmd += " -a"
        if blastVersion != "NCBI":
            cmd += " -W"
        if blastAlgo != "blastn":
            cmd += " -n " + blastAlgo
        if blastOpt != "":
            cmd += " -p " + blastOpt
        if cutLgth != "50000":
            cmd += " -l " + cutLgth
        if cutOver != "100":
            cmd += " -o " + cutOver
        if cutWord != "11":
            cmd += " -w " + str(cutWord)
        if cutExt != "_cut":
            cmd += " -e " + cutExt
        if sensitiv != "0":
            cmd += " -S " + sensitiv
        if evalFilter != "1e-10":
            cmd += " -E " + evalFilter
        if idFilter != "0":
            cmd += " -I " + idFilter
        if lgthFilter != "20":
            cmd += " -L " + str(lgthFilter)
        if outPrefix != "":
            cmd += " -B " + outPrefix
        if reRunAll != "no":
            cmd += " -r"
        if prepareOnly != "no":
            cmd += " -P"
        if verbose == "yes":
            print "launch: %s" % ( cmd ); sys.stdout.flush()

        if run == "yes":
            return self.launch( prg, cmd, verbose )

        elif run == "no":
            return cmd

    #--------------------------------------------------------------------------

    def launchGrouper( self, matchFileName, subjectBankName="", joinMatch="no", idTolerance="2", gapPenalty="0.05", distPenalty="0.2", authOver="20", evalFilter="1e-10", idFilter="0", lgthFilter="20", outPrefix="", covConnectGrp="100", rmvGrp="no", covGrp="0.95", grpSizeFilter="1", run="yes", verbose="no" ):

        prg = os.environ["REPET_PATH"] + "/bin/grouper"
        cmd = prg
        cmd += " -m " + matchFileName
        cmd += " -q " + self.inFileName
        if subjectBankName != "":
            cmd += " -s " + subjectBankName
        if joinMatch != "no":
            cmd += " -j"
        if idTolerance != "2":
            cmd += " -i " + idTolerance
        if gapPenalty != "0.05":
            cmd += " -g " + gapPenalty
        if distPenalty != "0.2":
            cmd += " -d " + distPenalty
        if authOver != "20":
            cmd += " -c " + authOver
        if evalFilter != "1e-10":
            cmd += " -E " + evalFilter
        if idFilter != "0":
            cmd += " -I " + idFilter
        if lgthFilter != "20":
            cmd += " -L " + lgthFilter
        if outPrefix != "":
            cmd += " -B " + outPrefix
        if covConnectGrp != "100":
            cmd += " -G " + covConnectGrp
        if rmvGrp != "no":
            cmd += " -X " + rmvGrp
        if covGrp != "0.95":
            cmd += " -C " + covGrp
        if grpSizeFilter != "1":
            cmd += " -Z " + grpSizeFilter

        if verbose == "yes":
            print "launch: %s" % ( cmd ); sys.stdout.flush()

        if run == "yes":
            return self.launch( prg, cmd, verbose )

        elif run == "no":
            return cmd

    #--------------------------------------------------------------------------

    def launchMatcher( self, queryBankName="", subjectBankName="", joinMatch="no", idTolerance="2", gapPenalty="0.05", distPenalty="0.2", authOver="20", evalFilter="1e-10", idFilter="0", lgthFilter="20", outPrefix="", keepAllConflictSbj=False, run="yes", verbose="no" ):

        prg = os.environ["REPET_PATH"] + "/bin/matcher"
        cmd = prg
        cmd += " -m " + self.inFileName
        if queryBankName != "":
            cmd += " -q " + queryBankName
        if subjectBankName != "":
            cmd += " -s " + subjectBankName
        if joinMatch != "no":
            cmd += " -j"
        if idTolerance != "2":
            cmd += " -i " + idTolerance
        if gapPenalty != "0.05":
            cmd += " -g " + gapPenalty
        if distPenalty != "0.2":
            cmd += " -d " + distPenalty
        if authOver != "20":
            cmd += " -c " + authOver
        if evalFilter != "1e-10":
            cmd += " -E " + evalFilter
        if idFilter != "0":
            cmd += " -I " + idFilter
        if lgthFilter != "20":
            cmd += " -L " + lgthFilter
        if outPrefix != "":
            cmd += " -B " + outPrefix
        if keepAllConflictSbj == True:
            cmd += " -a"

        if verbose == "yes":
            print "launch: %s" % ( cmd ); sys.stdout.flush()

        if run == "yes":
            return self.launch( prg, cmd, verbose )

        elif run == "no":
            return cmd

    #--------------------------------------------------------------------------

    def launchCutterDB( self, length="50000", overlap="100", wordN="11", run="yes", verbose=0 ):

        # slowly switch from yes/no to 0/1/2/...
        if verbose == "yes":
            verbose = 1
        if verbose == "no":
            verbose = 0

        prg = os.environ["REPET_PATH"] + "/bin/cutterDB"
        cmd = prg
        cmd += " -l " + length
        cmd += " -o " + overlap
        cmd += " -w " + wordN
        cmd += " " + self.inFileName

        if verbose > 0:
            print "launch: %s" % ( cmd ); sys.stdout.flush()

        if run == "yes":
            return self.launch( prg, cmd, verbose-1 )

        elif run == "no":
            return cmd

    #--------------------------------------------------------------------------

    def launchMap2db( self, faFileName, merge=False, flankSize="0", run="yes", verbose="no" ):

        prg = os.environ["REPET_PATH"] + "/bin/map2db"
        cmd = prg
        if merge == True:
            cmd += " -m"
        cmd += " -s %s" % ( flankSize )
        cmd += " %s" % ( self.inFileName )
        cmd += " %s" % ( faFileName )

        if verbose == "yes":
            print "launch: %s" % ( cmd ); sys.stdout.flush()

        if run == "yes":
            return self.launch( prg, cmd, verbose )

        elif run == "no":
            return cmd

    #--------------------------------------------------------------------------

    def launchTRsearch( self, run="yes", verbose="no" ):

        prg = os.environ["REPET_PATH"] + "/bin/TRsearch"
        cmd = prg
        cmd += " " + self.inFileName

        if verbose == "yes":
            print "launch: %s" % ( cmd ); sys.stdout.flush()

        if run == "yes":
            return self.launch( prg, cmd, verbose )

        elif run == "no":
            return cmd

    #--------------------------------------------------------------------------

    def launchPolyAtail( self, run="yes", verbose="no" ):

        prg = os.environ["REPET_PATH"] + "/bin/polyAtail"
        cmd = prg
        cmd += " " + self.inFileName

        if verbose == "yes":
            print "launch: %s" % ( cmd ); sys.stdout.flush()

        if run == "yes":
            return self.launch( prg, cmd, verbose )

        elif run == "no":
            return cmd

    #--------------------------------------------------------------------------

    def launchPals( self, subjectBankName="", selfAlign="yes", out="stdout", lgthFilter="400", idFilter="94", run="yes", verbose="no" ):

        prg = "pals"
        cmd = prg
        if subjectBankName == "" and selfAlign == "yes":
            cmd += " -self " + self.inFileName
        elif subjectBankName != "" and selfAlign != "yes":
            cmd += " -target " + subjectBankName
            cmd += " -query " + self.inFileName
        if out != "stdout":
            cmd += " -out " + out
        if lgthFilter != "400":
            cmd += " -length " + lgthFilter
        if idFilter != "94":
            cmd += " -pctid " + idFilter

        if verbose == "yes":
            print "launch: %s" % ( cmd ); sys.stdout.flush()

        if run == "yes":
            return self.launch( prg, cmd, verbose )

        elif run == "no":
            return cmd

    #--------------------------------------------------------------------------

    def launchMap( self, outFileName, gapSize="50", mismatch="-8", gapOpen="16", gapExtend="4", run="yes", verbose="no" ):

        print "DEPRECATED"

        prg = os.environ["REPET_PATH"] + "/bin/rpt_map"
        cmd = prg
        cmd += " " + self.inFileName
        cmd += " " + gapSize
        cmd += " " + mismatch
        cmd += " " + gapOpen
        cmd += " " + gapExtend
        cmd += " > " + outFileName

        if verbose == "yes":
            print "launch: %s" % ( cmd ); sys.stdout.flush()

        if run == "yes":
            return self.launch( prg, cmd, verbose )

        elif run == "no":
            return cmd
    #--------------------------------------------------------------------------

    def launchRefalign( self, outFileName, gapSize="10", match="10", mismatch="-8", gapOpen="16", gapExtend="4", refseqName="", run="yes", verbose="no" ):

        refFileName=self.inFileName + ".ref"
        cpyFileName=self.inFileName + ".cpy"
        
        file_db=open(self.inFileName)
        file_ref=open(refFileName,"w")
        file_cpy=open(cpyFileName,"w")
        
        numseq=0
        while 1:
            seq=Bioseq()
            seq.read(file_db)
            if seq.sequence==None:
                break
            numseq+=1
            if numseq==1:
                seq.write(file_ref)
            else:
                seq.write(file_cpy)
        file_db.close()
        file_ref.close()
        file_cpy.close()
        
        if numseq > 1:
            prg = os.environ["REPET_PATH"] + "/bin/refalign"
            cmd = prg
            cmd += " " + refFileName
            cmd += " " + cpyFileName
            cmd += " -m " + match
            cmd += " -l " + gapSize
            cmd += " -d " + mismatch
            cmd += " -g " + gapOpen
            cmd += " -e " + gapExtend
            
            cmd += " ; " 
            
            cmd += os.environ["REPET_PATH"] + "/bin/refalign2fasta.py"
            cmd += " -i " + cpyFileName + ".aligner"
            if refseqName != "":
                cmd += " -r %s" % ( refseqName )
            cmd += " -g d"
            cmd += " -o " + outFileName
            if verbose == "yes":
                cmd += " -v 1"
                
            cmd += " ; " 
           
            cmd += "rm -f "+refFileName + " " + cpyFileName + " " + cpyFileName + ".aligner " + cpyFileName + ".oriented " + cpyFileName + ".refalign.stat"
        else:
            prg = cmd = "echo empty"
            
        if verbose == "yes":
            print "launch: %s" % ( cmd ); sys.stdout.flush()

        if run == "yes":
            return self.launch( prg, cmd, verbose )

        elif run == "no":
            return cmd

    #--------------------------------------------------------------------------

    def launchMafft( self, outFileName, run="yes", verbose=0 ):

        print "DEPRECATED"

        prg = "mafft"
        cmd = prg
        cmd += " --auto"
        if verbose == "no" or verbose == 0:
            cmd += " --quiet"
        cmd += " " + self.inFileName
        cmd += " > " + outFileName

        if verbose == "yes" or verbose > 0:
            print "launch: %s" % ( cmd ); sys.stdout.flush()

        if run == "yes":
            return self.launch( prg, cmd, verbose )

        elif run == "no":
            return cmd

    #--------------------------------------------------------------------------

    def launchMuscle( self, outFileName, run="yes", verbose="no" ):

        prg = "muscle"
        cmd = prg
        cmd += " -in " + self.inFileName
        cmd += " -out " + outFileName

        if verbose == "yes":
            print "launch: %s" % ( cmd ); sys.stdout.flush()

        if run == "yes":
            return self.launch( prg, cmd, verbose )

        elif run == "no":
            return cmd

    #--------------------------------------------------------------------------

    def launchTcoffee( self, outFileName, param, run="yes", verbose=0 ):
        
        prg = "t_coffee"
        cmd = prg
        if self.inFileName != "":
            cmd += " -infile %s" % ( self.inFileName )
        cmd += " -outfile %s" % ( outFileName )
        cmd += " %s" % ( param )
        
        if verbose > 0:
            print "launch: %s" % ( cmd ); sys.stdout.flush()
            
        if run == "yes":
            return self.launch( prg, cmd, verbose )
        
        elif run == "no":
            return cmd
        
    #--------------------------------------------------------------------------

    def launchPrank( self, outFileName, param, run="yes", verbose=0 ):

        prg = "prank"
        cmd = prg
        cmd += " -d=%s" % ( self.inFileName )
        cmd += " -o=%s" % ( outFileName )
        cmd += " %s" % ( param )

        if verbose > 0:
            print "launch: %s" % ( cmd ); sys.stdout.flush()

        if run == "yes":
            return self.launch( prg, cmd, verbose )

        elif run == "no":
            return cmd

    #--------------------------------------------------------------------------

    def launchClustalw( self, outFileName, run="yes", verbose="no" ):

        prg = "clustalw"
        cmd = prg
        cmd += " -infile=" + self.inFileName
        cmd += " -outfile=" + outFileName
        cmd += " -output=fasta"
        cmd += " -type=dna"

        if verbose == "yes":
            print "launch: %s" % ( cmd ); sys.stdout.flush()

        if run == "yes":
            return self.launch( prg, cmd, verbose )

        elif run == "no":
            return cmd

    #--------------------------------------------------------------------------

    def launchRepeatMasker( self ):

        return 0

    #--------------------------------------------------------------------------

    def launchCensor( self ):

        return 0

    #--------------------------------------------------------------------------

    def launchPhyML( self, dataType="0", seqFormat="i", nbDataSets="1", nbBootDataSets="0", substModel="HKY", ratioTsTv="4.0", propInvSites="e", nbCat="1", gammaParam="1.0", startTree="BIONJ", optTopology="y", optBranchRate="y", run="yes", verbose=0 ):

        if verbose == "yes":
            verbose = 1
        if verbose == "no":
            verbose = 0

        prg = "phyml"
        cmd = prg
        cmd += " " + self.inFileName
        cmd += " " + dataType
        cmd += " " + seqFormat
        cmd += " " + nbDataSets
        cmd += " " + nbBootDataSets
        cmd += " " + substModel
        cmd += " " + ratioTsTv
        cmd += " " + propInvSites
        cmd += " " + nbCat
        cmd += " " + gammaParam
        cmd += " " + startTree
        cmd += " " + optTopology
        cmd += " " + optBranchRate
        if verbose == 0:
            cmd += " > /dev/null"

        if verbose > 0:
            print "launch: %s" % ( cmd ); sys.stdout.flush()

        if run == "yes":
            return self.launch( prg, cmd, verbose )

        elif run == "no":
            return cmd

    #--------------------------------------------------------------------------

    def launchSreformat( self, outFormat, outFileName, run="yes", verbose=0 ):

        if verbose == "yes":
            verbose = 1
        if verbose == "no":
            verbose = 0

        prg = "sreformat"
        cmd = prg
        cmd += " " + outFormat
        cmd += " " + self.inFileName
        cmd += " > " + outFileName

        if verbose > 0:
            print "launch: %s" % ( cmd ); sys.stdout.flush()

        if run == "yes":
            return self.launch( prg, cmd, verbose )

        elif run == "no":
            return cmd

    #--------------------------------------------------------------------------

    def launchTRF( self, match="2", mismatch="3", delta="5", pm="80", pi="10", minscore="20", maxperiod="15", html="no", dat="yes", run="yes", verbose="no" ):

        prg = "trf"
        cmd = prg
        cmd += " " + self.inFileName
        cmd += " " + match
        cmd += " " + mismatch
        cmd += " " + delta
        cmd += " " + pm
        cmd += " " + pi
        cmd += " " + minscore
        cmd += " " + maxperiod
        if html == "no":
            cmd += " -h"
        if dat == "yes":
            cmd += " -d"

        if verbose == "yes":
            print "launch: %s" % ( cmd ); sys.stdout.flush()

        if run == "yes":
            return self.launch( prg, cmd, verbose )

        elif run == "no":
            return cmd

    #--------------------------------------------------------------------------

    def launchMreps( self, outFileName, res="3", exp="3.0", maxsize="50", run="yes", verbose="no" ):

        prg = "mreps"
        cmd = prg
        cmd += " -res " + res
        cmd += " -exp " + exp
        cmd += " -maxsize " + maxsize
        cmd += " -xmloutput " + outFileName
        cmd += " -fasta " + self.inFileName

        if verbose == "yes":
            print "launch: %s" % ( cmd ); sys.stdout.flush()

        if run == "yes":
            return self.launch( prg, cmd, verbose )

        elif run == "no":
            return cmd

    #--------------------------------------------------------------------------

    def launchBlastclust( self, nbCPU="1", thresSimilarity="1.75", thresLengthCov="0.9", thresOnPair="T", outClustList="", outHitList="", prot="T", cfgFileName="", run="yes", verbose="no" ):

        prg = "blastclust"
        cmd = prg
        cmd += " -i " + self.inFileName
        if nbCPU != "1":
            cmd += " -a " + nbCPU
        if thresSimilarity != "1.75":
            cmd += " -S " + thresSimilarity
        if thresLengthCov != "0.9":
            cmd += " -L " + thresLengthCov
        if thresOnPair != "F":
            cmd += " -b " + thresOnPair
        if outClustList != "":
            cmd += " -o " + outClustList
        if outHitList != "":
            cmd += " -s " + outHitList
        if prot != "T":
            cmd += " -p " + prot
        if cfgFileName != "":
            cmd += " -c " + cfgFileName

        if verbose == "yes":
            print "launch: %s" % ( cmd ); sys.stdout.flush()

        if run == "yes":
            return self.launch( prg, cmd, verbose )

        elif run == "no":
            return cmd

    #--------------------------------------------------------------------------

    def launchShuffle( self, outFileName="", run="yes", verbose="no" ):
        if CheckerUtils.isExecutableInUserPath("esl-shuffle"):
            prg = "esl-shuffle"
        else : prg = "shuffle"
        cmd = prg
        cmd += " -d " + self.inFileName
        if outFileName != "":
            cmd += " > " + outFileName

        if verbose == "yes":
            print "launch: %s" % ( cmd ); sys.stdout.flush()

        if run == "yes":
            return self.launch( prg, cmd, verbose )

        elif run == "no":
            return cmd

    #--------------------------------------------------------------------------

    def launchDrawgram( self, outFileName="", run="yes", verbose="no" ):

        prg = "drawgram"
        cmd = prg
        cmd += " <<EOF\n"
        cmd += "%s\n" % ( self.inFileName )
        cmd += "V\nN\nY\nEOF\n"
        cmd += "mv plotfile %s" % ( outFileName )

        if verbose == "yes":
            print "launch: %s" % ( cmd ); sys.stdout.flush()

        if run == "yes":
            return self.launch( prg, cmd, verbose )

        elif run == "no":
            return cmd
        
    #--------------------------------------------------------------------------

    def launchSeqboot( self, nbReplicates="100", oddSeed="13579", outFileName="outfile", verbose=0 ):
        """
        Launch 'seqboot' from the PHYLIP package.
        """
        
        if os.path.exists( "outfile" ):
            os.remove( "outfile" )
            
        prg = "seqboot"
        cmd = "echo '%s\nR\n%s\nI\nY\n%s' > file_options.txt\n" % ( self.inFileName, nbReplicates, oddSeed )
        cmd += "cat file_options.txt | seqboot"
        if verbose <= 0:
            cmd += " > /dev/null"
        cmd += "\n"
        cmd += "rm file_options.txt\n"
        if outFileName != "outfile":
            cmd += "mv outfile %s\n" % ( outFileName )
            
        return self.launch( prg, cmd, verbose )
    
    #--------------------------------------------------------------------------          
        
    def launchHmmpfam( self, prg_path = "", evalFilter="10", inputFormat="FASTA", profilDatabank="", run="yes", verbose="no" ):

        cmd = "hmmpfam"
        if inputFormat != "":
            cmd += " --informat " + inputFormat
        if evalFilter != "":
            cmd += " -E " + evalFilter
        if profilDatabank != "":
            cmd += " " + profilDatabank
        cmd += " " + self.inFileName + " > " + self._OutputFile
        
        if not self._checkFileExistsAndNotEmpty( self.inFileName ):
            print "Warning : there is no input file : " + self.inFileName + "\n"
            return 0
        
        if self._OutputFile == "":
            print "Warning : You must specify an outputFile name\n"
            return 0
        
        if verbose == "yes":
            print "launch: %s" % ( cmd ); sys.stdout.flush()
        
        if run == "yes":
            return self.launch( prg_path, cmd, verbose )

        elif run == "no":
            return cmd

    #--------------------------------------------------------------------------

    def launchPilerTA( self, outFileName, motifFileName, pyramidFileName, minhitcount="2", maxmargin="0.05", minratio="0.5", run="yes", verbose="no" ):

        prg = "piler"
        cmd = prg
        cmd += " -tan " + self.inFileName
        cmd += " -out " + outFileName
        cmd += " -motif " + motifFileName 
        cmd += " -pyramid " + pyramidFileName
       
        if verbose == "yes":
            print "launch: %s" % ( cmd ); sys.stdout.flush()

        if run == "yes":
            return self.launch( prg, cmd, verbose )

        elif run == "no":
            return cmd
