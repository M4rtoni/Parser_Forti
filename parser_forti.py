#!/bin/python
# -*- coding: utf-8 -*-

"""################################################################################
#
# File Name         : parser_forti.py
# Created By        : Florian MAUFRAIS
# Contact           : florian.maufrais@nxosecurity.com
# Creation Date     : april  13th, 2015
# Version           : 1.2.2
# Last Change       : April 25th, 2017 at 11:28
# Last Changed By   : Florian MAUFRAIS
# Purpose           : This programm could parse backup files of a
#                     Fortigate appliance to a JSON/dict and XLSX structure
#
#
################################################################################"""

__version__ = "1.2.2"
__all__ = ['parse','Parser','Parsed_to_xls','main','prepare','build_xls']

################################################################################

import argparse
import sys
parser = argparse.ArgumentParser(description='Process some Fortigate configuration files.')
parser.add_argument('--files', dest='files', action='store',
    default='*.conf', help='type off file search (default: *.conf)')
parser.add_argument('--dir', dest='dir', action='store',
    default='./', help='searching folder (default: ./)')
parser.add_argument('--json', dest='JSON', action='store_true',
    default=False, help='write result in a JSON file (default: False)')
parser.add_argument('--xlsx', dest='XLSX', action='store_true',
    default=False, help='write result in a XLSX file (default: False)')
if __name__ == '__main__':
    args = parser.parse_args(sys.argv[1:])

import shlex
import json

# Openpyxl (c) 2017
# Author : Eric Gazoni, Charlie Clark
# Licence : MIT/Expat
# Version 2.4.7

from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment

class Parser(dict):
    def __init__(self,config):
        self.headers = []
        if type(config) is str:
            for conf in config.split('\n'):
                if conf.startswith('#'):
                    self.headers.append(conf)
                else: 
                    break
            index = sum([len(header) for header in self.headers])+len(self.headers)
            self.__config = parse(config[index:], res = {})
            self.__config.update({'headers':self.headers})
        elif type(config) is dict:
            self.__config = config
    def __repr__(self):
        return self.__config.__repr__()
    def __getitem__(self,*args):
        return self.__config.__getitem__(*args)
    def keys(self):
        return self.__config.keys()
    def prepare(self, key = None):
        if key == None:
            self.__prepared = prepare(self.__config)
        else:
            self.__prepared = prepare(self.__config.__get__(key,None))
        return self.__prepared
    def build_xls(self, key = None):
        if key == None:
            self.__built_xls = build_xls(self.__prepared)
        else:
            self.__built_xls = build_xls(self.__prepared.__get__(key,None))
    def Parsed_to_xls(self, key, name, save = False):
        self.__workbook = Parsed_to_xls(self.__prepared, key, name, save)
        return self.__workbook

def parse(config,end=('end','next'),res={},titles=('set','unset')):
    """ Function that take Fortigate backup configuration file and return
    a JSON/dict structure where every key is a JSON/dict elements 
    with an higer level
    
    Here is an example:
        >>> config = 'config system interface\\n'+\\
        ... '    edit "port 1"\\n'+\\
        ... '        set vdom "root"\\n'+\\
        ... '        set ip 192.168.1.254 255.255.255.0\\n'+\\
        ... '        set allowaccess ping\\n'+\\
        ... '        set type physical\\n'+\
        ... '        set alias "Internet access"\\n'+\\
        ... '        set snmp-index 1\\n'+\\
        ... '    next\\n'+\\
        ... 'end'
        >>> result = parse(config)
        >>> print result.keys()
        ['config system interface']
        >>> print result['config system interface']['edit "port 1"']['ip']
        {'set': ['192.168.1.254', '255.255.255.0']}
        >>> print result['config system interface']['edit "port 1"']['type']
        {'set': ['physical']}
    
    return a dict
    """
    
    #
    # On serape chaque entrée, en prenant compte des entrées multi-lignes
    #
    
    _config = config.split('\n')
    __config = []
    _c = ''
    for c in _config:
        _c += c
        __c = True
        try:
            ___c = shlex.split(_c)
        except:
            __c = False
            _c += '\n'
        if __c:
            __config.append(_c)
            _c = ''
    
    _config = __config
    index = 0
    _old_index = 0
    
    #
    # On boucle a chaque bloc
    #
    
    while index < len(_config):
        
        #
        # On prépare le titre du bloc
        #
        
        title = _config[index]
        _end = None
        
        #
        # On prend en compte l'indentation
        #
        
        if title.startswith(' '*4):
            _end = end
        
        while title.startswith(' '*4):
            end = tuple((' '*4+e for e in end))
            title = title[4:]
        
        index+=1
        
        #
        # On cherche la fin du bloc
        #
        
        if True in [_config[index:].__contains__(e) for e in end]:
            stop = max([_config.index(e,index) for e in end if _config[index:].__contains__(e)])
        else:
            stop = len(_config)
        
        #
        # Identification du bloc à travailler
        #
        
        working = _config[index:stop]
        
        #
        # On retire l'indentation
        #
        
        working = [w.replace(' '*4,'',1) for w in working] 
        while set([w[:4] for w in working if not w in end]) == set([' '*4]):
            working = [w.replace(' '*4,'',1) for w in working]
        
        rep = {}
        rem = []
        
        #
        # On cherche les titres de variable (set, unset, edit)
        # "edit" est un titre ambigu, il peut servir pour un titre de variable ou de bloc
        #
        
        for i in range(len(working)):
            for t in titles:
                if working[i].startswith(t):
                    r = shlex.split(working[i])
                    if r[2:] == []:
                        rep.update({r[1]:r[0]})
                    else:
                        rep.update({r[1]:{r[0]:r[2:]}})
                    rem.append(working[i])
                    break
        
        for r in rem: # On retire les variables identifiées du bloc
            working.remove(r)
        
        if set([w[:4] for w in working if not w in end]) == set([' '*4]):
            working = [w.replace(' '*4,'',1) for w in working]
        
        if _end != None:
            end = _end
        
        working = '\n'.join(working)
        # On remet le bloc en forme de texte, pret pour un récurtion d'un bloc de plus
        # haut niveau
        if _old_index == index or title == '':
            # On sort de la boucle si le bloc n'avance plus, pour éviter la boucle
            # infini
            for key in res.keys():
                # on retire des titres qui aurait pu être rajoutés
                for e in end+('',):
                    if e in res.keys() and res == {e:[]}:
                        res = e
                    elif e in res.keys() and res[e] in [{}]:
                        res.pop(e)
        elif working == '':
            # On ajout les variables avant de sortir
            res.update({title:rep})
        else:
            # On ajoute le bloc et on entre en récurtion avec la partie non traitée du bloc
            res.update({title:parse(working,end=end,res=rep)})
        # On prépare à passer au bloc suivant ou finir la boucle
        _old_index = index
        index = stop+1
    for key in res.keys():
        # On retire des titres qui aurait pu être rajoutés
        for e in end+('',):
            if e in res.keys() and res == {e:[]}:
                res = e
            elif e in res.keys() and res[e] in [{}]:
                res.pop(e)
    return res

def prepare(dico):
    """ Function that take Fortigate backup configuration file parsed 
    in a JSON/dict and return a JSON/dict structure where every key 
    of higer level is an option or a next level config
    
    Here is an example:
        >>> config = 'config system interface\\n'+\\
        ... '    edit "port 1"\\n'+\\
        ... '        set vdom "root"\\n'+\\
        ... '        set ip 192.168.1.254 255.255.255.0\\n'+\\
        ... '        set allowaccess ping\\n'+\\
        ... '        set type physical\\n'+\
        ... '        set alias "Internet access"\\n'+\\
        ... '        set snmp-index 1\\n'+\\
        ... '    next\\n'+\\
        ... 'end'
        >>> res = parse(config)
        >>> rem = prepare(res)
        >>> rem.keys()
        ['conf']
        >>> rem['conf'].keys()
        ['config system interface']
        >>> rem['conf']['config system interface'].keys()
        ['conf']
        >>> rem['conf']['config system interface']['conf'].keys()
        ['edit "port 1"']
        >>> rem['conf']['config system interface']['conf']['edit "port 1"'].keys()
        ['opt']
        >>> rem['conf']['config system interface']['conf']['edit "port 1"']['opt']
        ['alias', 'allowaccess', None, 'ip', 'type', 'snmp-index', 'vdom']
    
    return a dict or None
    """
    
    #
    # On verifie les entrées
    #
    
    if type(dico) is dict:
        keys = {'conf':{},'opt':{}}
        _keys = set()
        
        #
        # On va trier pour chacunes des valeurs du dictionnaire
        #
        
        for key in dico.keys():
            _key = shlex.split(key)
            if _key[0] in ['config','edit']: 
                # Si c'est un niveau des configurations plus élevées
                keys['conf'].update({key:dico[key]})
            else:
                # Sinon c'est une donnée
                try:
                    value = dico[key]['set']
                except:
                    value = str(dico[key])
                if type(value) is list:
                    keys['opt'].update({key:'\n'.join(value)})
                else:
                    keys['opt'].update({key:str(value)})
                _keys.update([key])
        
        #
        # On ajoute un entrée qui contient le titre des données
        #
        keys['opt'].update({None:list(_keys)})
        
        #
        # Pour chaque niveau de configuration plus élevé
        # On déclence une récurtion
        #
        
        conf = {key:prepare(keys['conf'][key]) for key in keys['conf'].keys()}
        keys.update({'conf':conf})
        
        #
        # On retire les entrée si elles n'ont pas reçu de données
        #
        
        if keys['opt'][None] == []:
            _ = keys.pop('opt')
        if keys['conf'] == {}:
            _= keys.pop('conf')
        return keys
    else:
        return None
    
def build_xls(dico):
    """ Function that take Fortigate backup configuration file parsed 
    and prepared in a JSON/dict and return a tuple of two lists :
        - rep : All data at current level
        - conf : All data with a higher level
    
    Here is an example:
        >>> config = 'config system interface\\n'+\\
        ... '    edit "port 1"\\n'+\\
        ... '        set vdom "root"\\n'+\\
        ... '        set ip 192.168.1.254 255.255.255.0\\n'+\\
        ... '        set allowaccess ping\\n'+\\
        ... '        set type physical\\n'+\
        ... '        set alias "Internet access"\\n'+\\
        ... '        set snmp-index 1\\n'+\\
        ... '    next\\n'+\\
        ... 'end'
        >>> res = parse(config)
        >>> rem = prepare(res)
        >>> rep , conf = build_xls(rem)
        >>> rep
        []
        >>> for item in conf:
        ...     item
        ['Names']
        ['config system interface']
        ['config system interface']
        [None, 'Names', 'ip', 'alias', 'allowaccess', 'type', 'snmp-index', 
        'vdom']
        [None, 'edit "port 1"', '192.168.1.254\n255.255.255.0', 
        'Internet access', 'ping', 'physical', '1', 'root']
    
    return a tuple of two lists
    """
    
    #
    # On verifie les entrées
    #
    
    if type(dico) is dict:
        if set([key in ['conf','opt'] for key in dico.keys()]) == set([True]):
            rep = []
            conf = []
            if dico.has_key('opt') and type(dico['opt']) is dict:
                
                #
                # On trie les données
                #
                
                rep += [dico['opt'][None]]# On donne le titre des futurs
                # colonnes
                index = len(rep)
                _ = dico['opt'].pop(None)
                rep += [[]]
                
                #
                # On rempli chaque colonne en s'assurant d'avoir une 
                # valeur pour chaque titre, sinon on remplie avec une
                # valeur nulle
                #
                
                for key in rep[index-1]:
                    if key in rep[index-1]:
                        rep[index] += [dico['opt'][key]]
                    else:
                        rep[index] += [None]
            
            if dico.has_key('conf') and type(dico['conf']) is dict:
                
                #
                # On trie les données des configurations plus élevées
                #
                
                __rep = {}
                __conf = {}
                for key in dico['conf'].keys():
                    
                    #
                    # On entre en récurtion pour chaque configuration
                    # de plus haut niveau
                    #
                    
                    rep__, conf__ = build_xls(dico['conf'][key])
                    __rep.update({key:rep__})
                    __conf.update({key:conf__})
                
                #
                # On trie les données de ce niveau en regroupant
                # l'ensemble des configuration de même niveau
                # (uniquement le le niveau N+1)
                #
                
                titles = set()
                for _index in __rep.keys():
                    if __rep[_index] in [None,[]]:
                        continue
                    titles.update(__rep[_index][0])
                
                titles = list(titles)
                conf += [['Names']+titles]
                for key in dico['conf'].keys():
                    index = len(conf)
                    conf += [[key]]
                    for _key in titles:
                        if __rep[key] in [None,[]]:
                            conf[index] += [None]
                        else:
                            if _key in __rep[key][0]:
                                conf[index] += [__rep[key][1]\
                                    [__rep[key][0].index(_key)]]
                            else:
                                conf[index] += [None]
                
                #
                # On regarde si on a un configuration de niveau N+2
                #
                
                if __conf == {key:[] for key in dico['conf'].keys()}:
                    # Ici toutes les configuration de niveau N+1 ne 
                    # contenait que des données
                    pass
                else:
                    for key in __conf.keys():
                        # Pour chaque configuration de niveau N+2,
                        # on prend l'ensemble de ces données que l'on
                        # décale d'une colonne après avoir rajouté un
                        # titre
                        if __conf[key] in [None,[]]:
                            pass
                        else:
                            conf += [[key]]
                            for line in __conf[key]:
                                conf += [[None]+line]
            return rep, conf
        else:
            return None, None
    else:
        return None, None

def Parsed_to_xls(dico, key, name, save = False):
    """ Function that take Fortigate backup configuration file parsed 
    and prepared in a JSON/dict and return a tuple of two lists :
        - rep : All data at current level
        - conf : All data with a higher level
    
    Here is an example:
        >>> config = 'config system interface\\n'+\\
        ... '    edit "port 1"\\n'+\\
        ... '        set vdom "root"\\n'+\\
        ... '        set ip 192.168.1.254 255.255.255.0\\n'+\\
        ... '        set allowaccess ping\\n'+\\
        ... '        set type physical\\n'+\
        ... '        set alias "Internet access"\\n'+\\
        ... '        set snmp-index 1\\n'+\\
        ... '    next\\n'+\\
        ... 'end'
        >>> res = parse(config)
        >>> rem = prepare(res)
        >>> rep , conf = build_xls(rem)
        >>> rep
        []
        >>> for item in conf:
        ...     item
        ['Names']
        ['config system interface']
        ['config system interface']
        [None, 'Names', 'ip', 'alias', 'allowaccess', 'type', 'snmp-index', 
        'vdom']
        [None, 'edit "port 1"', '192.168.1.254\n255.255.255.0', 
        'Internet access', 'ping', 'physical', '1', 'root']
    
    return a Workbook openpyxl or None
    """
    
    #
    # On réduit le dictionnaire à la ou les clés prédéfinit
    #
    
    if type(dico) is dict and type(key) in [str,unicode]:
        keys = sorted([_key for _key in dico.keys() if key in _key])
    elif type(dico) is dict and type(key) is list:
        keys = sorted([_key for _key in dico.keys() if True in [__key in _key for __key in key]])
    else:
        return None
    
    #
    # On prépare le Workbook
    # 
    
    wb = Workbook()
    accueil = wb.active
    accueil.title = "Accueil"
    for _key in keys: # Pour chacune des clés retenues
        __key = _key.split(' ',1)[1]
        wb.create_sheet(__key) # On crée une feuille de travail
        rep = prepare(dico[_key]) # On prepare le dictionnaire 
        rep, conf = build_xls(rep) # On recolte les données 
        # correctement formatées
        if rep == None:
            continue 
        _j = 0
        for j in range(len(rep)): # Pour l'ensemble des données
            _j = j # On se souvient du nombre de lignes écrites
            for i in range(len(rep[j])): # Pour chaque valeur
                value = rep[j][i]
                if value.isdigit(): # On la prépare sous forme de nombre...
                    wb[__key][get_column_letter(1+i)+str(j+1)].value = int(value)
                else: # ... ou de chaîne de caractère
                    wb[__key][get_column_letter(1+i)+str(j+1)].value = str(value)
                    if '\n' in str(value): # On prend en compte les données sur
                        # plusieurs lignes
                        wb[__key][get_column_letter(1+i)+str(j+1)].alignment = Alignment(wrapText=True)
        for j in range(len(conf)): # Pour l'ensemble des configurations de plus
            # haut niveau
            for i in range(len(conf[j])): # Pour chaque valeur
                value = conf[j][i]
                if value == None: # On s'assure qu'elle ne soit pas nulle
                    pass
                elif value.isdigit(): # On la prépare sous forme de nombre...
                    # On prend en compte les lignes déjà écritent
                    wb[__key][get_column_letter(1+i)+str(j+_j+1)].value = int(value)
                else: # ... ou de chaîne de caractère
                    # On prend en compte les lignes déjà écritent
                    wb[__key][get_column_letter(1+i)+str(j+_j+1)].value = str(value)
                    if '\n' in str(value): # On prend en compte les données sur
                        # plusieurs lignes et les lignes déjà écritent
                        wb[__key][get_column_letter(1+i)+str(j+_j+1)].alignment = Alignment(wrapText=True)
    
    #
    # On retire les feuilles vides
    #
    
    empty_worksheet = []
    for sheet in wb.sheetnames[1:]:
        if len(wb[sheet].__dict__['_cells']) < 2:
            empty_worksheet.append(sheet)
    
    #
    # On notifie sur la page d'accueil qu'elle ont tout de même
    # été traitée
    #
    
    accueil['J5'].value = 'Empty sheets'
    for sheet in empty_worksheet:
        wb.remove_sheet(wb[sheet])
        accueil['J'+str(6+empty_worksheet.index(sheet))].value = sheet
    
    #
    # On créer un lien vers l'ensemble des feuilles (non vide)
    #
    
    accueil['B5'].value = 'Links'
    for sheet in wb.sheetnames[1:]:
        accueil['B'+str(5+wb.sheetnames.index(sheet))].value = sheet
        accueil['B'+str(5+wb.sheetnames.index(sheet))].hyperlink = name +\
            '#'+(sheet,"'"+sheet+"'")[' ' in sheet]+'!A1'
    
    #
    # On ajuste la largeur des colonnes 
    #
    
    for sheet in wb.sheetnames: # Pour chaque feuille
        column_widths = []
        try:
            for row in wb[str(sheet)]: #Pour chacune ligne
                for i, cell in enumerate(row): # Pour chaque cellule
                    if cell.value != None: # si elle n'est pas vide
                        if len(column_widths) > i: # et que ce n'est pas une
                            # cellule de la première ligne
                            if type(cell.value) in [str,unicode]:
                                if '\n' in str(cell.value.encode('UTF-8')):
                                    # Si c'est une chaîne de caractère
                                    for value in cell.value.encode('UTF-8').split('\n'):
                                        # On verifie pour chaque ligne si le texte
                                        # est plus grand que la valeur maximale
                                        # déjà enregistrée
                                        if len(value) > column_widths[i]:
                                            column_widths[i] = len(value)+1
                                else:
                                    if len(cell.value) > column_widths[i]:
                                        column_widths[i] = len(cell.value)+1
                        else:
                            # Sinon, 
                            column_widths += [max(10,len(cell.value)+1)]
                    else:
                        if len(column_widths) < i:
                            # et que c'est une cellule de la première ligne
                            column_widths += [10]
            
            
            for i, column_width in enumerate(column_widths):
                # On fixe la largeur des colonne pour les valeurs données
                wb[str(sheet)].column_dimensions[get_column_letter(i+1)].width = column_width
        except TypeError, e:
            if e.message == "iter() returned non-iterator of type 'tuple'":
                pass
            else:
                raise TypeError, e
    if save: # On enregistre le fichier au besoin
        wb.save(name)
    return wb

def main():
    import os
    import re
    files = os.listdir(args.dir) # On liste l'ensemble des fichiers du répertoire choisit
    p = re.compile('('+args.files.replace('.','[.]').replace('*','.*?')+')$')
    files = [p.findall(file)[0] for file in files if p.findall(file) != []] 
    # On cherche tous les fichiers qui vont correspondre a critère définit
    for file in files: # Pour chaque fichier
        print 'Processing :',file
        
        #
        # Lecture du fichier
        #
        
        print '\tReading :',
        f = open('./'+file)
        config = f.read()
        f.close()
        print 'done'
        headers = []# Identification des headers
        print '\tHeader :',
        for conf in config.split('\n'):
            if conf.startswith('#'):
                headers.append(conf)
            else: 
                break
        index = sum([len(header) for header in headers])+len(headers)
        print 'done'
        
        #
        # Parsing de la conf
        #
        
        print '\tParsing :',
        res = parse(config[index:],res = {})
        print 'done'
        
        if args.XLSX:
            
            #
            # Creation des fichiers xlsx
            #
            
            print '\tFormat XLS :',
            wb = Parsed_to_xls(res, ['firewall','vpn','proxy','webfilter',
                'rooter','ips','system','application'], 
                file[::-1].split('.',1)[1][::-1]+'.xlsx', save = True)
            print 'done'
        
        if args.JSON:
            
            #
            # Ecriture des fichiers JSON
            #
            
            res.update({'headers':headers})
            print '\tFormat JSON :',
            str_ = json.dumps(res,indent=4, sort_keys=True, ensure_ascii=False)
            with open(file[::-1].split('.',1)[1][::-1]+'.json', 'w') as outfile:
                outfile.write(str_)
            print 'done'
        
        print

if __name__ == '__main__':
    main()
