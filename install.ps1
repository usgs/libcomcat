#!/bin/bash

$mini_conda_url="https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe"


echo "Path:"
echo $env:Path

$VENV="comcat"


# Is conda installed?
If ((Get-Command "conda" -ErrorAction SilentlyContinue) -eq $null){
    echo "No conda detected, installing miniconda..."
    echo "Install directory: $HOME/miniconda"
    Invoke-WebRequest -Uri $mini_conda_url -OutFile ".\condainstall.exe"
    Start-Process -FilePath ".\condainstall.exe" -PassThru -Wait -ArgumentList "/S /AddToPath=1"
}Else{
    echo "conda detected, installing $VENV environment..."
}
# So that the path is updated
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine")
$conda_path = Write-Output $env:CONDA_PREFIX
$env:Path += ";$conda_path"
conda --version

echo "PATH:"
echo $env:PATH
echo ""

# Start in conda base environment
echo "Activate base virtual environment"
conda activate base

# Remove existing libcomcat environment if it exists
conda remove -y -n $VENV --all

# Package list:
$package_list=
      "python>=3.6",
      "impactutils",
      "ipython",
      "jupyter",
      "numpy",
      "obspy",
      "pyproj",
      "pandas",
      "pip",
      "pytest",
      "pytest-cov",
      "vcrpy",
      "xlrd",
      "xlwt",
      "openpyxl",
      "xlsxwriter"

# Create a conda virtual environment
echo "Creating the $VENV virtual environment:"
echo "conda create -y -n $VENV -c conda-forge --channel-priority $package_list"
conda create -y -n $VENV -c conda-forge --channel-priority $package_list

# Bail out at this point if the conda create command fails.
# Clean up zip files we've downloaded
If (-NOT ($?) ) {
    Write-Output "Failed to create conda environment.  Resolve any conflicts, then try again."
    return False
} 


# Activate the new environment
echo "Activating the $VENV virtual environment"
conda activate $VENV

# This package
echo "Installing libcomcat..."
pip install -e .