import pandas as pd
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils import input, aggregation_tree

#MARKET_INT
def calculate_interest_rate_risk(data_id_enriched: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate interest rate risk.
    
    Args:
        data_id_enriched: data frame containing enriched input data
    """
    # Read aggregation tree for interest rate risk
    aggregation_tree_market_ir = aggregation_tree.read_aggregation_tree("MARKET_INT")
    
    # Aggregate the tree with the enriched data
    aggregation_tree_market_ir_enriched = aggregation_tree.aggregate_tree(aggregation_tree_market_ir, data_id_enriched, "MARKET_INT")
    
    # For the output liabilities subordinated loans are added to liabilities w/o sub loans

    sub_loan_value = data_id_enriched.loc[data_id_enriched['DATA_ID'] == 'MKT_INT_SUB_LOAN_L_BC', 'VALUE'].sum()
    mask = aggregation_tree_market_ir_enriched['NODE_ID'] == 'MKT_INT_L_BC'
    aggregation_tree_market_ir_enriched.loc[mask, 'VALUE'] = (
        pd.to_numeric(aggregation_tree_market_ir_enriched.loc[mask, 'VALUE'], errors='coerce').fillna(0) + sub_loan_value
    )

    sub_loan_dn_value = data_id_enriched.loc[data_id_enriched['DATA_ID'] == 'MKT_INT_SUB_LOAN_DN_L_SH_N', 'VALUE'].sum()
    mask_dn_n = aggregation_tree_market_ir_enriched['NODE_ID'] == 'MKT_INT_DN_L_SH_N'
    aggregation_tree_market_ir_enriched.loc[mask_dn_n, 'VALUE'] = (
        pd.to_numeric(aggregation_tree_market_ir_enriched.loc[mask_dn_n, 'VALUE'], errors='coerce').fillna(0) + sub_loan_dn_value
    )
    mask_dn_g = aggregation_tree_market_ir_enriched['NODE_ID'] == 'MKT_INT_DN_L_SH_G'
    aggregation_tree_market_ir_enriched.loc[mask_dn_g, 'VALUE'] = (
        pd.to_numeric(aggregation_tree_market_ir_enriched.loc[mask_dn_g, 'VALUE'], errors='coerce').fillna(0) + sub_loan_dn_value
    )

    sub_loan_up_value = data_id_enriched.loc[data_id_enriched['DATA_ID'] == 'MKT_INT_SUB_LOAN_UP_L_SH_N', 'VALUE'].sum()
    mask_up_n = aggregation_tree_market_ir_enriched['NODE_ID'] == 'MKT_INT_UP_L_SH_N'
    aggregation_tree_market_ir_enriched.loc[mask_up_n, 'VALUE'] = (
        pd.to_numeric(aggregation_tree_market_ir_enriched.loc[mask_up_n, 'VALUE'], errors='coerce').fillna(0) + sub_loan_up_value
    )
    mask_up_g = aggregation_tree_market_ir_enriched['NODE_ID'] == 'MKT_INT_UP_L_SH_G'
    aggregation_tree_market_ir_enriched.loc[mask_up_g, 'VALUE'] = (
        pd.to_numeric(aggregation_tree_market_ir_enriched.loc[mask_up_g, 'VALUE'], errors='coerce').fillna(0) + sub_loan_up_value
    )

    return aggregation_tree_market_ir_enriched

#MARKET_EQU
def calculate_equity_risk(data_id_enriched: pd.DataFrame) -> pd.DataFrame:
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
def calculate_property_risk(data_id_enriched: pd.DataFrame) -> pd.DataFrame:
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
def calculate_spread_risk(data_id_enriched: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate spread risk.
    
    Args:
        data_id_enriched: data frame containing enriched input data
    """
    # Read aggregation tree for spread risk
    aggregation_tree_market_spr = aggregation_tree.read_aggregation_tree("MARKET_SPR")
    
    # Aggregate the tree with the enriched data
    aggregation_tree_market_spr_enriched = aggregation_tree.aggregate_tree(aggregation_tree_market_spr, data_id_enriched, "MARKET_SPR")

    # Update specific scr values
    scr_to_update = ['MKT_SPR_BD_QI_CORP_SCR_N', 'MKT_SPR_BD_QI_CORP_SCR_G', 'MKT_SPR_BD_QI_NONCORP_SCR_N', 'MKT_SPR_BD_QI_NONCORP_SCR_G',
                    'MKT_SPR_BD_OT_SCR_N', 'MKT_SPR_BD_OT_SCR_G', 'MKT_SPR_SE_S_STS_SCR_N', 'MKT_SPR_SE_S_STS_SCR_G',
                    'MKT_SPR_SE_NS_STS_SCR_N', 'MKT_SPR_SE_NS_STS_SCR_G', 'MKT_SPR_SE_R_SCR_N', 'MKT_SPR_SE_R_SCR_G',
                    'MKT_SPR_SE_OTH_SCR_N', 'MKT_SPR_SE_OTH_SCR_G', 'MKT_SPR_SE_TT1_SCR_N','MKT_SPR_SE_TT1_SCR_G',
                    'MKT_SPR_SE_G_STS_SCR_N', 'MKT_SPR_SE_G_STS_SCR_G']  # list of nodes to update

    for node in scr_to_update:
    # Selecting liabilities for SCRs from, BS_TYPE == 'LIAB'
        relevant_liab = (
        (aggregation_tree_market_spr_enriched['PARENT_NODE_ID'] == node) &
        (aggregation_tree_market_spr_enriched['BS_TYPE'] == 'LIAB')
        )
        # Checking if found liabilities are empty - if yes, set SCR value also empty
        if (aggregation_tree_market_spr_enriched.loc[relevant_liab, 'VALUE'] == '').all():  # empty cells are recognised as empty strings
            relevant_node = aggregation_tree_market_spr_enriched['NODE_ID'] == node
            aggregation_tree_market_spr_enriched.loc[relevant_node, 'VALUE'] = ' ' # set empty string to the node value

    return aggregation_tree_market_spr_enriched

#MARKET - Total Market risk
def calculate_total_market_risk(data_id_enriched: pd.DataFrame) -> pd.DataFrame:
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


def calculate_market_risk_all_subrisks(input_file: str) -> pd.DataFrame:
    """
    Calculate market risk by aggregating various market risk components.
    
    Args:
        input_file (str): Path to the input file containing market risk data.
    
    Returns:
        pd.DataFrame: Aggregated market risk results
    """
    # Load input data
    data_id_enriched_market = input.run_Import(input_file, ['MarketR'])
    
    # Calculate individual market subrisks
    aggregation_tree_market_ir_enriched = calculate_interest_rate_risk(data_id_enriched_market)
    aggregation_tree_market_eq_enriched = calculate_equity_risk(data_id_enriched_market)
    aggregation_tree_market_pro_enriched = calculate_property_risk(data_id_enriched_market)
    aggregation_tree_market_spr_enriched = calculate_spread_risk(data_id_enriched_market)
    aggregation_tree_market_enriched = calculate_total_market_risk(data_id_enriched_market)
    
    # Combine all market risk components into a single DataFrame
    aggregation_tree_market_all_risks = pd.concat([aggregation_tree_market_enriched,
                                                    aggregation_tree_market_ir_enriched,
                                                    aggregation_tree_market_eq_enriched,
                                                    aggregation_tree_market_pro_enriched,
                                                    aggregation_tree_market_spr_enriched], ignore_index=True)
            
    return aggregation_tree_market_all_risks

