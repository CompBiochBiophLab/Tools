# adapted from 
# https://iwatobipen.wordpress.com/2019/12/14/new-trial-of-attentivefp-with-new-atom-feature-dgl-rdkit-chemoinformatics/


import sys
import os
from rdkit import Chem
from rdkit import RDPaths
from collections import defaultdict
from dgl.data.chem.utils import one_hot_encoding
 
ifg_path = os.path.join(RDPaths.RDContribDir, 'IFG')
sys.path.append(ifg_path)
 
import ifg
 
 
def map_fgs(mol):
    atoms = list(mol.GetAtoms())
    for atom in atoms:
        atom.SetProp("IFG_TYPE", "")
    fgs = ifg.identify_functional_groups(mol)
    for fg in fgs:
        for atmid in fg.atomIds:
            atom = mol.GetAtomWithIdx(atmid)
            atom.SetProp('IFG_TYPE', fg.type)
    return mol
 
def make_ifg_list(mols):
    res = set()
    for mol in mols:
        for atom in mol.GetAtoms():
            ifg = atom.GetProp('IFG_TYPE')
            res.add(ifg)
    return list(res)
 
def atom_ifg_one_hot(atom, allowable_set=None, encode_unknown=False):
    if allowable_set is None:
        raise Exception
    try:
        ifg = atom.GetProp('IFG_TYPE')
    except:
        print('get IFG TYPE at First')
         
    return one_hot_encoding(ifg, allowable_set, encode_unknown=encode_unknown)