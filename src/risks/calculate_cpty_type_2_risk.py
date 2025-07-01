import sys
sys.path.insert(0, "/workspaces/SolvMate")
import pandas as pd
import sys
import os
from src.utils import input


# Read input file to get exposures table for type 2 calculations
def read_exposures_table(data_id_enriched: pd.DataFrame) -> pd.DataFrame:
    df = input.get_dataframe(data_id_enriched, "CPTY_TYPE1")

    # Rename columns to match expected names
    df = df.rename(columns={
        "CPTY_LGD_CPTY_NAME_": "Counterparty",
        "CPTY_LGD_CPTY_PARENT_NAME_": "Parent Group",
        "CPTY_LGD_CPTY_CODE_": "LEI Code",
        "CPTY_LGD_EXP_TYPE_": "Type",
        "CPTY_LGD_CPTY_RATING_": "Rating",
        "CPTY_LGD_CPTY_SCR_RATIO_": "SCR Ratio",
        "CPTY_LGD_CPTY_MCR_RATIO_": "MCR Ratio",
        "CPTY_LGD_EXP_MVAL_": "Market Value",
        "CPTY_LGD_EXP_DEPO_": "RI Deposits",
        "CPTY_LGD_CPTY_RI_TIED_UP_": "RI > 60% tied up",
        "CPTY_LGD_EXP_RM_FLG_": "Risk Mitigation Flag",
        "CPTY_LGD_RM_EFFECT_": "Risk Mitigating Effect",
        "CPTY_LGD_RM_SIMPL_FLG_": "Simplified Risk Mitigation Flag",
        "CPTY_LGD_MORT_RISK_ADJ_VAL_": "Risk adjusted Mortgage",
        "CPTY_LGD_MORT_GUARANTEE_": "Morgage Guarantee",
        "CPTY_LGD_COLL_MVAL_": "Market Value Collateral",
        "CPTY_LGD_COLL_ADJ_MKT_": "Collateral Adjustment",
        "CPTY_LGD_COLL_3RD_REQ_MET_": "3rd Party Requirement",
        "CPTY_LGD_COLL_INSOLV_FLG_": "Collataral Insolvency",
        "CPTY_LGD_COLL_SIMPL_": "Simplified Collateral",
        "CPTY_LGD_POOL_NAME_": "Pool Name",
        "CPTY_LGD_POOL_TYPE_": "Pool Type",
        "CPTY_LGD_POOL_S2_SCOPE_": "Pool SII Scope",
        "CPTY_LGD_POOL_EOF_": "Pool EOF",
        "CPTY_LGD_POOL_C_SHARE_RISK_": "Pool SoR",
        "CPTY_LGD_POOL_U_SHARE_RISK_": "Pool USoR",
        "CPTY_LGD_POOL_COLL_FLG_": "Pool >= 60% Collateral",
        "CPTY_LGD_POOL_CONTR_RM_": "Pool RM Contribution"
    })
    return df


# Calculate  LGD for Mortgage loan
def calculate_lgd_mortgage(df: pd.DataFrame) -> float:
    """
    Calculate total LGD for mortgage loans in the given DataFrame.

    Args:
        df (pd.DataFrame): DataFrame with columns 'Type', 'Market Value', 'Risk adjusted Mortgage', 'Morgage Guarantee'

    Returns:
        float: Total LGD for mortgage loans
    """
    # Filter mortgage loans
    mortgage_loans = df.loc[df['Type'] == 'Mortgage loan'].copy()

    # Replace missing values with zero for calculation columns
    for col in ['Market Value', 'Risk adjusted Mortgage', 'Morgage Guarantee']:
        mortgage_loans[col] = mortgage_loans[col].fillna(0)

    # Calculate LGD for each row
    mortgage_loans['LGD'] = (
        mortgage_loans['Market Value'] - (0.8 * mortgage_loans['Risk adjusted Mortgage'] + mortgage_loans['Morgage Guarantee'])
    ).clip(lower=0)

    # Calculate total LGD
    total_LGD = mortgage_loans['LGD'].sum()

    return total_LGD


# Calculate total gross SCR for Counterparty Type 2 risk
def calculate_total_cpty_type2_scr(data_id_enriched: pd.DataFrame, exposures_table:  pd.DataFrame) -> tuple[float, dict] :
    """
    Calculate total gross SCR for Counterparty Type 2 risk from the given DataFrames.

    Args:
        data_id_enriched (pd.DataFrame), enriched DataFrame with Cpty Type 2 data
        exposures_table (pd.DataFrame): DataFrame with exposures data

    Returns:
        float: total SCR for Counterparty type 2 risk
        dict: Dictionary with values for specific DATA_IDs needed to get final results
    """
    # Calculate LGD for mortgage loans
    mortgage_loans = calculate_lgd_mortgage(exposures_table)
    
    # Filter data_id_enriched for CDR Type 2 data
    # Get float values for specific DATA_IDs
    ids = ['CPTY_TYPE2_EXP_INTER_NOT_DUE', 'CPTY_TYPE2_EXP_INTER_DUE', 'CPTY_TYPE2_EXP_PH', 'CPTY_TYPE2_EXP_OTH_CREDIT']

    # Make dictionary {DATA_ID: VALUE} with data necessary for calculation
    values_dict = data_id_enriched.set_index('DATA_ID').loc[ids, 'VALUE'].astype(float).to_dict()

    # Calculate total SCR for CDR Type 2 risk
    # Formula: SCR = 0.9 * CPTY_TYPE2_EXP_INTER_DUE + 0.15 * (CPTY_TYPE2_EXP_PH + CPTY_TYPE2_EXP_OTH_CREDIT + CPTY_TYPE2_EXP_INTER_NOT_DUE) + 0.15 * mortgage_loans
    scr = (
        0.9 * values_dict.get('CPTY_TYPE2_EXP_INTER_DUE', 0) +
        0.15 * (values_dict.get('CPTY_TYPE2_EXP_PH', 0) +
        values_dict.get('CPTY_TYPE2_EXP_OTH_CREDIT', 0) + values_dict.get('CPTY_TYPE2_EXP_INTER_NOT_DUE', 0) ) +
        0.15 * mortgage_loans
    )
    
    return scr, values_dict


def calculate_cpty_type2(data_id_enriched_cdr: pd.DataFrame) -> pd.DataFrame:
    """
    Create DataFrame with results in required aggregation_tree_enriched format.

    Args:
        input_file (str): Path to the input file containing data

    Returns:
        pd.DataFrame: DataFrame with calculated Counterparty Type 2 risk
    """

    # Read exposures table
    exposures_table = read_exposures_table(data_id_enriched_cdr)

    # Calculate mortgage loans LGD
    mortgage_loans_lgd = calculate_lgd_mortgage(exposures_table)

    # Calculate total SCR for Counterparty Type 2 risk
    total_scr, values_dict = calculate_total_cpty_type2_scr(data_id_enriched_cdr, exposures_table)

    # Dictionary with variables necessery for output and their values
    # Formula for CPTY_OTH_TYPE2_EXP = mortgage_loans_lgd + CPTY_TYPE2_EXP_INTER_NOT_DUE + CPTY_TYPE2_EXP_PH + CPTY_TYPE2_EXP_OTH_CREDIT 
    # CPTY_DETAIL_MORT_LOSS_TYPE2 and CPTY_DETAIL_MORT_LOSS_ALL are taken directly from data_id_enriched_cdr DataFrame (frame with input data)
    final_results = {
        'CPTY_TYPE2_SCR_G': total_scr,
        'CPTY_TYPE2_EXP_INTER_DUE': values_dict.get('CPTY_TYPE2_EXP_INTER_DUE', 0),
        'CPTY_OTH_TYPE2_EXP': mortgage_loans_lgd + values_dict.get('CPTY_TYPE2_EXP_INTER_NOT_DUE', 0) + values_dict.get('CPTY_TYPE2_EXP_PH', 0) + values_dict.get('CPTY_TYPE2_EXP_OTH_CREDIT', 0),
        'CPTY_DETAIL_MORT_LOSS_TYPE2': data_id_enriched_cdr.loc[data_id_enriched_cdr['DATA_ID'] == 'CPTY_DETAIL_MORT_LOSS_TYPE2', 'VALUE'].iloc[0],
        'CPTY_DETAIL_MORT_LOSS_ALL': data_id_enriched_cdr.loc[data_id_enriched_cdr['DATA_ID'] == 'CPTY_DETAIL_MORT_LOSS_ALL', 'VALUE'].iloc[0]
    }

    # Create the final DataFrame with all required columns
    results_frame = pd.DataFrame({
        'AGGREGATION_TREE_ID': 'CPD_TYPE2',
        'NODE_ID': list(final_results.keys()),
        'PARENT_NODE_ID': '',
        'NODE_DESC': '',
        'AGGREGATION_METHOD': 'calculate_cpty_type2',
        'MATRIX_ID': '',
        'MAX_SCENARIO_BASE': '',
        'BS_TYPE': '',
        'SCENARIO': '',
        'VALUE': list(final_results.values())
    })

    return results_frame

if __name__ == "__main__":
    # Example usage
    input_file = "/workspaces/SolvMate/input/04.12_SAS_Input_CDR.xlsb"
    data_id_enriched = input.run_Import(input_file, ["CDR"])
    result_df = calculate_cpty_type2(data_id_enriched)
