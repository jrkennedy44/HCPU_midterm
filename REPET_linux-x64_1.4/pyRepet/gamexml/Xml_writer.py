import os
from xml.dom.minidom import *
from pyRepet.seq.Bioseq import *
from pyRepet.coord.Map import *
from pyRepet.coord.Set import *
from pyRepet.coord.Align import *
from pyRepet.coord.Path import *
from pyRepet.coord.Match import *
from pyRepet.coord.Range import *
from computational import *

#------------------------------------------------------------------------------

class Xml_writer:

    #--------------------------------------------------------------------------

    def __init__( self, gamedom=None, reverse=0 ):
        self.__gamedom = gamedom
        self.__reverse = reverse        

    #--------------------------------------------------------------------------

    def parse_gamexml( self, f_gamexml ):
        self.__gamedom = parse( f_gamexml )

    #--------------------------------------------------------------------------

    def find_type_file( self, file_name ):

        lName = file_name.split(".")
        return lName[-1]

    #--------------------------------------------------------------------------

    def set_reverse(self):
        self.__reverse = 1

    #--------------------------------------------------------------------------

    def get_reverse(self):
        return self.__reverse

    #--------------------------------------------------------------------------

    def return_balise_residues( self, inFile ):

        """
        renvoi la balise <residues> d'un fichier XML et la retourne dans un objet Bioseq
        """

        bs = Bioseq()
        bs.read( inFile )
        if bs.sequence == "":
            return 0
        return bs.sequence

    #--------------------------------------------------------------------------

    def __return_balise_header( self, inFile ):

        """
        renvoi la balise <header> d'un fichier XML et la retourne dans un objet Bioseq
        """

        bs = Bioseq()
        bs.read( inFile )
        if bs.header == "":
            return 0
        return bs.header

    #--------------------------------------------------------------------------

    def __new_DOM( self, cle, residu, no_seq ):

        """
        create new '.gamexml' file with balises <game> and <seq>
        """

        #creation du document XML avec sa racine
        impl = getDOMImplementation()
        mon_doc = impl.createDocument( None, 'game', None )
        racine = mon_doc.documentElement

        #balise seq
        seq=mon_doc.createElement('seq')
        seq.setAttribute('id',cle)
        seq.setAttribute('focus','true')
        racine.appendChild(seq)
        name_seq=mon_doc.createElement('name')
        residus=mon_doc.createElement('residues')
        seq.appendChild(name_seq)
        if no_seq==0:
            seq.appendChild(residus)
            residus.appendChild(mon_doc.createTextNode(residu))
        name_seq.appendChild(mon_doc.createTextNode(cle))

        map_pos=mon_doc.createElement('map_position')
        racine.appendChild(map_pos)
        arm=mon_doc.createElement('arm')
        arm.appendChild(mon_doc.createTextNode(cle))
        map_pos.appendChild(arm)
        span=mon_doc.createElement('span')
        map_pos.appendChild(span)
        start=mon_doc.createElement('start')
        span.appendChild(start)
        start.appendChild(mon_doc.createTextNode('1'))
        end=mon_doc.createElement('end')
        span.appendChild(end)
        end.appendChild(mon_doc.createTextNode(str(len(residu))))
        self.__gamedom=mon_doc

    #--------------------------------------------------------------------------

    def verif_name_prog( self, name_prog, verbose=0 ):

        #suppresion de comput qui porte deja le nom de name-prog
        prog=self.__gamedom.getElementsByTagName('program')
        for i in prog:
            if (i.firstChild.data==name_prog):
                if verbose > 0:
                    print "deleting nodes..."
                comput_parent=i.parentNode
                comput_parent.parentNode.removeChild(comput_parent)

    #--------------------------------------------------------------------------

    def create_gamexml( self, path_fasta, path_file, name, comput, no_seq, verbose=0 ):

        # check the file format
        if path_file != "":
            type_file = self.find_type_file( path_file )
            if verbose > 0:
                print "type file is: %s" % ( type_file ); sys.stdout.flush()

        # open the files
        file_fasta = open( path_fasta )

        # count the nb of sequences and record them
        if verbose > 0:
            print "reading file %s" % ( path_fasta ); sys.stdout.flush()
        f = file_fasta.read()
        nb_seq = f.count(">")
        if verbose > 0:
            print "nb of sequences = %i" % ( nb_seq ); sys.stdout.flush()
        file_fasta.seek( 0 )
        i = 0
        liste_res = ()
        while i < nb_seq:
            liste_res = liste_res + (self.return_balise_residues(file_fasta),)
            i = i + 1

        dirName = os.path.dirname( os.path.abspath( path_fasta ) )

        file_fasta.seek(0)
        for res in liste_res:
            #extraction de la liste de donnees d'une cle du dictionnaire
            key = self.__return_balise_header( file_fasta )
            data_key = comput.get_key()
            #print "create gamexml file..."; sys.stdout.flush()
            self.__new_DOM( key, res, no_seq )
            if key in data_key:
                key = comput.add_computational( self.__gamedom, name )
            fileName = dirName + "/" + self.key2file( key )
            self.write( fileName )

    #--------------------------------------------------------------------------

    def update_gamexml_comput( self, name, comput, verbose=0 ):

        if verbose > 0:
            print "checking annotation name..."; sys.stdout.flush()
        self.verif_name_prog(name)       
        comput.add_computational(self.__gamedom,name)

    #--------------------------------------------------------------------------

    def update_gamexml_annot( self, table, comput, verbose=0 ):

        if verbose > 0:
            print "add annotations..."; sys.stdout.flush()
        comput.add_annotation(self.__gamedom,table)

    #--------------------------------------------------------------------------

    def write( self, fileName, verbose=0 ):

        """
        Write the data into the given file.
        """

        fileName = fileName + ".new"
        self.__gamedom.writexml( open(fileName,"w") )
        if verbose > 0:
            print "file '%s' written" % ( fileName.split("/")[-1] )
            sys.stdout.flush()

    #--------------------------------------------------------------------------

    def file_in_keys( self, file, comput ):

        key = file.replace( ".gamexml", "" )
        for k in comput.get_key():
            if k.split()[0] == key:
                return 1
        return 0

    #--------------------------------------------------------------------------

    def key2file( self, key ):
        return key.split()[0] + ".gamexml"
