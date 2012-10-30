import os
import sys
from pyRepet.launcher.programLauncher import programLauncher

## Prepare profiles databank and create command to search profiles from a profiles databank in a nucleotides databank
#
class ProfilesSearch(object):

    ## launch command to prepare profiles bank
    #
    # @param launch_1 string corresponding to pre command
    # @param launch_2 string corresponding to post command
    # @param config configParser object instance
    # @param cDir string current directory
    # @param verbose int (default = 0)
    #
    def prepareProfilesBank(self, launch_1, launch_2, config, cDir, verbose = 0):
        bank = self._getBankBaseName(config)
        prg = "hmmpress"
        pL = programLauncher()
        if verbose > 0:
            print "prepare bank '%s'..." % ( bank ); sys.stdout.flush()
        cmd = ""
        cmd += prg + " -f "
        cmd += "%s/%s" % ( cDir, bank )
        
        pL.launch( prg, cmd )
        
    
    ## create command to detect Hmm profiles in a nt sequence file
    #
    # @param inFileName string name of input file
    # @param launch_1 string corresponding to pre command
    # @param launch_2 string corresponding to post command
    # @param cDir string current directory
    # @param tmpDir string temporary directory
    # @param config configParser object instance
    # @return cmd string command to launch
    #        
    def detectHmmProfiles(self, inFileName, launch_1, launch_2, cDir, tmpDir, config):
        bank = self._getBankBaseName(config)
        evalueMax = config.get("detect_features","TE_HMMER_evalue")
        
        cmd = ""
        
        cmd += launch_1
        cmd += os.environ["REPET_PATH"] + "/bin/translateAfastaFileInAllFrameAndReplaceStopsByX_script.py"
        cmd += " -i %s" % ( inFileName )
        cmd += " -o %s_translated" % ( inFileName )
        cmd += launch_2
        
        cmd += launch_1
        cmd += "hmmscan "
        cmd += " -o %s_tr.hmmScanOut" % ( inFileName )
        cmd += " --domtblout %s_tr.hmmScanOutTab" % ( inFileName )
        cmd += " --noali -E " + evalueMax
        cmd += " %s/%s" % ( cDir, bank ) + " " + "%s_translated" % ( inFileName )
        cmd += launch_2
        
        cmd += "if os.path.exists( \"%s_translated\" ):\n" % ( inFileName )
        cmd += "\tos.remove( \"%s_translated\" )\n" % ( inFileName )
        
        cmd += launch_1
        cmd += os.environ["REPET_PATH"] + "/bin/HmmOutput2alignAndTransformCoordInNtAndFilterScores_script.py"
        cmd += " -i %s_tr.hmmScanOutTab" % ( inFileName )
        cmd += " -o %s_profiles_%s.align" % ( inFileName, bank )
        cmd += " -T %s" % ( inFileName )
        cmd += " -p hmmscan"
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
        cmd += "if os.path.exists( \"%s_hmmScanOut\" ):\n" % ( inFileName )
        cmd += "\tos.remove( \"%s_hmmScanOut\" )\n" % ( inFileName )
        
        if tmpDir != cDir:
            cmd += "if os.path.exists( \"%s\" ):\n" % ( bank )
            cmd += "\tos.remove( \"%s\" )\n" % ( bank )
            
        return cmd
    
    def _getBankBaseName(self, config):
        profilsHmmBank = config.get("detect_features", "TE_HMM_profiles")
        bank = os.path.basename(profilsHmmBank)
        return bank

