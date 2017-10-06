#!/bin/bash

VENV=comcat
PYVER=3.6

DEPARRAY=(obspy=1.0.3 ipython=6.1.0 jupyter=1.0.0 pandas=0.20.3 \
          xlrd=1.0.0 xlwt=1.2.0 openpyxl=2.5.0a2 pytest=3.1.2 \
          pytest-cov=2.5.1 sphinx=1.6.3  xlsxwriter=0.9.8)

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
echo "Installing impactutils..."
curl --retry 3 -L https://github.com/usgs/earthquake-impact-utils/archive/master.zip -o impact.zip
pip install impact.zip
rm impact.zip

# This package
echo "Installing libcomcat..."
pip install -e .

#tell the user they have to activate this environment
echo "Type 'source activate ${VENV}' to use this new virtual environment."
