import pandas as pd
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils import input, aggregation_tree


# LIFE MORTALITY RISK
def calculate_life_mortality_risk(data_id_enriched: pd.DataFrame) -> pd.DataFrame:
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
def calculate_life_longevity_risk(data_id_enriched: pd.DataFrame) -> pd.DataFrame:
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
def calculate_life_disability_risk(data_id_enriched: pd.DataFrame) -> pd.DataFrame:
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
def calculate_life_lapse_risk(data_id_enriched: pd.DataFrame) -> pd.DataFrame:
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
def calculate_life_expense_risk(data_id_enriched: pd.DataFrame) -> pd.DataFrame:
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
def calculate_life_revision_risk(data_id_enriched: pd.DataFrame) -> pd.DataFrame:
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
def calculate_life_catastrophe_risk(data_id_enriched: pd.DataFrame) -> pd.DataFrame:
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
def calculate_total_life_risk(data_id_enriched: pd.DataFrame) -> pd.DataFrame:
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


def diversification_life_risk(aggregation_tree_enriched: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate diversification effects for life risk.
    
    Args:
        aggregation_tree_enriched: DataFrame containing all life risk components
    
    Returns:
        pd.DataFrame: DataFrame with diversification values
    """
    # List of data IDs - SCRs necessary to calculate diversifications
    data_id = ['LIFE_MOR_SCR_N', 'LIFE_LON_SCR_N', 'LIFE_DIS_SCR_N','LIFE_LAP_SCR_N', 
               'LIFE_EXP_SCR_N', 'LIFE_REV_SCR_N', 'LIFE_CAT_SCR_N', 'LIFE_SCR_N',
                'LIFE_MOR_SCR_G', 'LIFE_LON_SCR_G', 'LIFE_DIS_SCR_G','LIFE_LAP_SCR_G',
                'LIFE_EXP_SCR_G', 'LIFE_REV_SCR_G', 'LIFE_CAT_SCR_G', 'LIFE_SCR_G']
    
    # Make dictionary {DATA_ID: VALUE} with data necessary for calculation
    values_series = pd.to_numeric(aggregation_tree_enriched.set_index('NODE_ID').loc[data_id, 'VALUE'], errors='coerce').dropna()
    values_dict = values_series.to_dict()

    # Calculate value of diversification for LIFE nett and gross as a difference of total SCR and sum of all subrisks SCRs
    values_dict['LIFE_DIV_N'] = values_dict.get('LIFE_SCR_N', 0) - (values_dict.get('LIFE_MOR_SCR_N', 0) + values_dict.get('LIFE_LON_SCR_N', 0) +
                                                              values_dict.get('LIFE_DIS_SCR_N', 0) + values_dict.get('LIFE_LAP_SCR_N', 0) + 
                                                              values_dict.get('LIFE_EXP_SCR_N', 0) + values_dict.get('LIFE_REV_SCR_N', 0) + values_dict.get('LIFE_CAT_SCR_N', 0))
    values_dict['LIFE_DIV_G'] = values_dict.get('LIFE_SCR_G', 0) - (values_dict.get('LIFE_MOR_SCR_G', 0) + values_dict.get('LIFE_LON_SCR_G', 0) +
                                                              values_dict.get('LIFE_DIS_SCR_G', 0) + values_dict.get('LIFE_LAP_SCR_G', 0) + 
                                                              values_dict.get('LIFE_EXP_SCR_G', 0) + values_dict.get('LIFE_REV_SCR_G', 0) + values_dict.get('LIFE_CAT_SCR_G', 0))    
    
    diversification_life_df = pd.DataFrame({
        'AGGREGATION_TREE_ID': 'LIFE',
        'NODE_ID': ['LIFE_DIV_N', 'LIFE_DIV_G'],
        'PARENT_NODE_ID': '',
        'NODE_DESC': '',
        'AGGREGATION_METHOD': '',
        'MATRIX_ID': '',
        'MAX_SCENARIO_BASE': '',
        'BS_TYPE': '',
        'SCENARIO': '',
        'VALUE': [ values_dict['LIFE_DIV_N'], values_dict['LIFE_DIV_G'] ],
    })

    return diversification_life_df


def calculate_life_risk_all_subrisks(input_file: str) -> pd.DataFrame:
    """
    Calculate life risk by aggregating various life risk components.
    
    Args:
        input_file (str): Path to the input file containing life risk data.
    
    Returns:
        pd.DataFrame: Aggregated life risk results
    """
    # Load input data
    data_id_enriched_life = input.run_Import(input_file,['LnH SLT UW'])
    
    # Calculate individual life subrisks
    aggregation_tree_life_mor_enriched = calculate_life_mortality_risk(data_id_enriched_life)
    aggregation_tree_life_lon_enriched = calculate_life_longevity_risk(data_id_enriched_life)
    aggregation_tree_life_dis_enriched = calculate_life_disability_risk(data_id_enriched_life)
    aggregation_tree_life_lap_enriched = calculate_life_lapse_risk(data_id_enriched_life)
    aggregation_tree_life_exp_enriched = calculate_life_expense_risk(data_id_enriched_life)
    aggregation_tree_life_rev_enriched = calculate_life_revision_risk(data_id_enriched_life)
    aggregation_tree_life_cat_enriched = calculate_life_catastrophe_risk(data_id_enriched_life)
    
    # Combine all life risk components into a single DataFrame
    aggregation_tree_life_all_risks = pd.concat([aggregation_tree_life_mor_enriched,
                                            aggregation_tree_life_lon_enriched,
                                            aggregation_tree_life_dis_enriched,
                                            aggregation_tree_life_lap_enriched,
                                            aggregation_tree_life_exp_enriched,
                                            aggregation_tree_life_rev_enriched,
                                            aggregation_tree_life_cat_enriched], ignore_index=True)
    
    # Calculate diversification effects for life risk
    diversification_life_df = diversification_life_risk(aggregation_tree_life_all_risks)    
    # Append diversification risk to the aggregated DataFrame
    aggregation_tree_life_all_risks = pd.concat([aggregation_tree_life_all_risks, diversification_life_df], ignore_index=True)  
            
    return aggregation_tree_life_all_risks