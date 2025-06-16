from utils import aggregation_tree


# HSLT MORTALITY RISK
def calculate_hslt_mortality_risk(data_id_enriched):
    """
    Calculate hslt mortality risk.
    
    Args:
        data_id_enriched: data frame containing enriched input data
    """
    # Read aggregation tree for hslt risk
    aggregation_tree_hslt_mor = aggregation_tree.read_aggregation_tree("HSLT_MOR")
    
    # Aggregate the tree with the enriched data
    aggregation_tree_hslt_mor_enriched = aggregation_tree.aggregate_tree(aggregation_tree_hslt_mor, data_id_enriched, "HSLT_MOR")
    
    return aggregation_tree_hslt_mor_enriched

# HSLT LONGEVITY RISK
def calculate_hslt_longevity_risk(data_id_enriched):
    """
    Calculate hslt mortality risk.
    
    Args:
        data_id_enriched: data frame containing enriched input data
    """
    # Read aggregation tree for hslt risk
    aggregation_tree_hslt_lon = aggregation_tree.read_aggregation_tree("HSLT_LON")
    
    # Aggregate the tree with the enriched data
    aggregation_tree_hslt_lon_enriched = aggregation_tree.aggregate_tree(aggregation_tree_hslt_lon, data_id_enriched, "HSLT_LON")
    
    return aggregation_tree_hslt_lon_enriched

# HSLT DISABILITY-MORBIDITY RISK
def calculate_hslt_disability_risk(data_id_enriched):
    """
    Calculate hslt disability risk.
    
    Args:
        data_id_enriched: data frame containing enriched input data
    """
    # Read aggregation tree for hslt risk
    aggregation_tree_hslt_dis = aggregation_tree.read_aggregation_tree("HSLT_DIS")
    
    # Aggregate the tree with the enriched data
    aggregation_tree_hslt_dis_enriched = aggregation_tree.aggregate_tree(aggregation_tree_hslt_dis, data_id_enriched, "HSLT_DIS")
    
    return aggregation_tree_hslt_dis_enriched

# hslt LAPSE RISK
def calculate_hslt_lapse_risk(data_id_enriched):
    """
    Calculate hslt lapse risk.
    
    Args:
        data_id_enriched: data frame containing enriched input data
    """
    # Read aggregation tree for hslt risk
    aggregation_tree_hslt_lap = aggregation_tree.read_aggregation_tree("HSLT_LAP")
    
    # Aggregate the tree with the enriched data
    aggregation_tree_hslt_lap_enriched = aggregation_tree.aggregate_tree(aggregation_tree_hslt_lap, data_id_enriched, "HSLT_LAP")
    
    return aggregation_tree_hslt_lap_enriched

# HSLT EXPENSE RISK
def calculate_hslt_expense_risk(data_id_enriched):
    """
    Calculate hslt expense risk.
    
    Args:
        data_id_enriched: data frame containing enriched input data
    """
    # Read aggregation tree for hslt risk
    aggregation_tree_hslt_exp = aggregation_tree.read_aggregation_tree("HSLT_EXP")
    
    # Aggregate the tree with the enriched data
    aggregation_tree_hslt_exp_enriched = aggregation_tree.aggregate_tree(aggregation_tree_hslt_exp, data_id_enriched, "HSLT_EXP")
    
    return aggregation_tree_hslt_exp_enriched

# HSLT REVISION RISK
def calculate_hslt_revision_risk(data_id_enriched):
    """
    Calculate hslt mrevision risk.
    
    Args:
        data_id_enriched: data frame containing enriched input data
    """
    # Read aggregation tree for hslt risk
    aggregation_tree_hslt_rev = aggregation_tree.read_aggregation_tree("HSLT_REV")
    
    # Aggregate the tree with the enriched data
    aggregation_tree_hslt_rev_enriched = aggregation_tree.aggregate_tree(aggregation_tree_hslt_rev, data_id_enriched, "HSLT_REV")
    
    return aggregation_tree_hslt_rev_enriched


#TOTAL HSLT RISK
def calculate_total_hslt_risk(data_id_enriched):
    """
    Calculate hslt risk.
    
    Args:
        data_id_enriched: data frame containing enriched input data
    """
    # Read aggregation tree for hslt risk
    aggregation_tree_hslt = aggregation_tree.read_aggregation_tree("HSLT")
    
    # Aggregate the tree with the enriched data
    aggregation_tree_hslt_enriched = aggregation_tree.aggregate_tree(aggregation_tree_hslt, data_id_enriched, "HSLT")
    
    return aggregation_tree_hslt_enriched