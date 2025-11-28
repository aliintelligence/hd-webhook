"""
Configuration file for Payroll Automation
Contains rep spreadsheet mappings and other constants
"""

# Rep name to Google Sheets ID mapping
REP_SPREADSHEETS = {
    "Adriana Botero": "1GgvsurqFuWznOg6krNUsdq_xLU1i20Nw1YxYXW-L2eM",
    "Alessandro Crisci": "11GdZlsJHtU4ciojvyu5yb4HXHCVBbVKykfarZHXRUe8",
    "Bryan Gonzalez": "1oHBoUnl3QSfBTbeCVhho6J14_EW2Lcu8odsgVAdgLm0",
    "David Rodriguez": "137vrFifCXbRc110Ja9voGhubcXUr1wuyAtMlwxslmYc",
    "Daniel Chuecos": "1ePBzg1TsGhTrQPSCWL7ypPHwkhUalNSZMm6pP56D9JM",
    "Edgar Lantigua": "1ygDT3lqm3hkqP6XSbnjRfHbcghwDMAT2QS_pCoGueKE",
    "Ennio Zucchino": "1QoxODjlHnDkO1vZceIDEpf4rUtTay1yUeP7U5jCWoYc",
    "Fernando Falco": "1ZGX5a2sN07kMqxXiP3r7cOJeihZMSqszcmKdzwIPeds",
    "Facundo Alvarez Nunez": "1-_TGJ7A4K3PvgebGdSg-IhGigmzn2FGRwH8xAedy-lo",
    "Estefania Nieto": "1W_VXo7HMTjtuqcrc_2g9wlZAjBcCta1okQerpxnIOKo",
    "Henry Velasco": "1gAllhtSkXAGEBWO7Wd04HODKB0Utaxa4jlOuxQ741E8",
    "Hamelet Louis": "15VPcPibdzFR8wZZpvgpyCxEF7Omt29Ls-U2zmVYYSz0",
    "Lisandra": "1g9fgVJYG5Qvu8GVkjWk13uz5NAss8XMKk3NI-rmMagY",
    "Marisol Medina": "1tevjmx8xg2eWFAlf-YVITS_NltkkBM4dnIay3yEfJ-4",
    "Rachel Miranda": "13tI2cIvw0HU2mcxb043ykHt4lBSLBj4mTZItEjqW9gE",
    "Rocny Rodriguez": "14Fef-8zquOc8aejaqStS6G1nuC6DyjBn_LPsrDxO3GU",
    "Romel Duran": "1rRa1ouur7HeFbP0gUKTLfjOto7MAE23tiM_W_W_huuE",
    "Shayne Luque": "1KoYYBMBnzjNPoS2otRKTq8-IBQ2voBrCh0af_3gqWKs",
    "Ulises Delgado": "1IZFujAIEh9fU3xd5CINJXA3RyKa_qPL_2z7gXzE63eY",
    "Yoan Bonet": "1To97mQqQ1Nc-1dQs3ZDie81Fk4d0TY7i4ODzONoONz8",
}

# Spreadsheet column headers for individual rep sheets
REP_SHEET_HEADERS = [
    "Date",
    "Customer Name",
    "Phone Number",
    "Customer Address",
    "Equipment",
    "Sold Price",
    "Installed",
    "Fin By",
    "Fin Status",
    "Comments",
    "Commission",
    "Date",
    "Contract"
]

# Main spreadsheet headers
MAIN_SHEET_HEADERS = [
    "Date",
    "Sales Rep",
    "Customer Name",
    "Equipment",
    "Sale Price",
    "Equipment Cost",
    "Marketing Fee (10%)",
    "Profit",
    "Lead/PO#",
    "Contract Link"
]

# Backup spreadsheet headers (same as rep sheets)
BACKUP_SHEET_HEADERS = REP_SHEET_HEADERS + ["Sales Rep Name"]

# Equipment costs for profit calculation
EQUIPMENT_COSTS = {
    "EC5": 927.21,
    "TCM": 721.55,
    "BCM": 721.55,
    "QRS": 275.95,
    "AM": 358.89,
    "CS": 472.36,
    "UV": 505.00,
    "ALK": 125.83,
    "HYD": 235.00,
    "OXY": 2066.40,
    "RO": 412.26,
    "PFAS": 190.74,
    "Cage": 500.00,
    "Base": 100.00,
    "Cooler": 348.00,
    "Portable Air": 520.00,
    "Pump": 1200.00,
    "Pressure Tank": 500.00,
    "RO Pump": 250.00,
    "Landscaping": 0.00,
    "Soap": 0.00
}

# Equipment name mapping (for parsing variations)
EQUIPMENT_MAPPING = {
    "EC5": ["EC5", "ECS", "E.C.5", "System 5", "ES5", "ES-5"],
    "TCM": ["TC", "TCM", "T.C.", "TC Series", "TC Conditioner"],
    "BCM": ["BCM", "BCM Series", "BCM Conditioner"],
    "HYD": ["Hydro", "HYD", "Hydro System", "Hydro Refiner"],
    "QRS": ["QRS", "Q.R.S", "Quad", "Carbon Filter"],
    "AM": ["AM", "Airmaster", "Air Purifier"],
    "CS": ["CS", "Clean Start", "Laundry System"],
    "UV": ["UV Light", "Ultraviolet", "Lamp", "UV"],
    "ALK": ["Alkaline", "Alka", "Alk", "Filtro Alcalino", "ALK"],
    "OXY": ["OXY", "Oxygen", "Iron Filter", "Oxy System"],
    "RO": ["Reverse Osmosis", "Osmosis", "R.O.", "RO"],
    "PFAS": ["PFAS", "PFOS", "Forever Chemical Filter"],
    "Cage": ["Cage", "Security Cage", "Reja", "CAGE"],
    "Base": ["Stand", "Base", "BASE"],
    "Cooler": ["Cooler", "Water Cooler", "Dispenser"],
    "Portable Air": ["Portable", "Air Filter", "Filtro Portatil"],
    "Pump": ["Well Pump", "Pump", "Bomba", "Jet Pump"],
    "Pressure Tank": ["Pressure Tank", "Tank", "Tanque"],
    "RO Pump": ["RO Pump", "Booster Pump", "Permeate Pump"],
    "Landscaping": ["Landscape", "Install", "Landscaping"],
    "Soap": ["Soap", "Jabon", "Soap Package"]
}

MARKETING_FEE_PERCENT = 0.10
