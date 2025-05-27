from utils import aggregation_tree

#MARKET_INT
def calculate_interest_rate_risk(data_id_enriched):
    """
    Calculate interest rate risk.
    
    Args:
        data_id_enriched: data frame containing enriched input data
    """
    # Read aggregation tree for interest rate risk
    aggregation_tree_market_ir = aggregation_tree.read_aggregation_tree("MARKET_INT")
    
    # Aggregate the tree with the enriched data
    aggregation_tree_market_ir_enriched = aggregation_tree.aggregate_tree(aggregation_tree_market_ir, data_id_enriched, "MARKET_INT")
    
    return aggregation_tree_market_ir_enriched

#MARKET_EQU
def calculate_equity_risk(data_id_enriched):
    """
    Calculate equity risk.
    
    Args:
        data_id_enriched: data frame containing enriched input data
    """
    # Read aggregation tree for equity risk
    aggregation_tree_market_eq = aggregation_tree.read_aggregation_tree("MARKET_EQU")
    
    # Aggregate the tree with the enriched data
    aggregation_tree_market_eq_enriched = aggregation_tree.aggregate_tree(aggregation_tree_market_eq, data_id_enriched, "MARKET_EQU")
    
    return aggregation_tree_market_eq_enriched


#MARKET_PRO
def calculate_property_risk(data_id_enriched):
    """
    Calculate property risk.
    
    Args:
        data_id_enriched: data frame containing enriched input data
    """
    # Read aggregation tree for property risk
    aggregation_tree_market_pro = aggregation_tree.read_aggregation_tree("MARKET_PRO")
    
    # Aggregate the tree with the enriched data
    aggregation_tree_market_pro_enriched = aggregation_tree.aggregate_tree(aggregation_tree_market_pro, data_id_enriched, "MARKET_PRO")
    
    return aggregation_tree_market_pro_enriched

#MARKET_SPR
def calculate_spread_risk(data_id_enriched):
    """
    Calculate spread risk.
    
    Args:
        data_id_enriched: data frame containing enriched input data
    """
    # Read aggregation tree for spread risk
    aggregation_tree_market_spr = aggregation_tree.read_aggregation_tree("MARKET_SPR")
    
    # Aggregate the tree with the enriched data
    aggregation_tree_market_spr_enriched = aggregation_tree.aggregate_tree(aggregation_tree_market_spr, data_id_enriched, "MARKET_SPR")
    
    return aggregation_tree_market_spr_enriched
    #TODO: #6 Update spread results based on input



#MARKET - Total Market risk
def calculate_total_market_risk(data_id_enriched):
    """
    Calculate total market risk.
    
    Args:
        data_id_enriched: data frame containing enriched input data
    """
    # Read aggregation tree for total market risk
    aggregation_tree_market = aggregation_tree.read_aggregation_tree("MARKET")
    
    # Aggregate the tree with the enriched data
    aggregation_tree_market_enriched = aggregation_tree.aggregate_tree(aggregation_tree_market, data_id_enriched, "MARKET")
    return aggregation_tree_market_enriched



