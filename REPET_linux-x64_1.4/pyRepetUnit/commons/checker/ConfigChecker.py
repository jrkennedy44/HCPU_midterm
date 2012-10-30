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


import ConfigParser
from ConfigParser import NoOptionError
from pyRepetUnit.commons.checker.IChecker import IChecker
from pyRepetUnit.commons.checker.ConfigException import ConfigException


## A checker for a configuration file
#
#
# A configuration file is formatted as follow:
#
# [section1]
#
# option_name1: option_value1
# 
# option_name2: option_value2
#
# option_name3: option_value3
#
# [section2]
# 
# ...
#
# 
# This class performs 3 checkes on a configuration file: 
#
# (i) check if file exists
#
# (ii) check if section exists
#
# (iii) check if option exists
#
class ConfigChecker( IChecker ):
    
    ## Constructor A checker for configuration file.
    #
    # @param  sectionName name of section to check in configuration file
    # @param  optionsDict dictionary with option(s) to check as keys and empty strings ("") as values
    def __init__ (self, sectionName, optionsDict):
        self._sectionName = sectionName
        self._optionsDict = optionsDict
        
        
    ## Perform 3 checks : file exists, sections exists, option exists
    # 
    # @param configFile configuration file to check
    # @exception ConfigException with a list of messages
    def check (self, configFile):
        config = ConfigParser.ConfigParser()
        msg = []
        try:
            config.readfp( open(configFile) )
        except IOError, e:
            msg.append("CONFIG FILE not found - " + e.message)
            raise ConfigException("", msg) 

        if not (config.has_section(self._sectionName)):
            msg.append("[" + self._sectionName + "]" + " section not found - ")
            raise ConfigException("", msg)
         
        isExceptionOccured = False        
        for key in self._optionsDict.keys():
            try:
                self._optionsDict[key] = config.get(self._sectionName, key) 
            except NoOptionError, e:
                msg.append("[" + self._sectionName + "]" + " - " + e.message)
                isExceptionOccured = True
        
        if (isExceptionOccured):
            raise ConfigException("", msg)
