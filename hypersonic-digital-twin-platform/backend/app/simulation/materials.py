MATERIALS = {
    "c_phenolic": {
        "name": "Carbon Phenolic",
        "max_temp_k": 2200,
        "conductivity_w_mk": 0.7,
        "density_kg_m3": 1450,
        "sustainability": 0.55,
    },
    "reinforced_carbon_carbon": {
        "name": "Reinforced Carbon-Carbon",
        "max_temp_k": 2700,
        "conductivity_w_mk": 4.5,
        "density_kg_m3": 1800,
        "sustainability": 0.62,
    },
    "ultra_high_temp_ceramic": {
        "name": "UHTC ZrB2-SiC",
        "max_temp_k": 3200,
        "conductivity_w_mk": 18.0,
        "density_kg_m3": 5600,
        "sustainability": 0.48,
    },
    "bio_ceramic_composite": {
        "name": "Bio-derived Ceramic Composite",
        "max_temp_k": 1900,
        "conductivity_w_mk": 1.4,
        "density_kg_m3": 1320,
        "sustainability": 0.86,
    },
}


def get_material(material_id: str) -> dict:
    return MATERIALS.get(material_id, MATERIALS["c_phenolic"])

