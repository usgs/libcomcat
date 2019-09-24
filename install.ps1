$VENV = comcat

# Is conda installed?
conda --version
If (($?)) {
    
    Write-Output "conda detected, installing $VENV environment..."

  }  Else {
    
    Write-Output "No conda detected, please install miniconda or anaconda..."
    return False

} 

conda init powershell

# Start in conda base environment
Write-Output "Activate base virtual environment"
conda activate base

# Remove existing libcomcat environment if it exists
conda remove -y -n $VENV --all

# Package list:
$package_list=@(
      ("python>=3.6"),
      ("impactutils"),
      ("ipython"),
      ("jupyter"),
      ("numpy"),
      ("obspy"),
      ("pandas"),
      ("pip"),
      ("pytest"),
      ("pytest-cov"),
      ("vcrpy"),
      ("xlrd"),
      ("xlwt"),
      ("openpyxl"),
      ("xlsxwriter")
)

# Create a conda virtual environment
echo "Creating the $VENV virtual environment:"
conda create -y -n $VENV -c conda-forge --channel-priority=flexible $package_list

# Bail out at this point if the conda create command fails.
# Clean up zip files we've downloaded
If (-NOT ($?) ) {
    Write-Output "Failed to create conda environment.  Resolve any conflicts, then try again."
    return False
} 

# Activate the new environment
Write-Output "Activating the $VENV virtual environment"
conda activate $VENV

# This package
Write-Output "Installing libcomcat..."
pip install -e .

# Tell the user they have to activate this environment
Write-Output "Type 'conda activate $VENV' to use this new virtual environment."
