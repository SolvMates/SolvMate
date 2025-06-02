from utils import aggregation_tree


# LIFE MORTALITY RISK
def calculate_life_mortality_risk(data_id_enriched):
    """
    Calculate life mortality risk.
    
    Args:
        data_id_enriched: data frame containing enriched input data
    """
    # Read aggregation tree for life risk
    aggregation_tree_life_mor = aggregation_tree.read_aggregation_tree("LIFE_MOR")
    
    # Aggregate the tree with the enriched data
    aggregation_tree_life_mor_enriched = aggregation_tree.aggregate_tree(aggregation_tree_life_mor, data_id_enriched, "LIFE_MOR")
    
    return aggregation_tree_life_mor_enriched

# LIFE LONGEVITY RISK
def calculate_life_longevity_risk(data_id_enriched):
    """
    Calculate life mortality risk.
    
    Args:
        data_id_enriched: data frame containing enriched input data
    """
    # Read aggregation tree for life risk
    aggregation_tree_life_lon = aggregation_tree.read_aggregation_tree("LIFE_LON")
    
    # Aggregate the tree with the enriched data
    aggregation_tree_life_lon_enriched = aggregation_tree.aggregate_tree(aggregation_tree_life_lon, data_id_enriched, "LIFE_LON")
    
    return aggregation_tree_life_lon_enriched

# LIFE DISABILITY-MORBIDITY RISK
def calculate_life_disability_risk(data_id_enriched):
    """
    Calculate life disability risk.
    
    Args:
        data_id_enriched: data frame containing enriched input data
    """
    # Read aggregation tree for life risk
    aggregation_tree_life_dis = aggregation_tree.read_aggregation_tree("LIFE_DIS")
    
    # Aggregate the tree with the enriched data
    aggregation_tree_life_dis_enriched = aggregation_tree.aggregate_tree(aggregation_tree_life_dis, data_id_enriched, "LIFE_DIS")
    
    return aggregation_tree_life_dis_enriched

# LIFE LAPSE RISK
def calculate_life_lapse_risk(data_id_enriched):
    """
    Calculate life lapse risk.
    
    Args:
        data_id_enriched: data frame containing enriched input data
    """
    # Read aggregation tree for life risk
    aggregation_tree_life_lap = aggregation_tree.read_aggregation_tree("LIFE_LAP")
    
    # Aggregate the tree with the enriched data
    aggregation_tree_life_lap_enriched = aggregation_tree.aggregate_tree(aggregation_tree_life_lap, data_id_enriched, "LIFE_LAP")
    
    return aggregation_tree_life_lap_enriched

# LIFE EXPENSE RISK
def calculate_life_expense_risk(data_id_enriched):
    """
    Calculate life expense risk.
    
    Args:
        data_id_enriched: data frame containing enriched input data
    """
    # Read aggregation tree for life risk
    aggregation_tree_life_exp = aggregation_tree.read_aggregation_tree("LIFE_EXP")
    
    # Aggregate the tree with the enriched data
    aggregation_tree_life_exp_enriched = aggregation_tree.aggregate_tree(aggregation_tree_life_exp, data_id_enriched, "LIFE_EXP")
    
    return aggregation_tree_life_exp_enriched

# LIFE REVISION RISK
def calculate_life_revision_risk(data_id_enriched):
    """
    Calculate life mrevision risk.
    
    Args:
        data_id_enriched: data frame containing enriched input data
    """
    # Read aggregation tree for life risk
    aggregation_tree_life_rev = aggregation_tree.read_aggregation_tree("LIFE_REV")
    
    # Aggregate the tree with the enriched data
    aggregation_tree_life_rev_enriched = aggregation_tree.aggregate_tree(aggregation_tree_life_rev, data_id_enriched, "LIFE_REV")
    
    return aggregation_tree_life_rev_enriched

# LIFE CATASTROPHE RISK
def calculate_life_catastrophe_risk(data_id_enriched):
    """
    Calculate life catastrophe risk.
    
    Args:
        data_id_enriched: data frame containing enriched input data
    """
    # Read aggregation tree for life risk
    aggregation_tree_life_cat = aggregation_tree.read_aggregation_tree("LIFE_CAT")
    
    # Aggregate the tree with the enriched data
    aggregation_tree_life_cat_enriched = aggregation_tree.aggregate_tree(aggregation_tree_life_cat, data_id_enriched, "LIFE_CAT")
    
    return aggregation_tree_life_cat_enriched

#TOTAL LIFE RISK
def calculate_total_life_risk(data_id_enriched):
    """
    Calculate life risk.
    
    Args:
        data_id_enriched: data frame containing enriched input data
    """
    # Read aggregation tree for life risk
    aggregation_tree_life = aggregation_tree.read_aggregation_tree("LIFE")
    
    # Aggregate the tree with the enriched data
    aggregation_tree_life_enriched = aggregation_tree.aggregate_tree(aggregation_tree_life, data_id_enriched, "LIFE")
    
    return aggregation_tree_life_enriched