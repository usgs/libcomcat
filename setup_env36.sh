#!/bin/bash

VENV=comcat36
PYVER=3.6

DEPARRAY=(obspy ipython jupyter pandas xlrd xlwt openpyxl)

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

#download neicmap, install it using pip locally
curl --retry 3 -L https://github.com/usgs/earthquake-impact-utils/archive/master.zip -o impact.zip
pip install impact.zip
rm impact.zip

#tell the user they have to activate this environment
echo "Type 'source activate ${VENV}' to use this new virtual environment."
