import pandas as pd
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import input


# Read input file to get exposures table for type 2 calculations
def read_exposures_table(input_file: str):
    engine = 'pyxlsb' if input_file.endswith('.xlsb') else None
    df = pd.read_excel(
        input_file,
        sheet_name='CDR',
        header=None,
        skiprows=17,
        usecols='C:AD',
        nrows=2000,
        engine=engine
        )
    
    # Choose relevant columns
    df = df[[2, 3, 5, 9, 15, 16]]
    df = df.rename(columns={
        2: 'Counterparty', 3: 'Parent Group', 5: 'Type',
        9: 'Market Value', 15: 'Risk adjustet Mortgage',
        16: 'Guarantee'
        })
    
    return df


# Calculate  LGD for Mortgage loan
def calculate_lgd_mortgage(df: pd.DataFrame) -> float:
    """
    Calculate total LGD for mortgage loans in the given DataFrame.

    Args:
        df (pd.DataFrame): DataFrame with columns 'Type', 'Market Value', 'Risk adjustet Mortgage', 'Guarantee'

    Returns:
        float: Total LGD for mortgage loans
    """
    # Filter mortgage loans
    mortgage_loans = df.loc[df['Type'] == 'Mortgage loan'].copy()

    # Replace missing values with zero for calculation columns
    for col in ['Market Value', 'Risk adjustet Mortgage', 'Guarantee']:
        mortgage_loans[col] = mortgage_loans[col].fillna(0)

    # Calculate LGD for each row
    mortgage_loans['LGD'] = (
        mortgage_loans['Market Value'] - (0.8 * mortgage_loans['Risk adjustet Mortgage'] + mortgage_loans['Guarantee'])
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


def calculate_cpty_type2(input_file: str) -> pd.DataFrame:
    """
    Create DataFrame with results in required aggregation_tree_enriched format.

    Args:
        input_file (str): Path to the input file containing data

    Returns:
        pd.DataFrame: DataFrame with calculated Counterparty Type 2 risk
    """
    # Read input file to get data_id_enriched DataFrame
    data_id_enriched_cdr = input.run_Import(input_file, ['CDR'])

    # Read exposures table
    exposures_table = read_exposures_table(input_file)

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
