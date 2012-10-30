#!/usr/bin/env python

"""
Pipeline for the de novo identification of transposable elements (TEs) in genomic sequences.
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
import ConfigParser
import glob

if not "REPET_PATH" in os.environ.keys():
    print "ERROR: no environment variable REPET_PATH"
    sys.exit(1)
sys.path.append( os.environ["REPET_PATH"] )

from pyRepet.launcher.programLauncher import programLauncher
from pyRepetUnit.commons.launcher.Launcher import Launcher
from pyRepetUnit.commons.sql.RepetJob import RepetJob
from pyRepetUnit.commons.checker.CheckerUtils import CheckerUtils
from pyRepetUnit.commons.checker.CheckerException import CheckerException
from repet_base.MapClusterLauncher import MapClusterLauncher
from repet_base.MafftClusterLauncher import MafftClusterLauncher
from ConfigParser import NoOptionError
from ConfigParser import NoSectionError
from ConfigParser import MissingSectionHeaderError


#TODO : node use copy instead of symbolic link ?
#------------------------------------------------------------------------------

def setup_env( config ):

    """
    Setup the required environment.

    @param config: configuration file
    @type config: file handling
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
    print "usage: TEdenovo.py [ options ]"
    print "options:"
    print "     -h: this help"
    print "     -P: project name (<=15 symbols, alphanumeric or underscore)"
    print "     -C: configuration file"
    print "     -S: step (1/2/3/4/5/6/7)"
    print "     -s: program to self-align (default=Blaster/Pals)"
    print "     -c: program to cluster HSPs (default=Grouper/Recon/Piler or GrpRec/GrpPil/RecPil/GrpRecPil)"
    print "     -m: program to build MSAs (default=Map/Mafft/Muscle/Clustalw/Tcoffee/Prank)"
    print "     -v: verbose (0/default=1)"
    print

#------------------------------------------------------------------------------

def main():

    """
    This program is a pipeline for the de novo identification of transposable elements (TEs) in genomic sequences.
    """
    global projectName
    projectName = ""
    global configFileName
    configFileName = ""
    step = ""
    smplAlign = "Blaster"
    clustHsp = "Grouper"
    multAlign = "Map"
    global verbose
    verbose = 1
    global configFileHandle
    
    try:
        opts, args = getopt.getopt(sys.argv[1:],"hP:C:S:s:c:m:v:")
    except getopt.GetoptError, err:
        print str(err)
        help()
        sys.exit(1)
    for o, a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-P":
            projectName = a
        elif o == "-C":
            configFileName = a
        elif o == "-S":
            step = a
        elif o == "-s":
            smplAlign = a
        elif o == "-c":
            clustHsp = a
        elif o == "-m":
            multAlign = a
        elif o == "-v":
            verbose = int(a)

    if projectName == "" or configFileName == "" or step == "":
        print "ERROR: missing compulsory options"
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
    configFileHandle = open(configFileName)
    config = ConfigParser.ConfigParser()
    
    try :
        config.readfp( configFileHandle )
    except MissingSectionHeaderError:
        print "ERROR: config file " + configFileName + " must begin with a section header "  
        sys.exit(1)
    
    isOptionErrorRaised = False
    sectionName = "repet_env"
    try:
        CheckerUtils.checkSectionInConfigFile(config, sectionName)
    except NoSectionError:
        print "ERROR: the section " + sectionName + " must be in your config file : " + configFileName
        sys.exit(1)

    optionName = "repet_version"
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, optionName) 
    except NoOptionError:
        print "ERROR: the option " +  optionName +" must be define in " + sectionName +" in your config file : " + configFileName
        isOptionErrorRaised = True 
    optionName = "repet_host"
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, optionName) 
    except NoOptionError:
        print "ERROR: the option " +  optionName +" must be define in " + sectionName +" in your config file : " + configFileName
        isOptionErrorRaised = True 
            
    optionName = "repet_user"
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, optionName) 
    except NoOptionError:
        print "ERROR: the option " +  optionName +" must be define in " + sectionName +" in your config file : " + configFileName
        isOptionErrorRaised = True 
            
    optionName = "repet_pw"
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, optionName) 
    except NoOptionError:
        print "ERROR: the option " +  optionName +" must be define in " + sectionName +" in your config file : " + configFileName
        isOptionErrorRaised = True 
            
    optionName = "repet_db"
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, optionName) 
    except NoOptionError:
        print "ERROR: the option " +  optionName +" must be define in " + sectionName +" in your config file : " + configFileName
        isOptionErrorRaised = True 
            
    optionName = "repet_port"
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, optionName) 
    except NoOptionError:
        print "ERROR: the option " +  optionName +" must be define in " + sectionName +" in your config file : " + configFileName
        isOptionErrorRaised = True 
        
    if isOptionErrorRaised:
        sys.exit(1)

        
    setup_env( config )
    
    changeLogFileName = os.environ["REPET_PATH"] + "/CHANGELOG" 
    changeLogFileHandle = open(changeLogFileName, "r")
    
    try:
        CheckerUtils.checkConfigVersion(changeLogFileHandle, config)
    except CheckerException, e:
        print e.msg
        sys.exit(1)
    
    sectionName = "project"
    
    try:
        CheckerUtils.checkSectionInConfigFile(config, sectionName)
    except NoSectionError:
        print "ERROR: the section " + sectionName + " must be in your config file : " + configFileName
        sys.exit(1)
    
    isOptionErrorRaised = False
    optionName = "project_name"
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, optionName) 
    except NoOptionError:
        print "ERROR: the option " +  optionName +" must be define in " + sectionName +" in your config file : " + configFileName
        isOptionErrorRaised = True    

    optionName = "project_dir"
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, optionName) 
    except NoOptionError:
        print "ERROR: the option " +  optionName +" must be define in " + sectionName +" in your config file : " + configFileName
        isOptionErrorRaised = True    

    if isOptionErrorRaised :
        sys.exit(1)


    if verbose > 0:
        print "\nSTART TEdenovo.py (%s)" % ( time.strftime("%Y-%m-%d %H:%M:%S") )
        print "version %s" % ( config.get("repet_env","repet_version") )
        sys.stdout.flush()

    if config.get( "project", "project_name" ) != projectName:
        print "ERROR: project name different between configuration file and command-line option"
        sys.exit(1)
    if verbose > 0:
        print "project name = %s" % ( projectName ); sys.stdout.flush()

    global projectDir
    projectDir = config.get(sectionName, "project_dir" )
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

    if step == "1":
        selfAlign( smplAlign )

    if step == "2":
        clusterHsp( smplAlign, clustHsp )

    if step == "3":
        buildConsensus( smplAlign, clustHsp, multAlign )

    if step == "4":
        detectFeatures( smplAlign, clustHsp, multAlign )

    if step == "5":
        classifConsensus( smplAlign, clustHsp, multAlign )

    if step == "6":
        filterConsensus( smplAlign, clustHsp, multAlign )

    if step == "7":
        clusteringConsensus( smplAlign, clustHsp, multAlign )

    if verbose > 0:
        print "version %s" % ( config.get("repet_env","repet_version") )
        print "END TEdenovo.py (%s)\n" % ( time.strftime("%Y-%m-%d %H:%M:%S") )
        sys.stdout.flush()

    return 0

#------------------------------------------------------------------------------

def selfAlign( smplAlign ):
    """
    step 1: self-alignment of the input data bank

    @param smplAlign: name of the alignment program (Blaster or Pals)
    @type smplAlign: string
    """

    if verbose > 0:
        print "beginning of step 1"
        print "self-alignment with %s" % ( smplAlign )
        sys.stdout.flush()

    if os.path.exists( projectName + "_" + smplAlign ):
        print "ERROR: directory " + projectName + "_" + smplAlign + "/ already exists"
        sys.exit(1)

    sectionName = "self_align"
    
    try:
        CheckerUtils.checkSectionInConfigFile(config, sectionName)
    except NoSectionError:
        print "ERROR: the section " + sectionName + " must be in your config file : " + configFileName
        sys.exit(1)

    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "blast")
    except NoOptionError:
        print "ERROR: the option blast must be define in " + sectionName +" in your config file : " + configFileName
        sys.exit(1)
    if config.get(sectionName,"blast") == "wu":
        if not (CheckerUtils.isExecutableInUserPath("wu-blastall") or CheckerUtils.isExecutableInUserPath("wu-formatdb")):
            print "ERROR: wu-blastall and wu-formatdb must be in your path"
            sys.exit(1)
    else:
        if not (CheckerUtils.isExecutableInUserPath("blastall") or CheckerUtils.isExecutableInUserPath("formatdb")):
            print "ERROR: ncbi blastall and formatdb must be in your path"
            sys.exit(1)
    if smplAlign == "Blaster":
        try:
            CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "Evalue") 
        except NoOptionError:
            print "ERROR: the option Evalue must be define in " + sectionName +" in your config file : " + configFileName
            sys.exit(1)
    if smplAlign == "Pals" and not CheckerUtils.isExecutableInUserPath("pals"):
        print "ERROR: 'pals' must be in your path"
        sys.exit(1)
    if smplAlign == "Yass" and not CheckerUtils.isExecutableInUserPath("yass"):
        print "ERROR: 'yass' must be in your path"
        sys.exit(1)
    if smplAlign == "Blat" and not CheckerUtils.isExecutableInUserPath("blat"):
        print "ERROR: 'blat' must be in your path"
        sys.exit(1)

    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "clean") 
    except NoOptionError:
        print "ERROR: the option 'clean' must be define in " + sectionName +" in your config file : " + configFileName
        sys.exit(1) 
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "length") 
    except NoOptionError:
        print "ERROR: the option 'length' must be define in " + sectionName +" in your config file : " + configFileName
        sys.exit(1)
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "identity") 
    except NoOptionError:
        print "ERROR: the option 'identity' must be define in " + sectionName +" in your config file : " + configFileName
        sys.exit(1)

    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "filter_HSP") 
    except NoOptionError:
        print "ERROR: the option 'filter_HSP' must be define in " + sectionName +" in your config file : " + configFileName
        sys.exit(1)      
    if config.get(sectionName,"filter_HSP") == "yes":
        try:
            CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "min_Evalue") 
        except NoOptionError:
            print "ERROR: the option 'min_Evalue' must be define in " + sectionName +" in your config file : " + configFileName
            sys.exit(1)
        try:
            CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "min_identity") 
        except NoOptionError:
            print "ERROR: the option 'min_identity' must be define in " + sectionName +" in your config file : " + configFileName
            sys.exit(1)
        try:
            CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "min_length") 
        except NoOptionError:
            print "ERROR: the option 'min_length' must be define in " + sectionName +" in your config file : " + configFileName
            sys.exit(1)
        try:
            CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "max_length") 
        except NoOptionError:
            print "ERROR: the option 'max_length' must be define in " + sectionName +" in your config file : " + configFileName
            sys.exit(1)

    os.mkdir( projectName + "_" + smplAlign )
    os.chdir( projectName + "_" + smplAlign )
    os.system( "ln -s ../" + projectName + ".fa ." )
    os.system( "cp ../%s ." % ( configFileName ) )

    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "chunk_length") 
    except NoOptionError:
        print "ERROR: the option 'chunk_length' must be define in " + sectionName +" in your config file : " + configFileName
        sys.exit(1)
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "chunk_overlap") 
    except NoOptionError:
        print "ERROR: the option 'chunk_overlap' must be define in " + sectionName +" in your config file : " + configFileName
        sys.exit(1)
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "nb_seq_per_batch") 
    except NoOptionError:
        print "ERROR: the option 'nb_seq_per_batch' must be define in " + sectionName +" in your config file : " + configFileName
        sys.exit(1)       
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "resources") 
    except NoOptionError:
        print "ERROR: the option 'resources' must be define in " + sectionName +" in your config file : " + configFileName
        sys.exit(1)
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "tmpDir") 
    except NoOptionError:
        print "ERROR: the option 'tmpDir' must be define in " + sectionName +" in your config file : " + configFileName
        sys.exit(1)  
                                  
    #TODO: add checkHeaders()
    lCmds = []
    
    # build the chunks
    prg = os.environ["REPET_PATH"] + "/bin/dbChunks.py"
    cmd = prg
    cmd += " -i %s.fa" % ( projectName )
    cmd += " -l %s" % ( config.get(sectionName,"chunk_length") )
    cmd += " -o %s" % ( config.get(sectionName,"chunk_overlap") )
    cmd += " -w 0"
    cmd += " -O %s_chunks" % ( projectName )
    cmd += " -c"
    cmd += " -v %i" % ( verbose - 1 )
    if config.get(sectionName,"clean") == "yes":
        cmd += " -c"
    lCmds.append(cmd)
        
    # save the chunks into batch files
    prg = os.environ["REPET_PATH"] + "/bin/dbSplit.py"
    cmd = prg
    cmd += " -i %s_chunks.fa" % ( projectName )
    cmd += " -n %s" % ( config.get(sectionName,"nb_seq_per_batch") )
    cmd += " -d"
    cmd += " -v %i" % ( verbose - 1 )
    lCmds.append(cmd)
    
    queue = config.get(sectionName, "resources")
    cDir = os.getcwd()
    if config.get(sectionName, "tmpDir" ) != "":
        tmpDir = config.get(sectionName, "tmpDir")
    else:
        tmpDir = cDir
        
    groupid = "%s_TEdenovo_%s_dbChunks_dbSplit" % ( projectName, smplAlign )
    acronym = "dbChunks_dbSplit"
    jobdb = RepetJob(cfgFileName = configFileName)
    cL = Launcher(jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym)
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
    cL.runSingleJob( cmd_start, cmd_finish )
    cL.endRun()
    if config.get(sectionName, "clean") == "yes":
        cL.clean( acronym )
    jobdb.close()

    # if the program is Blaster
    if smplAlign == "Blaster":

        # prepare the subject data bank
        pL.reset( projectName + "_chunks.fa" )
        cmd = pL.launchBlaster( prepareOnly="yes", outPrefix=projectName+"_chunks.fa-BLRaPrepare", run="no" )
        groupid = "%s_TEdenovo_%s_prepareBank" % ( projectName, smplAlign )
        acronym = "prepareBank"
        jobdb = RepetJob( cfgFileName=configFileName )
        cL = Launcher( jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
        cL.beginRun()
        cL.job.jobname = acronym
        cmd_start = "os.system( \"ln -s " "%s/%s_chunks.fa .\" )\n" % ( cDir, projectName )
        cmd_start += "log = os.system( \""
        cmd_start += cmd
        cmd_start += "\" )\n"
        #TODO: if index with WU ? => tests...
        cmd_finish = "if not os.path.exists( \"%s/%s_chunks.fa-BLRaPrepare.param\" ):\n" % ( cDir, projectName )
        cmd_finish += "\tos.system( \"mv %s_chunks.fa-BLRaPrepare.param %s/.\" )\n" % ( projectName, cDir )
        cmd_finish += "if not os.path.exists( \"%s/%s_chunks.fa_cut\" ):\n" % ( cDir, projectName )
        cmd_finish += "\tos.system( \"mv %s_chunks.fa_cut %s/.\" )\n" % ( projectName, cDir )
        cmd_finish += "if not os.path.exists( \"%s/%s_chunks.fa_cut.nhr\" ):\n" % ( cDir, projectName )
        cmd_finish += "\tos.system( \"mv %s_chunks.fa_cut.nhr %s/.\" )\n" % ( projectName, cDir )
        cmd_finish += "if not os.path.exists( \"%s/%s_chunks.fa_cut.nin\" ):\n" % ( cDir, projectName )
        cmd_finish += "\tos.system( \"mv %s_chunks.fa_cut.nin %s/.\" )\n" % ( projectName, cDir )
        cmd_finish += "if not os.path.exists( \"%s/%s_chunks.fa_cut.nsq\" ):\n" % ( cDir, projectName )
        cmd_finish += "\tos.system( \"mv %s_chunks.fa_cut.nsq %s/.\" )\n" % ( projectName, cDir )
        cmd_finish += "if not os.path.exists( \"%s/%s_chunks.fa.Nstretch.map\" ):\n" % ( cDir, projectName )
        cmd_finish += "\tos.system( \"mv %s_chunks.fa.Nstretch.map %s/.\" )\n" % ( projectName, cDir )
        cL.runSingleJob( cmd_start, cmd_finish )
        cL.endRun()
        if config.get(sectionName, "clean") == "yes":
            cL.clean( acronym )
        jobdb.close()

        # launch Blaster on all the chunks in parallel
        prg = os.environ["REPET_PATH"] + "/bin/srptBlasterMatcher.py"
        cmd = prg
        cmd += " -g %s_TEdenovo_%s_srptBlasterMatcher" % ( projectName, smplAlign )
        cmd += " -q %s/%s_%s/batches" % ( projectDir, projectName, smplAlign )
        cmd += " -s %s/%s_%s/%s_chunks.fa" % ( projectDir, projectName, smplAlign, projectName )
        cmd += " -Q \"%s\"" % ( config.get(sectionName,"resources") )
        cmd += " -m 1"   # launch Blaster only
        cmd += " -B \""
        cmd += " -a"
        cmd += " -E " + config.get(sectionName,"Evalue")
        cmd += " -L " + config.get(sectionName,"length")
        cmd += " -I " + config.get(sectionName,"identity")
        if config.get(sectionName,"blast") == "wu":
            cmd += " -W"
            cmd += " -p -cpus=1"
        elif config.get(sectionName,"blast") == "mega":
            cmd += " -n megablast"
        cmd += " -v %i" % ( verbose - 1 )
        cmd += "\""
        if config.get(sectionName,"tmpDir" ) != "":
            cmd += " -d %s" % ( config.get(sectionName,"tmpDir") )
        cmd += " -Z align"
        cmd += " -C %s" % ( configFileName )
        if config.get(sectionName,"clean") == "yes":
            cmd += " -c"
        cmd += " -v %i" % ( verbose - 1 )
        log = os.system( cmd )
        if log != 0:
            print "ERROR: %s returned %i" % ( prg, log )
            sys.exit(1)

        log = os.system( "mv %s_TEdenovo_%s_srptBlasterMatcher.align %s.align" % ( projectName, smplAlign, projectName ) )
        if log != 0:
            print "ERROR while renaming the 'align' file"
            sys.exit(1)

        # clean 'cut' files
        if config.get(sectionName,"clean") == "yes":
            os.system( "rm -f formatdb.log %s_chunks.fa_cut*" % ( projectName ) )


    # if the program is Pals
    elif smplAlign == "Pals":
        
        # launch Pals on all the chunks in parallel
        prg = os.environ["REPET_PATH"] + "/bin/srptPals.py"
        cmd = prg
        cmd += " -t jobs"
        cmd += " -g %s_TEdenovo_%s_srptPals" % ( projectName, smplAlign )
        cmd += " -q %s/%s_%s/batches" % ( projectDir, projectName, smplAlign )
        cmd += " -s " + projectDir + "/" + projectName + "_" + smplAlign + "/" + projectName + "_chunks.fa"
        cmd += " -Q \"%s\"" % ( config.get(sectionName,"resources") )
        if config.get(sectionName,"tmpDir" ) != "":
            cmd += " -d %s" % ( config.get(sectionName,"tmpDir") )
        cmd += " -C %s" % ( configFileName )
        cmd += " -P \""
        cmd += "-length " + config.get(sectionName,"length")  #400
        cmd += " -pctid " + config.get(sectionName,"identity")  #94
        cmd += "\""
        cmd += " -Z"
        cmd += " -a"
        if config.get(sectionName,"clean") == "yes":
            cmd += " -c"
        log = os.system( cmd )
        if log != 0:
            print "ERROR: %s returned %i" % ( prg, log )
            sys.exit(1)

        os.system( "mv %s_TEdenovo_%s_srptPals.align %s.align" % ( projectName, smplAlign, projectName ) )

    # if the program is Yass or Blat or Blast
    elif smplAlign in [ "Yass", "Blat", "Blast" ]:
        prg = os.environ["REPET_PATH"] + "/bin/%sClusterLauncher.py" % ( smplAlign )
        cmd = prg
        cmd += " -i %s/%s_%s/batches" % ( projectDir, projectName, smplAlign )
        cmd += " -Q \"%s\"" % ( config.get(sectionName,"resources") )
        cmd += " -g %s_TEdenovo_%s_%sClusterLauncher" % ( projectName, smplAlign, smplAlign )
        cmd += " -C %s" % ( configFileName )
        if config.get(sectionName,"tmpDir") != "":
            cmd += " -d %s" % ( config.get(sectionName,"tmpDir") )
        cmd += " -j jobs"
        cmd += " -s %s/%s_%s/%s_chunks.fa" % ( projectDir, projectName, smplAlign, projectName )
        if smplAlign == "Yass":
            cmd += " -p \"-E %s\"" % ( config.get(sectionName,"Evalue") )
        elif smplAlign == "Blat":
            cmd += " -p \"-minIdentity=%s\"" % ( config.get(sectionName,"identity") )
        elif smplAlign == "Blast":
            cmd += " -p blastn -P \"-F F -e %s\"" % ( config.get(sectionName,"Evalue") )
        cmd += " -Z"
        cmd += " -A"
        if config.get(sectionName,"clean") == "yes":
            cmd += " -c"
        cmd += " -v %i" % ( verbose - 1 )
        log = os.system( cmd )
        if log != 0:
            print "ERROR: %s returned %i" % ( prg, log )
            sys.exit(1)
            
        os.system( "mv %s_TEdenovo_%sClusterLauncher.align %s.align" % ( projectName, smplAlign, projectName ) )

    # remove the chunk overlaps
    prg = os.environ["REPET_PATH"] + "/bin/RmvPairAlignInChunkOverlaps.py"
    cmd = prg
    cmd += " -i %s.align" % ( projectName) 
    cmd += " -l %s" % config.get(sectionName,"chunk_length") 
    cmd += " -o %s" % config.get(sectionName,"chunk_overlap")
    cmd += " -m %d" % 10
    cmd += " -O %s.align.not_over" % ( projectName )
    cmd += " -v %d" % (verbose - 1 )
     
    cmd_start = ""
    cmd_start += "os.system( \"ln -s %s/%s.align %s.align\" )\n" % ( cDir, projectName, projectName )      
    cmd_start += "log = os.system( \""
    cmd_start += cmd
    cmd_start += "\" )\n"
            
    cmd_finish = "os.system( \"mv %s.align.not_over %s/.\" )\n" % ( projectName, cDir )
    
    groupid = "%s_TEdenovo_%s_RmvPairAlignInChunkOverlaps" % ( projectName, smplAlign )
    acronym = "RmvPairAlignInChunkOverlaps"
    jobdb = RepetJob( cfgFileName=configFileName )
    cL = Launcher( jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
    cL.beginRun()
    cL.job.jobname = acronym
    cL.runSingleJob( cmd_start, cmd_finish )
    cL.endRun()
    if config.get(sectionName, "clean") == "yes":
        cL.clean( acronym )
    jobdb.close()
        
    # filter the HSPs
    if config.get(sectionName,"filter_HSP") == "yes":
        prg = os.environ["REPET_PATH"] + "/bin/FilterAlign.py"
        cmd = prg
        cmd += " -i "
        cmd += "%s.align.not_over" % ( projectName )
        cmd += " -E %s" % ( config.get(sectionName,"min_Evalue") )
        cmd += " -I %s" % ( config.get(sectionName,"min_identity") )
        cmd += " -l %s" % ( config.get(sectionName,"min_length") )
        cmd += " -L %s" % ( config.get(sectionName,"max_length") )
        cmd += " -v %i" % ( verbose - 1 )
        
        groupid = "%s_TEdenovo_%s_FilterAlign" % ( projectName, smplAlign )
        acronym = "FilterAlign"
        jobdb = RepetJob( cfgFileName=configFileName )
        cL = Launcher( jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
        cmd_start = "os.system( \"ln -s %s/%s.align.not_over %s.align.not_over\" )\n" % ( cDir, projectName, projectName )  
        cmd_start += "log = os.system( \""
        cmd_start += cmd
        cmd_start += "\" )\n"
        cmd_finish = "os.system( \"mv %s.align.not_over.filtered  %s/.\" )\n" % ( projectName, cDir )
        cL.beginRun()
        cL.job.jobname = acronym
        cL.runSingleJob( cmd_start, cmd_finish )
        cL.endRun()
        if config.get(sectionName, "clean") == "yes":
            cL.clean( acronym )
        jobdb.close()
        
    # clean
    if config.get(sectionName,"clean") == "yes":

        # for each job, remove the file containing the HSPs
        cmd = "find . -name \"batch_*.align\" -exec rm {} \;"
        log = os.system( cmd )
        if log != 0:
            print "ERROR while removing the 'align' files from the jobs"
            sys.exit(1)

        # remove the files "_cut"
        cmd = "find . -name \"%s*_cut*\" -exec rm {} \;" % ( projectName )
        log = os.system( cmd )
        if log != 0:
            print "ERROR while removing the '_cut' files"
            sys.exit(1)

        # remove the files "Nstretch.map"
        cmd = "find . -name \"*Nstretch.map\" -exec rm {} \;"
        log = os.system( cmd )
        if log != 0:
            print "ERROR while removing the 'Nstretch.map' files"
            sys.exit(1)

        # remove the temporary file(s) with the HSPs
        if config.get(sectionName,"filter_HSP") == "yes":
            cmd = "rm -f %s.align %s.align.not_over" % ( projectName, projectName )
            log = os.system( cmd )
            if log != 0:
                print "ERROR while removing an intermediary file"
                sys.exit(1)

        # remove the genomic sequences (symlink and batches)
        os.system( "rm -rf %s.fa batches" % ( projectName ) )

    os.chdir( ".." )

    if verbose > 0:
        print "step 1 finished successfully"; sys.stdout.flush()

#------------------------------------------------------------------------------

def clusterHsp( smplAlign, clustHsp ):
    """
    step 2: cluster the resulting HSPs (high-scoring segment pairs)

    @param smplAlign: name of the alignment program (Blaster or Pals)
    @type smplAlign: string

    @param clustHsp: name of the clustering program (Grouper, Recon or Piler)
    @type clustHsp: string
    """

    if verbose > 0:
        print "beginning of step 2"
        print "self-alignment with %s" % ( smplAlign )
        print "clustering with %s" % ( clustHsp )
        sys.stdout.flush()

    sectionName = "self_align"
    sectionNameClusterHSP = "cluster_HSPs"
    try:
        CheckerUtils.checkSectionInConfigFile(config, sectionNameClusterHSP)
    except NoSectionError:
        print "ERROR: " + sectionNameClusterHSP + " must be in your config file : " + configFileName
        sys.exit(1)

    if clustHsp == "Grouper" or clustHsp == "Recon" or clustHsp == "Piler":
        if os.path.exists( projectName + "_" + smplAlign + "_" + clustHsp ):
            print "ERROR: directory " + projectName + "_" + smplAlign + "_" + clustHsp +"/ already exists"
            sys.exit(1)
            
        try:
            CheckerUtils.checkOptionInSectionInConfigFile(config, sectionNameClusterHSP, "minNbSeqPerGroup") 
        except NoOptionError:
            print "ERROR: the option minNbSeqPerGroup must be define in " + sectionNameClusterHSP +" in your config file : " + configFileName
            sys.exit(1)
        try:
            CheckerUtils.checkOptionInSectionInConfigFile(config, sectionNameClusterHSP, "nbLongestSeqPerGroup") 
        except NoOptionError:
            print "ERROR: the option nbLongestSeqPerGroup must be define in " + sectionNameClusterHSP +" in your config file : " + configFileName
            sys.exit(1)
        try:
            CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "filter_HSP") 
        except NoOptionError:
            print "ERROR: the option filter_HSP must be define in " + sectionName +" in your config file : " + configFileName
            sys.exit(1)
            
        if int(config.get(sectionNameClusterHSP, "minNbSeqPerGroup")) < 3:
            print "ERROR: groups with less than %i members should be filtered out" % ( int(config.get(sectionNameClusterHSP, "minNbSeqPerGroup")) )
            print "as they are likely to correspond to segmental duplications"
            print "change this parameter value in your configuration file"
            sys.exit(1)

        os.mkdir( projectName + "_" + smplAlign + "_" + clustHsp )
        os.chdir( projectName + "_" + smplAlign + "_" + clustHsp )

        prefix = projectName + "_" + smplAlign + "_" + clustHsp + "_"
        prefix += config.get(sectionNameClusterHSP, "minNbSeqPerGroup") + "elem_"
        prefix += config.get(sectionNameClusterHSP, "nbLongestSeqPerGroup") + "seq"

        alignFileName = projectName + ".align"
        alignFileName += ".not_over"
        if config.get(sectionName, "filter_HSP") == "yes":
            alignFileName += ".filtered"
        pathToAlignFile = "%s/%s_%s/%s" % ( projectDir, projectName, smplAlign, alignFileName )
        if os.path.exists( "%s.onChr" % ( pathToAlignFile ) ):
            alignFileName += ".onChr"
            pathToAlignFile += ".onChr"

        bankName = projectName
        bankName += "_chunks.fa"
        if "onChr" in alignFileName:
            bankName = "%s.fa" % ( projectName )
        pathToFasta = "%s/%s_%s/%s" % ( projectDir, projectName, smplAlign, bankName )

        os.system( "ln -s " + pathToAlignFile + " " + alignFileName )
        os.system( "ln -s %s ." % pathToFasta )

        #----------------------------------------------------------------------

        lCmds = []
        minSeq = config.get(sectionNameClusterHSP, "minNbSeqPerGroup")
        maxSeq = config.get(sectionNameClusterHSP, "nbLongestSeqPerGroup")

        try:
            CheckerUtils.checkOptionInSectionInConfigFile(config, sectionNameClusterHSP, "clean") 
        except NoOptionError:
            print "ERROR: the option 'clean' must be define in " + sectionNameClusterHSP +" in your config file : " + configFileName
            sys.exit(1)
        try:
            CheckerUtils.checkOptionInSectionInConfigFile(config, sectionNameClusterHSP, "maxSeqLength") 
        except NoOptionError:
            print "ERROR: the option 'maxSeqLength' must be define in " + sectionNameClusterHSP +" in your config file : " + configFileName
            sys.exit(1)
                
        try:
            CheckerUtils.checkOptionInSectionInConfigFile(config, sectionNameClusterHSP, "resources") 
        except NoOptionError:
            print "ERROR: the option 'resources' must be define in " + sectionNameClusterHSP +" in your config file : " + configFileName
            sys.exit(1)
        try:
            CheckerUtils.checkOptionInSectionInConfigFile(config, sectionNameClusterHSP, "tmpDir") 
        except NoOptionError:
            print "ERROR: the option 'tmpDir' must be define in " + sectionNameClusterHSP +" in your config file : " + configFileName
            sys.exit(1)
        os.system( "ln -s ../%s ." % ( configFileName ) )
        queue = config.get(sectionNameClusterHSP, "resources")
        cDir = os.getcwd()
        if config.get(sectionNameClusterHSP, "tmpDir" ) != "":
            tmpDir = config.get(sectionNameClusterHSP, "tmpDir")
        else:
            tmpDir = cDir
        groupid = "%s_TEdenovo_%s_%s" % ( projectName, smplAlign, clustHsp )
        acronym = clustHsp
        jobdb = RepetJob( cfgFileName=configFileName )
        cL = Launcher( jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
        cL.beginRun()
        cL.job.jobname = acronym
        cmd_start = ""
        cmd_start += "os.system( \"ln -s %s/%s .\" )\n" % (cDir, bankName)
        cmd_start += "os.system( \"ln -s %s/%s .\" )\n" % (cDir, alignFileName)
        cmd_finish = ""
        cmd_finish += "if os.path.exists( \"%s/%s\" ):\n" % (tmpDir, bankName)
        cmd_finish += "\tos.system( \"rm -f %s/%s\" )\n" % (tmpDir, bankName)
        cmd_finish += "if os.path.exists( \"%s/%s\" ):\n" % (tmpDir, alignFileName)
        cmd_finish += "\tos.system( \"rm -f %s/%s\" )\n" % (tmpDir, alignFileName)

        if clustHsp == "Grouper":
            try:
                CheckerUtils.checkOptionInSectionInConfigFile(config, sectionNameClusterHSP, "Grouper_coverage") 
            except NoOptionError:
                print "ERROR: the option Grouper_coverage must be define in '%s' in your config file : %s" % (sectionNameClusterHSP, configFileName)
                sys.exit(1)
            try:
                CheckerUtils.checkOptionInSectionInConfigFile(config, sectionNameClusterHSP, "Grouper_join") 
            except NoOptionError:
                print "ERROR: the option Grouper_join must be define in '%s' in your config file : %s" % (sectionNameClusterHSP, configFileName)
                sys.exit(1)
            try:
                CheckerUtils.checkOptionInSectionInConfigFile(config, sectionNameClusterHSP, "Grouper_include") 
            except NoOptionError:
                print "ERROR: the option Grouper_include must be define in '%s' in your config file : %s" % (sectionNameClusterHSP, configFileName)
                sys.exit(1)
            try:
                CheckerUtils.checkOptionInSectionInConfigFile(config, sectionNameClusterHSP, "Grouper_maxJoinLength") 
            except NoOptionError:
                print "ERROR: the option Grouper_maxJoinLength must be define in '%s' in your config file : %s" % (sectionNameClusterHSP, configFileName)
                sys.exit(1)
            coverage = config.get(sectionNameClusterHSP, "Grouper_coverage")
            prg = "%s/bin/grouper" % os.environ["REPET_PATH"]
            cmd = prg
            cmd += " -q %s" % bankName
            cmd += " -s %s" % bankName
            cmd += " -m %s" % alignFileName
            if config.get(sectionNameClusterHSP, "Grouper_join") == "yes":
                cmd += " -j"
            cmd += " -C %s" % coverage
            cmd += " -Z %s" % config.get(sectionNameClusterHSP, "minNbSeqPerGroup")
            cmd += " -X %s" % config.get(sectionNameClusterHSP, "Grouper_include")
            cmd += " -G -1"
            cmd += " -v %i" % verbose
            lCmds.append(cmd)
            cmd_finish += "if not os.path.exists( \"" + cDir + "/" + alignFileName + ".group.c" + coverage + ".fa \" ):\n"
            cmd_finish += "\tos.system( \"mv " + alignFileName + ".group.c" + coverage + ".fa " + cDir + "\" )\n"
            cmd_finish += "if not os.path.exists( \"" + cDir + "/" + alignFileName + ".group.c" + coverage + ".map \" ):\n"
            cmd_finish += "\tos.system( \"mv " + alignFileName + ".group.c" + coverage + ".map " + cDir + "\" )\n"
            cmd_finish += "if not os.path.exists( \"" + cDir + "/" + alignFileName + ".group.c" + coverage + ".param \" ):\n"
            cmd_finish += "\tos.system( \"mv " + alignFileName + ".group.c" + coverage + ".param " + cDir + "\" )\n"
            cmd_finish += "if not os.path.exists( \"" + cDir + "/" + alignFileName + ".group.c" + coverage + ".set \" ):\n"
            cmd_finish += "\tos.system( \"mv " + alignFileName + ".group.c" + coverage + ".set " + cDir + "\" )\n"
            cmd_finish += "if not os.path.exists( \"" + cDir + "/" + alignFileName + ".group.c" + coverage + ".txt \" ):\n"
            cmd_finish += "\tos.system( \"mv " + alignFileName + ".group.c" + coverage + ".txt " + cDir + "\" )\n"
            cmd_finish += "if not os.path.exists( \"" + cDir + "/" + alignFileName + ".chains.path \" ):\n"
            cmd_finish += "\tos.system( \"mv " + alignFileName + ".chains.path " + cDir + "\" )\n"
            prg = os.environ["REPET_PATH"] + "/bin/filterOutGrouper.py"
            cmd = prg
            cmd += " -i %s.group.c%s.fa" % ( alignFileName, config.get(sectionNameClusterHSP, "Grouper_coverage") )
            cmd += " -m %s" % ( minSeq )
            cmd += " -M %s" % ( maxSeq )
            cmd += " -L %s" % ( config.get(sectionNameClusterHSP, "maxSeqLength" ) )
            cmd += " -J %s" % ( config.get(sectionNameClusterHSP, "Grouper_maxJoinLength" ) )
            if "onChr" not in alignFileName:
                try:
                    CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, "chunk_overlap") 
                except NoOptionError:
                    print "ERROR: the option chunk_overlap must be define in '%s' in your config file : %s" % (sectionName, configFileName)
                    sys.exit(1)
                cmd += " -O %s" % config.get(sectionName, "chunk_overlap")
            else:
                cmd += " -O -1"
            cmd += " -o %s_%s_%s_%selem_%sseq.fa" % ( projectName, smplAlign, clustHsp, minSeq, maxSeq )
            cmd += " -v %i" % ( verbose - 1 )
            lCmds.append( cmd )
            cmd_finish += "if not os.path.exists( \"%s/%s_%s_%s_%selem_%sseq.fa\" ):\n" % ( cDir, projectName, smplAlign, clustHsp, minSeq, maxSeq )
            cmd_finish += "\tos.system( \"mv %s_%s_%s_%selem_%sseq.fa %s\" )\n" % ( projectName, smplAlign, clustHsp, minSeq, maxSeq, cDir )
            cmd_finish += "if not os.path.exists( \"%s/%s.group.c%s.fa_filtered.log\" ):\n" % ( cDir, alignFileName, config.get(sectionNameClusterHSP, "Grouper_coverage") )
            cmd_finish += "\tos.system( \"mv %s.group.c%s.fa_filtered.log %s\" )\n" % ( alignFileName, config.get(sectionNameClusterHSP, "Grouper_coverage"), cDir )

        elif clustHsp == "Recon":
            if not CheckerUtils.isExecutableInUserPath("recon.pl") :
                print "ERROR: recon.pl must be in your path"
                sys.exit(1)
            prg = os.environ["REPET_PATH"] + "/bin/launchRecon.py"
            cmd = prg
            cmd += " -p %s_%s" % (projectName, smplAlign)
            cmd += " -f %s" % bankName
            cmd += " -a %s"  % alignFileName
            if config.get(sectionNameClusterHSP, "clean") == "yes":
                cmd += " -c"
            cmd += " -v %i" % ( verbose - 1 )
            lCmds.append(cmd)
            cmd_finish += "if not os.path.exists( \"" + cDir + "/" + projectName + "_" + smplAlign + "_Recon.map \" ):\n"
            cmd_finish += "\tos.system( \"mv " + projectName + "_" + smplAlign + "_Recon.map " + cDir + "\" )\n"
            cmd_finish += "if not os.path.exists( \"" + cDir + "/" + projectName + "_" + smplAlign + "_Recon.fa \" ):\n"
            cmd_finish += "\tos.system( \"mv " + projectName + "_" + smplAlign + "_Recon.fa " + cDir + "\" )\n"
            cmd_finish += "if not os.path.exists( \"" + cDir + "/" + projectName + "_" + smplAlign + "_MSP_file \" ):\n"
            cmd_finish += "\tos.system( \"mv " + projectName + "_" + smplAlign + "_MSP_file " + cDir + "\" )\n"
            cmd_finish += "if not os.path.exists( \"" + cDir + "/" + projectName + "_" + smplAlign + "_seq_list \" ):\n"
            cmd_finish += "\tos.system( \"mv " + projectName + "_" + smplAlign + "_seq_list " + cDir + "\" )\n"
            
            if config.get(sectionNameClusterHSP, "clean") == "no":
                cmd_finish += "if not os.path.exists( \"" + cDir + "/images\" ):\n"
                cmd_finish += "\tshutil.move( 'images', '" + cDir + "/images' )\n"
                cmd_finish += "if not os.path.exists( \"" + cDir + "/ele_def_res\" ):\n"
                cmd_finish += "\tshutil.move( 'ele_def_res', '" + cDir + "/ele_def_res' )\n"
                cmd_finish += "if not os.path.exists( \"" + cDir + "/ele_redef_res\" ):\n"
                cmd_finish += "\tshutil.move( 'ele_redef_res', '" + cDir + "/ele_redef_res' )\n"
                cmd_finish += "if not os.path.exists( \"" + cDir + "/edge_redef_res\" ):\n"
                cmd_finish += "\tshutil.move( 'edge_redef_res', '" + cDir + "/edge_redef_res' )\n"
                cmd_finish += "if not os.path.exists( \"" + cDir + "/summary\" ):\n"
                cmd_finish += "\tshutil.move( 'summary', '" + cDir + "/summary' )\n"
            prg = "%s/bin/filterSeqClusters.py" % os.environ["REPET_PATH"]
            cmd = prg
            cmd += " -i %s_%s_%s.map" % (projectName, smplAlign, clustHsp)
            cmd += " -c %s" % clustHsp
            cmd += " -m %s" % minSeq
            cmd += " -M %s" % maxSeq
            cmd += " -L %s" % config.get(sectionNameClusterHSP, "maxSeqLength" )
            cmd += " -d"
            cmd += " -v %i" % ( verbose - 1 )
            lCmds.append(cmd)
            prg = "%s/bin/map2db" % os.environ["REPET_PATH"]
            cmd = prg
            cmd += " %s_%s_%s.map.filtered-%s-%s" % (projectName, smplAlign, clustHsp, minSeq, maxSeq)
            cmd += " %s" % bankName
            lCmds.append(cmd)
            cmd_finish += "if not os.path.exists( \"%s/%s_%s_%s.map.filtered-%s-%s\" ):\n" % ( cDir, projectName, smplAlign, clustHsp, minSeq, maxSeq )
            cmd_finish += "\tos.system( \"mv %s_%s_%s.map.filtered-%s-%s %s\" )\n" % ( projectName, smplAlign, clustHsp, minSeq, maxSeq, cDir )
            cmd_finish += "if not os.path.exists( \"%s/%s_%s_%s.map_filtered.log\" ):\n" % ( cDir,projectName, smplAlign, clustHsp )
            cmd_finish += "\tos.system( \"mv %s_%s_%s.map_filtered.log %s\" )\n" % ( projectName, smplAlign, clustHsp, cDir )
            cmd_finish += "if not os.path.exists( \"%s/%s_%s_%s.map.distribC\" ):\n" % ( cDir, projectName, smplAlign, clustHsp )
            cmd_finish += "\tos.system( \"mv %s_%s_%s.map.distribC %s\" )\n" % ( projectName, smplAlign, clustHsp, cDir )
            cmd_finish += "if not os.path.exists( \"%s/%s_%s_%s.map.filtered-%s-%s.flank_size0.fa\" ):\n" % ( cDir, projectName, smplAlign, clustHsp, minSeq, maxSeq )
            cmd_finish += "\tos.system( \"mv %s_%s_%s.map.filtered-%s-%s.flank_size0.fa %s\" )\n" % ( projectName, smplAlign, clustHsp, minSeq, maxSeq, cDir )

        elif clustHsp == "Piler":
            if not CheckerUtils.isExecutableInUserPath("piler") :
                print "ERROR: piler must be in your path"
                sys.exit(1)
            prg = "%s/bin/launchPiler.py" % os.environ["REPET_PATH"]
            cmd = prg
            cmd += " -p %s_%s" % (projectName, smplAlign)
            cmd += " -f %s" % bankName
            cmd += " -a %s"  % alignFileName
            if config.get(sectionNameClusterHSP, "clean") == "yes":
                cmd += " -c"
            cmd += " -v %i" % ( verbose - 1 )
            lCmds.append(cmd)
            cmd_finish += "if not os.path.exists( \"" + cDir + "/" + projectName + "_" + smplAlign + "_Piler.map \" ):\n"
            cmd_finish += "\tos.system( \"mv " + projectName + "_" + smplAlign + "_Piler.map " + cDir + "\" )\n"
            cmd_finish += "if not os.path.exists( \"" + cDir + "/" + projectName + "_" + smplAlign + "_Piler.fa \" ):\n"
            cmd_finish += "\tos.system( \"mv " + projectName + "_" + smplAlign + "_Piler.fa " + cDir + "\" )\n"
            cmd_finish += "if not os.path.exists( \"" + cDir + "/" + alignFileName + ".gff \" ):\n"
            cmd_finish += "\tos.system( \"mv " + alignFileName + ".gff " + cDir + "\" )\n"
            cmd_finish += "if not os.path.exists( \"" + cDir + "/" + projectName + "_" + smplAlign + "_Piler-trs.gff \" ):\n"
            cmd_finish += "\tos.system( \"mv " + projectName + "_" + smplAlign + "_Piler-trs.gff " + cDir + "\" )\n"
            prg = os.environ["REPET_PATH"] + "/bin/filterSeqClusters.py"
            cmd = prg
            cmd += " -i %s_%s_%s.map" % (projectName, smplAlign, clustHsp)
            cmd += " -c %s" % clustHsp
            cmd += " -m %s" % minSeq
            cmd += " -M %s" % maxSeq
            cmd += " -L %s" % config.get(sectionNameClusterHSP, "maxSeqLength" )
            cmd += " -d"
            cmd += " -v %i" % ( verbose - 1 )
            lCmds.append(cmd)
            prg = "%s/bin/map2db" % os.environ["REPET_PATH"]
            cmd = prg
            cmd += " %s_%s_%s.map.filtered-%s-%s" % (projectName, smplAlign, clustHsp, minSeq, maxSeq)
            cmd += " %s" % bankName
            lCmds.append(cmd)
            cmd_finish += "if not os.path.exists( \"%s/%s_%s_%s.map.filtered-%s-%s\" ):\n" % ( cDir, projectName, smplAlign, clustHsp, minSeq, maxSeq )
            cmd_finish += "\tos.system( \"mv %s_%s_%s.map.filtered-%s-%s %s\" )\n" % ( projectName, smplAlign, clustHsp, minSeq, maxSeq, cDir )
            cmd_finish += "if not os.path.exists( \"%s/%s_%s_%s.map_filtered.log\" ):\n" % ( cDir,projectName, smplAlign, clustHsp )
            cmd_finish += "\tos.system( \"mv %s_%s_%s.map_filtered.log %s\" )\n" % ( projectName, smplAlign, clustHsp, cDir )
            cmd_finish += "if not os.path.exists( \"%s/%s_%s_%s.map.distribC\" ):\n" % ( cDir, projectName, smplAlign, clustHsp )
            cmd_finish += "\tos.system( \"mv %s_%s_%s.map.distribC %s\" )\n" % ( projectName, smplAlign, clustHsp, cDir )
            cmd_finish += "if not os.path.exists( \"%s/%s_%s_%s.map.filtered-%s-%s.flank_size0.fa\" ):\n" % ( cDir, projectName, smplAlign, clustHsp, minSeq, maxSeq )
            cmd_finish += "\tos.system( \"mv %s_%s_%s.map.filtered-%s-%s.flank_size0.fa %s\" )\n" % ( projectName, smplAlign, clustHsp, minSeq, maxSeq, cDir )

        for c in lCmds:
            cmd_start += "log = os.system( \""
            cmd_start += c
            cmd_start += "\" )\n"
        cL.runSingleJob( cmd_start, cmd_finish )
        cL.endRun()
        if config.get(sectionNameClusterHSP, "clean") == "yes":
            cL.clean( clustHsp )
        jobdb.close()

        if clustHsp in [ "Recon", "Piler" ]:
            cmd = "ln -s"
            cmd += " %s_%s_%s.map.filtered-%s-%s.flank_size0.fa" % (projectName, smplAlign, clustHsp, minSeq, maxSeq)
            cmd += " %s_%s_%s_%selem_%sseq.fa" % (projectName, smplAlign, clustHsp, minSeq, maxSeq)
            log = os.system( cmd )
            if log != 0:
                print "ERROR with command '%s'" % cmd
                sys.exit(1)

        os.chdir( ".." )

    #--------------------------------------------------------------------------

    elif clustHsp == "":
        print "ERROR: missing option -c"
        help()
        sys.exit(1)

    else:
        print "ERROR: unknown option -c %s" % ( clustHsp )
        sys.exit(1)

    if verbose > 0:
        print "step 2 finished successfully"; sys.stdout.flush()

#------------------------------------------------------------------------------

def buildConsensus( smplAlign, clustHsp, multAlign ):

    """
    step 3: build consensus from multiple alignments

    @param smplAlign: name of the alignment program (Blaster or Pals)
    @type smplAlign: string

    @param clustHsp: name of the clustering program (Grouper, Recon or Piler)
    @type clustHsp: string

    @param multAlign: name of the multiple alignment program MSA (MAP, Mafft, Muscle, Tcoffee, ClustalW or Prank)
    @type multAlign: string
    """

    if verbose > 0:
        print "beginning of step 3"
        print "self-alignment with %s" % ( smplAlign )
        print "clustering with %s" % ( clustHsp )
        print "multiple alignment with %s" % ( multAlign )
        sys.stdout.flush()

    isOptionErrorRaised = False

    sectionNameClusterHSPs = "cluster_HSPs"
    try:
        CheckerUtils.checkSectionInConfigFile(config, sectionNameClusterHSPs) 
    except NoSectionError:
        print "ERROR: the section '%s' must be define in your config file : %s" % (sectionNameClusterHSPs, configFileName)
        sys.exit(1)
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionNameClusterHSPs, "minNbSeqPerGroup") 
    except NoOptionError:
        print "ERROR: the option 'minNbSeqPerGroup' must be define in '%s' in your config file : %s" % (sectionNameClusterHSPs, configFileName)
        isOptionErrorRaised = True
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionNameClusterHSPs, "nbLongestSeqPerGroup") 
    except NoOptionError:
        print "ERROR: the option 'nbLongestSeqPerGroup' must be define in '%s' in your config file : %s" % (sectionNameClusterHSPs, configFileName)
        isOptionErrorRaised = True
   
    sectionNameBuildConsensus = "build_consensus" 
    try:
        CheckerUtils.checkSectionInConfigFile(config, sectionNameBuildConsensus) 
    except NoSectionError:
        print "ERROR: the section '%s' must be define in your config file : %s" % (sectionNameBuildConsensus, configFileName)
        sys.exit(1)
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionNameBuildConsensus, "resources") 
    except NoOptionError:
        print "ERROR: the option 'resources' must be define in '%s' in your config file : %s" % (sectionNameBuildConsensus, configFileName)
        isOptionErrorRaised = True
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionNameBuildConsensus, "tmpDir") 
    except NoOptionError:
        print "ERROR: the option 'tmpDir' must be define in '%s' in your config file : %s" % (sectionNameBuildConsensus, configFileName)
        isOptionErrorRaised = True
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionNameBuildConsensus, "minBasesPerSite") 
    except NoOptionError:
        print "ERROR: the option 'minBasesPerSite' must be define in '%s' in your config file : %s" % (sectionNameBuildConsensus, configFileName)
        isOptionErrorRaised = True
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionNameBuildConsensus, "clean") 
    except NoOptionError:
        print "ERROR: the option 'clean' must be define in  in your config file : %s" % (sectionNameBuildConsensus, configFileName)
        isOptionErrorRaised = True
    
    if isOptionErrorRaised:
        sys.exit(1)
    
    prefix1 = projectName + "_" + smplAlign + "_" + clustHsp
    prefix2 = prefix1
    prefix2 += "_" + config.get(sectionNameClusterHSPs, "minNbSeqPerGroup") + "elem_"
    prefix2 += config.get(sectionNameClusterHSPs, "nbLongestSeqPerGroup") + "seq"

    if clustHsp == "Grouper" or clustHsp == "Recon" or clustHsp == "Piler":

        if not os.path.exists( "%s/%s.fa" % ( prefix1, prefix2 ) ):
            print "ERROR: %s/%s.fa not found" % ( prefix1, prefix2 )
            sys.exit(1)

        if os.path.exists( "%s_%s" % ( prefix1, multAlign ) ):
            print "ERROR: directory %s_%s/ already exists" % ( prefix1, multAlign )
            sys.exit(1)

        if multAlign not in ["Map","MAP","Mafft","Clustalw","Muscle","Prank","Tcoffee"]:
            print "ERROR: %s not implememented" % ( multAlign )
            sys.exit(1)

        os.mkdir( "%s_%s" % ( prefix1, multAlign ) )
        os.chdir( "%s_%s" % ( prefix1, multAlign ) )
        
        os.system( "ln -s ../%s ." % ( configFileName ) )
        queue = config.get(sectionNameBuildConsensus, "resources")
        cDir = os.getcwd()
        if config.get(sectionNameBuildConsensus, "tmpDir" ) != "":
            tmpDir = config.get(sectionNameBuildConsensus, "tmpDir")
        else:
            tmpDir = cDir
        
        prg = os.environ["REPET_PATH"] + "/bin/splitSeqPerCluster.py"
        cmd = prg
        
        cmd += " -i " + prefix2 + ".fa"
        cmd += " -c %s" % ( clustHsp )
        cmd += " -v %i" % ( verbose - 1 )
        
        groupid = "%s_TEdenovo_%s_%s_splitSeqPerCluster" % ( projectName, clustHsp, multAlign )
        acronym = "splitSeqPerCluster"
        jobdb = RepetJob( cfgFileName = configFileName )
        cL = Launcher( jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
        cmd_start = "os.system( \"ln -s %s/%s/%s.fa .\" )\n" % ( projectDir, prefix1, prefix2 )
        cmd_start += "log = os.system( \""
        cmd_start += cmd
        cmd_start += "\" )\n"
        cmd_finish = "os.system( \"find . -type f -name 'seqCluster*.fa' -exec mv {} %s/. \\;\" )\n" % ( cDir )
        cL.beginRun()
        cL.job.jobname = acronym
        cL.runSingleJob( cmd_start, cmd_finish )
        cL.endRun()
        if config.get(sectionNameBuildConsensus, "clean") == "yes":
            cL.clean( acronym )
        jobdb.close()
                
        mapChunkFile = "%s/%s_%s/%s_chunks.map" % ( projectDir, projectName, smplAlign, projectName )
        if os.path.exists( mapChunkFile ):
            lFiles = glob.glob( "seqCluster*.fa" )
            f = open( lFiles[0] )
            if "chunk" in f.readline():
                f.close()
                prg = "%s/bin/ConvertFastaHeadersFromChkToChr.py" % os.environ["REPET_PATH"]
                groupid = "%s_TEdenovo_%s_%s_convertFastaHeadersFromChkToChr" % ( projectName, clustHsp, multAlign )
                acronym = "convertFastaHeadersFromChkToChr"
                jobdb = RepetJob( cfgFileName = configFileName )
                cL = Launcher( jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
                cL.beginRun()
                cmd = prg
                cmd += " -i '%s/seqCluster*.fa'" % ( os.getcwd() )
                cmd += " -m %s" % ( mapChunkFile )
                cmd += " -v %i" % ( verbose - 1 )
                cmd_start = "log = os.system( \""
                cmd_start += cmd
                cmd_start += "\" )\n"
                cmd_finish = ""
                cL.job.jobname = acronym
                cL.runSingleJob( cmd_start, cmd_finish )
                cL.endRun()
                if config.get(sectionNameBuildConsensus, "clean") == "yes":
                    cL.clean( acronym )
                jobdb.close()
                for f in lFiles:         
                    os.rename( f, "%s.onChk" % ( f ) )
                    os.rename( "%s.onChr" % ( f ), f )
            else:
                f.close()

        if multAlign == "Mafft" and not CheckerUtils.isExecutableInUserPath("mafft") :
                print "ERROR: mafft must be in your path"
                sys.exit(1)
        if multAlign == "Clustalw" and not CheckerUtils.isExecutableInUserPath("clustalw") :
                print "ERROR: clustalw must be in your path"
                sys.exit(1)
        if multAlign == "Muscle" and not CheckerUtils.isExecutableInUserPath("muscle") :
                print "ERROR: muscle must be in your path"
                sys.exit(1)       
        if multAlign == "Tcoffee" and not CheckerUtils.isExecutableInUserPath("t_coffee") :
                print "ERROR: t_coffee must be in your path"
                sys.exit(1)
        if multAlign == "Prank" and not CheckerUtils.isExecutableInUserPath("prank") :
                print "ERROR: prank must be in your path"
                sys.exit(1) 
        if multAlign in [ "Clustalw", "Muscle", "Tcoffee", "Prank" ]:
            prg = os.environ["REPET_PATH"] + "/bin/srpt%s.py" % ( multAlign )
            cmd = prg
            cmd += " -g %s_TEdenovo_%s_%s_%s" % ( projectName, smplAlign, clustHsp, multAlign )
            cmd += " -q %s" % ( os.getcwd() )
            cmd += " -Q \"%s\"" % ( config.get(sectionNameBuildConsensus, "resources") )
            if config.get(sectionNameBuildConsensus, "tmpDir" ) != "":
                cmd += " -d %s" % ( config.get(sectionNameBuildConsensus, "tmpDir") )
            if config.get(sectionNameBuildConsensus, "clean") == "yes":
                cmd += " -c"
            if multAlign == "Prank":
                cmd += " -P \"%s\"" % ( "-f=8 -noxml -notree -F -quiet" )
            elif multAlign == "Tcoffee":
                cmd += " -P \"%s\"" % ( "-type dna -output fasta_aln" )
            pL.launch( prg, cmd )
        elif multAlign in [ "Map", "MAP", "Mafft" ]:
            if multAlign in [ "Map", "MAP" ]:
                cL = MapClusterLauncher()
            elif multAlign == "Mafft":
                cL = MafftClusterLauncher()
            cL.setInputDirectory( os.getcwd() )
            cL.setQueueName( config.get(sectionNameBuildConsensus, "resources") )
            cL.setGroupIdentifier( "%s_TEdenovo_%s_%s_%s" % ( \
                    projectName, smplAlign, clustHsp, multAlign ) )
            cL.setAcronym( multAlign )
            cL.setConfigFile( "%s/%s" % ( \
                    config.get("project","project_dir"), configFileName ) )
            cL.setTemporaryDirectory( config.get(sectionNameBuildConsensus, "tmpDir" ) )
            if config.get(sectionNameBuildConsensus, "clean" ) == "yes":
                cL.setClean()
            cL.setVerbosityLevel( verbose )
            cL.setSingleProgramLauncher()
            try :
                cL.run()
            except CheckerException, e:
                print e.message
                sys.exit(1)

        # build the consensus for each MSA and concatenate them into a single fasta file
        prg = os.environ["REPET_PATH"] + "/bin/buildConsLib.py"
        cmd = prg
        
        cmd += " -d %s" % ( os.getcwd() )
        cmd += " -r \'*.fa_aln\'"
        cmd += " -n %s" % ( config.get(sectionNameBuildConsensus, "minBasesPerSite") )
        cmd += " -o %s_%s_consensus.fa" % ( prefix1, multAlign )
        if config.get(sectionNameBuildConsensus, "clean") == "yes":
            cmd += " -c"
        cmd += " -v %i" % ( verbose - 1 )
        
        groupid = "%s_TEdenovo_%s_%s_buildConsLib" % ( projectName, clustHsp, multAlign )
        acronym = "builConsLib"
        jobdb = RepetJob( cfgFileName=configFileName )
        cL = Launcher( jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
        lFiles = glob.glob( cDir + "/*.fa_aln" )
        cmd_start = ""
        for files in lFiles:
            cmd_start += "os.system( \"ln -s %s .\" )\n" % ( files )
        cmd_start += "log = os.system( \""
        cmd_start += cmd
        cmd_start += "\" )\n"
        cmd_finish = ""
        cL.beginRun()
        cL.job.jobname = acronym + "_job"
        cL.runSingleJob( cmd_start, cmd_finish )
        cL.endRun()
        if config.get(sectionNameBuildConsensus, "clean") == "yes":
            cL.clean( acronym )
        jobdb.close()

        os.chdir( ".." )

    else:
        print "ERROR: %s not implememented" % ( clustHsp )
        sys.exit(1)

    if config.get(sectionNameBuildConsensus, "clean") == "yes":
        cmd = "find . -name \"profil*\" -exec rm {} \;"
        pL.launch( "find", cmd )

    if verbose > 0:
        print "step 3 finished successfully"; sys.stdout.flush()

#------------------------------------------------------------------------------

def detectFeatures( smplAlign, clustHsp, multAlign ):

    """
    step 4: detect TE features on the consensus

    @param smplAlign: name of the alignment program (Blaster or Pals)
    @type smplAlign: string

    @param clustHsp: name of the clustering program (Grouper, Recon or Piler)
    @type clustHsp: string

    @param multAlign: name of the multiple alignment program MSA (Map, Mafft, Muscle, Tcoffee, ClustalW or Prank)
    @type multAlign: string
    """

    if verbose > 0:
        print "beginning of step 4"
        print "self-alignment with %s" % ( smplAlign )
        print "clustering with %s" % ( clustHsp )
        print "multiple alignment with %s" % ( multAlign )
        sys.stdout.flush()

    if verbose > 0:
        print "detect features on the consensus (step 1 of TEclassifier)"; sys.stdout.flush()

    prefix = "%s_%s_%s_%s" % ( projectName, smplAlign, clustHsp, multAlign )

    if os.path.exists( "%s_TEclassif" % ( prefix ) ):
        print "ERROR: directory '%s_TEclassif/' already exists" % ( prefix )
        sys.exit(1)
    os.mkdir( "%s_TEclassif" % ( prefix ) )
    os.chdir( "%s_TEclassif" % ( prefix ) )

    if not os.path.exists( "detectFeatures" ):
        os.mkdir( "detectFeatures" )
    else:
        if verbose > 0:
            print "** Warning: directory detectFeatures/ already exists"
            sys.stdout.flush()
    os.chdir( "detectFeatures" )

    if not os.path.exists( configFileName ):
        if not os.path.exists( "../../" + configFileName ):
            print "ERROR: %s not in project directory" % ( configFileName )
            sys.exit(1)
        else:
            os.system( "ln -s ../../%s ." % ( configFileName ) )
            
    sectionName = "detect_features"
    
    try:
        CheckerUtils.checkSectionInConfigFile(config, sectionName) 
    except NoSectionError:
        print "ERROR: the section " + sectionName + " must be define in your config file : " + configFileName
        sys.exit(1)
    
    isOptionErrorRaised = False
    
    optionName = "TE_BLRtx"
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, optionName) 
    except NoOptionError:
        print "ERROR: the option " + optionName + " must be define in " + sectionName +" in your config file : " + configFileName
        isOptionErrorRaised = True
        
    optionName = "TE_BLRn"
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, optionName) 
    except NoOptionError:
        print "ERROR: the option " + optionName + " must be define in " + sectionName +" in your config file : " + configFileName
        isOptionErrorRaised = True
        
    optionName = "TE_BLRx"
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, optionName) 
    except NoOptionError:
        print "ERROR: the option " + optionName + " must be define in " + sectionName +" in your config file : " + configFileName
        isOptionErrorRaised = True
        
    optionName = "HG_BLRn"
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, optionName) 
    except NoOptionError:
        print "ERROR: the option " + optionName + " must be define in " + sectionName +" in your config file : " + configFileName
        isOptionErrorRaised = True
        
    option = "rDNA_BLRn"
    try:
        CheckerUtils.checkOptionInSectionInConfigFile( config, sectionName, option )
    except NoOptionError:
        print "ERROR: the option '" + option + "' must be define in section '" + sectionName +"' in your config file '" + configFileName + "'"
        isOptionErrorRaised = True
        
    optionName = "TE_hmmer"
    try:
        CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, optionName) 
    except NoOptionError:
        print "ERROR: the option " + optionName + " must be define in " + sectionName +" in your config file : " + configFileName
        isOptionErrorRaised = True
        
    if isOptionErrorRaised:
        sys.exit(1)
        
    if (config.get(sectionName, "TE_BLRtx") == "yes" or config.get(sectionName, "TE_BLRn") == "yes"):
        optionName = "TE_nucl_bank"
        try:
            CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, optionName) 
        except NoOptionError:
            print "ERROR: the option " + optionName + " must be define in " + sectionName +" in your config file : " + configFileName
            sys.exit(1)
        TE_nucl_bank = config.get(sectionName, "TE_nucl_bank")
        if not os.path.exists( TE_nucl_bank ):
            if not os.path.exists( "../../" + TE_nucl_bank ):
                print "ERROR: %s not in project directory" % ( TE_nucl_bank )
                sys.exit(1)
            else:
                os.system( "ln -s ../../%s ." % ( TE_nucl_bank ) )

    if config.get(sectionName, "TE_BLRx") == "yes":
        optionName = "TE_prot_bank"
        try:
            CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, optionName) 
        except NoOptionError:
            print "ERROR: the option " + optionName + " must be define in " + sectionName +" in your config file : " + configFileName
            sys.exit(1)
        TE_prot_bank = config.get(sectionName, "TE_prot_bank")
        if not os.path.exists( TE_prot_bank ):
            if not os.path.exists( "../../" + TE_prot_bank ):
                print "ERROR: %s not in project directory" % ( TE_prot_bank )
                sys.exit(1)
            else:
                os.system( "ln -s ../../%s ." % ( TE_prot_bank ) )

    if config.get(sectionName, "HG_BLRn") == "yes":
        optionName = "HG_nucl_bank"
        try:
            CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, optionName) 
        except NoOptionError:
            print "ERROR: the option " + optionName + " must be define in " + sectionName +" in your config file : " + configFileName
            sys.exit(1)
        HG_nucl_bank = config.get(sectionName, "HG_nucl_bank")
        if not os.path.exists( HG_nucl_bank ):
            if not os.path.exists( "../../" + HG_nucl_bank ):
                print "ERROR: %s not in project directory" % ( HG_nucl_bank )
                sys.exit(1)
            else:
                os.system( "ln -s ../../%s ." % ( HG_nucl_bank ) )

    if config.get(sectionName, "te_hmmer") == "yes":
        optionName = "te_hmm_profiles"
        try:
            CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, optionName) 
        except NoOptionError:
            print "ERROR: the option " + optionName + " must be define in " + sectionName +" in your config file : " + configFileName
            sys.exit(1)
        HMM_profiles = config.get(sectionName, "te_hmm_profiles")
        if not os.path.exists( HMM_profiles ):
            if not os.path.exists( "../../" + HMM_profiles ):
                print "ERROR: %s not in project directory" % ( HMM_profiles )
                sys.exit(1)
            else:
                os.system( "ln -s ../../%s ." % ( HMM_profiles ) )
                
    if config.get(sectionName, "rDNA_BLRn") == "yes":
        optionName = "rDNA_bank"
        try:
            CheckerUtils.checkOptionInSectionInConfigFile(config, sectionName, optionName) 
        except NoOptionError:
            print "ERROR: the option " + optionName + " must be define in " + sectionName +" in your config file : " + configFileName
            sys.exit(1)
        rDNA_bank = config.get(sectionName, "rDNA_bank")
        if not os.path.exists( rDNA_bank ):
            if not os.path.exists( "../../" + rDNA_bank ):
                print "ERROR: %s not in project directory" % ( rDNA_bank )
                sys.exit(1)
            else:
                os.system( "ln -s ../../%s ." % ( rDNA_bank ) )

    if not os.path.exists( "%s_consensus.fa" % ( prefix ) ):

        # shorten the headers of the consensus
        prg = os.environ["REPET_PATH"] + "/bin/shortenHeaderConsensus.py"
        cmd = prg
        cmd += " -p %s" % ( projectName )
        cmd += " -s %s" % ( smplAlign )
        cmd += " -m %s" % ( multAlign )
        cmd += " -v %i" % ( verbose - 1 )
       
        cDir = os.getcwd()
        
        if config.get(sectionName, "tmpDir" ) != "":
            tmpDir = config.get(sectionName, "tmpDir")
        else:
            tmpDir = cDir
            
        queue = config.get(sectionName, "resources")
        groupid = "%s_TEdenovo_%s_%s_shortenHeaderConsensus" % ( projectName, clustHsp, multAlign )
        acronym = "shortenHeaderConsensus"
        jobdb = RepetJob( cfgFileName=configFileName )
        cL = Launcher( jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
        cL.beginRun()
        
        if "Grouper" in clustHsp or "Grp" in clustHsp:
            inFile = "%s/%s_%s_Grouper_%s/%s_%s_Grouper_%s_consensus.fa" % ( projectDir, projectName, smplAlign, multAlign, projectName, smplAlign, multAlign )
            if not os.path.exists( inFile ):
                msg = "ERROR: consensus file '%s' doesn't exist" % ( inFile.replace( "%s/" % projectDir, "" ) )
                sys.stderr.write( "%s\n" % msg )
                sys.exit(1)
            cmd_start = "os.system( \"ln -s %s .\")\n"  % ( inFile)
            cmd += " -c Grouper"
            cmd += " -i %s" % ( inFile )
            cmd += " -o %s_%s_Grouper_%s_consensus_shortH.fa" % ( projectName, smplAlign, multAlign )
            cmd_start += "log = os.system( \""
            cmd_start += cmd
            cmd_start += "\" )\n"
            cmd_finish = "os.system(\"mv %s_%s_Grouper_%s_consensus_shortH.fa %s\")\n" % ( projectName, smplAlign, multAlign, cDir )
            cL.job.jobname = acronym + "_Grouper_"
            cL.runSingleJob( cmd_start, cmd_finish )
            
        if "Recon" in clustHsp or "Rec" in clustHsp:
            inFile = "%s/%s_%s_Recon_%s/%s_%s_Recon_%s_consensus.fa" % ( projectDir, projectName, smplAlign, multAlign, projectName, smplAlign, multAlign )
            if not os.path.exists( inFile ):
                msg = "ERROR: consensus file '%s' doesn't exist" % ( inFile.replace( "%s/" % projectDir, "" ) )
                sys.stderr.write( "%s\n" % msg )
                sys.exit(1)
            cmd_start = "os.system( \"ln -s %s .\")\n" % ( inFile )
            cmd += " -c Recon"
            cmd += " -i %s" % ( inFile )
            cmd += " -o %s_%s_Recon_%s_consensus_shortH.fa" % ( projectName, smplAlign, multAlign )
            cmd_start += "log = os.system( \""
            cmd_start += cmd
            cmd_start += "\" )\n"
            cmd_finish = "os.system(\"mv %s_%s_Recon_%s_consensus_shortH.fa %s\")\n" % ( projectName, smplAlign, multAlign, cDir )
            cL.job.jobname = acronym + "_Recon_"
            cL.runSingleJob( cmd_start, cmd_finish )
            
        if "Piler" in clustHsp or "Pil" in clustHsp:
            inFile = "%s/%s_%s_Piler_%s/%s_%s_Piler_%s_consensus.fa" % ( projectDir, projectName, smplAlign, multAlign, projectName, smplAlign, multAlign )
            if not os.path.exists( inFile ):
                msg = "ERROR: consensus file '%s' doesn't exist" % ( inFile.replace( "%s/" % projectDir, "" ) )
                sys.stderr.write( "%s\n" % msg )
                sys.exit(1)
            cmd_start = "os.system( \"ln -s %s .\")\n" % ( inFile )
            cmd += " -c Piler"
            cmd += " -i %s" % ( inFile )
            cmd += " -o %s_%s_Piler_%s_consensus_shortH.fa" % ( projectName, smplAlign, multAlign )
            cmd_start += "log = os.system( \""
            cmd_start += cmd
            cmd_start += "\" )\n"
            cmd_finish = "os.system(\"mv %s_%s_Piler_%s_consensus_shortH.fa %s\")\n" % ( projectName, smplAlign, multAlign, cDir )
            cL.job.jobname = acronym + "_Piler_"
            cL.runSingleJob( cmd_start, cmd_finish )
            
        cL.endRun()
        if config.get(sectionName, "clean") == "yes":
            cL.clean( acronym )
        jobdb.close()

        # concatenate all the consensus
        lFiles = glob.glob( "%s_%s_*_%s_consensus_shortH.fa" % ( projectName, smplAlign, multAlign ) )
        lFiles.sort()
        for resFile in lFiles:
            prg = "cat"
            cmd = prg
            cmd += " %s >> %s_consensus.fa" % ( resFile, prefix )
            pL.launch( prg, cmd )

        # clean
        if os.path.exists( "%s_%s_Grouper_%s_consensus_shortH.fa" % ( projectName, smplAlign, multAlign ) ):
            os.system( "rm -f %s_%s_Grouper_%s_consensus_shortH.fa" % ( projectName, smplAlign, multAlign ) )
        if os.path.exists( "%s_%s_Recon_%s_consensus_shortH.fa" % ( projectName, smplAlign, multAlign ) ):
            os.system( "rm -f %s_%s_Recon_%s_consensus_shortH.fa" % ( projectName, smplAlign, multAlign ) )
        if os.path.exists( "%s_%s_Piler_%s_consensus_shortH.fa" % ( projectName, smplAlign, multAlign ) ):
            os.system( "rm -f %s_%s_Piler_%s_consensus_shortH.fa" % ( projectName, smplAlign, multAlign ) )

    # launch TEclassifier.py step 1
    prg = os.environ["REPET_PATH"] + "/bin/TEclassifier.py"
    cmd = prg
    cmd += " -p %s" % ( prefix )
    cmd += " -c %s" % ( configFileName )
    cmd += " -i %s_consensus.fa" % ( prefix )
    cmd += " -s 1"
    if CheckerUtils.isExecutableInUserPath("hmmscan") and CheckerUtils.isExecutableInUserPath("hmmpress"):
        cmd += " -n"
    cmd += " -v %i" % ( verbose - 1 )
    pL.launch( prg, cmd )

    os.chdir ( "../.." )

    if verbose > 0:
        print "step 4 finished successfully"; sys.stdout.flush()

#------------------------------------------------------------------------------

def classifConsensus( smplAlign, clustHsp, multAlign ):

    """
    step 5: classify the consensus according to their features

    @param smplAlign: name of the alignment program (Blaster or Pals)
    @type smplAlign: string

    @param clustHsp: name of the clustering program (Grouper, Recon or Piler)
    @type clustHsp: string

    @param multAlign: name of the multiple alignment program MSA (Map, Mafft, Muscle, Tcoffee, ClustalW or Prank)
    @type multAlign: string
    """

    if verbose > 0:
        print "beginning of step 5"
        print "self-alignment with %s" % ( smplAlign )
        print "clustering with %s" % ( clustHsp )
        print "multiple alignment with %s" % ( multAlign )
        print "classify the consensus according to their features (step 2 of TEclassifier)"
        sys.stdout.flush()

    prefix = "%s_%s_%s_%s" % ( projectName, smplAlign, clustHsp, multAlign )

    if not os.path.exists( prefix + "_TEclassif" ):
        print "ERROR: run step 4 before step 5"
        help()
        sys.exit(1)
    else:
        os.chdir( prefix + "_TEclassif" )

    if os.path.exists( "./classifConsensus" ):
        print "ERROR: directory %s_TEclassif/classifConsensus already exists" % ( prefix )
        sys.exit(1)
    else:
        os.mkdir( "classifConsensus" )
    os.chdir( "classifConsensus" )

    if not os.path.exists( "%s/%s" % ( projectDir, configFileName ) ):
        print "ERROR: %s not in project directory" % ( configFileName )
        sys.exit(1)
    else:
        os.system( "ln -s %s/%s ." % ( projectDir, configFileName ) )

    sectionName = "classif_consensus"
    
    os.system( "ln -s ../detectFeatures/%s_consensus.fa ." % ( prefix ) )

    # classify consensus according to their features and remove redundancy
    prg = os.environ["REPET_PATH"] + "/bin/TEclassifier.py"
    cmd = prg
    cmd += " -p %s" % ( prefix )
    cmd += " -c %s" % ( configFileName )
    cmd += " -i %s_consensus.fa" % ( prefix )
    cmd += " -s 2"
    cmd += " -v %i" % ( verbose - 1 )
    pL.launch( prg, cmd )

    # shorten the headers
    prg = os.environ["REPET_PATH"] + "/bin/shortenHeaderClassif.py"
    cmd = prg
    cmd += " -i %s_uniq_TEclassifier.fa" % prefix
    cmd += " -c"
    cmd += " -p %s" % projectName
    cmd += " -s '_'"
    cmd += " -o %s_denovoLibTEs.fa" % projectName
    cmd += " -v %i" % ( verbose - 1 )
    
    queue = config.get(sectionName, "resources")
    cDir = os.getcwd()
    if config.get(sectionName, "tmpDir" ) != "":
        tmpDir = config.get(sectionName, "tmpDir")
    else:
        tmpDir = cDir
        
    groupid = "%s_TEdenovo_%s_%s_shortenHeaderClassif" % ( projectName, clustHsp, multAlign )
    acronym = "shortenHeaderClassif"
    jobdb = RepetJob( cfgFileName=configFileName )
    cL = Launcher( jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
    cmd_start = "os.system( \"ln -s %s/%s_uniq_TEclassifier.fa .\" )\n" % ( cDir, prefix )
    cmd_start += "log = os.system( \""
    cmd_start += cmd
    cmd_start += "\" )\n"
    cmd_finish = "os.system( \"mv %s_denovoLibTEs.fa %s/.\" )\n" % ( projectName, cDir )
    cL.beginRun()
    cL.job.jobname = acronym
    cL.runSingleJob( cmd_start, cmd_finish )
    cL.endRun()
    if config.get(sectionName, "clean") == "yes":
        cL.clean( acronym )
    jobdb.close()

    pL.launch( "mv", "mv %s_denovoLibTEs.fa ../.." % ( projectName ) )
    os.chdir ( "../.." )

    if verbose > 0:
        print "step 5 finished successfully"; sys.stdout.flush()

#------------------------------------------------------------------------------

def filterConsensus( smplAlign, clustHsp, multAlign ):

    """
    step 6: filter the consensus no SSR and no noCat

    @param smplAlign: name of the alignment program (Blaster or Pals)
    @type smplAlign: string

    @param clustHsp: name of the clustering program (Grouper, Recon or Piler)
    @type clustHsp: string

    @param multAlign: name of the multiple alignment program MSA (Map, Mafft, Muscle, Tcoffee, ClustalW or Prank)
    @type multAlign: string
    """

    if verbose > 0:
        print "beginning of step 6"
        print "self-alignment with %s" % smplAlign
        print "clustering with %s" % clustHsp
        print "multiple alignment with %s" % multAlign
        print "filter the consensus no SSR and no noCat"
        sys.stdout.flush()

    prefix = "%s_%s_%s_%s" % (projectName, smplAlign, clustHsp, multAlign)

    if not os.path.exists("%s_TEclassif/classifConsensus" % prefix):
        print "ERROR: run step 5 before step 6"
        help()
        sys.exit(1)
    else:
        os.mkdir("%s_TEclassif_Filtered" % prefix)
        os.chdir("%s_TEclassif_Filtered" % prefix)


    if not os.path.exists( "%s/%s" % (projectDir, configFileName) ):
        print "ERROR: %s not in project directory" % configFileName
        sys.exit(1)
    else:
        os.symlink("%s/%s" % (projectDir, configFileName), configFileName)

    sectionName = "filter_consensus"
    
    completeClassifInHeadersFileName = "%s_uniq_TEclassifier.fa" % prefix
    classifFileName = "%s_uniq_TEclassifier.classif" % prefix
    os.symlink("%s/%s_TEclassif/classifConsensus/%s" % (projectDir, prefix, completeClassifInHeadersFileName), completeClassifInHeadersFileName)
    os.symlink("%s/%s_TEclassif/classifConsensus/%s" % (projectDir, prefix, classifFileName), classifFileName)

    lCmds = []
    # filter consensus no SSR and no noCat
    prg = "%s/bin/FilterClassifiedSequences.py" % os.environ["REPET_PATH"]
    cmd = prg
    cmd += " -i %s" % completeClassifInHeadersFileName
    if config.get(sectionName, "filter_SSR") == "yes":
        cmd += " -S"
        cmd += " -s %s" % config.get(sectionName, "length_SSR")
    if config.get(sectionName, "filter_noCat_built_from_less_than_10_fragments") == "yes":
        cmd += " -N 2 -n 10"
    if config.get(sectionName, "filter_host_gene") == "yes":
        cmd += " -g"
    if config.get(sectionName, "filter_confused") == "yes":
        cmd += " -c"
    if config.get(sectionName, "filter_incomplete") == "yes":
        cmd += " -u"
    cmd += " -C %s" % classifFileName
    cmd += " -v %i" % (verbose - 1)
    lCmds.append(cmd)
    
    # shorten the headers
    prg = "%s/bin/shortenHeaderClassif.py" % os.environ["REPET_PATH"]
    cmd = prg
    cmd += " -i %s.filtered" % completeClassifInHeadersFileName
    cmd += " -c"
    cmd += " -p %s" % projectName
    cmd += " -v %i" % (verbose - 1)
    lCmds.append(cmd)

    queue = config.get(sectionName, "resources")
    cDir = os.getcwd()
    if config.get(sectionName, "tmpDir" ) != "":
        tmpDir = config.get(sectionName, "tmpDir")
    else:
        tmpDir = cDir

    groupid = "%s_TEdenovo_%s_%s_filterConsensus" % (projectName, clustHsp, multAlign)
    acronym = "filterConsensus"
    jobdb = RepetJob(cfgFileName = configFileName)
    cL = Launcher(jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym)
    cmd_start = "shutil.copy( \"%s/%s\", \"%s\" )\n" % (cDir, completeClassifInHeadersFileName, completeClassifInHeadersFileName)
    cmd_start += "shutil.copy( \"%s/%s\", \"%s\" )\n" % (cDir, classifFileName, classifFileName)
    for cmd in lCmds:
        cmd_start += "log = os.system( \""
        cmd_start += cmd
        cmd_start += "\" )\n"
    cmd_finish = "shutil.move(\"%s.filtered.shortH\", \"%s/%s_denovoLibTEs_filtered.fa\")\n" % (completeClassifInHeadersFileName, cDir, projectName)
    cL.beginRun()
    cL.job.jobname = acronym
    cL.runSingleJob(cmd_start, cmd_finish)
    cL.endRun()
    if config.get(sectionName, "clean") == "yes":
        cL.clean(acronym)
    jobdb.close()
    
    os.chdir ("../..")

    if verbose > 0:
        print "step 6 finished successfully"
        sys.stdout.flush()

#------------------------------------------------------------------------------

def clusteringConsensus( smplAlign, clustHsp, multAlign ):

    """
    step 7: clustering the consensus 
    
    @param smplAlign: name of the alignment program (Blaster or Pals)
    @type smplAlign: string

    @param clustHsp: name of the clustering program (Grouper, Recon or Piler)
    @type clustHsp: string

    @param multAlign: name of the multiple alignment program MSA (Map, Mafft, Muscle, Tcoffee, ClustalW or Prank)
    @type multAlign: string
    """
    
    if verbose > 0:
        print "beginning of step 7"
        print "self-alignment with %s" % smplAlign
        print "clustering with %s" % clustHsp
        print "multiple alignment with %s" % multAlign
        print "clustering the filtered consensus"
        sys.stdout.flush()

    prefix = "%s_%s_%s_%s" % (projectName, smplAlign, clustHsp, multAlign)

    if not os.path.exists("%s_TEclassif_Filtered/%s_denovoLibTEs_filtered.fa" % (prefix, projectName)):
        print "ERROR: run step 6 before step 7"
        help()
        sys.exit(1)
    else:
        os.mkdir("%s_TEclassif_Filtered_Clustered" % prefix)
        os.chdir("%s_TEclassif_Filtered_Clustered" % prefix)
        
    if not os.path.exists( "%s/%s" % (projectDir, configFileName) ):
        print "ERROR: %s not in project directory" % configFileName
        sys.exit(1)
    else:
        os.symlink("%s/%s" % (projectDir, configFileName), configFileName)

    sectionName = "cluster_consensus"

    filteredFileName = "%s_denovoLibTEs_filtered.fa" % projectName
    absPathFilteredFile = os.path.abspath("../%s_TEclassif_Filtered/%s" % (prefix, filteredFileName))

    # clustering consensus
    prg = "%s/bin/ClusterConsensus.py" % os.environ["REPET_PATH"]
    cmd = prg
    cmd += " -s 1"
    cmd += " -i %s" % filteredFileName
    cmd += " -I %s" % config.get(sectionName, "identity")
    cmd += " -c %s" % config.get(sectionName, "coverage")
    cmd += " -v %i" % (verbose - 1)

    queue = config.get(sectionName, "resources")
    cDir = os.getcwd()
    if config.get(sectionName, "tmpDir" ) != "":
        tmpDir = config.get(sectionName, "tmpDir")
    else:
        tmpDir = cDir

    groupid = "%s_TEdenovo_%s_%s_clusterConsensus" % (projectName, clustHsp, multAlign)
    acronym = "clustering"
    jobdb = RepetJob(cfgFileName = configFileName)
    cL = Launcher(jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym)
    
    cmd_start = "shutil.copy( \"%s\", \".\" )\n" % (absPathFilteredFile)
    cmd_start += "log = os.system( \""
    cmd_start += cmd
    cmd_start += "\" )\n"
    cmd_finish = "shutil.copy( \"Blastclust/clusteredSequences.fa\", \"%s/%s_denovoLibTEs_filtered_clustered.fa\")\n" % (cDir, projectName)
    cmd_finish += "shutil.copy( \"Blastclust/GiveInfoBlastclust_%s_denovoLibTEs_filtered.fa_blastclust.fa.log\", \"%s/%s_denovoLibTEs_filtered_blastclustInfo.txt\")\n" % (projectName, cDir, projectName)
    cL.beginRun()
    cL.job.jobname = acronym
    cL.runSingleJob(cmd_start, cmd_finish)
    cL.endRun()
    if config.get(sectionName, "clean") == "yes":
        cL.clean(acronym)
    jobdb.close()
    
    os.chdir ("../..")

    if verbose > 0:
        print "step 7 finished successfully"
        sys.stdout.flush()
        
if __name__ == "__main__":
    main()
