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


## @mainpage Documentation of the REPET API
#
# Welcome to the API documentation!
# This API is a set of packages and classes for pipeline(s) development.
#
# @par The "logger" package
# 
# Logging is managed via LoggerFactory. This class creates instances of logging.logging python class. It's strongly encouraged to use this factory each time you need to log something.
#
# @par The "checker" package
#
# This package is a set of classes designed to facilitate development of different kind of checks: filesystem  checks, environment checks, configuration file checks ...
#
# Classes should subclass checker::IChecker or if a logger is needed: checker::AbstractChecker.
#
# Methods should raise checker::CheckerException.
#
# Use checker::ConfigChecker and checker::ConfigException for configuration files checks.
#
# checker::CheckerUtils is a set of small static methods shared by other classes of checker package.
#
# @par The "coord" package
#
# This package is a set of classes dedicated to coordinates manipulations.
# 
# A coord::Range instance records a region on a given sequence (start, end and sequence name).
#
# A coord::Map instance is a coord::Range instance and record a named region on a given sequence (start, end, sequence name and name).
#
# A coord::Set instance is a coord::Map instance and record a named region on a given sequence with an identifier (start, end, sequence name, name and id).
#
# A coord::Align instance handle a match between two sequences, query and subject (pair of coordinates with E-value, score and identity).
#
# A coord::Path instance is a coord::Align instance and handle a match between two sequences, query and subject (pair of coordinates with E-value, score and identity) with an identifier.
#
# A coord::Match instance is a coord::Path instance and handle a chain of match(es) between two sequences, query and subject, with an identifier and the length of the input sequences.
#
# coord::Align, coord::Map, coord::Path and coord::Set come with utils classes: coord::AlignUtils, coord::MapUtils, coord::PathUtils and coord::SetUtils.        
#
# @par The "seq" package
#
# This package a set of classes dedicated to sequences manipulations.
#
# A seq::Bioseq instance records a sequence with its header. seq::Bioseq comes with an utils class: seq::BioseqUtils.
#
# A seq::BioseqDB instance handle a collection of a Bioseq (header-sequence).
#
# A seq::AlignedBioseqDB instance is a multiple sequence alignment representation.
#
# A seq::FastaUtils is a set of static methods for fasta file manipulation.
#
# @par The "sql" package
#
# This package is dedicated to persistance of coord package objects.   
# All classes come with dedicated interfaces. Use these interfaces for class manipulation.
# Class names patterns are ITable*Adaptator and Table*Adaptator.
#
# sql::ITablePathAdaptator, sql::TablePathAdaptator /
# sql::ITableSetAdaptator, sql::TableSetAdaptator /
# sql::ITableSeqAdaptator, sql::TableSeqAdaptator /
# sql::ITableMapAdaptator, sql::TableMapAdaptator /
# sql::ITableMatchAdaptator, sql::TableMatchAdaptator.
#   


import logging
import time
import os

DEFAULT_LEVEL = logging.INFO
DEFAULT_FORMAT = "%(asctime)s %(levelname)s %(message)s"


## Use this class to create a instance of logging class.
#
class LoggerFactory( object ):
    
    ## Create a logging instance
    #
    # @param logFileName name of log file
    # @param level logging levels (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL). Default is logging.INFO
    # @param format message format. Default format is "%(asctime)s %(levelname)s %(message)s".
    #
    def createLogger(logFileName, level=DEFAULT_LEVEL, format=DEFAULT_FORMAT):
        uniqId = "%s_%s" % ( time.strftime("%Y%m%d%H%M%S") , os.getpid() )

        logger = logging.getLogger(uniqId)
        logger.setLevel(level) 
        formatter = logging.Formatter(format)

        handler = logging.FileHandler(logFileName)
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        
        return logger
    
    createLogger = staticmethod( createLogger )
