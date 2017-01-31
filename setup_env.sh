#!/bin/bash

VENV=libcomcat
PYVER=2.7

DEPARRAY=(numpy scipy matplotlib jupyter ipython)

#if we're already in an environment called pager, switch out of it so we can remove it
source activate root
    
#remove any previous virtual environments called libcomcat
CWD=`pwd`
cd $HOME;
conda remove --name $VENV --all -y
cd $CWD
    
#create a new virtual environment called $VENV with the below list of dependencies installed into it
conda create --name $VENV --yes --channel conda-forge python=$PYVER ${DEPARRAY[*]} -y

#activate the new environment
source activate $VENV

#download neicio, install it using pip locally
curl --retry 3 -L https://github.com/usgs/neicio/archive/master.zip -o neicio.zip
pip install neicio.zip
rm neicio.zip

#download neicmap, install it using pip locally
curl --retry 3 -L https://github.com/usgs/neicmap/archive/master.zip -o neicmap.zip
pip install neicmap.zip
rm neicmap.zip

#tell the user they have to activate this environment
echo "Type 'source activate ${VENV}' to use this new virtual environment."
