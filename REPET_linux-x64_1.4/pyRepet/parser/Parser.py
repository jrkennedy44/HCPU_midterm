import os
import sys
import re

from xml.sax import ContentHandler
from xml.sax import make_parser
from xml.sax.handler import feature_namespaces

from pyRepet.seq.BioseqDB import BioseqDB


class Parser( object ):
    
    def __init__( self, inFileName="", outFileName="" ):
        """
        Constructor

        @param inFileName: name of the input file to be converted
        @type inFileName: string

        @param outFileName: name of the output file
        @type outFileName: string
        """

        if os.path.exists( inFileName ):
            self.inFileName = inFileName
        else:
            print "*** Error: input file '%s' doesn't exist" % ( inFileName )
            sys.exit(1)
        self.inFile = open( inFileName, "r" )

        self.outFileName = outFileName
        if outFileName != "":
            self.outFile = open( outFileName, "w" )
        else:
            print "*** Error: output file name is missing"
            sys.exit(1)

    #--------------------------------------------------------------------------

    def tab2align( self ):

        """
        Convert a 'tab' file (output from Matcher) into an 'align' file.
        """

        line = self.inFile.readline()   # skip the first line
        line = self.inFile.readline()

        while True:

            if line == "":
                break

            data = line.split("\t")
            qryName = data[0]
            qryStart = data[1]
            qryEnd = data[2]
            qryLength = data[3]
            qryLengthPerc = data[4]
            matchLengthPerc = data[5]
            sbjName = data[6]
            sbjStart = data[7]
            sbjEnd = data[8]
            sbjLength = data[9]
            sbjLengthPerc = data[10]
            Evalue = data[11]
            score = data[12]
            identity = data[13]
            path = data[14]

            string = "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % ( qryName, qryStart, qryEnd, sbjName, sbjStart, sbjEnd, Evalue, score, identity )

            self.outFile.write( string )

            line = self.inFile.readline()

        self.inFile.close()
        self.outFile.close()

    #--------------------------------------------------------------------------

    def tabnum2id( self ):

        """
        Adapt the path IDs as the input file is the concatenation of several 'tab' files, and remove the extra header lines.
        """

        line = self.inFile.readline()
        self.outFile.write( line )
        line = self.inFile.readline()

        dID2count = {}
        count = 1

        while True:

            if line == "":
                break

            data = line.split("\t")

            if data[0] != "query.name":
                qryName = data[0]
                qryStart = data[1]
                qryEnd = data[2]
                qryLength = data[3]
                qryLengthPerc = data[4]
                matchLengthPerc = data[5]
                sbjName = data[6]
                sbjStart = data[7]
                sbjEnd = data[8]
                sbjLength = data[9]
                sbjLengthPerc = data[10]
                Evalue = data[11]
                score = data[12]
                identity = data[13]
                path = data[14]

                key_id = path + "-" + qryName + "-" + sbjName
                if key_id not in dID2count.keys():
                    newPath = count
                    count += 1
                    dID2count[ key_id ] = newPath
                else:
                    newPath = dID2count[ key_id ]

                cmd = "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%i\n" % ( qryName, qryStart, qryEnd, qryLength, qryLengthPerc, matchLengthPerc, sbjName, sbjStart, sbjEnd, sbjLength, sbjLengthPerc, Evalue, score, identity, newPath )

                self.outFile.write( cmd )

            line = self.inFile.readline()

        self.inFile.close()
        self.outFile.close()

    #--------------------------------------------------------------------------

    def pathrange2set( self ):

        """
        Converts a file from the 'path_range' format to the 'set' format, an entry being a subject (TE) matching on a query (chr).
        """

        line = self.inFile.readline()

        while True:

            if line == "":
                break

            data = line.split("\t")
            string = "%s\t%s\t%s\t%s\t%s\n" % ( data[0], data[4], data[1], data[2], data[3] )

            self.outFile.write( string )

            line = self.inFile.readline()

        self.inFile.close()
        self.outFile.close()

    #--------------------------------------------------------------------------

    def pals2align( self, sameSequences=False ):

        """
        Convert the output from PALS (GFF2 format) into the 'align' format.
        """

        self.outFile.close()
        tmpFile = "%s_tmp%s" % ( self.outFileName, os.getpid() )
        tmpFileHandler = open( tmpFile, "w" )

        line = self.inFile.readline()

        while True:

            if line == "":
                break

            data = line.split("\t")

            qryName = data[0]
            source = data[1]
            feature = data[2]
            qryStart = data[3]
            qryEnd = data[4]
            score = data[5]
            strand = data[6]
            frame = data[7]
            attributes = data[8][:-1].split()

            sbjName = attributes[1]
            sbjStart = attributes[2]
            sbjEnd = attributes[3][:-1]
            percId = (1 - float(attributes[-1])) * 100.0

            if strand != "+":
                tmp = sbjStart
                sbjStart = sbjEnd
                sbjEnd = tmp

            if sameSequences \
            and "chunk" in qryName and "chunk" in sbjName \
            and min(int(qryStart),int(qryEnd)) == 1 \
            and min(int(sbjStart),int(sbjEnd)) == 1 \
            and percId == 100.0:
                line = self.inFile.readline()
                continue

            if qryStart < qryEnd:
                string = "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % ( qryName, qryStart, qryEnd, sbjName, sbjStart, sbjEnd, "0.0", score, percId )
            else:
                string = "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % ( qryName, qryEnd, qryStart, sbjName, sbjEnd, sbjStart, "0.0", score, percId )

            tmpFileHandler.write( string )

            line = self.inFile.readline()

        self.inFile.close()
        tmpFileHandler.close()

        os.system( "sort -k 1,1 -k 4,4 -k 2,2n -k 3,3n -k 5,5n -k 6,6n -k 8,8n %s > %s" % ( tmpFile, self.outFileName ) )
        os.remove( tmpFile )

    #--------------------------------------------------------------------------
    
    def pilerTA2grouperMap(self):
        """
        Convert the output file from Piler into grouper format.
        """

        inFilePyrName = self.inFileName.split('.') [0] + "_pyr.gff"
        if os.path.exists( inFilePyrName ):
            print "*** OK: input file '%s' does exist" % ( inFilePyrName )
        else:
            print "*** Error: input file '%s' doesn't exist" % ( inFilePyrName )
            sys.exit(1)
        inFilePyr = open( inFilePyrName, "r" )    


        #step 0 : get pile Info and write out an info file
    
        lineFilePyr = inFilePyr.readline() #-tan_pyr.gff
    
        while True:
            if lineFilePyr == "":
                break
    
            
            data = lineFilePyr.split('\t')
            pyrData = data [8]
    
            pyrIndex = pyrData.replace ('PyramidIndex', 'Pyramid')
    
            lineFile = self.inFile.readline() #-tan.gff
            while True:
                if lineFile == "":
                    break
                
                if pyrIndex in lineFile:
                    
                    dataTan = lineFile.split(';')
                    pileIndex = dataTan [1]
                    pileIndex = pileIndex.strip()
                   
                    break
                lineFile = self.inFile.readline()
    
            string = "%s\t%s" % ( pileIndex, pyrIndex)
    
           
                
            self.outFile.write( string )
            pileIndex = ""
            pyrIndex = "" 
            lineFilePyr = inFilePyr.readline()
    
        self.inFile.close()
        self.outFile.close()    
                
        
        #Step 1 : Add pile info to motif file and write out two files one with grouperID and one in map format
    
        ############################################################################################################
    
        inFileInfoName = self.outFileName
        if os.path.exists( inFileInfoName ):
            print "*** OK: input file '%s' does exist" % ( inFileInfoName )
        else:
            print "*** Error: input file '%s' doesn't exist" % ( inFileInfoName )
            sys.exit(1)
        inFileInfo = open( inFileInfoName, "r" )
    
        ############################################################################################################
    
        inFileMotifName = self.inFileName.split('.') [0] + "_motif.gff"
        if os.path.exists( inFileMotifName ):
            print "*** OK: input file '%s' does exist" % ( inFileMotifName )
        else:
            print "*** Error: input file '%s' doesn't exist" % ( inFileMotifName )
            sys.exit(1)
        inFileMotif = open( inFileMotifName, "r" )
    
        ############################################################################################################
    
        outFileMotifName = inFileMotifName + ".grp"
        if outFileMotifName != "":
            outFileMotif = open( outFileMotifName, "w" )
        else:
            print "*** Error: output file name is missing"
               
        ############################################################################################################
    
        outFileMotifGrpMapName = inFileMotifName + ".grp.map"
        if outFileMotifGrpMapName != "":
            outFileMotifGrpMap = open( outFileMotifGrpMapName, "w" )
        else:
            print "*** Error: output file name is missing"
        
        ############################################################################################################
    
        
        countMotif = 0
        lineFileMotif = inFileMotif.readline()
        lineFileInfo = inFileInfo.readline()
        
        while True:
            if lineFileMotif == "":
                    break
            dataMotif = lineFileMotif.split(';')
            pyrNameMotif = dataMotif [1]
            pyrNameMotif = pyrNameMotif.strip()
           
            motif = dataMotif [0]
            
            
            while True:
            
                if lineFileInfo == "":
                        break
                if pyrNameMotif in lineFileInfo:
               
                    dataTan = lineFileInfo.split('\t')
                    pileNameMotif = dataTan [0]
                  
                    break
            
                lineFileInfo = inFileInfo.readline()
    
            
            
            #translate to Grouper IdFormat
    
            pyrID = pyrNameMotif.split(' ') [1]
         
            pileID = pileNameMotif.split(' ') [1]
           
            dataMotif = motif.split ('\t')
            dataTarget = dataMotif [8].split(' ')
            
            
            chr = dataMotif [0]
            start = dataMotif [3]
            end =  dataMotif [4]
            countMotif += 1
            memberID = "MbS%sGr" % (countMotif) + pyrID + "Cl" + pileID
            
            stringMotif = "%s\t%s\t%s\t%s\n" % ( memberID, motif, pileNameMotif, pyrNameMotif)
            outFileMotif.write( stringMotif )
    
            stringGrpMap = "%s\t%s\t%s\t%s\n" % ( memberID, chr, start, end )
            outFileMotifGrpMap.write( stringGrpMap )    
          
            lineFileMotif = inFileMotif.readline()
        
        inFileMotif.close()
        inFileInfo.close()
        outFileMotif.close()
        outFileMotifGrpMap.close()

#------------------------------------------------------------------------------

# used in MrepsParser

class FindRep( ContentHandler ):

    #--------------------------------------------------------------------------

    def __init__(self,fileoutname,filter,count=0):
        self.inWindowContent=0
        self.inSeqNameContent=0
        self.inStartContent=0
        self.inEndContent=0
        self.inPeriodContent=0
        self.inUnitContent=0
        self.inScoreContent=0
        self.count=count
        self.fileout=open(fileoutname,"w")
        self.filter=filter

    #--------------------------------------------------------------------------

    def startElement(self,name,attrs):
        if name=="window":
            self.inWindowContent=1
        elif name=="sequence-name":
            self.inSeqNameContent=1
            self.seqname=""
        elif name=="repeat":
            self.inRepContent=1
            self.start=""
            self.end=""
            self.period=""
            self.type={}
        elif name=="start":
            self.inStartContent=1
        elif name=="end":
            self.inEndContent=1
        elif name=="period":
            self.inPeriodContent=1
        elif name=="unit":
            self.inUnitContent=1
            self.unit=""
        elif name=="score":
            self.inScoreContent=1
            self.score=""

    #--------------------------------------------------------------------------

    def characters(self,ch):
        if self.inSeqNameContent:
            self.seqname+=ch
        elif self.inStartContent:
            self.start+=ch
        elif self.inEndContent:
            self.end+=ch
        elif self.inPeriodContent:
            self.period+=ch            
        elif self.inUnitContent:
            self.unit+=ch            
        elif self.inScoreContent:
            self.score+=ch            

    #--------------------------------------------------------------------------

    def endElement(self,name):
        if name=="window":
            self.inWindowContent=0
        elif name=="sequence-name":
            self.inSeqNameContent=0
        elif name=="repeat":
            self.inRepContent=0
            start=int(self.start)
            end=int(self.end)
            period=int(self.period)
            score=float(self.score)
            if score>self.filter:
                return
            max=0
            self.count+=1
            for k,n in self.type.items():
                if n>max:
                    max=n
                    k_max=k

            m=re.match("^[0-9]+.+\{Cut\}",self.seqname)
            if m!=None:
                seqname=self.seqname[m.start(0):m.end(0)-5].rstrip()
                seqname=re.sub("^[0-9]+ ","",seqname).lstrip()
                tok=self.seqname[m.end(0):].split("..")
                astart=start+int(tok[0])-1
                aend=end+int(tok[0])-1
            else:
                astart=start
                aend=end
                seqname=self.seqname
            if len(k_max) > 100:
                k_max=k_max[:48]+"..."+k_max[-51:]
            strout="%d\t(%s)%d\t%s\t%d\t%d"%\
                               (self.count,k_max,(abs(start-end)+1)/period,\
                                seqname,astart,aend)
            self.fileout.write("%s\n"%(strout))
            print strout

        elif name=="start":
            self.inStartContent=0
        elif name=="end":
            self.inEndContent=0
        elif name=="period":
            self.inPeriodContent=0
        elif name=="score":
            self.inScoreContent=0
        elif name=="unit":
            self.inUnitContent=0
            if self.type.has_key(self.unit):
                self.type[self.unit]+=1
            else:
                self.type[self.unit]=1

#------------------------------------------------------------------------------

class MrepsParser:

    #--------------------------------------------------------------------------

    def __init__( self, inFileName, MrepsOutFileName, outFileName, errorFilter ):

        """
        constructor

        @param inFileName: name of the input file given to Mreps
        @type inFileName: string

        @param MrepsOutFileName: name of the output file from Mreps ('xml' format)
        @type MrepsOutFileName: string

        @param outFileName: name of the output file ('set' format)
        @type outFileName: string

        @param errorFilter: error filter
        @type errorFilter: float
        """

        self.inFileName = inFileName
        self.MrepsOutFileName = MrepsOutFileName
        if outFileName == "":
            outFileName = inFileName + ".SSRtrf.set"
        self.outFileName = outFileName
        self.errorFilter = errorFilter

    #--------------------------------------------------------------------------

    def xml2set( self ):

        xmlParser = make_parser()
        xmlParser.setFeature( feature_namespaces, 0 )
        xmlParser.setContentHandler( FindRep( self.outFileName, self.errorFilter, 0 ) )

        MrepsOutFile = open( self.MrepsOutFileName, "r" )
        xmlParser.parse( MrepsOutFile )
        MrepsOutFile.close()

    #--------------------------------------------------------------------------

    def clean( self ):

        """
        Remove the output file (xml) from Mreps to keep only the 'set' file.
        """

        cmd = "rm -f %s" % ( self.MrepsOutFileName )
        log = os.system( cmd )
        if log != 0:
            print "*** Error in pyRepet.parser.Parser.MrepsParser.clean"
            sys.exit(1)
