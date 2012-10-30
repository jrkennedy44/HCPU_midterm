"""
Launch Blaster and then Matcher to compare the input sequences with known TEs via blastn and record the results into a MySQL table.
"""

import os
import sys
import ConfigParser
from pyRepet.util.file.FileUtils import FileUtils


class RepbaseBLRnForClassifierStep1( object ):
    
    """
    Launch Blaster and then Matcher to compare the input sequences with known TEs via blastn and record the results into a MySQL table.
    
    @param inFileName: name of the input fasta file
    @type inFileName: string
    
    @param launch_1: generic command at the beginning of a specific command
    @type launch_1: string
    
    @param launch_2: generic command at the end of a specific command
    @type launch_2: string

    @return: all the commands to run the job
    @rtype: string
    
    @param cDir: current directory (where to retrieve the result files)
    @ype cDir: string

    @param tmpDir: temporary directory (where the job will run)
    @type tmpDir: string
    
    @param configFileName: configuration file name
    @type configFileName: string
    
    @param logger: a logger Instance
    @type logger: logger
    
    @param verbose: verbose(0/1/2)
    @type verbose: int
    
    @param pL: program launcher
    @type pL: programLauncher Instance
    
    @param project: project name
    @type project: string
    
    """

    def __init__(self, inFileName, launch_1, launch_2, cDir, tmpDir, configFileName, logger, verbose, pL, project):
        """
        Constructor
        """
        self._inFileName = inFileName
        self._launch_1 = launch_1
        self._launch_2 = launch_2
        self._cDir = cDir
        self._tmpDir = tmpDir
        self._logger = logger
        self._verbose = verbose
        self._pL = pL
        self._project = project
        self._fileUtils = FileUtils()
        self._config = ConfigParser.ConfigParser()
        self._configFileName = configFileName
        self._config.readfp( open(self._configFileName) )
        self._bank = self._config.get("detect_features","TE_nucl_bank")

    def formatRepbase_ntIfNecessary( self ):
        """
        Format Repbase (make 'cut' files).
        """
        if not os.path.exists( "%s_cut" % ( self._bank ) ):
            self._logger.debug("prepare bank '%s'..." % ( self._bank ))
            prg = os.environ["REPET_PATH"] + "/bin/blaster"
            cmd = prg
            cmd += " -s %s" % ( self._bank )
            cmd += " -n blastn"
            if self._config.get("detect_features","wublast") == "yes":
                cmd += " -W"
            cmd += " -r"
            cmd += " -P"
            self._pL.launch( prg, cmd )
            os.system( "rm -f %s-blastn-*.param" % ( self._bank ) )
        
    def createCmdToLaunch( self ):
        cmd = self._launch_1 + os.environ["REPET_PATH"] + "/bin/blaster"
        cmd += " -q %s" % ( self._inFileName )
        cmd += " -s %s/%s" % ( self._cDir, self._bank )
        cmd += " -B %s_BLRn_%s" % ( self._inFileName, self._bank )
        cmd += " -n blastn"
        if self._config.get("detect_features","wublast") == "yes":
            cmd += " -W"
        cmd += " -r"
        cmd += " -v 1"
        cmd += self._launch_2
    
        cmd += "if not os.path.exists( \"%s/%s_BLRn_%s.param\" ):\n" % ( self._cDir, self._inFileName, self._bank )
        cmd += "\tos.system( \"mv %s_BLRn_%s.param %s\" )\n" % ( self._inFileName, self._bank, self._cDir )
        cmd += "if os.path.exists( \"%s_cut\" ):\n" % ( self._inFileName )
        cmd += "\tos.system( \"rm -f %s_cut*\" )\n" % ( self._inFileName )
        cmd += "if os.path.exists( \"%s.Nstretch.map\" ):\n" % ( self._inFileName )
        cmd += "\tos.remove( \"%s.Nstretch.map\" )\n" % ( self._inFileName )
        cmd += "if os.path.exists( \"%s_BLRn_%s.raw\" ):\n" % ( self._inFileName, self._bank )
        cmd += "\tos.remove( \"%s_BLRn_%s.raw\" )\n" % ( self._inFileName, self._bank )
        cmd += "if os.path.exists( \"%s_BLRn_%s.seq_treated\" ):\n" % ( self._inFileName, self._bank )
        cmd += "\tos.remove( \"%s_BLRn_%s.seq_treated\" )\n" % ( self._inFileName, self._bank )
    
        cmd += self._launch_1
        cmd += os.environ["REPET_PATH"] + "/bin/matcher"
        cmd += " -m %s_BLRn_%s.align" % ( self._inFileName, self._bank )
        cmd += " -q %s" % ( self._inFileName )
        cmd += " -s %s/%s" % ( self._cDir, self._bank )
        cmd += " -j"
        cmd += " -v 1"
        cmd += self._launch_2
    
        cmd += "if not os.path.exists( \"%s/%s_BLRn_%s.align.clean_match.path\" ):\n" % ( self._cDir, self._inFileName, self._bank )
        cmd += "\tos.system( \"mv %s_BLRn_%s.align.clean_match.path %s\" )\n" % ( self._inFileName, self._bank, self._cDir )
        cmd += "if not os.path.exists( \"%s/%s_BLRn_%s.align.clean_match.param\" ):\n" % ( self._cDir, self._inFileName, self._bank )
        cmd += "\tos.system( \"mv %s_BLRn_%s.align.clean_match.param %s\" )\n" % ( self._inFileName, self._bank, self._cDir )
        cmd += "if os.path.exists( \"%s_BLRn_%s.align\" ):\n" % ( self._inFileName, self._bank )
        cmd += "\tos.remove( \"%s_BLRn_%s.align\" )\n" % ( self._inFileName, self._bank )
        cmd += "if os.path.exists( \"%s_BLRn_%s.align.clean_match.fa\" ):\n" % ( self._inFileName, self._bank )
        cmd += "\tos.remove( \"%s_BLRn_%s.align.clean_match.fa\" )\n" % ( self._inFileName, self._bank )
        cmd += "if os.path.exists( \"%s_BLRn_%s.align.clean_match.map\" ):\n" % ( self._inFileName, self._bank )
        cmd += "\tos.remove( \"%s_BLRn_%s.align.clean_match.map\" )\n" % ( self._inFileName, self._bank )
        cmd += "if os.path.exists( \"%s_BLRn_%s.align.clean_match.tab\" ):\n" % ( self._inFileName, self._bank )
        cmd += "\tos.remove( \"%s_BLRn_%s.align.clean_match.tab\" )\n" % ( self._inFileName, self._bank )
    
        if self._tmpDir != self._cDir:
            cmd += "if os.path.exists( \"%s\" ):\n" % ( self._bank )
            cmd += "\tos.remove( \"%s\" )\n" % ( self._bank )
            
        return cmd
    
    def collectRepbaseBLRn( self ):
        """
        Concatenate the outputs of blastn, adapt the ID and load the results into a table.
        """
        bankFull = self._bank
        bankPath, bank = os.path.split( bankFull )
        self._concatPathFile(bank)
        self._adaptIDInPathFile(bank)
        self._loadPathFileInTable(bank)    
        self._findAndRemoveUselessFiles(bank)
        
    def _concatPathFile(self, bank):
        FileUtils.catFilesUsingPattern( "../batch_*.fa_BLRn_%s.align.clean_match.path" % ( bank ),
                                        "%s_BLRn_%s.align.clean_match.path.tmp" % ( self._project, bank ) )

    def _adaptIDInPathFile(self, bank):
        if os.path.exists(os.environ["REPET_PATH"] + "/bin/pathnum2id"):
            prg = os.environ["REPET_PATH"] + "/bin/pathnum2id"
            cmd = prg
            cmd += " -i %s_BLRn_%s.align.clean_match.path.tmp" % (self._project, bank)
            cmd += " -o %s_BLRn_%s.align.clean_match.path" % (self._project, bank)
            cmd += " -v %i" % (self._verbose - 1)
            self._pL.launch(prg, cmd)
        else:
            prg = os.environ["REPET_PATH"] + "/bin/pathnum2id.py"
            cmd = prg
            cmd += " -i %s_BLRn_%s.align.clean_match.path.tmp" % (self._project, bank)
            cmd += " -o %s_BLRn_%s.align.clean_match.path" % (self._project, bank)
            self._pL.launch(prg, cmd)

    def _loadPathFileInTable(self, bank):
        prg = os.environ["REPET_PATH"] + "/bin/srptCreateTable.py"
        cmd = prg
        cmd += " -f %s_BLRn_%s.align.clean_match.path" % (self._project, bank)
        cmd += " -n %s_TE_BLRn_path" % (self._project)
        cmd += " -t path"
        cmd += " -c ../%s" % (self._configFileName)
        self._pL.launch(prg, cmd)

    def _findAndRemoveUselessFiles(self, bank):
        prg = "find"
        cmd = prg
        cmd += " .. -name \"batch_*.fa_BLRn_%s.*\" -exec rm {} \;" % (bank)
        self._pL.launch(prg, cmd)
        prg = "rm"
        cmd = prg
        cmd += " %s_BLRn_%s.align.clean_match.path.tmp" % (self._project, bank)
        self._pL.launch(prg, cmd)
