from distutils.core import setup
import os.path


setup(
    name="libcomcat",
    description="USGS ComCat search API in Python",
    author="Mike Hearne",
    author_email="mhearne@usgs.gov",
    url="https://github.com/usgs/libcomcat",
    version="2.1.2",
    packages=["libcomcat", "libcomcat.bin"],  # must be here or scripts won't install!
    package_data={
        "libcomcat": [
            os.path.join("data", "ne_50m_admin_0_countries.prj"),
            os.path.join("data", "ne_50m_admin_0_countries.dbf"),
            os.path.join("data", "ne_50m_admin_0_countries.shp"),
            os.path.join("data", "ne_50m_admin_0_countries.cpg"),
            os.path.join("data", "ne_50m_admin_0_countries.shx"),
        ]
    },
    entry_points={
        "console_scripts": [
            "findid = libcomcat.bin.findid:main",
            "getcsv = libcomcat.bin.getcsv:main",
            "geteventhist = libcomcat.bin.geteventhist:main",
            "getmags = libcomcat.bin.getmags:main",
            "getpager = libcomcat.bin.getpager:main",
            "getphases = libcomcat.bin.getphases:main",
            "getproduct = libcomcat.bin.getproduct:main",
        ]
    },
    install_requires=[
        "esi-extern-openquake",
        "esi-utils-io",
        "esi-utils-time",
        "fiona>=1.8.20",
        "numpy>=1.21",
        "obspy",
        "openpyxl",
        "pandas",
        "pip",
        "pyproj",
        "pytest",
        "pytest-cov",
        "shapely",
        "vcrpy",
        "xlrd",
        "xlsxwriter",
        "xlwt",
    ],
)
