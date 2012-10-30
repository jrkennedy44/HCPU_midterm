#!/usr/bin/env python

"""
Pipeline for the annotation of transposable elements (TEs) in genomic sequences.
"""

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
import time
import glob
import ConfigParser
from ConfigParser import NoOptionError
from ConfigParser import NoSectionError
from ConfigParser import MissingSectionHeaderError

if not os.environ.has_key( "REPET_PATH" ):
    print "ERROR: no environment variable REPET_PATH"
    sys.exit(1)
sys.path.append( os.environ["REPET_PATH"] )
from pyRepet.launcher.programLauncher import programLauncher
from pyRepetUnit.commons.launcher.Launcher import Launcher
from pyRepetUnit.commons.sql.RepetJob import RepetJob
from pyRepetUnit.commons.checker.CheckerUtils import CheckerUtils
from pyRepetUnit.commons.checker.CheckerException import CheckerException
from pyRepetUnit.commons.sql.DbMySql import DbMySql
from pyRepetUnit.commons.utils.FileUtils import FileUtils

#------------------------------------------------------------------------------

def setup_env():

    """
    Setup the required environment for MySQL.
    """

    os.environ["REPET_HOST"] = config.get("repet_env","repet_host")
    os.environ["REPET_USER"] = config.get("repet_env","repet_user")
    os.environ["REPET_PW"] = config.get("repet_env","repet_pw")
    os.environ["REPET_DB"] = config.get("repet_env","repet_db")
    os.environ["REPET_PORT"] = config.get("repet_env","repet_port")

#------------------------------------------------------------------------------

def help():

    """
    Give the list of the command-line options.
    """

    print
    print "usage: TEannot.py [ options ]"
    print "options:"
    print "     -h: this help"
    print "     -P: project name (<=15 character only alphanumeric or underscore)"
    print "     -C: configuration file"
    print "     -S: step (1/2 with -a/3 with -c/4 with -s/5/6 with -b/7/8 with -o)"
    print "     -a: program to align sequences (BLR/RM/CEN)"
    print "     -r: use randomized chunks (with \"-S 2\")"
    print "     -c: combine the alignment programs (default=BLR+RM+CEN)"
    print "     -s: program to detect short repeats (TRF/Mreps/RMSSR)"
    print "     -b: blast for step 6 (tblastx/blastx)"
    print "     -o: output format for the annotations (gameXML or GFF3)"
    print "     -y: clean (default='no'/'yes')"
    print "     -v: verbose (0/default=1/2/3)"
    print

#------------------------------------------------------------------------------

def main():

    """
    Pipeline for the annotation of transposable elements (TEs) in genomic sequences.
    """

    global projectName
    projectName = ""
    global configFileName
    configFileName = ""
    step = ""
    align = ""
    useRndChunks = False
    combAlign = "BLR+RM+CEN"
    sat = ""
    typeBlast = ""
    outFormat = ""
    global clean
    clean = False
    global verbose
    verbose = 1

    try:
        opts,args = getopt.getopt( sys.argv[1:], "hP:C:S:a:rc:s:b:o:y:v:" )
    except getopt.GetoptError, err:
        print str(err); help(); sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-P":
            projectName = a
        elif o == "-C":
            configFileName = a
        elif o == "-S":
            step = a
        elif o == "-a":
            align = a
        elif o == "-r":
            useRndChunks = True
        elif o == "-c":
            combAlign = a
        elif o == "-s":
            sat = a
        elif o == "-b":
            typeBlast = a
        elif o == "-o":
            outFormat = a
        elif o == "-y":
            if a == "no":
                clean = False
            elif a == "yes":
                clean = True
        elif o == "-v":
            verbose = int(a)

    if projectName == "":
        print "ERROR: no project provided (-P)"
        help()
        sys.exit(1)
    if configFileName == "":
        print "ERROR: no configuration file provided (-C)"
        help()
        sys.exit(1)
    if step == "":
        print "ERROR: no step provided (-S)"
        help()
        sys.exit(1)
        
    if not CheckerUtils.isMax15Char(projectName):
        print "ERROR: project name must have 15 character max"
        help()
        sys.exit(1)
        
    if not CheckerUtils.isCharAlphanumOrUnderscore(projectName):
        print "ERROR: project name must contain only alphanumeric or underscore character"
        help()
        sys.exit(1)

    global config
    config = ConfigParser.ConfigParser()
    try:
        config.readfp( open(configFileName) )
    except MissingSectionHeaderError:
        print "ERROR: your config file " + configFileName + " must begin with a section name"
        sys.exit(1)

    isExceptionRaised = False
    sectionName = "repet_env"
    try:
        CheckerUtils.checkSectionInConfigFile(config, sectionName)
    except NoSectionError:
        print "ERROR: the section " + sectionName + " must be in your config file : " + configFileName
        sys.exit(1)
        
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "repet_version") 
    except NoOptionError:
        print "ERROR: the option repet_version must be define in " + sectionName +" in your config file : " + configFileName
        isExceptionRaised = True
        
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "repet_host") 
    except NoOptionError:
        print "ERROR: the option repet_host must be define in " + sectionName +" in your config file : " + configFileName
        isExceptionRaised = True
        
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "repet_user") 
    except NoOptionError:
        print "ERROR: the option repet_user must be define in " + sectionName +" in your config file : " + configFileName
        isExceptionRaised = True
        
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "repet_pw") 
    except NoOptionError:
        print "ERROR: the option repet_pw must be define in " + sectionName +" in your config file : " + configFileName
        isExceptionRaised = True
        
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "repet_db") 
    except NoOptionError:
        print "ERROR: the option repet_db must be define in " + sectionName +" in your config file : " + configFileName
        isExceptionRaised = True
        
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "repet_port") 
    except NoOptionError:
        print "ERROR: the option repet_port must be define in " + sectionName +" in your config file : " + configFileName
        isExceptionRaised = True
        
    if isExceptionRaised: 
        sys.exit(1)

    setup_env()

    changeLogFileName = os.environ["REPET_PATH"] + "/CHANGELOG" 
    changeLogFileHandler = open(changeLogFileName, "r")
    try:
        CheckerUtils.checkConfigVersion(changeLogFileHandler, config)
    except CheckerException, e:
        print e.msg
        sys.exit(1)
    
    isExceptionRaised = False
    sectionName = "project"
    try:
        CheckerUtils.checkSectionInConfigFile(config, sectionName)
    except NoSectionError:
        print "ERROR: the section " + sectionName + " must be in your config file : " + configFileName
        sys.exit(1)
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "project_name") 
    except NoOptionError:
        print "ERROR: the option project_name must be define in " + sectionName +" in your config file : " + configFileName
        isExceptionRaised = True
        
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "project_dir") 
    except NoOptionError:
        print "ERROR: the option project_dir must be define in " + sectionName +" in your config file : " + configFileName
        isExceptionRaised = True
        
    if isExceptionRaised: 
        sys.exit(1)


    if verbose > 0:
        print "\nSTART %s" % (sys.argv[0].split("/")[-1])
        print "version %s" % ( config.get("repet_env","repet_version") )
        now = time.localtime()
        print "local date/time = %s-%s-%s / %s:%s:%s" % ( now[0], now[1], now[2], now[3], now[4], now[5] )
        sys.stdout.flush()

    if config.get( "project", "project_name" ) != projectName:
        print "ERROR: project name different between configuration file ('%s') and command-line option ('%s')" % ( config.get( "project", "project_name" ), projectName )
        sys.exit(1)
    if verbose > 0:
        print "project name = %s" % ( projectName )

    global projectDir
    projectDir = config.get( "project", "project_dir" )
    if projectDir[-1] == "/":
        projectDir = projectDir[:-1]
    if os.path.exists( projectDir ):
        if verbose > 0:
            print "project directory = %s" % ( projectDir ); sys.stdout.flush()
        os.chdir( projectDir )
    else:
        print "ERROR: project directory %s doesn't exist" % ( projectDir )
        sys.exit(1)

    global pL
    pL = programLauncher()
    
    global jobsSectionName
    jobsSectionName = "parallelized_jobs"
    isExceptionRaised = False
    try:
        CheckerUtils.checkSectionInConfigFile(config, jobsSectionName)
    except NoSectionError:
        print "ERROR: the section '%s' must be in your config file : %s" % (jobsSectionName, configFileName)
        sys.exit(1)
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, jobsSectionName, "resources") 
    except NoOptionError:
        print "ERROR: the option 'resources' must be define in %s in your config file : %s" % (jobsSectionName, configFileName)
        isExceptionRaised = True
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, jobsSectionName, "tmpDir") 
    except NoOptionError:
        print "ERROR: the option 'tmpDir' must be define in %s in your config file : %s" % (jobsSectionName, configFileName)
        isExceptionRaised = True
    if isExceptionRaised: 
        sys.exit(1)
    global queue
    queue = config.get(jobsSectionName, "resources")
    
    if step == "1":            
        prepareInputFilesAndLoadTables()

    elif step == "2":
        if align == "":
            print "ERROR: missing option -a"
            help()
            sys.exit(1)
        if useRndChunks == False:
            alignChunksAndTEs( "", align )
        else:
            alignChunksAndTEs( "_rnd", align )

    elif step == "3":
        filterAndCombineTEsAnnot( combAlign )

    elif step == "4":
        if sat == "":
            print "ERROR: missing option -s"
            help()
            sys.exit(1)
        detectSSRs( sat )

    elif step == "5":
        filterAndCombineSSRsAnnot()

    elif step == "6":
        if typeBlast in [ "tblastx", "blastx" ]:
            alignChunksAndTEsForCoding( typeBlast )
        else:
            print "ERROR: blast '%s' not recognized" % ( typeBlast )
            sys.exit(1)
    
    elif step == "7":
        pathsProcessing( config )
        
    elif step == "8":
        if outFormat == "":
            print "ERROR: missing option -o"
            help()
            sys.exit(1)
        exportAnnotations( outFormat )
    
    if verbose > 0:
        now = time.localtime()
        print "local date/time = %s-%s-%s / %s:%s:%s" % ( now[0], now[1], now[2], now[3], now[4], now[5] )
        print "version %s" % config.get("repet_env", "repet_version")
        print "END %s\n" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    return 0

#------------------------------------------------------------------------------

def prepareInputFilesAndLoadTables():

    """
    Step 1:
    * cut the input genomic sequences into chunks and load them in a MySQL table
    * randomize the chunks and load them in a MySQL table
    * load the reference TE library in a MySQL table
    * prepare the reference TE library for Blaster (blastn)
    """
    
    if verbose > 0:
        print "\nbeginning of step 1"
        print "prepare the input files and load them in MySQL tables"
        sys.stdout.flush()
    
    genomeFastaFileName = "%s/%s.fa" % ( projectDir, projectName ) 
    
    if not os.path.exists( genomeFastaFileName ):
        print "ERROR: %s/%s.fa doesn't exist" % ( projectDir, projectName )
        sys.exit(1)
        
    separator = "\n"    
    
    inGenomeFileHandler = open(genomeFastaFileName, "r")
        
    try:
        CheckerUtils.checkHeaders(inGenomeFileHandler)
    except CheckerException, e:
        print "Error in file " + genomeFastaFileName + ". Wrong headers are :"
        print separator.join(e.messages)
        print "Authorized characters are : a-z A-Z 0-9 - . : _\n"
        inGenomeFileHandler.close()
        sys.exit(1)
            
    inGenomeFileHandler.close()
    
    FileUtils.fromWindowsToUnixEof( genomeFastaFileName )
    
    
    refTEFileName = "%s/%s_refTEs.fa" % ( projectDir, projectName )
    if not os.path.exists( refTEFileName ):
        print "ERROR: %s/%s_refTEs.fa doesn't exist" % ( projectDir, projectName )
        sys.exit(1)

    refTEFileHandler = open(refTEFileName, "r")
        
    try:
        CheckerUtils.checkHeaders(refTEFileHandler)
    except CheckerException, e:
        
        print "Error in file " + refTEFileName + ". Wrong headers are :"
        print separator.join(e.messages)
        print "Authorized characters are : a-z A-Z 0-9 - . : _\n"
        inGenomeFileHandler.close()
        sys.exit(1)
        
    refTEFileHandler.close()
    
    FileUtils.fromWindowsToUnixEof( refTEFileName )
        
    if os.path.exists( "%s_db" % ( projectName ) ):
        os.system( "rm -rf %s_db" % ( projectName ) )
    os.mkdir( "%s_db" % ( projectName ) )
    os.chdir( "%s_db" % ( projectName ) )

    #--------------------------------------------------------------------------

    if not os.path.exists( "%s/%s_db/%s.fa" % ( projectDir, projectName, projectName ) ):
        os.system( "ln -s ../%s.fa %s.fa" % ( projectName, projectName ) )
        
    isExceptionRaised = False
    sectionName = "prepare_data"
    try:
        CheckerUtils.checkSectionInConfigFile(config, sectionName)
    except NoSectionError:
        print "ERROR: the section '%s' must be in your config file : %s" % (sectionName, configFileName)
        sys.exit(1)
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "chunk_length") 
    except NoOptionError:
        print "ERROR: the option 'chunk_length' must be define in '%s' in your config file : %s" % (sectionName, configFileName)
        isExceptionRaised = True
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "chunk_overlap") 
    except NoOptionError:
        print "ERROR: the option 'chunk_overlap' must be define in '%s' in your config file : %s" % (sectionName, configFileName)
        isExceptionRaised = True
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "nb_seq_per_batch") 
    except NoOptionError:
        print "ERROR: the option 'nb_seq_per_batch' must be define in '%s' in your config file : %s" % (sectionName, configFileName)
        isExceptionRaised = True
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "make_random_chunks") 
    except NoOptionError:
        print "ERROR: the option 'make_random_chunks' must be define in '%s' in your config file : %s" % (sectionName, configFileName)
        isExceptionRaised = True
        
    if isExceptionRaised: 
        sys.exit(1)

    cDir = os.getcwd()
    if config.get(jobsSectionName, "tmpDir" ) != "":
        tmpDir = config.get(jobsSectionName, "tmpDir")
    else:
        tmpDir = cDir

    lCmds = []
    # load the chromosome sequences into a MySQL table
    prg = os.environ["REPET_PATH"] + "/bin/srptCreateTable.py"
    cmd = prg
    cmd += " -f %s.fa" % ( projectName )
    cmd += " -n %s_chr_seq" % ( projectName )
    cmd += " -t fasta"
    cmd += " -o"
    cmd += " -v %i" % ( verbose - 1 )
    lCmds.append(cmd)

    # cut the genomic sequences into chunks
    prg = os.environ["REPET_PATH"] + "/bin/dbChunks.py"
    cmd = prg
    cmd += " -i %s.fa" % projectName
    cmd += " -l %s" % config.get(sectionName, "chunk_length")
    cmd += " -o %s" % config.get(sectionName, "chunk_overlap")
    cmd += " -w 0"
    cmd += " -O %s_chunks" % projectName
    cmd += " -c"
    cmd += " -v %i" % ( verbose - 1 )
    lCmds.append(cmd)

    # load the chunk sequences into a MySQL table
    prg = os.environ["REPET_PATH"] + "/bin/srptCreateTable.py"
    cmd = prg
    cmd += " -f %s_chunks.fa" % projectName
    cmd += " -n %s_chk_seq" % projectName
    cmd += " -t fasta"
    cmd += " -o"
    cmd += " -v %i" % ( verbose - 1 )
    lCmds.append(cmd)

    # load the links between chunks and chromosomes into a MySQL table
    prg = os.environ["REPET_PATH"] + "/bin/srptCreateTable.py"
    cmd = prg
    cmd += " -f %s_chunks.map" % projectName
    cmd += " -n %s_chk_map" % projectName
    cmd += " -t map"
    cmd += " -o"
    cmd += " -v %i" % ( verbose - 1 )
    lCmds.append(cmd)

    # allocate one (or several) chunks(s) into the same file (-> batch)
    prg = "%s/bin/dbSplit.py" % os.environ["REPET_PATH"]
    cmd = prg
    cmd += " -i %s_chunks.fa" % projectName
    cmd += " -n %s" % config.get(sectionName, "nb_seq_per_batch")
    cmd += " -d"
    cmd += " -v %i" % ( verbose - 1 )
    lCmds.append(cmd)

    # shuffle each chunk independently to get randomized chunks
    if config.get(sectionName, "make_random_chunks") == "yes":
        if os.path.exists("batches_rnd"):
            os.rmdir("batches_rnd")
        prg = "%s/bin/dbShuffle.py" % os.environ["REPET_PATH"]
        cmd = prg
        cmd += " -I batches"
        cmd += " -O batches_rnd"
        cmd += " -v %i" % ( verbose - 1 )
        lCmds.append(cmd)
    
    groupid = "%s_TEannot_step1_prepareChkAndChr" % projectName
    acronym = "prepareChkAndChr"
    jobdb = RepetJob( cfgFileName = "%s/%s" % (projectDir, configFileName) )
    cL = Launcher( jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
    cL.beginRun()
    cL.job.jobname = acronym
    cmd_start = ""
    cmd_start += "os.system( \"ln -s %s/%s.fa .\" )\n" % ( cDir, projectName )
    for c in lCmds:
        cmd_start += "log = os.system( \""
        cmd_start += c
        cmd_start += "\" )\n"
    cmd_finish = "if not os.path.exists( \"%s/%s_chunks.fa\" ):\n" % ( cDir, projectName )
    cmd_finish += "\tos.system( \"mv %s_chunks.fa %s/.\" )\n" % ( projectName, cDir )
    cmd_finish += "if not os.path.exists( \"%s/%s_chunks.map\" ):\n" % ( cDir, projectName )
    cmd_finish += "\tos.system( \"mv %s_chunks.map %s/.\" )\n" % ( projectName, cDir )
    cmd_finish += "if not os.path.exists( \"%s/batches\" ):\n" % ( cDir )
    cmd_finish += "\tos.system( \"mv batches %s/.\" )\n" % ( cDir )
    if config.get( sectionName, "make_random_chunks" ) == "yes":
        cmd_finish += "if not os.path.exists( \"%s/batches_rnd\" ):\n" % ( cDir )
        cmd_finish += "\tos.system( \"mv batches_rnd %s/.\" )\n" % ( cDir )
    cL.runSingleJob( cmd_start, cmd_finish )
    cL.endRun()
    if clean:
        cL.clean( acronym )
    jobdb.close()

    #--------------------------------------------------------------------------

    if not os.path.exists( "%s/%s_db/%s_refTEs.fa" % ( projectDir, projectName, projectName ) ):
        os.system( "ln -s ../%s_refTEs.fa %s_refTEs.fa_initH" % ( projectName, projectName ) )

    lCmds = []
    # load the TE library into a MySQL table
    prg = os.environ["REPET_PATH"] + "/bin/srptCreateTable.py"
    cmd = prg
    cmd += " -f %s_refTEs.fa_initH" % ( projectName )
    cmd += " -n %s_refTEs_seq" % ( projectName )
    cmd += " -t fasta"
    cmd += " -o"
    cmd += " -v %i" % ( verbose - 1 )
    lCmds.append(cmd)

    # shorten sequence headers
    prg = os.environ["REPET_PATH"] + "/bin/shortenSeqHeader.py"
    cmd = prg
    cmd += " -i %s_refTEs.fa_initH" % ( projectName )
    cmd += " -l 1"
    cmd += " -p refTE_"
    cmd += " -o %s_refTEs.fa" % ( projectName )
    cmd += " -v %i" % ( verbose - 1 )
    lCmds.append(cmd)

    # load the links between initial headers and new headers into a MySQL table
    prg = os.environ["REPET_PATH"] + "/bin/srptCreateTable.py"
    cmd = prg
    cmd += " -f %s_refTEs.fa_initH.shortHlink" % ( projectName )
    cmd += " -n %s_refTEs_map" % ( projectName )
    cmd += " -t map"
    cmd += " -o"
    cmd += " -v %i" % ( verbose - 1 )
    lCmds.append(cmd)

    # prepare the TE library for BLASTER
    sectionName = "align_refTEs_with_genome"
    if config.get(sectionName, "BLR_blast") == "ncbi":
        if not CheckerUtils.isExecutableInUserPath("formatdb"):
            print "ERROR: 'formatdb' from NCBI-BLAST must be in your path"
            sys.exit(1)
    elif config.get(sectionName, "BLR_blast") == "wu":
        if not CheckerUtils.isExecutableInUserPath("xdformat"):
            print "ERROR: 'xdformat' from WU-BLAST must be in your path"
            sys.exit(1)
    prg = os.environ["REPET_PATH"] + "/bin/blaster"
    cmd = prg
    cmd += " -q %s_refTEs.fa" % ( projectName )
    cmd += " -B %s_refTEs.fa-BLRnPrepare" % ( projectName )
    cmd += " -P"
    if config.get(sectionName, "BLR_blast") == "wu":
        cmd += " -p -cpus=1"
        cmd += " -W"
    lCmds.append(cmd)
    
    groupid = "%s_TEannot_step1_prepareTElib" % ( projectName )
    acronym = "prepareTElib"
    jobdb = RepetJob( cfgFileName = "%s/%s" % (projectDir, configFileName) )
    cL = Launcher( jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
    cL.beginRun()
    cL.job.jobname = acronym
    cmd_start = ""
    cmd_start += "os.system( \"cp %s/%s_refTEs.fa_initH .\" )\n" % ( cDir, projectName )
    for c in lCmds:
        cmd_start += "log = os.system( \""
        cmd_start += c
        cmd_start += "\" )\n"
    cmd_finish = "if not os.path.exists( \"%s/%s_refTEs.fa\" ):\n" % ( cDir, projectName )
    cmd_finish += "\tos.system( \"mv %s_refTEs.fa %s/.\" )\n" % ( projectName, cDir )
    cmd_finish += "if not os.path.exists( \"%s/%s_refTEs.fa_initH.shortHlink\" ):\n" % ( cDir, projectName )
    cmd_finish += "\tos.system( \"mv %s_refTEs.fa_initH.shortHlink %s/.\" )\n" % ( projectName, cDir )
    cmd_finish += "if not os.path.exists( \"%s/%s_refTEs.fa.Nstretch.map\" ):\n" % ( cDir, projectName )
    cmd_finish += "\tos.system( \"mv %s_refTEs.fa.Nstretch.map %s/.\" )\n" % ( projectName, cDir )
    cmd_finish += "if not os.path.exists( \"%s/%s_refTEs.fa_cut\" ):\n" % ( cDir, projectName )
    cmd_finish += "\tos.system( \"mv %s_refTEs.fa_cut %s/.\" )\n" % ( projectName, cDir )
    if config.get(sectionName, "BLR_blast") == "wu":
        cmd_finish += "if not os.path.exists( \"%s/%s_refTEs.fa-BLRnPrepare.param\" ):\n" % ( cDir, projectName )
        cmd_finish += "\tos.system( \"mv %s_refTEs.fa-BLRnPrepare.param %s/.\" )\n" % ( projectName, cDir )
        cmd_finish += "if not os.path.exists( \"%s/%s_refTEs.fa_cut.xnd\" ):\n" % ( cDir, projectName )
        cmd_finish += "\tos.system( \"mv %s_refTEs.fa_cut.xnd %s/.\" )\n" % ( projectName, cDir )
        cmd_finish += "if not os.path.exists( \"%s/%s_refTEs.fa_cut.xnt\" ):\n" % ( cDir, projectName )
        cmd_finish += "\tos.system( \"mv %s_refTEs.fa_cut.xnt %s/.\" )\n" % ( projectName, cDir )
        cmd_finish += "if not os.path.exists( \"%s/%s_refTEs.fa_cut.xns\" ):\n" % ( cDir, projectName )
        cmd_finish += "\tos.system( \"mv %s_refTEs.fa_cut.xns %s/.\" )\n" % ( projectName, cDir )
    else:
        cmd_finish += "if not os.path.exists( \"%s/%s_refTEs.fa-BLRnPrepare.param\" ):\n" % ( cDir, projectName )
        cmd_finish += "\tos.system( \"mv %s_refTEs.fa-BLRnPrepare.param %s/.\" )\n" % ( projectName, cDir )
        cmd_finish += "if not os.path.exists( \"%s/%s_refTEs.fa_cut.nhr\" ):\n" % ( cDir, projectName )
        cmd_finish += "\tos.system( \"mv %s_refTEs.fa_cut.nhr %s/.\" )\n" % ( projectName, cDir )
        cmd_finish += "if not os.path.exists( \"%s/%s_refTEs.fa_cut.nin\" ):\n" % ( cDir, projectName )
        cmd_finish += "\tos.system( \"mv %s_refTEs.fa_cut.nin %s/.\" )\n" % ( projectName, cDir )
        cmd_finish += "if not os.path.exists( \"%s/%s_refTEs.fa_cut.nsq\" ):\n" % ( cDir, projectName )
        cmd_finish += "\tos.system( \"mv %s_refTEs.fa_cut.nsq %s/.\" )\n" % ( projectName, cDir )
    cL.runSingleJob( cmd_start, cmd_finish )
    cL.endRun()
    if clean:
        cL.clean( acronym )
    jobdb.close()

    os.chdir( ".." )

    if verbose > 0:
        print "step 1 finished successfully\n"; sys.stdout.flush()

#------------------------------------------------------------------------------

def alignChunksAndTEs( qryDirSuffix, align ):

    """
    Step 2: map the sequence from the TE library on the genomic chunks

    @param qryDirSuffix: query directory suffix ('' or '_rnd')
    @type qryDirSuffix: string

    @param align: alignment program (Blaster, RepeatMasker or Censor)
    @type align: string
    """

    if verbose > 0:
        print "\nbeginning of step 2"
        if qryDirSuffix == "":
            print "use %s to align the TE sequences on the chunks" % ( align )
        else:
            print "use %s to align the TE sequences on the randomized chunks" % ( align )
            if not os.path.exists( projectDir + "/%s_db/batches_rnd" % ( projectName ) ):
                print "ERROR: you didn't build random chunks at step 1, check the configuration file"
                sys.exit(1)
        sys.stdout.flush()

    if not os.path.exists( "%s_TEdetect%s" % ( projectName, qryDirSuffix ) ):
        os.mkdir( "%s_TEdetect%s" % ( projectName, qryDirSuffix ) )
    os.chdir( "%s_TEdetect%s" % ( projectName, qryDirSuffix ) )
    if not os.path.exists( align ):
        os.mkdir( align )
    else:
        print "ERROR: directory %s_TEdetect%s/%s/ already exists" % ( projectName, qryDirSuffix, align )
        sys.exit(1)
    os.chdir( align )

    # launch the alignment program (BLR+M or RM or CEN) on all the chunks in parallel
    if align == "RM":
        if not CheckerUtils.isExecutableInUserPath("RepeatMasker"):
            print "ERROR: RepeatMasker must be in your path"
            sys.exit(1)
    if align == "CEN":
        if not CheckerUtils.isExecutableInUserPath("censor"):
            print "ERROR: censor must be in your path"
            sys.exit(1)
        
    cmdEnd = " -g %s_TEannot_%s%s" % ( projectName, align, qryDirSuffix )
    cmdEnd += " -t jobs"
    cmdEnd += " -q %s/%s_db/batches%s" % ( projectDir, projectName, qryDirSuffix )
    cmdEnd += " -s %s/%s_db/%s_refTEs.fa" % ( projectDir, projectName, projectName )
    cmdEnd += " -Q \"%s\"" % queue
    if config.get(jobsSectionName, "tmpDir") != "":
        cmdEnd += " -d %s" % config.get(jobsSectionName, "tmpDir")
    if clean:
        cmdEnd += " -c"
    if os.environ["REPET_JOBS"] == "files":
        cmdEnd += " -p " + projectDir

    sectionName = "align_refTEs_with_genome"
    try:
        CheckerUtils.checkSectionInConfigFile(config, sectionName)
    except NoSectionError:
        print "ERROR: the section '%s' must be in your config file : %s" % (sectionName, configFileName)
        sys.exit(1)
        
    if align == "BLR":
        try:
            CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "BLR_blast") 
        except NoOptionError:
            print "ERROR: the option 'BLR_blast' must be define in '%s' in your config file : %s" % (sectionName, configFileName)
            sys.exit(1)
        try:
            CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "BLR_sensitivity") 
        except NoOptionError:
            print "ERROR: the option 'BLR_sensitivity' must be define in '%s' in your config file : %s" % (sectionName, configFileName)
            sys.exit(1)
        prg = "%s/bin/srptBlasterMatcher.py" % os.environ["REPET_PATH"]
        cmd = prg
        cmd += " -m 1"
        cmd += " -B \"-S %s" % config.get(sectionName, "BLR_sensitivity")
        if config.get(sectionName, "BLR_blast") not in ["ncbi","wu"]:
            print "ERROR: 'BLR_blast: %s' in your configuration file is not authorized" % config.get(sectionName, "BLR_blast")
            sys.exit(1)
        if config.get(sectionName, "BLR_blast") == "wu":
            cmd += " -p -cpus=1"
            cmd += " -W"
        cmd += "\""
        cmd += cmdEnd
        
    elif align == "RM":
        try:
            CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "RM_engine") 
        except NoOptionError:
            print "ERROR: the option 'RM_engine' must be define in '%s' in your config file : %s" % (sectionName, configFileName)
            sys.exit(1)
        try:
            CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "RM_sensitivity") 
        except NoOptionError:
            print "ERROR: the option 'RM_sensitivity' must be define in '%s' in your config file : %s" % (sectionName, configFileName)
            sys.exit(1)
        prg = "%s/bin/srptRM.py" % os.environ["REPET_PATH"]
        cmd = prg
        cmd += " -P \"-cutoff 200"
        if config.get(sectionName, "RM_engine") == "wu":
            cmd += " -e wublast"
        elif config.get(sectionName, "RM_engine") == "cm":
            cmd += " -e crossmatch"
        else:
            print "ERROR: 'RM_engine: %s' in your configuration file is not authorized" % config.get(sectionName,"RM_engine")
            sys.exit(1)
        if config.get(sectionName, "RM_sensitivity") == "s":
            cmd += " -s"
        elif config.get(sectionName, "RM_sensitivity") == "q":
            cmd += " -q"
        elif config.get(sectionName, "RM_sensitivity") == "qq":
            cmd += " -qq"
        elif config.get(sectionName, "RM_sensitivity") == "":
            pass
        else:
            print "ERROR: 'RM_sensitivity: %s' in your configuration file is not authorized" % config.get("align_refTEs_with_genome", "RM_sensitivity")
            sys.exit(1)
        cmd += "\""
        cmd += cmdEnd
        
    elif align == "CEN":
        prg = "%s/bin/srptCEN.py" % os.environ["REPET_PATH"]
        cmd = prg
        cmd += " -P \"-s -ns\""
        cmd += cmdEnd
        
    else:
        print "ERROR: option -a %s not recognized" % ( align )
        sys.exit(1)
        
    pL.launch( prg, cmd, verbose - 1 )
    
    os.chdir( "../.." )
    
    if verbose > 0:
        print "step 2 finished successfully\n"; sys.stdout.flush()
        
#------------------------------------------------------------------------------

def filterAndCombineTEsAnnot( combAlign ):

    """
    Step 3: filter the true HSPs with the randomized ones and combine them among the 3 programs
    """

    if verbose > 0:
        print "\nbeginning of step 3"
        print "filter the real HSPs with the random HSPs and combine them"
        sys.stdout.flush()

    if combAlign == "":
        print "ERROR: no alignment program specified with option -c"
        sys.exit(1)

    # retrieve for each program ran on the random chunks the highest score from all 'align' files
    thres = {}
    isExceptionRaised = False
    sectionName = "filter"
    try:
        CheckerUtils.checkSectionInConfigFile(config, sectionName)
    except NoSectionError:
        print "ERROR: the section '%s' must be in your config file : %s" % (sectionName, configFileName)
        sys.exit(1)
                    
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "force_default_values") 
    except NoOptionError:
        print "ERROR: the option 'force_default_values' must be define in '%s' in your config file : %s" % (sectionName, configFileName)
        isExceptionRaised = True
       
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "BLR") 
    except NoOptionError:
        print "ERROR: the option 'BLR' must be define in '%s' in your config file : %s" % (sectionName, configFileName)
        isExceptionRaised = True
       
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "RM") 
    except NoOptionError:
        print "ERROR: the option 'RM' must be define in '%s' in your config file : %s" % (sectionName, configFileName)
        isExceptionRaised = True
       
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "CEN") 
    except NoOptionError:
        print "ERROR: the option 'CEN' must be define in '%s' in your config file : %s" % (sectionName, configFileName)
        isExceptionRaised = True

    if isExceptionRaised: 
        sys.exit(1)

    if os.path.exists( "%s_TEdetect_rnd" % projectName):
        os.chdir( "%s/%s_TEdetect_rnd/" % (projectDir, projectName) )
        # retrieve for each program ran on the random chunks the highest score from all 'align' files
        prg = os.environ["REPET_PATH"] + "/bin/srptRetrieveTheHighestScore.py"
        cmd = prg
        cmd += " -p %s" % projectName
        cmd += " -c %s" % configFileName
        cmd += " -v %i" % verbose
        
        cDir = os.getcwd()
        if config.get(jobsSectionName, "tmpDir" ) != "":
            tmpDir = config.get(jobsSectionName, "tmpDir")
        else:
            tmpDir = cDir

        groupid = "%s_TEannot_step3_retrieveTheHighestScore" % ( projectName )
        acronym = "retrieveTheHighestScore"
        jobdb = RepetJob( cfgFileName = "%s/%s" % (projectDir, configFileName) )
        cL = Launcher( jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
        cL.beginRun()
        cL.job.jobname = acronym
        cmd_start = ""
        cmd_start += "os.system( \"ln -s %s/%s .\" )\n" % ( projectDir, configFileName )
        cmd_start += "os.system( \"ln -s %s .\" )\n" % cDir
        cmd_start += "log = os.system( \""
        cmd_start += cmd
        cmd_start += "\" )\n"
        cL.runSingleJob( cmd_start )
        cL.endRun()
        if clean:
            cL.clean( acronym )
        jobdb.close()
        
        thresFile = "%s/threshold.tmp" % cDir
        thresFileHandler = open(thresFile, "r")
        for line in thresFileHandler:
            lElt = line.split()
            thres[lElt[0]] = lElt[1]
        thresFileHandler.close()

    if config.get( "filter", "force_default_values" ) == "yes":
        if verbose > 0:
            print "\n* force the use of the default values from the configuration file"
            sys.stdout.flush()
            for alignProgram in ["BLR","RM","CEN"]:
                thres[alignProgram] = config.get( "filter", alignProgram )
                if verbose > 0:
                    print "default threshold %s: %s" % (alignProgram, thres[alignProgram])
                    sys.stdout.flush()

    if thres == {}:
        print "ERROR: you have to launch step 2 with option \"-r\" or specify default filter values in the configuration file"
        sys.exit(1)

    os.chdir( "%s/%s_TEdetect/" % ( projectDir, projectName ) )

    # filter the 'align' files
    if verbose > 0:
        print "\n* filter the 'align' files according to the threshold"; sys.stdout.flush()
        
    for prg in ["BLR","RM","CEN"]:
        if os.path.exists( prg ):
            os.chdir( prg )
            
            cDir = os.getcwd()
            if config.get(jobsSectionName, "tmpDir" ) != "":
                tmpDir = config.get(jobsSectionName, "tmpDir")
            else:
                tmpDir = cDir
                
            lCmds = []
            lAlignFiles = glob.glob( "*.align" )
            for alignFile in lAlignFiles:
                cmd = os.environ["REPET_PATH"] + "/bin/FilterAlign.py"
                cmd += " -i %s" % ( alignFile )
                cmd += " -S %s" % ( thres[prg] )
                cmd += " -v %i" % ( verbose )
                lCmds.append(cmd)
                #TODO: how to precise error message ('print "ERROR while filtering '%s' from %s" % ( alignFile, prg )')
                
            groupid = "%s_TEannot_step3_FilterAlign_%s" % ( projectName, prg )
            acronym = "FilterAlign_%s" % ( prg )
            jobdb = RepetJob( cfgFileName = "%s/%s" % (projectDir, configFileName) )
            cL = Launcher( jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
            cL.beginRun()
            cL.job.jobname = acronym
            cmd_start = ""
            for alignFile in lAlignFiles:
                cmd_start += "os.system( \"ln -s %s/%s .\" )\n" % ( cDir, alignFile )
            for c in lCmds:
                cmd_start += "log = os.system( \""
                cmd_start += c
                cmd_start += "\" )\n"
            cmd_finish = ""
            for alignFile in lAlignFiles:
                cmd_finish += "if not os.path.exists( \"%s/%s.filtered\" ):\n" % ( cDir, alignFile )
                cmd_finish += "\tos.system( \"mv %s.filtered %s/.\" )\n" % ( alignFile, cDir )
            cL.runSingleJob( cmd_start, cmd_finish )
            cL.endRun()
            if clean:
                cL.clean( acronym )
            jobdb.close()
                    
            os.chdir( ".." )
    
    # concatenate chunk by chunk the filtered 'align' files from each alignment program
    if verbose > 0:
        print "\n* concatenate chunk by chunk the filtered 'align' files from each alignment program"; sys.stdout.flush()
    if os.path.exists( "Comb" ):
        os.system( "rm -rf Comb" )
    os.mkdir( "Comb" )
    os.chdir( "Comb" )
    lChkFilePaths = glob.glob( "%s/%s_db/batches/batch*.fa" % ( projectDir, projectName ) )
    for chkFilePath in lChkFilePaths:
        chkFileName = os.path.basename( chkFilePath )
        concatFile = "%s_allTEs.align" % ( chkFileName )
        prg = "cat"
        cmd = prg
        if "BLR" in combAlign and os.path.exists( "../BLR/%s.align.filtered" % chkFileName ):
            if "RM" in combAlign and os.path.exists( "../RM/%s.cat.align.filtered" % chkFileName ):
                if "CEN" in combAlign and os.path.exists( "../CEN/%s.map.align.filtered" % chkFileName ):
                    cmd += " ../BLR/%s.align.filtered ../RM/%s.cat.align.filtered ../CEN/%s.map.align.filtered > %s" % ( chkFileName, chkFileName, chkFileName, concatFile )
                elif "CEN" not in combAlign or not os.path.exists( "../CEN/%s.map.align.filtered" % chkFileName ):
                    cmd += " ../BLR/%s.align.filtered ../RM/%s.cat.align.filtered > %s" % ( chkFileName, chkFileName, concatFile )
            elif "RM" not in combAlign or not os.path.exists( "../RM/%s.cat.align.filtered" % chkFileName ):
                if "CEN" in combAlign and os.path.exists( "../CEN/%s.map.align.filtered" % chkFileName ):
                    cmd += " ../BLR/%s.align.filtered ../CEN/%s.map.align.filtered > %s" % ( chkFileName, chkFileName, concatFile )
                elif "CEN" not in combAlign or not os.path.exists( "../CEN/%s.map.align.filtered" % chkFileName ):
                    cmd += " ../BLR/%s.align.filtered > %s" % ( chkFileName, concatFile )
        elif "BLR" not in combAlign or not os.path.exists( "../BLR/%s.align.filtered" % chkFileName ):
            if "RM" in combAlign and os.path.exists( "../RM/%s.cat.align.filtered" % chkFileName ):
                if "CEN" in combAlign and os.path.exists( "../CEN/%s.map.align.filtered" % chkFileName ):
                    cmd += " ../RM/%s.cat.align.filtered ../CEN/%s.map.align.filtered > %s" % ( chkFileName, chkFileName, concatFile )
                elif "CEN" not in combAlign or not os.path.exists( "../CEN/%s.map.align.filtered" % chkFileName ):
                    cmd += " ../RM/%s.cat.align.filtered > %s" % ( chkFileName, concatFile )
            elif "RM" not in combAlign or not os.path.exists( "../RM/%s.cat.align.filtered" % chkFileName ):
                if "CEN" in combAlign and os.path.exists( "../CEN/%s.map.align.filtered" % chkFileName ):
                    cmd += " ../CEN/%s.map.align.filtered > %s" % ( chkFileName, concatFile )
                elif "CEN" not in combAlign or not os.path.exists( "../CEN/%s.map.align.filtered" % chkFileName ):
                    continue
        pL.launch( prg, cmd, verbose - 1 )
        
        #TODO: UpdateScoreOfMatches.py to launch on node
        if len(combAlign) > 5:
            prg = os.environ["REPET_PATH"] + "/bin/UpdateScoreOfMatches.py"
            cmd = prg
            cmd += " -i %s" % ( concatFile )
            cmd += " -f align"
            cmd += " -o %s.newScores" % ( concatFile )
            cmd += " -v %i" % ( verbose - 1 )
            pL.launch( prg, cmd, verbose - 1 )
            
    # join the matches with Matcher
    string = "join the matches with Matcher"
    if verbose > 0:
        print "\n* %s" % ( string ); sys.stdout.flush()
    prg = os.environ["REPET_PATH"] + "/bin/srptBlasterMatcher.py"
    cmd = prg
    cmd += " -g %s_TEannot_Matcher" % ( projectName )
    cmd += " -q %s/%s_TEdetect/Comb" % ( projectDir, projectName )
    if len(combAlign) > 5:
        cmd += " -S '*.newScores'"
    cmd += " -Q \"%s\"" % queue
    cmd += " -m 2"   # launch Matcher only
    cmd += " -M \"-j -x\""
    cmd += " -Z path"
    cmd += " -C %s/%s" % ( projectDir, configFileName )
    if clean:
        cmd += " -c"
    cmd += " -v %i" % ( verbose - 1 )
    if config.get(jobsSectionName, "tmpDir") != "":
        cmd += " -d %s" % config.get(jobsSectionName, "tmpDir")
    pL.launch( prg, cmd, verbose - 1 )
    
    lCmds = []
    # load data in MySQL
    prg = os.environ["REPET_PATH"] + "/bin/srptCreateTable.py"
    cmd = prg
    cmd += " -f %s_TEannot_Matcher.path" % ( projectName )
    cmd += " -n %s_chk_allTEs_tmpH_path" % ( projectName )
    cmd += " -t path"
    cmd += " -o"
    cmd += " -v %i" % ( verbose - 1 )
    lCmds.append(cmd)

    # retrieve the initial headers of the reference TEs
    prg = os.environ["REPET_PATH"] + "/bin/srptRetrieveInitHeaders.py"
    cmd = prg
    cmd += " -n %s_chk_allTEs_tmpH_path" % ( projectName )
    cmd += " -l %s/%s_db/%s_refTEs.fa_initH.shortHlink" % ( projectDir, projectName, projectName )
    cmd += " -s"
    cmd += " -C %s/%s" % ( projectDir, configFileName )
    cmd += " -o %s_chk_allTEs_path" % ( projectName )
    cmd += " -c"
    lCmds.append(cmd)

    # convert the coordinates from chunks to chromosomes
    prg = os.environ["REPET_PATH"] + "/bin/srptConvChunk2Chr.py"
    cmd = prg
    cmd += " -m %s_chk_map" % ( projectName )
    cmd += " -q %s_chk_allTEs_path" % ( projectName )
    cmd += " -t path"
    cmd += " -c"
    cmd += " -o %s_chr_allTEs_path" % ( projectName )
    cmd += " -v %i" % ( verbose - 1 )
    lCmds.append(cmd)
        
    cDir = os.getcwd()
    if config.get(jobsSectionName, "tmpDir" ) != "":
        tmpDir = config.get(jobsSectionName, "tmpDir")
    else:
        tmpDir = cDir

    groupid = "%s_TEannot_step3_RetrieveInitHeadersAndConvChkToChr" % ( projectName )
    acronym = "srptCreateTable_srptRetrieveInitHeaders_srptConvChunk2Chr"
    jobdb = RepetJob( cfgFileName = "%s/%s" % (projectDir, configFileName) )
    cL = Launcher( jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
    cL.beginRun()
    cL.job.jobname = acronym
    cmd_start = ""
    cmd_start += "os.system( \"ln -s %s/%s .\" )\n" % ( cDir, configFileName )
    cmd_start += "os.system( \"ln -s %s/%s_db/%s_refTEs.fa_initH.shortHlink .\" )\n" % ( projectDir, projectName, projectName )
    cmd_start += "os.system( \"ln -s %s/%s_TEannot_Matcher.path .\" )\n" % ( cDir, projectName )
    for cmd in lCmds:
        cmd_start += "log = os.system( \""
        cmd_start += cmd
        cmd_start += "\" )\n"
    cL.runSingleJob( cmd_start )
    cL.endRun()
    if clean:
        cL.clean( acronym )
    jobdb.close()

    if clean:
        cmd = "find . -name \"*.align\" -exec rm {} \;"
        log = os.system( cmd )
        if log != 0:
            print "ERROR while removing temporary 'align' files"
            sys.exit(1)
        cmd = "find . -name \"*.align.clean_match.map\" -exec rm {} \;"
        log = os.system( cmd )
        if log != 0:
            print "ERROR while removing temporary 'map' files"
            sys.exit(1)

    os.chdir( "../.." )

    if verbose > 0:
        print "step 3 finished successfully\n"; sys.stdout.flush()

#------------------------------------------------------------------------------

def detectSSRs( sat ):

    """
    Step 4: detect SSRs

    @param sat: SSR detection program (TRF, RMSSR, Mreps)
    @type sat: string
    """

    if verbose > 0:
        print "\nbeginning of step 4"
        print "search for satellites on the chunks with %s" %( sat )
        sys.stdout.flush()

    if not os.path.exists( "%s_SSRdetect" % ( projectName ) ):
        os.mkdir( "%s_SSRdetect" % ( projectName ) )
    os.chdir( "%s_SSRdetect" % ( projectName ) )
    if not os.path.exists( sat ):
        os.mkdir( sat )
    else:
        print "ERROR: directory %s_SSRdetect/%s/ already exists" % ( projectName, sat )
        sys.exit(1)
    os.chdir( sat )

    # launch the SSR-detection program (TRF or Mreps or RM) on  all the chunks in parallel
    if sat ==  "TRF" and not CheckerUtils.isExecutableInUserPath("trf"):
        print "ERROR: trf must be in your path"
        sys.exit(1)
    if sat ==  "RMSSR" and not CheckerUtils.isExecutableInUserPath("RepeatMasker"):
        print "ERROR: RepeatMasker must be in your path"
        sys.exit(1)
    if sat ==  "Mreps" and not CheckerUtils.isExecutableInUserPath("mreps"):
        print "ERROR: mreps must be in your path"
        sys.exit(1)
        
    cmdEnd = " -g %s_TEannot_%s" % ( projectName, sat )
    cmdEnd += " -t jobs"
    cmdEnd += " -q %s/%s_db/batches" % ( projectDir, projectName )
    cmdEnd += " -Q \"%s\"" % queue
    cmdEnd += " -C"
    if clean:
        cmdEnd += " -c"
    if config.get(jobsSectionName, "tmpDir") != "":
        cmdEnd += " -d %s" % config.get(jobsSectionName, "tmpDir")
    if sat == "TRF":
        prg = os.environ["REPET_PATH"] + "/bin/srptTRF.py"
        cmd = prg
        cmd += cmdEnd
    elif sat == "RMSSR":
        prg = os.environ["REPET_PATH"] + "/bin/srptRMSSR.py"
        cmd = prg
        cmd += " -P \"-s"
        cmd += " -e wublast"
        cmd += "\""
        cmd += cmdEnd
    elif sat == "Mreps":
        prg = os.environ["REPET_PATH"] + "/bin/srptMreps.py"
        cmd = prg
        cmd += cmdEnd
    else:
        print "ERROR: option -s %s not recognized" % ( sat )
        sys.exit(1)
    pL.launch( prg, cmd, verbose - 1 )

    # load the results into a MySQL table
    prg = os.environ["REPET_PATH"] + "/bin/srptCreateTable.py"
    cmd = prg
    if sat == "TRF":
        cmd += " -f %s_TEannot_%s.set" % ( projectName, sat )
        cmd += " -n %s_chk_%s_set" % ( projectName, sat )
        cmd += " -t set"
    elif sat == "RMSSR":
        cmd += " -f %s_TEannot_%s.path" % ( projectName, sat )
        cmd += " -n %s_chk_%s_path" % ( projectName, sat )
        cmd += " -t path"
    elif sat == "Mreps":
        cmd += " -f %s_TEannot_%s.set" % ( projectName, sat )
        cmd += " -n %s_chk_%s_set" % ( projectName, sat )
        cmd += " -t set"
    cmd += " -o"
    cmd += " -v %i" % ( verbose - 1 )
    pL.launch( prg, cmd, verbose - 1 )

    os.chdir( ".." )

    if verbose > 0:
        print "step 4 finished successfully\n"; sys.stdout.flush()

#------------------------------------------------------------------------------

def filterAndCombineSSRsAnnot():

    """
    Step 5: merge the SSR annotations from TRF, Mreps and RepeatMasker
    """

    if verbose > 0:
        print "\nbeginning of step 5"
        print "filter and combine the SSR annotations from TRF, Mreps and RepeatMasker"
        sys.stdout.flush()

    if not os.path.exists( "%s_SSRdetect" % ( projectName ) ):
        print "ERROR: directory %s_SSRdetect doesn't exist" % ( projectName )
        sys.exit(1)
    os.chdir( "%s_SSRdetect" % ( projectName ) )
    if os.path.exists( "Comb" ):
        print "ERROR: directory %s_SSRdetect/Comb already exists" % ( projectName )
        sys.exit(1)
    os.mkdir( "Comb" )
    os.chdir( "Comb" )

    mergeFile = open( "mergeSSR.txt", "w" )
    cmd = ""
    if os.path.exists( "../TRF" ):
        cmd += "%s_chk_TRF_set\tset\tmerge\n" % ( projectName )
    if os.path.exists( "../Mreps" ):
        cmd += "%s_chk_Mreps_set\tset\tmerge\n" % ( projectName )
    if os.path.exists( "../RMSSR" ):
        cmd += "%s_chk_RMSSR_path\tpath\tmerge\n" % ( projectName )
    mergeFile.write( cmd )
    mergeFile.close()

    lCmds = []
    prg = os.environ["REPET_PATH"] + "/bin/srptAutoPromote.py"
    cmd = prg
    cmd += " -f mergeSSR.txt"
    cmd += " -o %s_chk_allSSRs_set" % ( projectName )
    cmd += " -v %i" % ( verbose - 1 )
    lCmds.append(cmd)

    # convert the coordinates from chunks to chromosomes
    prg = os.environ["REPET_PATH"] + "/bin/srptConvChunk2Chr.py"
    cmd = prg
    cmd += " -m %s_chk_map" % ( projectName )
    cmd += " -q %s_chk_allSSRs_set" % ( projectName )
    cmd += " -t set"
    cmd += " -c"
    cmd += " -o %s_chr_allSSRs_set" % ( projectName )
    cmd += " -v %i" % ( verbose - 1 )
    lCmds.append(cmd)
        
    cDir = os.getcwd()
    if config.get(jobsSectionName, "tmpDir" ) != "":
        tmpDir = config.get(jobsSectionName, "tmpDir")
    else:
        tmpDir = cDir

    groupid = "%s_TEannot_step5_SrptAutoPromoteAndSrptConvChunk2Chr" % ( projectName )
    acronym = "srptAutoPromote_srptConvChunk2Chr"
    jobdb = RepetJob( cfgFileName = "%s/%s" % (projectDir, configFileName) )
    cL = Launcher( jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
    cL.beginRun()
    cL.job.jobname = acronym
    cmd_start = ""
    cmd_start += "os.system( \"ln -s %s/%s .\" )\n" % ( cDir, configFileName )
    cmd_start += "os.system( \"ln -s %s/mergeSSR.txt .\" )\n" % ( cDir )
    for cmd in lCmds:
        cmd_start += "log = os.system( \""
        cmd_start += cmd
        cmd_start += "\" )\n"
    cL.runSingleJob( cmd_start )
    cL.endRun()
    if clean:
        cL.clean( acronym )
    jobdb.close()

    os.chdir( "../.." )

    if verbose > 0:
        print "step 5 finished successfully\n"; sys.stdout.flush()

#------------------------------------------------------------------------------

def alignChunksAndTEsForCoding( typeBlast ):

    """
    Step 6: align the 2nd data bank on the genomic sequences via Blaster with tblastx or blastx
    * load the bank in a MySQL table
    * prepare the bank
    * launch BLASTER with tblastx or blastx
    """

    if verbose > 0:
        print "\nbeginning of step 6"; sys.stdout.flush()

    #--------------------------------------------------------------------------

    if not os.path.exists( "%s_db" % ( projectName ) ):
        os.mkdir( "%s_db" % ( projectName ) )
    os.chdir( "%s_db" % ( projectName ) )
    typeSeq = ""
    
    if typeBlast == "tblastx":
        bankBlast = "bankBLRtx"
        typeSeq = "nt"
        bankExtensionChar = "n"
    elif typeBlast == "blastx":
        bankBlast = "bankBLRx"
        typeSeq = "prot"
        bankExtensionChar = "p"

    sectionName = "align_other_banks"
    try:
        CheckerUtils.checkSectionInConfigFile(config, sectionName)
    except NoSectionError:
        print "ERROR: the section '%s' must be in your config file : %s" % (sectionName, configFileName)
        sys.exit(1)
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, bankBlast) 
    except NoOptionError:
        print "ERROR: the option '%s' must be define in '%s' in your config file : %s" % (bankBlast, sectionName, configFileName)
        sys.exit(1)

    bankName = config.get(sectionName, bankBlast)
    if not os.path.exists( "%s/%s" % (projectDir, bankName) ):
        print "ERROR: %s/%s doesn't exist" % (projectDir, bankName)
        sys.exit(1)

    #TODO: usefull ?
    if not os.path.exists( "%s/%s_db/%s" % (projectDir, projectName, bankName) ):
        os.system( "ln -s ../%s %s" % (bankName, bankName) )
        
    FileUtils.fromWindowsToUnixEof( bankName )
    
    lCmds = []
    # load the bank in a MySQL table
    prg = os.environ["REPET_PATH"] + "/bin/srptCreateTable.py"
    cmd = prg
    cmd += " -f %s" % ( bankName )
    cmd += " -n %s_%s_%s_seq" % ( projectName, bankBlast, typeSeq )
    cmd += " -t fasta"
    cmd += " -o"
    cmd += " -v %i" % ( verbose - 1 )
    lCmds.append(cmd)

    # prepare the bank
    pL.reset( bankName )
    cmd = pL.launchBlaster( prepareOnly="yes", blastAlgo=typeBlast, outPrefix="%s-%sPrepare" % ( bankName, bankBlast ), run="no" )
    lCmds.append(cmd)
        
    cDir = os.getcwd()
    if config.get(jobsSectionName, "tmpDir" ) != "":
        tmpDir = config.get(jobsSectionName, "tmpDir")
    else:
        tmpDir = cDir
    
    groupid = "%s_TEannot_step6_prepareAlignOtherBank_%s" % (projectName, typeBlast)
    acronym = "srptCreateTable_prepareAlignOtherBank_%s" % typeBlast
    jobdb = RepetJob( cfgFileName = "%s/%s" % (projectDir, configFileName) )
    cL = Launcher( jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
    cL.beginRun()
    cL.job.jobname = acronym
    cmd_start = "os.system( \"ln -s " "%s/%s .\" )\n" % ( projectDir, bankName )
    for cmd in lCmds:
        cmd_start += "log = os.system( \""
        cmd_start += cmd
        cmd_start += "\" )\n"
    cmd_finish = "if not os.path.exists( \"%s/%s-%sPrepare.param\" ):\n" % ( cDir, bankName, bankBlast )
    cmd_finish += "\tos.system( \"mv %s-%sPrepare.param %s/.\" )\n" % ( bankName, bankBlast, cDir )
    cmd_finish += "if not os.path.exists( \"%s/%s_cut\" ):\n" % ( cDir, bankName )
    cmd_finish += "\tos.system( \"mv %s_cut %s/.\" )\n" % ( bankName, cDir )
    cmd_finish += "if not os.path.exists( \"%s/%s_cut.%shr\" ):\n" % ( cDir, bankName, bankExtensionChar )
    cmd_finish += "\tos.system( \"mv %s_cut.%shr %s/.\" )\n" % ( bankName, bankExtensionChar, cDir )
    cmd_finish += "if not os.path.exists( \"%s/%s_cut.%sin\" ):\n" % ( cDir, bankName, bankExtensionChar )
    cmd_finish += "\tos.system( \"mv %s_cut.%sin %s/.\" )\n" % ( bankName, bankExtensionChar, cDir )
    cmd_finish += "if not os.path.exists( \"%s/%s_cut.%ssq\" ):\n" % ( cDir, bankName, bankExtensionChar )
    cmd_finish += "\tos.system( \"mv %s_cut.%ssq %s/.\" )\n" % ( bankName, bankExtensionChar, cDir )
    cmd_finish += "if not os.path.exists( \"%s/%s.Nstretch.map\" ):\n" % ( cDir, bankName )
    cmd_finish += "\tos.system( \"mv %s.Nstretch.map %s/.\" )\n" % ( bankName, cDir )
    cL.runSingleJob( cmd_start, cmd_finish )
    cL.endRun()
    if clean:
        cL.clean( acronym )
    jobdb.close()

    os.chdir( ".." )

    #--------------------------------------------------------------------------

    if verbose > 0:
        print "\nalign '%s' and the chunks via Blaster with %s" % ( bankName, typeBlast )
        sys.stdout.flush()

    if not os.path.exists( projectName + "_TEdetect" ):
        os.mkdir( projectName + "_TEdetect" )
    os.chdir( projectName + "_TEdetect" )
    if not os.path.exists( bankBlast ):
        os.mkdir( bankBlast )
    else:
        print "ERROR: directory %s_TEdetect/%s/ already exists" % ( projectName, bankBlast )
        sys.exit(1)
    os.chdir( bankBlast )

    # launch Blaster with tblastx followed by Matcher on each chunk in parallel
    prg = os.environ["REPET_PATH"] + "/bin/srptBlasterMatcher.py"
    cmd = prg
    cmd += " -g %s_TEannot_%s" % ( projectName, bankBlast )
    cmd += " -t jobs"
    cmd += " -q %s/%s_db/batches" % ( projectDir, projectName )
    cmd += " -s %s/%s_db/%s" % ( projectDir, projectName, bankName )
    cmd += " -m 3"
    cmd += " -B \"-n %s -r\"" % ( typeBlast )
    cmd += " -M \"-j\""
    cmd += " -Q \"%s\"" % queue
    cmd += " -Z path"
    if clean:
        cmd += " -c"
    if config.get(jobsSectionName, "tmpDir") != "":
        cmd += " -d %s" % config.get(jobsSectionName, "tmpDir")
    if os.environ["REPET_JOBS"] == "files":
        cmd += " -p " + projectDir
    pL.launch( prg, cmd, verbose - 1 )

    os.system( "mv %s_TEannot_%s.path %s_%s.path" % ( projectName, bankBlast, projectName, bankBlast ) )

    lCmds = []
    # load data in MySQL
    prg = os.environ["REPET_PATH"] + "/bin/srptCreateTable.py"
    cmd = prg
    cmd += " -f %s_%s.path" % ( projectName, bankBlast )
    cmd += " -n %s_chk_%s_path" % ( projectName, bankBlast )
    cmd += " -t path"
    cmd += " -o"
    cmd += " -v %i" % ( verbose - 1 )
    lCmds.append(cmd)

    # convert the coordinates from chunks to chromosomes
    prg = os.environ["REPET_PATH"] + "/bin/srptConvChunk2Chr.py"
    cmd = prg
    cmd += " -m %s_chk_map" % ( projectName )
    cmd += " -q %s_chk_%s_path" % ( projectName, bankBlast )
    cmd += " -t path"
    cmd += " -c"
    cmd += " -o %s_chr_%s_path" % ( projectName, bankBlast )
    cmd += " -v %i" % ( verbose - 1 )
    lCmds.append(cmd)
    
    cDir = os.getcwd()
    if config.get(jobsSectionName, "tmpDir" ) != "":
        tmpDir = config.get(jobsSectionName, "tmpDir")
    else:
        tmpDir = cDir

    groupid = "%s_TEannot_step6_createTableAndconvChunk2Chr_%s" % (projectName, typeBlast)
    acronym = "srptCreateTable_srptConvChunk2Chr_%s" % typeBlast
    jobdb = RepetJob( cfgFileName = "%s/%s" % (projectDir, configFileName) )
    cL = Launcher( jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
    cL.beginRun()
    cL.job.jobname = acronym
    cmd_start = ""
    cmd_start += "os.system( \"ln -s %s/%s_%s.path .\" )\n" % ( cDir, projectName, bankBlast )
    for cmd in lCmds:
        cmd_start += "log = os.system( \""
        cmd_start += cmd
        cmd_start += "\" )\n"
    cL.runSingleJob( cmd_start )
    cL.endRun()
    if clean:
        cL.clean( acronym )
    jobdb.close()

    os.chdir( ".." )

    if verbose > 0:
        print "step 6 finished successfully\n"; sys.stdout.flush()

#------------------------------------------------------------------------------

def pathsProcessing( config ):

    """
    Step 7: remove path doublons, spurious paths and apply long join procedure

    @param config: configuration file handling
    @type config: file handling
    """

    if verbose > 0:
        print "\nbeginning of step 7"
        sys.stdout.flush()

    os.chdir( "%s_TEdetect" % ( projectName ) )

    isExceptionRaised = False
    sectionName = "annot_processing"
    try:
        CheckerUtils.checkSectionInConfigFile(config, sectionName)
    except NoSectionError:
        print "ERROR: the section '%s' must be in your config file : %s" % (sectionName, configFileName)
        sys.exit(1)
        
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "min_size") 
    except NoOptionError:
        print "ERROR: the option 'min_size' must be define in '%s' in your config file : %s" % (sectionName, configFileName)
        isExceptionRaised = True
        
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "join_id_tolerance") 
    except NoOptionError:
        print "ERROR: the option 'join_id_tolerance' must be define in '%s' in your config file : %s" % (sectionName, configFileName)
        isExceptionRaised = True
        
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "join_max_gap_size") 
    except NoOptionError:
        print "ERROR: the option 'join_max_gap_size' must be define in '%s' in your config file : %s" % (sectionName, configFileName)
        isExceptionRaised = True
        
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "join_max_mismatch_size") 
    except NoOptionError:
        print "ERROR: the option 'join_max_mismatch_size' must be define in '%s' in your config file : %s" % (sectionName, configFileName)
        isExceptionRaised = True
        
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "join_TEinsert_cov") 
    except NoOptionError:
        print "ERROR: the option 'join_TEinsert_cov' must be define in '%s' in your config file : %s" % (sectionName, configFileName)
        isExceptionRaised = True
        
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "join_overlap") 
    except NoOptionError:
        print "ERROR: the option 'join_overlap' must be define in '%s' in your config file : %s" % (sectionName, configFileName)
        isExceptionRaised = True
        
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "join_minlength_split") 
    except NoOptionError:
        print "ERROR: the option 'join_minlength_split' must be define in '%s' in your config file : %s" % (sectionName, configFileName)
        isExceptionRaised = True
        
    if isExceptionRaised == True:
        sys.exit(1)

    lCmds = []
    if verbose > 0:
        print "remove path doublons among the TE annotations"
        sys.stdout.flush()
    prg = "%s/bin/srptRemovePathDoublons.py" % os.environ["REPET_PATH"]
    cmd = "log = os.system( \"%s" % prg
    cmd += " -i %s_chk_allTEs_path" % projectName
    cmd += " -o %s_chk_allTEs_nr_path" % projectName
    cmd += " -v %i" % ( verbose - 1 )
    cmd += "\" )\n"
    lCmds.append(cmd)

    iDb = DbMySql( cfgFileName = "%s/%s" % (projectDir, configFileName) ) 

    #TODO: how to have comments at the correct moment ? 
    if verbose > 0:
        print "remove TE annotations corresponding to SSRs"
        sys.stdout.flush()
    if iDb.doesTableExist( "%s_chk_allSSRs_set" % projectName ):
        prg = "%s/bin/srptRemoveSpurious.py" % os.environ["REPET_PATH"]
        cmd = "log = os.system( \"%s" % prg
        cmd += " -q %s_chk_allTEs_nr_path" % projectName
        cmd += " -s %s_chk_allSSRs_set" % projectName
        cmd += " -t path/set"
        cmd += " -r %s" % config.get(sectionName, "min_size")
        cmd += " -o %s_chk_allTEs_nr_noSSR_path" % projectName
        cmd += " -v %i" % ( verbose - 1 )
        cmd += "\" )\n"
        lCmds.append(cmd)
    else:
        print "WARNING: can't find table '%s_chk_allSSRs_set" % projectName
        sys.stdout.flush()
        cmd = "from pyRepetUnit.commons.sql.DbMySql import DbMySql\n"
        cmd += "iDb = DbMySql()\n"
        cmd += "iDb.copyTable( \"%s_chk_allTEs_nr_path\", \"%s_chk_allTEs_nr_noSSR_path\" )\n" % (projectName, projectName)
        cmd += "iDb.close()\n"
        lCmds.append(cmd)
    
    # avoid time out on iDb, close db handler
    iDb.close()

    # convert the coordinates from chunks to chromosomes
    prg = "%s/bin/srptConvChunk2Chr.py" % os.environ["REPET_PATH"]
    cmd = "log = os.system( \"%s" % prg
    cmd += " -m %s_chk_map" % projectName
    cmd += " -q %s_chk_allTEs_nr_noSSR_path" % projectName
    cmd += " -t path"
    cmd += " -c"
    cmd += " -o %s_chr_allTEs_nr_noSSR_path" % projectName
    cmd += " -v %i" % ( verbose - 1 )
    cmd += "\" )\n"
    lCmds.append(cmd)
    
    cDir = os.getcwd()
    if config.get(jobsSectionName, "tmpDir" ) != "":
        tmpDir = config.get(jobsSectionName, "tmpDir")
    else:
        tmpDir = cDir

    groupid = "%s_TEannot_step7_RemovePathDuplicates_Spurious_And_ConvChunk2Chr" % projectName
    acronym = "srptRemovePathDoublons_srptRemoveSpurious_srptConvChunk2Chr"
    jobdb = RepetJob( cfgFileName = "%s/%s" % (projectDir, configFileName) )
    cL = Launcher( jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
    cL.beginRun()
    cL.job.jobname = acronym
    cmd_start = ""
    for cmd in lCmds:
        cmd_start += cmd
    cL.runSingleJob( cmd_start )
    cL.endRun()
    if clean:
        cL.clean( acronym )
    jobdb.close()
    
    # long join procedure to connect fragmented, nested TE copies
    if verbose > 0:
        print "long join procedure to connect fragmented TE copies"
        sys.stdout.flush()
    prg = "%s/bin/LongJoinsForTEs.py" % os.environ["REPET_PATH"]
    cmd = "log = os.system( \"%s" % prg
    cmd += " -t %s_chr_allTEs_nr_noSSR_path" % projectName
    cmd += " -i %s" % config.get(sectionName, "join_id_tolerance")
    cmd += " -g %s" % config.get(sectionName, "join_max_gap_size")
    cmd += " -m %s" % config.get(sectionName, "join_max_mismatch_size")
    cmd += " -c %s" % config.get(sectionName, "join_TEinsert_cov")
    cmd += " -o %s" % config.get(sectionName, "join_overlap")
    cmd += " -s %s" % config.get(sectionName, "join_minlength_split")
    cmd += " -l %s" % config.get(sectionName, "min_size")
    cmd += " -O %s_chr_allTEs_nr_noSSR_join_path" % projectName
    cmd += " -C %s/%s" % (projectDir, configFileName)
    cmd += " -v %s" % verbose
    cmd += "\" )\n"
    
    groupid = "%s_TEannot_step7_LongJoinsForTEs" % projectName
    acronym = "LongJoinsForTEs"
    jobdb = RepetJob( cfgFileName = "%s/%s" % (projectDir, configFileName) )
    cL = Launcher( jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
    cL.beginRun()
    cL.job.jobname = acronym
    cmd_start = "os.system(\"ln -s %s/%s .\" )\n" % ( projectDir, configFileName )
    cmd_start += cmd
    cL.runSingleJob( cmd_start )
    cL.endRun()
    if clean:
        cL.clean( acronym )
    jobdb.close()
    
    # end of long join procedure, re open db connection
    if clean:
        iDb = DbMySql( cfgFileName = "%s/%s" % ( projectDir, configFileName ) )
        iDb.dropTable( "%s_chr_allTEs_nr_noSSR_path" % projectName )
        iDb.close()
    
    # convert the coordinates from chromosomes to chunks
    prg = os.environ["REPET_PATH"] + "/bin/srptConvChr2Chunk.py"
    cmd = prg
    cmd += " -m %s_chk_map" % ( projectName )
    cmd += " -q %s_chr_allTEs_nr_noSSR_join_path" % ( projectName )
    cmd += " -t path"
    cmd += " -o %s_chk_allTEs_nr_noSSR_join_path" % ( projectName )
    
    groupid = "%s_TEannot_step7_srptConvChr2Chunk" % ( projectName )
    acronym = "srptConvChr2Chunk"
    jobdb = RepetJob( cfgFileName = "%s/%s" % (projectDir, configFileName) )
    cL = Launcher( jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
    cL.beginRun()
    cL.job.jobname = acronym
    cmd_start = "log = os.system( \""
    cmd_start += cmd
    cmd_start += "\" )\n"
    cL.runSingleJob( cmd_start )
    cL.endRun()
    if clean:
        cL.clean( acronym )
    jobdb.close()

    os.chdir( ".." )

    if verbose > 0:
        print "step 7 finished successfully\n"; sys.stdout.flush()

#------------------------------------------------------------------------------

def exportAnnotations( outFormat ):

    """
    Step 8: export files recording the annotations for each chunk

    @outFormat: gameXML or GFF3
    @type outFormat: string
    """

    if verbose > 0:
        print "\nbeginning of step 8"
        print "build %s files" % ( outFormat )
        sys.stdout.flush()

    isExceptionRaised = False
    sectionName = "export"
    try:
        CheckerUtils.checkSectionInConfigFile(config, sectionName)
    except NoSectionError:
        print "ERROR: the section '%s' must be in your config file : %s" % (sectionName, configFileName)
        sys.exit(1)
        
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "sequences") 
    except NoOptionError:
        print "ERROR: the option 'sequences' must be define in '%s' in your config file : %s" % (sectionName, configFileName)
        isExceptionRaised = True
        
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "add_SSRs") 
    except NoOptionError:
        print "ERROR: the option 'add_SSRs' must be define in '%s' in your config file : %s" % (sectionName, configFileName)
        isExceptionRaised = True
        
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "add_tBx") 
    except NoOptionError:
        print "ERROR: the option 'add_tBx' must be define in '%s' in your config file : %s" % (sectionName, configFileName)
        isExceptionRaised = True
        
    if isExceptionRaised == True:
        sys.exit(1)

    refSeq = config.get(sectionName, "sequences")
    if refSeq == "chromosomes":
        refSeq = "chr"
    elif refSeq == "chunks":
        refSeq = "chk"
    else:
        print "ERROR: '%s' not recognized"
        sys.exit(1)

    if not os.path.exists( "%s_%s%s" % (projectName, outFormat, refSeq) ):
        os.mkdir( "%s_%s%s" % (projectName, outFormat, refSeq) )
    os.chdir( "%s_%s%s" % (projectName, outFormat, refSeq) )

    # write the file with the annotation tables
    tableFileName = "annotation_tables.txt"
    tableFile = open( tableFileName, "w" )
    string = "%s_REPET_TEs\t" % projectName
    string += "path\t"
    string += "%s_%s_allTEs_nr_noSSR_join_path\n" % (projectName, refSeq)
    if config.get(sectionName, "add_SSRs") == "yes":
        if os.path.exists( "%s/%s_SSRdetect/Comb" % (projectDir, projectName) ): 
            string += "%s_REPET_SSRs\t" % projectName
            string += "set\t"
            string += "%s_%s_allSSRs_set\n" % (projectName, refSeq)
        else:
            print "WARNING: can't export SSR annotations, launch step 4 and 5 first"
    if config.get(sectionName, "add_tBx") == "yes":
        if os.path.exists( "%s/%s_TEdetect/bankBLRtx" % (projectDir, projectName) ):
            string += "%s_REPET_tblastx\t" % projectName
            string += "path\t"
            string += "%s_%s_bankBLRtx_path\n" % (projectName, refSeq)
        else:
            print "WARNING: can't export tblastx annotations, launch step 6 first"
    if config.get(sectionName, "add_Bx") == "yes":
        if os.path.exists( "%s/%s_TEdetect/bankBLRx" % (projectDir, projectName) ):
            string += "%s_REPET_blastx\t" % projectName
            string += "path\t"
            string += "%s_%s_bankBLRx_path\n" % (projectName, refSeq)
        else:
            print "WARNING: can't export blastx annotations, launch step 6 first"
    tableFile.write(string)
    tableFile.close()

    #--------------------------------------------------------------------------
    if outFormat == "GFF3":
        
        try:
            CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "gff3_chado") 
        except NoOptionError:
            print "ERROR: the option gff3_chado must be define in '%s' in your config file : %s" % (sectionName, configFileName)
            sys.exit(1)

        # create the source GFF3 file(s), one per genomic sequence
        if verbose > 0:
            print "create source files..."
            sys.stdout.flush()
        prg = "%s/bin/srptGFF3Maker.py" % os.environ["REPET_PATH"]
        cmd = prg
        if refSeq == "chr":
            cmd += " -f %s_chr_seq" % projectName
        elif refSeq == "chk":
            cmd += " -f %s_chk_seq" % projectName
        cmd += " -v %i" % ( verbose - 1 )
    
        cDir = os.getcwd()
        if config.get(jobsSectionName, "tmpDir") != "":
            tmpDir = config.get(jobsSectionName, "tmpDir")
        else:
            tmpDir = cDir

        groupid = "%s_TEannot_step8_srptGFF3Maker_createGFF3Files" % projectName
        acronym = "srptGFF3Maker_createGff3Files"
        jobdb = RepetJob( cfgFileName = "%s/%s" % (projectDir, configFileName) )
        cL = Launcher(jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym)
        cL.beginRun()
        cL.job.jobname = acronym
        cmd_start = "os.mkdir( \"src_GFF3\" )\n"
        cmd_start += "os.chdir( \"src_GFF3\" )\n"
        cmd_start += "log = os.system( \""
        cmd_start += cmd
        cmd_start += "\" )\n"
        cmd_finish = "if not os.path.exists( \"%s/src_GFF3\" ):\n" % cDir
        cmd_finish += "\tos.mkdir(\"%s/src_GFF3\")\n" % cDir
        cmd_finish += "os.system( \"find . -type f -name '*.gff3' -exec mv {} %s/src_GFF3/. \\;\" )\n" % cDir
        cL.runSingleJob( cmd_start, cmd_finish )
        cL.endRun()
        if clean:
            cL.clean( acronym )
        jobdb.close()
        
        # add the annotations to the GFF3 files
        if verbose > 0:
            print "add annotations to source files..."
            sys.stdout.flush()
        if os.path.exists( "annotations" ):
            os.system( "rm -rf annotations" )
        os.mkdir( "annotations" )
        os.chdir( "annotations" )
    
        cDir = os.getcwd()
        if config.get(jobsSectionName, "tmpDir" ) != "":
            tmpDir = config.get(jobsSectionName, "tmpDir")
        else:
            tmpDir = cDir

        groupid = "%s_TEannot_step8_srptGFF3Maker_saveAnnotations" % ( projectName )
        acronym = "srptGFF3Maker_saveAnnot"
        jobdb = RepetJob( cfgFileName = "%s/%s" % (projectDir, configFileName) )
        cL = Launcher( jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
        cL.beginRun()
        cL.job.jobname = acronym
        cmd_start = ""
        lGff3FilePaths = glob.glob("../src_GFF3/*.gff3")
        for gff3FilePath in lGff3FilePaths:
            gff3FileName = os.path.basename(gff3FilePath)
            prg = "%s/bin/srptGFF3Maker.py" % os.environ["REPET_PATH"]
            cmd = prg
            cmd += " -t %s" % os.path.abspath("../%s" % tableFileName)
            cmd += " -g %s" % gff3FileName
            if config.get(sectionName, "gff3_chado") == "yes":
                cmd += " -c"
            cmd += " -v %i" % ( verbose - 1 )
            
            cmd_start += "os.system(\"cp %s .\")\n" % os.path.abspath(gff3FilePath)
            cmd_start += "log = os.system( \""
            cmd_start += cmd
            cmd_start += "\" )\n"
            
        cmd_finish = "os.system( \"find . -type f -name '*.gff3' -exec mv {} %s/. \\;\" )\n" % cDir
        cL.runSingleJob( cmd_start, cmd_finish )
        cL.endRun()
        if clean:
            cL.clean( acronym )
        jobdb.close()
            
        os.chdir( ".." )
        os.system( "rm -rf src_GFF3/" )
        os.chdir( ".." )

    #--------------------------------------------------------------------------

    elif outFormat == "gameXML":

        # create the source gameXML file(s), one per genomic sequence
        if verbose > 0:
            print "create source files..."
            sys.stdout.flush()

        prg = "%s/bin/srptGameXmlMaker.py" % os.environ["REPET_PATH"]
        cmd = prg
        if refSeq == "chr":
            cmd += " -f %s.fa" % projectName
        elif refSeq == "chk":
            cmd += " -f %s_chunks.fa" % projectName
        cmd += " -v %i" % ( verbose - 1 )
        
        cDir = os.getcwd()
        if config.get(jobsSectionName, "tmpDir" ) != "":
            tmpDir = config.get(jobsSectionName, "tmpDir")
        else:
            tmpDir = cDir

        groupid = "%s_TEannot_step8_srptGameXmlMaker_createGameXML" % ( projectName )
        acronym = "srptGameXmlMaker_createGameXML"
        jobdb = RepetJob( cfgFileName = "%s/%s" % (projectDir, configFileName) )
        cL = Launcher( jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
        cL.beginRun()
        cL.job.jobname = acronym
        cmd_start = "os.mkdir( \"src_gameXML\" )\n"
        cmd_start += "os.chdir( \"src_gameXML\" )\n"
        if refSeq == "chr":
            cmd_start += "os.system( \"ln -s %s/%s.fa %s.fa\" )\n" % (projectDir, projectName, projectName)
        elif refSeq == "chk":
            cmd_start += "os.system( \"ln -s %s/%s_db/%s_chunks.fa %s_chunks.fa\" )\n" % (projectDir, projectName, projectName, projectName)
        cmd_start += "log = os.system( \""
        cmd_start += cmd
        cmd_start += "\" )\n"
        cmd_finish = "if not os.path.exists( \"%s/src_gameXML\" ):\n" % cDir
        cmd_finish += "\tos.mkdir(\"%s/src_gameXML\")\n" % cDir
        cmd_finish += "os.system( \"find . -type f -name '*.gamexml.*' -exec mv {} %s/src_gameXML/. \\;\" )\n" % cDir
        cL.runSingleJob( cmd_start, cmd_finish )
        cL.endRun()
        if clean:
            cL.clean( acronym )
        jobdb.close()

        os.chdir( "src_gameXML" )
        exitStatus = os.system( "%s/bin/renameFiles.py -i gamexml.new -o gamexml.ori -l \"*.new\" > /dev/null 2>&1" % (os.environ["REPET_PATH"]))
        if exitStatus != 0:
            print "ERROR while renaming gameXML files ('.new'->'.ori')"
            sys.exit(1)
        os.chdir( ".." )

        # add the annotations to the gameXML files
        if verbose > 0:
            print "add annotations to source files..."
            sys.stdout.flush()
        if os.path.exists( "annotations" ):
            os.system( "rm -rf annotations" )
        os.mkdir( "annotations" )
        os.chdir( "annotations" )
        os.system("find ../src_gameXML/ -name '*.ori' -exec cp {} . \;")
        exitStatus = os.system( "%s/bin/renameFiles.py -i gamexml.ori -o gamexml -l \"*.ori\" > /dev/null 2>&1" % (os.environ["REPET_PATH"]))
        if exitStatus != 0:
            print "ERROR while renaming gameXML files ('.ori'->'.gamexml')"
            sys.exit(1)
    
        cDir = os.getcwd()
        if config.get(jobsSectionName, "tmpDir" ) != "":
            tmpDir = config.get(jobsSectionName, "tmpDir")
        else:
            tmpDir = cDir

        groupid = "%s_TEannot_step8_srptGameXmlMaker_saveAnnotations" % ( projectName )
        acronym = "srptGameXmlMaker_saveAnnot"
        jobdb = RepetJob( cfgFileName = "%s/%s" % (projectDir, configFileName) )
        cL = Launcher( jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
        cL.beginRun()
        cL.job.jobname = acronym
        cmd_start = ""
        lGXmlFilePaths = glob.glob( "*.gamexml" )
        for gXmlFilePath in lGXmlFilePaths:
            gXmlFileName = os.path.basename( gXmlFilePath )
            prg = "%s/bin/srptGameXmlMaker.py" % os.environ["REPET_PATH"]
            cmd = prg
            cmd += " -t %s" % os.path.abspath("../%s" % tableFileName)
            cmd += " -g %s" % gXmlFileName
            cmd += " -v %i" % ( verbose - 1 )
            
            cmd_start += "os.system(\"cp %s .\")\n" % os.path.abspath(gXmlFileName)
            cmd_start += "log = os.system( \""
            cmd_start += cmd
            cmd_start += "\" )\n"
            
        cmd_finish = "os.system( \"find . -type f -name '*.gamexml.*' -exec mv {} %s/. \\;\" )\n" % cDir
        cL.runSingleJob( cmd_start, cmd_finish )
        cL.endRun()
        if clean:
            cL.clean( acronym )
        jobdb.close()
            
        exitStatus = os.system( "%s/bin/renameFiles.py -i gamexml.new -o gamexml -l \"*.new\" > /dev/null 2>&1" % (os.environ["REPET_PATH"]))
        if exitStatus != 0:
            print "ERROR while renaming gameXML files ('.new'->'.gamexml')"
            sys.stdout.flush()

        os.chdir( ".." )
        os.system( "rm -rf src_gameXML/" )
        os.chdir( ".." )
        
    #--------------------------------------------------------------------------
    
    if clean:
        iDb = DbMySql( cfgFileName = "%s/%s" % ( projectDir, configFileName ) )
        lTables = iDb.getTableListFromPattern( "%s_%%" % projectName )
        for table in lTables:
            iDb.dropTable( table )
        iDb.close()
            
    if verbose > 0:
        print "step 8 finished successfully\n"
        sys.stdout.flush()
        
#------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
