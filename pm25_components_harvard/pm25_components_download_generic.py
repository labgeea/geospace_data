#!/usr/bin/env python3
"""
Harvard Super-Learned PM2.5 Components Download Script
======================================================

Downloads annual predictions of 15 PM2.5 chemical components across the
contiguous United States (2000-2019) from Harvard Dataverse:
- Gridded (50-m urban / 1-km non-urban): doi:10.7910/DVN/3H7DNP
- Geography-Aggregated (state, county, tract, ZCTA, block group, ESRI ZIP, block):
  doi:10.7910/DVN/F6PQAA

Author: GEOSPACE Project
License: Public Domain
"""

import sys
import os
import argparse
import logging
from pathlib import Path
import requests

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

# Setup GEOSPACE framework version mapping
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from version import get_module_version
    __version__ = get_module_version("pm25_components_harvard")
except ImportError:
    __version__ = "1.0.0"

__module__ = "PM2.5 Components (Harvard) Download"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Harvard Dataverse API endpoint for file downloads
DATAVERSE_BASE_URL = "https://dataverse.harvard.edu/api/access/datafile/"

DATASET_DOIS = {
    "gridded": "doi:10.7910/DVN/3H7DNP",
    "aggregated": "doi:10.7910/DVN/F6PQAA",
}

# Variable definitions for all 15 PM2.5 chemical components
PM25_COMPONENT_VARIABLES = {
    # Major components (ug/m3)
    "ec": {
        "name": "Elemental Carbon",
        "formula": "EC",
        "category": "major",
        "units": "ug/m3",
        "r2_urban": 0.910,
        "r2_non_urban": 0.913,
        "description": "Annual mean ambient PM2.5 elemental carbon concentration",
        "aliases": ["elemental_carbon", "black_carbon", "bc"],
    },
    "nh4": {
        "name": "Ammonium",
        "formula": "NH4+",
        "category": "major",
        "units": "ug/m3",
        "r2_urban": 0.910,
        "r2_non_urban": 0.918,
        "description": "Annual mean ambient PM2.5 ammonium ion concentration",
        "aliases": ["ammonium", "nh4_ion"],
    },
    "no3": {
        "name": "Nitrate",
        "formula": "NO3-",
        "category": "major",
        "units": "ug/m3",
        "r2_urban": 0.879,
        "r2_non_urban": 0.878,
        "description": "Annual mean ambient PM2.5 nitrate ion concentration",
        "aliases": ["nitrate", "no3_ion"],
    },
    "oc": {
        "name": "Organic Carbon",
        "formula": "OC",
        "category": "major",
        "units": "ug/m3",
        "r2_urban": 0.856,
        "r2_non_urban": 0.857,
        "description": "Annual mean ambient PM2.5 organic carbon concentration",
        "aliases": ["organic_carbon", "om", "organic_matter"],
    },
    "so4": {
        "name": "Sulfate",
        "formula": "SO4(2-)",
        "category": "major",
        "units": "ug/m3",
        "r2_urban": 0.952,
        "r2_non_urban": 0.957,
        "description": "Annual mean ambient PM2.5 sulfate ion concentration",
        "aliases": ["sulfate", "sulphate", "so4_ion"],
    },
    # Trace elements (ng/m3)
    "br": {
        "name": "Bromine",
        "formula": "Br",
        "category": "trace",
        "units": "ng/m3",
        "r2_urban": 0.859,
        "r2_non_urban": 0.863,
        "description": "Annual mean ambient PM2.5 bromine (bromium) concentration",
        "aliases": ["bromine", "bromium"],
    },
    "ca": {
        "name": "Calcium",
        "formula": "Ca",
        "category": "trace",
        "units": "ng/m3",
        "r2_urban": 0.865,
        "r2_non_urban": 0.875,
        "description": "Annual mean ambient PM2.5 calcium concentration",
        "aliases": ["calcium"],
    },
    "cu": {
        "name": "Copper",
        "formula": "Cu",
        "category": "trace",
        "units": "ng/m3",
        "r2_urban": 0.797,
        "r2_non_urban": 0.787,
        "description": "Annual mean ambient PM2.5 copper concentration",
        "aliases": ["copper"],
    },
    "fe": {
        "name": "Iron",
        "formula": "Fe",
        "category": "trace",
        "units": "ng/m3",
        "r2_urban": 0.875,
        "r2_non_urban": 0.875,
        "description": "Annual mean ambient PM2.5 iron concentration",
        "aliases": ["iron"],
    },
    "k": {
        "name": "Potassium",
        "formula": "K",
        "category": "trace",
        "units": "ng/m3",
        "r2_urban": 0.868,
        "r2_non_urban": 0.866,
        "description": "Annual mean ambient PM2.5 potassium concentration",
        "aliases": ["potassium"],
    },
    "ni": {
        "name": "Nickel",
        "formula": "Ni",
        "category": "trace",
        "units": "ng/m3",
        "r2_urban": 0.848,
        "r2_non_urban": 0.850,
        "description": "Annual mean ambient PM2.5 nickel concentration",
        "aliases": ["nickel"],
    },
    "pb": {
        "name": "Lead",
        "formula": "Pb",
        "category": "trace",
        "units": "ng/m3",
        "r2_urban": 0.833,
        "r2_non_urban": 0.843,
        "description": "Annual mean ambient PM2.5 lead concentration",
        "aliases": ["lead"],
    },
    "si": {
        "name": "Silicon",
        "formula": "Si",
        "category": "trace",
        "units": "ng/m3",
        "r2_urban": 0.851,
        "r2_non_urban": 0.857,
        "description": "Annual mean ambient PM2.5 silicon concentration",
        "aliases": ["silicon"],
    },
    "v": {
        "name": "Vanadium",
        "formula": "V",
        "category": "trace",
        "units": "ng/m3",
        "r2_urban": 0.838,
        "r2_non_urban": 0.841,
        "description": "Annual mean ambient PM2.5 vanadium concentration",
        "aliases": ["vanadium"],
    },
    "zn": {
        "name": "Zinc",
        "formula": "Zn",
        "category": "trace",
        "units": "ng/m3",
        "r2_urban": 0.878,
        "r2_non_urban": 0.881,
        "description": "Annual mean ambient PM2.5 zinc concentration",
        "aliases": ["zinc"],
    },
}

VARIABLE_PACKAGES = {
    "major": ["ec", "nh4", "no3", "oc", "so4"],
    "trace": ["br", "ca", "cu", "fe", "k", "ni", "pb", "si", "v", "zn"],
    "all": [
        "ec", "nh4", "no3", "oc", "so4",
        "br", "ca", "cu", "fe", "k", "ni", "pb", "si", "v", "zn",
    ],
}

# 9 CONUS Census Divisions used by the gridded dataset (doi:10.7910/DVN/3H7DNP)
CENSUS_REGIONS = {
    "NE1": {"name": "New England", "states": "CT, MA, ME, NH, RI, VT", "urban_points": 10750894, "non_urban_points": 176590},
    "MA2": {"name": "Middle Atlantic", "states": "NJ, NY, PA", "urban_points": 21308981, "non_urban_points": 195225},
    "ENC3": {"name": "East North Central", "states": "IL, IN, MI, OH, WI", "urban_points": 29712644, "non_urban_points": 529891},
    "WNC4": {"name": "West North Central", "states": "IA, KS, MN, MO, ND, NE, SD", "urban_points": 13431160, "non_urban_points": 1228700},
    "SA5": {"name": "South Atlantic", "states": "DC, DE, FL, GA, MD, NC, SC, VA, WV", "urban_points": 44100142, "non_urban_points": 565638},
    "ESC6": {"name": "East South Central", "states": "AL, KY, MS, TN", "urban_points": 15769846, "non_urban_points": 407153},
    "WSC7": {"name": "West South Central", "states": "AR, LA, OK, TX", "urban_points": 24000000, "non_urban_points": 1012195},
    "M8": {"name": "Mountain", "states": "AZ, CO, ID, MT, NM, NV, UT, WY", "urban_points": 13668782, "non_urban_points": 2074693},
    "P9": {"name": "Pacific (CONUS)", "states": "CA, OR, WA", "urban_points": 20021752, "non_urban_points": 738363},
}

GEOGRAPHY_CHOICES = [
    "state",
    "county",
    "tract",
    "zcta",
    "block_group",
    "esri_zip",
    "block",
    "grid_non_urban",
    "grid_urban",
    "all_aggregated",
]

# Dataverse File ID Manifest across 3H7DNP (gridded) and F6PQAA (aggregated)
FILE_MANIFEST = {
    "gridded": {
        "docs": {
            "README-PM-components.pdf": {"id": "11094552", "name": "README-PM-components.pdf", "size": 455938},
            "example-code.zip": {"id": "11093420", "name": "example-code.zip", "size": 30508896},
        },
        "grids": {
            "ENC3-non-urban.csv": {"id": "11093516", "name": "ENC3-non-urban.csv", "size": 14608781},
            "ENC3-non-urban.gpkg.zip": {"id": "11093517", "name": "ENC3-non-urban.gpkg.zip", "size": 19172587},
            "ENC3-urban.csv": {"id": "11093515", "name": "ENC3-urban.csv", "size": 873669355},
            "ENC3-urban.gpkg.zip": {"id": "11094385", "name": "ENC3-urban.gpkg.zip", "size": 1059848135},
            "ESC6-non-urban.csv": {"id": "11093525", "name": "ESC6-non-urban.csv", "size": 11198545},
            "ESC6-non-urban.gpkg.zip": {"id": "11093526", "name": "ESC6-non-urban.gpkg.zip", "size": 14672488},
            "ESC6-urban.csv": {"id": "11094440", "name": "ESC6-urban.csv", "size": 458476527},
            "ESC6-urban.gpkg.zip": {"id": "11094441", "name": "ESC6-urban.gpkg.zip", "size": 560160059},
            "M8-non-urban.csv": {"id": "11093529", "name": "M8-non-urban.csv", "size": 60670094},
            "M8-non-urban.gpkg.zip": {"id": "11093530", "name": "M8-non-urban.gpkg.zip", "size": 78562462},
            "M8-urban.csv": {"id": "11094485", "name": "M8-urban.csv", "size": 409582850},
            "M8-urban.gpkg.zip": {"id": "11094486", "name": "M8-urban.gpkg.zip", "size": 477514837},
            "MA2-non-urban.csv": {"id": "11093424", "name": "MA2-non-urban.csv", "size": 5311625},
            "MA2-non-urban.gpkg.zip": {"id": "11093513", "name": "MA2-non-urban.gpkg.zip", "size": 7208910},
            "MA2-urban.csv": {"id": "11093423", "name": "MA2-urban.csv", "size": 623423499},
            "MA2-urban.gpkg.zip": {"id": "11093512", "name": "MA2-urban.gpkg.zip", "size": 762158838},
            "NE1-non-urban.csv": {"id": "11093422", "name": "NE1-non-urban.csv", "size": 4794074},
            "NE1-non-urban.gpkg.zip": {"id": "11093511", "name": "NE1-non-urban.gpkg.zip", "size": 6519553},
            "NE1-urban.csv": {"id": "11093421", "name": "NE1-urban.csv", "size": 309028636},
            "NE1-urban.gpkg.zip": {"id": "11093510", "name": "NE1-urban.gpkg.zip", "size": 384030152},
            "P9-non-urban.csv": {"id": "11093532", "name": "P9-non-urban.csv", "size": 21137521},
            "P9-non-urban.gpkg.zip": {"id": "11093533", "name": "P9-non-urban.gpkg.zip", "size": 27603586},
            "P9-urban.csv": {"id": "11094512", "name": "P9-urban.csv", "size": 605115226},
            "P9-urban.gpkg.zip": {"id": "11094513", "name": "P9-urban.gpkg.zip", "size": 710037083},
            "SA5-non-urban.csv": {"id": "11093523", "name": "SA5-non-urban.csv", "size": 15601095},
            "SA5-non-urban.gpkg.zip": {"id": "11093524", "name": "SA5-non-urban.gpkg.zip", "size": 20697881},
            "SA5-urban.csv": {"id": "11093522", "name": "SA5-urban.csv", "size": 1302093220},
            "SA5-urban.gpkg.zip": {"id": "11094422", "name": "SA5-urban.gpkg.zip", "size": 1576294463},
            "WNC4-non-urban.csv": {"id": "11093519", "name": "WNC4-non-urban.csv", "size": 34587266},
            "WNC4-non-urban.gpkg.zip": {"id": "11093520", "name": "WNC4-non-urban.gpkg.zip", "size": 44146860},
            "WNC4-urban.csv": {"id": "11093518", "name": "WNC4-urban.csv", "size": 389503490},
            "WNC4-urban.gpkg.zip": {"id": "11094406", "name": "WNC4-urban.gpkg.zip", "size": 448898666},
            "WSC7-non-urban.csv": {"id": "11093527", "name": "WSC7-non-urban.csv", "size": 28303928},
            "WSC7-non-urban.gpkg.zip": {"id": "11093528", "name": "WSC7-non-urban.gpkg.zip", "size": 36161818},
            "WSC7-urban.csv": {"id": "11094463", "name": "WSC7-urban.csv", "size": 705251397},
            "WSC7-urban.gpkg.zip": {"id": "11094464", "name": "WSC7-urban.gpkg.zip", "size": 420645385},
        },
        "non_urban_dat": {
            "ENC3": {"id": "11092673", "name": "ENC3.zip", "size": 471998091},
            "ESC6": {"id": "11092678", "name": "ESC6.zip", "size": 369685516},
            "MA2": {"id": "11092672", "name": "MA2.zip", "size": 178004700},
            "NE1": {"id": "11092671", "name": "NE1.zip", "size": 154151002},
            "P9": {"id": "11092682", "name": "P9.zip", "size": 662652093},
            "SA5": {"id": "11092677", "name": "SA5.zip", "size": 516934716},
            "WNC4": {"id": "11092675", "name": "WNC4.zip", "size": 1110680465},
            "WSC7": {"id": "11092680", "name": "WSC7.zip", "size": 945083179},
        },
        # Mountain (M8) non-urban predictions are split into two RDS archives on Dataverse
        "non_urban_rds_m8": {
            "major": {"id": "11081688", "name": "M8-major-components.zip", "size": 729470756},
            "trace": {"id": "11081703", "name": "M8-trace-elements.zip", "size": 1680385821},
        },
        "urban_dat": {
            "NE1": {
                "br": {"id": "11094350", "name": "br.zip", "size": 574207948},
                "ca": {"id": "11094351", "name": "ca.zip", "size": 736932796},
                "cu": {"id": "11094352", "name": "cu.zip", "size": 620136431},
                "ec": {"id": "11094345", "name": "ec.zip", "size": 512846343},
                "fe": {"id": "11094353", "name": "fe.zip", "size": 784264403},
                "k": {"id": "11094354", "name": "k.zip", "size": 755182308},
                "nh4": {"id": "11094346", "name": "nh4.zip", "size": 484010961},
                "ni": {"id": "11094355", "name": "ni.zip", "size": 527928300},
                "no3": {"id": "11094347", "name": "no3.zip", "size": 231740606},
                "oc": {"id": "11094348", "name": "oc.zip", "size": 557922574},
                "pb": {"id": "11094359", "name": "pb.zip", "size": 565739955},
                "si": {"id": "11094360", "name": "si.zip", "size": 702202633},
                "so4": {"id": "11094349", "name": "so4.zip", "size": 534134139},
                "v": {"id": "11094361", "name": "v.zip", "size": 568506383},
                "zn": {"id": "11094362", "name": "zn.zip", "size": 681158410},
            },
            "MA2": {
                "br": {"id": "11094374", "name": "br.zip", "size": 1176293923},
                "ca": {"id": "11094375", "name": "ca.zip", "size": 1507247541},
                "cu": {"id": "11094376", "name": "cu.zip", "size": 1269989273},
                "ec": {"id": "11094363", "name": "ec.zip", "size": 1070424417},
                "fe": {"id": "11094377", "name": "fe.zip", "size": 1613892623},
                "k": {"id": "11094378", "name": "k.zip", "size": 1522205259},
                "nh4": {"id": "11094364", "name": "nh4.zip", "size": 1033463671},
                "ni": {"id": "11094379", "name": "ni.zip", "size": 1069266697},
                "no3": {"id": "11094365", "name": "no3.zip", "size": 507300138},
                "oc": {"id": "11094366", "name": "oc.zip", "size": 1124376320},
                "pb": {"id": "11094380", "name": "pb.zip", "size": 1170181827},
                "si": {"id": "11094382", "name": "si.zip", "size": 1450793689},
                "so4": {"id": "11094367", "name": "so4.zip", "size": 1098054211},
                "v": {"id": "11094383", "name": "v.zip", "size": 1134129504},
                "zn": {"id": "11094384", "name": "zn.zip", "size": 1404168152},
            },
            "ENC3": {
                "br": {"id": "11094391", "name": "br.zip", "size": 1633948156},
                "ca": {"id": "11094392", "name": "ca.zip", "size": 2174958916},
                "cu": {"id": "11094396", "name": "cu.zip", "size": 1746061439},
                "ec": {"id": "11094386", "name": "ec.zip", "size": 1458989596},
                "fe": {"id": "11094397", "name": "fe.zip", "size": 2255179647},
                "k": {"id": "11094398", "name": "k.zip", "size": 2131046531},
                "nh4": {"id": "11094387", "name": "nh4.zip", "size": 1323323947},
                "ni": {"id": "11094399", "name": "ni.zip", "size": 1413041650},
                "no3": {"id": "11094388", "name": "no3.zip", "size": 592523643},
                "oc": {"id": "11094389", "name": "oc.zip", "size": 1536431875},
                "pb": {"id": "11094402", "name": "pb.zip", "size": 1607001149},
                "si": {"id": "11094403", "name": "si.zip", "size": 1993955164},
                "so4": {"id": "11094390", "name": "so4.zip", "size": 1507565263},
                "v": {"id": "11094404", "name": "v.zip", "size": 1463365650},
                "zn": {"id": "11094405", "name": "zn.zip", "size": 1956493470},
            },
            "WNC4": {
                "br": {"id": "11094412", "name": "br.zip", "size": 243319710},
                "ca": {"id": "11094413", "name": "ca.zip", "size": 343299912},
                "cu": {"id": "11094414", "name": "cu.zip", "size": 261473551},
                "ec": {"id": "11094407", "name": "ec.zip", "size": 222494015},
                "fe": {"id": "11094415", "name": "fe.zip", "size": 346772705},
                "k": {"id": "11094416", "name": "k.zip", "size": 333756834},
                "nh4": {"id": "11094408", "name": "nh4.zip", "size": 214562299},
                "ni": {"id": "11094417", "name": "ni.zip", "size": 214257592},
                "no3": {"id": "11094409", "name": "no3.zip", "size": 77558064},
                "oc": {"id": "11094410", "name": "oc.zip", "size": 238466307},
                "pb": {"id": "11094418", "name": "pb.zip", "size": 211677062},
                "si": {"id": "11094419", "name": "si.zip", "size": 269040444},
                "so4": {"id": "11094411", "name": "so4.zip", "size": 205704338},
                "v": {"id": "11094420", "name": "v.zip", "size": 198456967},
                "zn": {"id": "11094421", "name": "zn.zip", "size": 252951932},
            },
            "SA5": {
                "br": {"id": "11094428", "name": "br.zip", "size": 1655056541},
                "ca": {"id": "11094429", "name": "ca.zip", "size": 2161277527},
                "cu": {"id": "11094430", "name": "cu.zip", "size": 1810345010},
                "ec": {"id": "11094423", "name": "ec.zip", "size": 1512109014},
                "fe": {"id": "11094431", "name": "fe.zip", "size": 2287537324},
                "k": {"id": "11094432", "name": "k.zip", "size": 2029613759},
                "nh4": {"id": "11094424", "name": "nh4.zip", "size": 1316766509},
                "ni": {"id": "11094433", "name": "ni.zip", "size": 1376935547},
                "no3": {"id": "11094425", "name": "no3.zip", "size": 605002983},
                "oc": {"id": "11094426", "name": "oc.zip", "size": 1518140190},
                "pb": {"id": "11094434", "name": "pb.zip", "size": 1458944613},
                "si": {"id": "11094435", "name": "si.zip", "size": 1897193972},
                "so4": {"id": "11094427", "name": "so4.zip", "size": 1485718245},
                "v": {"id": "11094438", "name": "v.zip", "size": 1549180903},
                "zn": {"id": "11094439", "name": "zn.zip", "size": 1756123588},
            },
            "ESC6": {
                "br": {"id": "11094447", "name": "br.zip", "size": 826216731},
                "ca": {"id": "11094448", "name": "ca.zip", "size": 1111348778},
                "cu": {"id": "11094449", "name": "cu.zip", "size": 905789648},
                "ec": {"id": "11094442", "name": "ec.zip", "size": 749242262},
                "fe": {"id": "11094453", "name": "fe.zip", "size": 1160530925},
                "k": {"id": "11094454", "name": "k.zip", "size": 1121653372},
                "nh4": {"id": "11094443", "name": "nh4.zip", "size": 707785969},
                "ni": {"id": "11094455", "name": "ni.zip", "size": 716470056},
                "no3": {"id": "11094444", "name": "no3.zip", "size": 290124965},
                "oc": {"id": "11094445", "name": "oc.zip", "size": 812147986},
                "pb": {"id": "11094456", "name": "pb.zip", "size": 797718656},
                "si": {"id": "11094459", "name": "si.zip", "size": 1020972916},
                "so4": {"id": "11094446", "name": "so4.zip", "size": 773453920},
                "v": {"id": "11094460", "name": "v.zip", "size": 753829175},
                "zn": {"id": "11094462", "name": "zn.zip", "size": 968945597},
            },
            "WSC7": {
                "br": {"id": "11094471", "name": "br.zip", "size": 1267732814},
                "ca": {"id": "11094473", "name": "ca.zip", "size": 1804517443},
                "cu": {"id": "11094474", "name": "cu.zip", "size": 1408051313},
                "ec": {"id": "11094465", "name": "ec.zip", "size": 1141840965},
                "fe": {"id": "11094475", "name": "fe.zip", "size": 1808965698},
                "k": {"id": "11094477", "name": "k.zip", "size": 1720377525},
                "nh4": {"id": "11094466", "name": "nh4.zip", "size": 1079233130},
                "ni": {"id": "11094478", "name": "ni.zip", "size": 1113214218},
                "no3": {"id": "11094467", "name": "no3.zip", "size": 448563770},
                "oc": {"id": "11094469", "name": "oc.zip", "size": 1254026761},
                "pb": {"id": "11094480", "name": "pb.zip", "size": 1213693102},
                "si": {"id": "11094482", "name": "si.zip", "size": 1625518834},
                "so4": {"id": "11094470", "name": "so4.zip", "size": 1177452480},
                "v": {"id": "11094483", "name": "v.zip", "size": 1215257092},
                "zn": {"id": "11094484", "name": "zn.zip", "size": 1493976640},
            },
            "M8": {
                "br": {"id": "11094495", "name": "br.zip", "size": 693280965},
                "ca": {"id": "11094496", "name": "ca.zip", "size": 998925082},
                "cu": {"id": "11094497", "name": "cu.zip", "size": 765310187},
                "ec": {"id": "11094487", "name": "ec.zip", "size": 650808201},
                "fe": {"id": "11094498", "name": "fe.zip", "size": 1017826079},
                "k": {"id": "11094501", "name": "k.zip", "size": 987150217},
                "nh4": {"id": "11094488", "name": "nh4.zip", "size": 574820680},
                "ni": {"id": "11094502", "name": "ni.zip", "size": 578881444},
                "no3": {"id": "11094491", "name": "no3.zip", "size": 262506867},
                "oc": {"id": "11094492", "name": "oc.zip", "size": 718054269},
                "pb": {"id": "11094508", "name": "pb.zip", "size": 672808444},
                "si": {"id": "11094509", "name": "si.zip", "size": 888154590},
                "so4": {"id": "11094494", "name": "so4.zip", "size": 577284509},
                "v": {"id": "11094510", "name": "v.zip", "size": 648105339},
                "zn": {"id": "11094511", "name": "zn.zip", "size": 810021906},
            },
            "P9": {
                "br": {"id": "11094519", "name": "br.zip", "size": 1084696661},
                "ca": {"id": "11094520", "name": "ca.zip", "size": 1442766966},
                "cu": {"id": "11094521", "name": "cu.zip", "size": 1190025269},
                "ec": {"id": "11094514", "name": "ec.zip", "size": 1010614675},
                "fe": {"id": "11094522", "name": "fe.zip", "size": 1515020864},
                "k": {"id": "11094523", "name": "k.zip", "size": 1468846042},
                "nh4": {"id": "11094515", "name": "nh4.zip", "size": 915212186},
                "ni": {"id": "11094525", "name": "ni.zip", "size": 973078837},
                "no3": {"id": "11094516", "name": "no3.zip", "size": 440764721},
                "oc": {"id": "11094517", "name": "oc.zip", "size": 1124055362},
                "pb": {"id": "11094526", "name": "pb.zip", "size": 1047013089},
                "si": {"id": "11094528", "name": "si.zip", "size": 1349834065},
                "so4": {"id": "11094518", "name": "so4.zip", "size": 956578490},
                "v": {"id": "11094529", "name": "v.zip", "size": 1057144897},
                "zn": {"id": "11094530", "name": "zn.zip", "size": 1262846534},
            },
        },
    },
    "aggregated": {
        "docs": {
            "README-PM-components-aggregated.pdf": {
                "id": "11714342",
                "name": "README-PM-components-aggregated.pdf",
                "size": 512234,
            },
            "statistics-csv.zip": {
                "id": "11714144",
                "name": "statistics-csv.zip",
                "size": 135421525,
            },
        },
        "bundles": {
            "census_2000_2010": {
                "id": "11714330",
                "name": "block-groups-tracts-counties-states-zctas-2000-2010.zip",
                "size": 976148146,
            },
            "esri_zip": {
                "id": "11714332",
                "name": "esri-zip-codes-2000-to-2019.zip",
                "size": 858885748,
            },
        },
        "blocks_2000": {
            "br": {"id": "11714256", "name": "br.csv.zip", "size": 842220175},
            "ca": {"id": "11714299", "name": "ca.csv.zip", "size": 980602766},
            "cu": {"id": "11714301", "name": "cu.csv.zip", "size": 865885251},
            "ec": {"id": "11714303", "name": "ec.csv.zip", "size": 809272355},
            "fe": {"id": "11714361", "name": "fe.csv.zip", "size": 988579752},
            "k": {"id": "11714363", "name": "k.csv.zip", "size": 976317679},
            "nh4": {"id": "11714365", "name": "nh4.csv.zip", "size": 819148172},
            "ni": {"id": "11714367", "name": "ni.csv.zip", "size": 813918043},
            "no3": {"id": "11714369", "name": "no3.csv.zip", "size": 820770328},
            "oc": {"id": "11714371", "name": "oc.csv.zip", "size": 840327504},
            "pb": {"id": "11714373", "name": "pb.csv.zip", "size": 870635904},
            "si": {"id": "11714375", "name": "si.csv.zip", "size": 1017389141},
            "so4": {"id": "11714377", "name": "so4.csv.zip", "size": 835163991},
            "v": {"id": "11714379", "name": "v.csv.zip", "size": 829513039},
            "zn": {"id": "11714381", "name": "zn.csv.zip", "size": 897688731},
        },
        "blocks_2010": {
            "br": {"id": "11714257", "name": "br.csv.zip", "size": 1113319217},
            "ca": {"id": "11714300", "name": "ca.csv.zip", "size": 1291618789},
            "cu": {"id": "11714302", "name": "cu.csv.zip", "size": 1143807727},
            "ec": {"id": "11714305", "name": "ec.csv.zip", "size": 1073312527},
            "fe": {"id": "11714362", "name": "fe.csv.zip", "size": 1302181585},
            "k": {"id": "11714364", "name": "k.csv.zip", "size": 1285764373},
            "nh4": {"id": "11714366", "name": "nh4.csv.zip", "size": 1083893410},
            "ni": {"id": "11714368", "name": "ni.csv.zip", "size": 1078466758},
            "no3": {"id": "11714370", "name": "no3.csv.zip", "size": 1080856242},
            "oc": {"id": "11714372", "name": "oc.csv.zip", "size": 1110691744},
            "pb": {"id": "11714374", "name": "pb.csv.zip", "size": 1149496685},
            "si": {"id": "11714376", "name": "si.csv.zip", "size": 1338257875},
            "so4": {"id": "11714378", "name": "so4.csv.zip", "size": 1104657287},
            "v": {"id": "11714380", "name": "v.csv.zip", "size": 1097538837},
            "zn": {"id": "11714382", "name": "zn.csv.zip", "size": 1195005775},
        },
    },
}


def resolve_variables(var_arg: str):
    """Resolve package names, aliases, or comma-separated variable codes to canonical codes."""
    alias_map = {}
    for code, meta in PM25_COMPONENT_VARIABLES.items():
        alias_map[code] = code
        for alias in meta.get("aliases", []):
            alias_map[alias.lower()] = code

    tokens = [t.strip().lower() for t in var_arg.split(",") if t.strip()]
    resolved = []
    for tok in tokens:
        if tok in VARIABLE_PACKAGES:
            for v in VARIABLE_PACKAGES[tok]:
                if v not in resolved:
                    resolved.append(v)
        elif tok in alias_map:
            canon = alias_map[tok]
            if canon not in resolved:
                resolved.append(canon)
        else:
            raise ValueError(
                f"Unknown variable or package '{tok}'. Use --list-variables to see valid options."
            )
    return resolved


def resolve_regions(region_arg: str):
    """Resolve Census division codes ('all' or comma-separated list)."""
    tokens = [t.strip().upper() for t in region_arg.split(",") if t.strip()]
    if "ALL" in tokens:
        return list(CENSUS_REGIONS.keys())
    resolved = []
    for tok in tokens:
        if tok not in CENSUS_REGIONS:
            raise ValueError(
                f"Unknown Census division '{tok}'. Valid options: {', '.join(CENSUS_REGIONS.keys())} or all"
            )
        if tok not in resolved:
            resolved.append(tok)
    return resolved


def list_variables():
    """Print available PM2.5 component variables, packages, geographies, and regions."""
    print(f"\n{__module__} v{__version__}")
    print("=" * 78)
    print("\nAvailable PM2.5 Component Variables (2000-2019 Annual):")
    print("-" * 78)
    print(f"{'Code':<6} {'Name':<20} {'Formula':<10} {'Category':<8} {'Units':<8} {'Aliases'}")
    print("-" * 78)
    for code, meta in PM25_COMPONENT_VARIABLES.items():
        aliases = ", ".join(meta.get("aliases", []))
        print(
            f"{code:<6} {meta['name']:<20} {meta['formula']:<10} "
            f"{meta['category']:<8} {meta['units']:<8} {aliases}"
        )

    print("\nVariable Packages (--variables):")
    print("-" * 78)
    for pkg, members in VARIABLE_PACKAGES.items():
        print(f"  {pkg:<8} : {', '.join(members)}")

    print("\nSupported Geographies (--geography):")
    print("-" * 78)
    print("  Aggregated (doi:10.7910/DVN/F6PQAA):")
    print("    state, county, tract, zcta, block_group (bundled 931 MB archive)")
    print("    esri_zip                                (819 MB archive, 2000-2019)")
    print("    block                                   (per-component CSV archives)")
    print("    all_aggregated                          (census_2000_2010 + esri_zip bundles)")
    print("  Gridded (doi:10.7910/DVN/3H7DNP):")
    print("    grid_non_urban                          (1-km non-urban grid by Census division)")
    print("    grid_urban                              (50-m urban grid by Census division & component)")

    print("\nCensus Divisions for Gridded Data (--region):")
    print("-" * 78)
    for reg, info in CENSUS_REGIONS.items():
        print(f"  {reg:<6} : {info['name']:<20} ({info['states']})")
    print()


def download_file(file_id: str, output_path: Path, expected_size: int = 0):
    """Download a file from Harvard Dataverse using its File ID."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists() and output_path.stat().st_size > 0:
        logger.info(f"File {output_path} already exists. Skipping download.")
        return

    url = f"{DATAVERSE_BASE_URL}{file_id}"
    size_mb = (expected_size / (1024 * 1024)) if expected_size else 0
    size_str = f" (~{size_mb:.1f} MB)" if size_mb else ""
    logger.info(f"Downloading {output_path.name}{size_str} from Dataverse (ID: {file_id})...")

    try:
        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            total_size = int(r.headers.get("content-length", expected_size or 0))
            if tqdm is not None:
                with open(output_path, "wb") as f, tqdm(
                    desc=output_path.name,
                    total=total_size,
                    unit="iB",
                    unit_scale=True,
                    unit_divisor=1024,
                ) as pbar:
                    for chunk in r.iter_content(chunk_size=65536):
                        if chunk:
                            written = f.write(chunk)
                            pbar.update(written)
            else:
                with open(output_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)
        logger.info(f"Successfully downloaded {output_path}")
    except Exception as e:
        logger.error(f"Failed to download {output_path.name}: {e}")
        if output_path.exists():
            output_path.unlink()
        sys.exit(1)


def create_parser():
    parser = argparse.ArgumentParser(
        description=f"{__module__} Framework v{__version__} - Download Harvard Super-Learned PM2.5 Components",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all 15 PM2.5 component variables, packages, geographies, and regions
  python3 pm25_components_download_generic.py --list-variables

  # Download aggregated Census geography bundle (state, county, tract, zcta, block_group)
  python3 pm25_components_download_generic.py --geography county --output-dir ./data/raw/pm25_components_harvard/

  # Download 1-km non-urban grid for New England (NE1)
  python3 pm25_components_download_generic.py --geography grid_non_urban --region NE1 --output-dir ./data/raw/pm25_components_harvard/

  # Download 50-m urban grid for Elemental Carbon and Sulfate in New England (NE1)
  python3 pm25_components_download_generic.py --geography grid_urban --region NE1 --variables ec,so4 --output-dir ./data/raw/pm25_components_harvard/
        """,
    )

    parser.add_argument("--version", "-V", action="version", version=f"{__module__} v{__version__}")
    parser.add_argument(
        "--list-variables", "-l", action="store_true",
        help="List all available PM2.5 components, packages, geographies, and regions"
    )
    parser.add_argument(
        "--geography", "-g", choices=GEOGRAPHY_CHOICES, default="county",
        help="Target spatial resolution / geography (default: county)"
    )
    parser.add_argument(
        "--variables", "-v", default="all",
        help="Comma-separated component codes or package (major, trace, all; default: all)"
    )
    parser.add_argument(
        "--region", "-r", default="all",
        help="Census division(s) for grid_non_urban / grid_urban (NE1,MA2,ENC3,WNC4,SA5,ESC6,WSC7,M8,P9, or all; default: all)"
    )
    parser.add_argument(
        "--boundary-year", "-b", choices=["2000", "2010", "both"], default="2010",
        help="Census TIGER/Line boundary vintage for block downloads (default: 2010)"
    )
    parser.add_argument(
        "--output-dir", "-o", type=Path, default=Path("./data/raw/pm25_components_harvard"),
        help="Output directory for downloaded files"
    )
    parser.add_argument(
        "--include-gpkg", action="store_true",
        help="For gridded geographies, also download GeoPackage grid files (*.gpkg.zip)"
    )
    parser.add_argument(
        "--include-statistics", action="store_true",
        help="For aggregated geographies, also download polygon assignment statistics (statistics-csv.zip)"
    )
    parser.add_argument(
        "--include-docs", action="store_true",
        help="Also download dataset README PDFs"
    )

    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    if args.list_variables:
        list_variables()
        sys.exit(0)

    try:
        variables = resolve_variables(args.variables)
        regions = resolve_regions(args.region)
    except ValueError as err:
        logger.error(str(err))
        sys.exit(1)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    geo = args.geography

    logger.info(f"Starting {__module__} v{__version__}")
    logger.info(f"Geography: {geo}")
    logger.info(f"Selected Variables ({len(variables)}): {', '.join(variables)}")
    logger.info(f"Output Directory: {args.output_dir.resolve()}")

    if args.include_docs:
        for doc_key, doc_info in FILE_MANIFEST["gridded"]["docs"].items():
            if doc_key.endswith(".pdf"):
                download_file(doc_info["id"], args.output_dir / doc_info["name"], doc_info["size"])
        for doc_key, doc_info in FILE_MANIFEST["aggregated"]["docs"].items():
            if doc_key.endswith(".pdf"):
                download_file(doc_info["id"], args.output_dir / doc_info["name"], doc_info["size"])

    # 1. Standard Census geographies (state, county, tract, zcta, block_group)
    if geo in ("state", "county", "tract", "zcta", "block_group", "all_aggregated"):
        bundle = FILE_MANIFEST["aggregated"]["bundles"]["census_2000_2010"]
        download_file(
            bundle["id"],
            args.output_dir / "aggregates-csv" / bundle["name"],
            bundle["size"],
        )

    # 2. ESRI / TomTom ZIP codes
    if geo in ("esri_zip", "all_aggregated"):
        bundle = FILE_MANIFEST["aggregated"]["bundles"]["esri_zip"]
        download_file(
            bundle["id"],
            args.output_dir / "aggregates-csv" / bundle["name"],
            bundle["size"],
        )

    # 3. Census blocks (split by boundary vintage and component)
    if geo == "block":
        b_years = ["2000", "2010"] if args.boundary_year == "both" else [args.boundary_year]
        for byr in b_years:
            block_manifest = FILE_MANIFEST["aggregated"][f"blocks_{byr}"]
            for var in variables:
                finfo = block_manifest[var]
                download_file(
                    finfo["id"],
                    args.output_dir / "aggregates-csv" / f"blocks-{byr}" / finfo["name"],
                    finfo["size"],
                )

    if args.include_statistics and geo not in ("grid_non_urban", "grid_urban"):
        stat_info = FILE_MANIFEST["aggregated"]["docs"]["statistics-csv.zip"]
        download_file(
            stat_info["id"],
            args.output_dir / stat_info["name"],
            stat_info["size"],
        )

    # 4. Gridded 1-km non-urban
    if geo == "grid_non_urban":
        logger.info(f"Target Census Divisions: {', '.join(regions)}")
        for reg in regions:
            grid_csv = FILE_MANIFEST["gridded"]["grids"][f"{reg}-non-urban.csv"]
            download_file(
                grid_csv["id"],
                args.output_dir / "grids" / grid_csv["name"],
                grid_csv["size"],
            )
            if args.include_gpkg:
                grid_gpkg = FILE_MANIFEST["gridded"]["grids"][f"{reg}-non-urban.gpkg.zip"]
                download_file(
                    grid_gpkg["id"],
                    args.output_dir / "grids" / grid_gpkg["name"],
                    grid_gpkg["size"],
                )

            if reg in FILE_MANIFEST["gridded"]["non_urban_dat"]:
                dat_info = FILE_MANIFEST["gridded"]["non_urban_dat"][reg]
                download_file(
                    dat_info["id"],
                    args.output_dir / "non-urban-dat" / dat_info["name"],
                    dat_info["size"],
                )
            elif reg == "M8":
                # M8 non-urban is provided as split RDS archives on Dataverse
                need_major = any(PM25_COMPONENT_VARIABLES[v]["category"] == "major" for v in variables)
                need_trace = any(PM25_COMPONENT_VARIABLES[v]["category"] == "trace" for v in variables)
                if need_major:
                    m_info = FILE_MANIFEST["gridded"]["non_urban_rds_m8"]["major"]
                    download_file(
                        m_info["id"],
                        args.output_dir / "non-urban-rds" / m_info["name"],
                        m_info["size"],
                    )
                if need_trace:
                    t_info = FILE_MANIFEST["gridded"]["non_urban_rds_m8"]["trace"]
                    download_file(
                        t_info["id"],
                        args.output_dir / "non-urban-rds" / t_info["name"],
                        t_info["size"],
                    )

    # 5. Gridded 50-m urban
    if geo == "grid_urban":
        logger.info(f"Target Census Divisions: {', '.join(regions)}")
        for reg in regions:
            grid_csv = FILE_MANIFEST["gridded"]["grids"][f"{reg}-urban.csv"]
            download_file(
                grid_csv["id"],
                args.output_dir / "grids" / grid_csv["name"],
                grid_csv["size"],
            )
            if args.include_gpkg:
                grid_gpkg = FILE_MANIFEST["gridded"]["grids"][f"{reg}-urban.gpkg.zip"]
                download_file(
                    grid_gpkg["id"],
                    args.output_dir / "grids" / grid_gpkg["name"],
                    grid_gpkg["size"],
                )

            for var in variables:
                u_info = FILE_MANIFEST["gridded"]["urban_dat"][reg][var]
                download_file(
                    u_info["id"],
                    args.output_dir / "urban-dat" / reg / u_info["name"],
                    u_info["size"],
                )

    logger.info("All requested downloads completed successfully.")


if __name__ == "__main__":
    main()

