import pandas as pd
import numpy as np
import os
import logging
from typing import Tuple, Dict, List, Optional
from dotenv import load_dotenv
from supabase import create_client, Client

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Constants
DEFAULT_PD = 0.042
MIN_SCR_RATIO_PD = 0.0001
MAX_SCR_RATIO_PD = 0.042
SCR_RATIO_UPPER_BOUND = 1.96
SCR_RATIO_LOWER_BOUND = 0.75


# Initialize Supabase client
load_dotenv()
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)

def fetch_lookup_tables() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Fetch lookup tables from Supabase database.
    
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: CDR LGD factors, CDR rating PD, CDR ratio PD, and CDR pool ratio tables
    
    Raises:
        Exception: If database connection fails or tables don't exist
    """
    try:
        cdr_lgd_factors_response = supabase.table('CDR_lgd_factors').select('*').execute()
        cdr_lgd_factors = pd.DataFrame(cdr_lgd_factors_response.data)
    
        rating_pd_response = supabase.table('CDR_rating_PD').select('*').execute()
        cdr_rating_pd = pd.DataFrame(rating_pd_response.data)

        ratio_pd_response = supabase.table('CDR_ratio_PD').select('*').execute()
        cdr_ratio_pd = pd.DataFrame(ratio_pd_response.data)
        
        pool_ratio_response = supabase.table('CDR_pool_ratio').select('*').execute()
        cdr_pool_ratio = pd.DataFrame(pool_ratio_response.data)

        return cdr_lgd_factors, cdr_rating_pd, cdr_ratio_pd, cdr_pool_ratio
    except Exception as e:
        raise Exception(f"Failed to fetch lookup tables: {str(e)}")


def get_pd_lgd(aggregated_sne: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Get unique PDs and sum LGDs for each PD.
    
    Args:
        aggregated_sne (pd.DataFrame): DataFrame containing PD and LGD values
        
    Returns:
        Tuple[np.ndarray, np.ndarray]: Arrays of PD values and corresponding summed LGD values
        
    Note:
        The function drops any rows with NaN PD values and sorts by PD
    """
    pd_lgd = (
        aggregated_sne
        .groupby('PD_weighted', dropna=True, as_index=False)
        .agg(sum_lgd=('LGD', 'sum'))
        .sort_values('PD_weighted')
        .reset_index(drop=True)
    )
    pd_lgd = pd_lgd.dropna(subset=['PD_weighted'])

    return pd_lgd['PD_weighted'].values, pd_lgd['sum_lgd'].values


def calculate_pd(row: pd.Series, rating_pd_dict: Dict[str, float], ratio_pd_df: pd.DataFrame) -> float:
    """
    Calculate Probability of Default (PD) based on Rating or SCR Ratio.
    
    Args:
        row (pd.Series): Row containing Rating and SCR Ratio information
        rating_pd_dict (Dict[str, float]): Mapping of ratings to PD values
        ratio_pd_df (pd.DataFrame): DataFrame containing SCR ratio to PD mappings
        
    Returns:
        float: Calculated PD value
        
    Raises:
        ValueError: If both Rating and SCR Ratio are filled or if input values are invalid
    """
    rating = row.get('Rating', None)
    scr_ratio = row.get('SCR Ratio', None)

    if pd.notnull(rating) and pd.notnull(scr_ratio):
        raise ValueError(f"Both Rating and SCR Ratio are filled (Rating: {rating}, SCR Ratio: {scr_ratio})")

    # Rating case
    if pd.notnull(rating):
        pd_value = rating_pd_dict.get(rating)
        if pd_value is None:
            raise ValueError(f"No PD found for Rating '{rating}'.")
        return pd_value

    # SCR Ratio case
    if pd.notnull(scr_ratio):
        try:
            scr_ratio = float(scr_ratio)
        except (ValueError, TypeError):
            raise ValueError(f"SCR Ratio '{scr_ratio}' is not a valid number.")

        if scr_ratio > SCR_RATIO_UPPER_BOUND:
            return MIN_SCR_RATIO_PD
        if scr_ratio < SCR_RATIO_LOWER_BOUND:
            return MAX_SCR_RATIO_PD

        ratio_pd_df_sorted = ratio_pd_df.sort_values('SII Ratio')
        ratios = ratio_pd_df_sorted['SII Ratio'].astype(float).values
        pds = ratio_pd_df_sorted['PD'].astype(float).values

        return np.interp(scr_ratio, ratios, pds)

    # Default case: neither Rating nor SCR Ratio is filled
    return DEFAULT_PD


def calculate_risk_adjusted_collateral(row: pd.Series) -> float:
    """
    Calculate Risk Adjusted Collateral based on exposure type and conditions.
    
    Args:
        row (pd.Series): Row containing exposure information
        
    Returns:
        float: Calculated Risk Adjusted Collateral value
    """
    type_of_exposure = str(row.get('Type', ''))
    
    # For derivatives with specific types, return Market Value Collateral directly
    if type_of_exposure in ['Derivatives_[DA]192(3)', 'Derivatives_[DA]192(3a)', 'Derivatives_[DA]192(3b)']:
        return float(row.get('Market Value Collateral', 0) or 0)
    
    # For specified types, apply complex logic
    if type_of_exposure in ['Ceding reinsurance', 'Securitisations', 'Derivatives_[DA]192(3c)']:
        market_value_collateral = float(row.get('Market Value Collateral', 0) or 0)
        collateral_adjustment = float(row.get('Collateral Adjustment', 0) or 0)
        is_simplified = str(row.get('Simplified Collateral', '')).lower() == 'yes'
        is_third_party = str(row.get('3rd Party Requirement', '')).lower() == 'yes'
        
        # Constants from config
        COLLATERAL_ADJUSTMENT_3RD_PARTY = 1.0
        COLLATERAL_ADJUSTMENT = 0.9
        COLLATERAL_ADJUSTMENT_3RD_PARTY_SIMPL = 0.85
        COLLATERAL_ADJUSTMENT_SIMPL = 0.75
        
        if is_simplified:
            # Simplified approach
            return COLLATERAL_ADJUSTMENT_3RD_PARTY_SIMPL * market_value_collateral if is_third_party else COLLATERAL_ADJUSTMENT_SIMPL * market_value_collateral
        else:
            # Standard approach
            adjusted_value = market_value_collateral - collateral_adjustment
            return COLLATERAL_ADJUSTMENT_3RD_PARTY * adjusted_value if is_third_party else COLLATERAL_ADJUSTMENT * adjusted_value

    # For all other types
    return 0.0


def calculate_lgd(exposure_row: pd.Series, lgd_factors_df: pd.DataFrame) -> float:
    """
    Calculate Loss Given Default (LGD) based on exposure type and related values.
    
    Args:
        exposure_row (pd.Series): Row containing exposure information
        lgd_factors_df (pd.DataFrame): Configuration table with LGD factors
        
    Returns:
        float: Calculated LGD value
    """

    # Extract values with proper NaN handling
    type_of_exposure = str(exposure_row.get('Type', ''))
    
    # Handle numeric values with proper NaN checking
    def safe_float(value, default=0):
        if pd.isna(value):
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
            
    market_value = safe_float(exposure_row.get('Market Value', 0))
    reinsurance_deposits = safe_float(exposure_row.get('RI Deposits', 0))
    risk_mitigating_effect = safe_float(exposure_row.get('Risk Mitigating Effect', 0))
    risk_adjusted_collateral = safe_float(exposure_row.get('RACollateral', 0))
    risk_adjusted_mortgage = safe_float(exposure_row.get('Risk adjustet Mortgage', 0))
    reinsurance_tied_up = str(exposure_row.get('RI > 60% tied up', '')).lower() == 'yes'

    # Get factors from config table
    factors = lgd_factors_df[
        (lgd_factors_df['type_of_exposure'] == type_of_exposure) & 
        (lgd_factors_df['reinsurance_tied_up'].astype(str).str.lower() == str(reinsurance_tied_up).lower())
    ]

    if factors.empty:
        # Try without reinsurance_tied_up condition
        factors = lgd_factors_df[lgd_factors_df['type_of_exposure'] == type_of_exposure]
    
    if factors.empty:
        logger.warning(f"No configuration found for exposure type: {type_of_exposure}")
        return 0
    
    # Get first matching row
    factor = factors.iloc[0]

    # Calculate net market value for reinsurance and securitizations
    if type_of_exposure in ['Ceding reinsurance', 'Securitisations']:
        net_market_value = market_value - reinsurance_deposits
    else:
        net_market_value = market_value
    
    # Calculate LGD based on exposure type
    try:
        if type_of_exposure in ['Ceding reinsurance', 
                               'Securitisations',
                               'Derivatives', 
                               'Derivatives_[DA]192(3)', 
                               'Derivatives_[DA]192(3a)', 
                               'Derivatives_[DA]192(3b)', 
                               'Derivatives_[DA]192(3c)']:
            
            lgd = max(
                factor['LOSS_FACTOR'] * (net_market_value + factor['ALPHA'] * risk_mitigating_effect) - 
                factor['COL_ADJ'] * factor['F_FACTOR'] * risk_adjusted_collateral, 
                0)
            return lgd
            
        elif type_of_exposure in ['Accepting reinsurance', 'Other credit exposures']:
            return max(net_market_value, 0)
            
        elif type_of_exposure == 'Mortgage loan':
            return max(market_value - factor['F_FACTOR'] * risk_adjusted_mortgage, 0)
            
        else:
            logger.info(f"Unknown exposure type, returning 0")
            return 0
            
    except Exception as e:
        logger.error(f"Error during LGD calculation: {str(e)}")
        logger.error(f"Factor values: {factor.to_dict()}")
        raise


def aggregate_by_parent_group(counterparty_exposures: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate LGD (sum) and PD (weighted mean by LGD) by Parent Group.
    
    Args:
        counterparty_exposures (pd.DataFrame): DataFrame containing exposure data
            Must have columns: 'Parent Group', 'LGD', 'PD'
            
    Returns:
        pd.DataFrame: Aggregated data by Parent Group
        
    Raises:
        ValueError: If required columns are missing
    """
    required_columns = ['Parent Group', 'LGD', 'PD']
    missing_columns = [col for col in required_columns if col not in counterparty_exposures.columns]
    
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
    
    try:
        # Calculate weights for PD averaging
        weights = counterparty_exposures['LGD']
        total_weight = weights.sum()
        
        if total_weight == 0:
            logger.warning("All LGD values are zero, PD weighted average will be NaN")
        
        # Perform aggregation
        aggregated = counterparty_exposures.groupby('Parent Group').agg(
            LGD=('LGD', 'sum'),
            PD_weighted=('PD', lambda x: np.average(
                x, weights=counterparty_exposures.loc[x.index, 'LGD']
            ) if counterparty_exposures.loc[x.index, 'LGD'].sum() > 0 else np.nan)
        ).reset_index()
        
        logger.info(f"Aggregated {len(counterparty_exposures)} exposures into {len(aggregated)} parent groups")
        return aggregated
        
    except Exception as e:
        logger.error(f"Error during aggregation: {str(e)}")
        raise


def calculate_v_inter(distinct_pd: np.ndarray, sum_lgd: np.ndarray) -> Tuple[float, np.ndarray]:
    """
    Calculate V_Inter with squared sum_lgd.
    
    Args:
        distinct_pd (np.ndarray): Array of distinct PD values
        sum_lgd (np.ndarray): Array of corresponding LGD sums
        
    Returns:
        Tuple[float, np.ndarray]: Total V_Inter value and array of individual terms
    """
    v_inter_terms = (1.5 * distinct_pd * (1 - distinct_pd) * sum_lgd**2) / (2.5 - distinct_pd)
    V_Inter = float(np.sum(v_inter_terms))
    return V_Inter, v_inter_terms


def calculate_v_intra(distinct_pd: np.ndarray, sum_lgd: np.ndarray) -> float:
    """
    Calculate V_Intra using matrix operations.
    
    Args:
        distinct_pd (np.ndarray): Array of distinct PD values
        sum_lgd (np.ndarray): Array of corresponding LGD sums
        
    Returns:
        float: Calculated V_Intra value
    
    Note:
        Uses broadcasting for efficient computation of the correlation matrix
    """
    pd_j, pd_k = np.meshgrid(distinct_pd, distinct_pd, indexing='ij')
    lgd_j, lgd_k = np.meshgrid(sum_lgd, sum_lgd, indexing='ij')
    
    numerator = pd_k * (1 - pd_k) * pd_j * (1 - pd_j) * lgd_k * lgd_j
    denominator = 1.25 * (pd_j + pd_k) - pd_j * pd_k
    
    # Handle division by zero
    mask = denominator != 0
    v_intra_matrix = np.zeros_like(numerator, dtype=float)
    v_intra_matrix[mask] = numerator[mask] / denominator[mask]
    
    return float(np.sum(v_intra_matrix))


def calculate_pool_sii_ratio(row: pd.Series, pool_ratio_dict: Dict[str, float]) -> float:
    """
    Calculate Pool SII Ratio based on rating or SCR ratio.
    
    Args:
        row (pd.Series): Row containing exposure data
        pool_ratio_dict (Dict[str, float]): Mapping of ratings to pool SII ratios
        
    Returns:
        float: Calculated Pool SII Ratio
    """
    rating = row.get('Rating')
    if pd.notnull(rating):
        return pool_ratio_dict.get(rating, 0.75)
    elif row.get('Pool SII Scope') == 'yes':
        return row.get('SCR Ratio', 0.75)
    return 0.75


def calculate_pool_metrics(df: pd.DataFrame, lgd_factors_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate pool metrics and update the dataframe for all pool types.
    
    Args:
        df (pd.DataFrame): DataFrame containing exposure data
        lgd_factors_df (pd.DataFrame): Configuration table with LGD factors
        
    Returns:
        pd.DataFrame: Updated DataFrame with pool calculations
    """
    # Create a copy to avoid SettingWithCopyWarning
    df = df.copy()
    
    # Always store original LGD as LGD_Base before any pool adjustments
    if 'LGD_Base' not in df.columns:
        df['LGD_Base'] = df['LGD'].copy()  # Deep copy to preserve original values
    
    # Process pool types B and C first
    pool_bc_mask = (df['Pool Name'].notna()) & (df['Pool Type'].isin(['B', 'C']))
    if pool_bc_mask.any():
        logger.info(f"Found {pool_bc_mask.sum()} pool type B/C exposures")
        
        # Update original LGD_Base for B/C pools
        df.loc[pool_bc_mask, 'LGD_Base'] = df.loc[pool_bc_mask, 'LGD']
        
        # Calculate new LGD for pool types B and C
        for idx in df[pool_bc_mask].index:
            try:
                old_lgd = df.loc[idx, 'LGD_Base']  # Use LGD_Base instead of LGD
                new_lgd = calculate_pool_type_bc_lgd(df.loc[idx], lgd_factors_df)
                df.loc[idx, 'LGD'] = new_lgd
            except Exception as e:
                logger.error(f"Error calculating LGD for row {idx}: {str(e)}")
                logger.error(f"Row data: {df.loc[idx].to_dict()}")
                raise

    # Process pool type A
    pool_a_mask = (df['Pool Name'].notna()) & (df['Pool Type'] == 'A')
    if not pool_a_mask.any():
        logger.info("No pool type A exposures found")
        return df
        
    logger.info(f"Found {pool_a_mask.sum()} pool type A exposures")
    
    # Ensure required columns exist
    required_cols = ['Pool EOF', 'Pool SII Ratio', 'Pool SoR']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for pool calculation: {missing_cols}")
    
    # Calculate intermediary metrics
    df['eof_pool_ratio'] = df['Pool EOF'] / df['Pool SII Ratio']
    df['sor_pool_ratio'] = df['Pool SoR'] * df['Pool SII Ratio']
    
    # Aggregate pool metrics
    pool_agg = (df[pool_a_mask]
                .groupby('Pool Name')
                .agg({
                    'Pool EOF': 'sum',
                    'Pool SoR': 'sum',
                    'Pool SII Ratio': 'first',
                    'eof_pool_ratio': 'sum',
                    'sor_pool_ratio': 'sum'
                }))
    
    # Rename columns to match expected names
    pool_agg.columns = [
        'aggregated_Pool EOF',
        'aggregated_Pool SoR',
        'aggregated_Pool SII Ratio',
        'aggregated_EOF/Pool SII Ratio',
        'aggregated_SoR * Pool SII Ratio'
    ]
    
    # Reset index to make Pool Name a column for merging
    pool_agg = pool_agg.reset_index()
    
    # Merge aggregated values back to original DataFrame
    df = df.merge(pool_agg, on='Pool Name', how='left')
    
    # Calculate Q value for pool type A
    # Only apply to type A pools
    mask_nonzero_eof = (pool_a_mask) & (df['aggregated_EOF/Pool SII Ratio'].notna()) & (df['aggregated_EOF/Pool SII Ratio'] != 0)
    mask_zero_eof = (pool_a_mask) & (df['aggregated_EOF/Pool SII Ratio'].notna()) & (df['aggregated_EOF/Pool SII Ratio'] == 0)
    
    # Calculate Q for non-zero EOF/Pool SII Ratio
    df.loc[mask_nonzero_eof, 'Q'] = np.exp(-0.15 * np.minimum(1.96, 
        ((1 - df.loc[mask_nonzero_eof, 'aggregated_Pool SoR']) * 
         df.loc[mask_nonzero_eof, 'aggregated_Pool EOF']) / 
        df.loc[mask_nonzero_eof, 'aggregated_EOF/Pool SII Ratio'] +
        df.loc[mask_nonzero_eof, 'aggregated_SoR * Pool SII Ratio'] - 1
    ))
    
    # Calculate Q for zero EOF/Pool SII Ratio
    df.loc[mask_zero_eof, 'Q'] = np.exp(-0.15 * np.minimum(1.96,
        df.loc[mask_zero_eof, 'aggregated_SoR * Pool SII Ratio'] - 1
    ))
    
    # Update original LGD_Base for type A pools
    df.loc[pool_a_mask, 'LGD_Base'] = df.loc[pool_a_mask, 'LGD']
    # Update LGD for pool type A using original LGD value as base
    df.loc[pool_a_mask, 'LGD'] = df.loc[pool_a_mask, 'Q'] * df.loc[pool_a_mask, 'LGD_Base']
    
    return df

def calculate_pool_type_bc_lgd(row: pd.Series, lgd_factors_df: pd.DataFrame) -> float:
    """
    Calculate LGD for Pool Types B and C.
    
    Args:
        row (pd.Series): Row containing exposure data
        lgd_factors_df (pd.DataFrame): Configuration table with LGD factors
        
    Returns:
        float: Calculated LGD value
    """
    logger.info(f"Calculating LGD for Pool Type {row['Pool Type']}")

    # Calculate Recovery Rate factor
    has_collateral = str(row.get('Pool >= 60% Collateral', '')).lower() == 'yes'
    rr = 0.10 if has_collateral else 0.50
    
    # Get exposure type specific F factor from config
    type_of_exposure = str(row.get('Type', ''))
    factors = lgd_factors_df[lgd_factors_df['type_of_exposure'] == type_of_exposure]
    
    if factors.empty:
        logger.warning(f"No configuration found for exposure type: {type_of_exposure}")
        return 0
    
    # Use F_FACTOR from configuration
    f_factor = float(factors.iloc[0].get('F_FACTOR', 0))
    
    # Get common values
    market_value = float(row.get('Market Value', 0) or 0)
    risk_mitigating_effect = float(row.get('Risk Mitigating Effect', 0) or 0)
    market_value_collateral = float(row.get('Market Value Collateral', 0) or 0)
    pool_rm_contribution = float(row.get('Pool RM Contribution', 0) or 0)
    
    # Calculate type-specific multiplier
    multiplier = 0
    if row['Pool Type'] == 'B':
        pool_sor = float(row.get('Pool SoR', 0) or 0)
        pool_usor = float(row.get('Pool USoR', 0) or 0)

        # Handle division by zero case explicitly
        if pool_sor >= 1:
            multiplier = max(pool_sor, pool_usor)
        elif pool_sor > 0:  # Only calculate ratio if SoR is present
            sor_ratio = pool_usor / (1 - pool_sor) if pool_usor > 0 else 0
            multiplier = max(pool_sor, sor_ratio)
        else:  # If no SoR, use USoR as fallback
            multiplier = pool_usor
    else:  # Type C
        pool_usor = float(row.get('Pool USoR', 0) or 0)
        multiplier = pool_usor if pool_usor > 0 else 0

# Calculate intermediate values for LGD
    mv_term = max(0, market_value)
    first_term = (1 - rr) * multiplier * mv_term
    second_term = pool_rm_contribution * risk_mitigating_effect if not pd.isna(pool_rm_contribution) else 0
    third_term = f_factor * market_value_collateral
    
    # Calculate final LGD ensuring non-negative value
    lgd = max(0, first_term + second_term - third_term)
    
    return lgd

def transform_to_aggregation_tree(aggregated_sne: pd.DataFrame) -> pd.DataFrame:
    """
    Transform aggregated_sne DataFrame into the required cpd_aggregation_tree_enriched format.
    """
    # Sort by LGD descending and rename columns
    df = aggregated_sne.sort_values('LGD', ascending=False).reset_index(drop=True)
    df = df.rename(columns={
        'Parent Group': 'PARENT_GROUP',
        'LGD': 'LGD',
        'PD_weighted': 'PD'
    })
    
    # Keep only top 10 rows
    df = df.head(10).reset_index(drop=True)
    
    # Add line numbers (1-based)
    df.index = df.index + 1
    
    # Create list of all NODE_IDs we want to create
    cols = df.columns
    nums = [f"{i:02d}" for i in range(1, len(df) + 1)]
    node_ids = [f"{col}_{num}" for col in cols for num in nums]
    
    # Melt the DataFrame to get all values in one column
    melted = pd.melt(df.reset_index(), id_vars=['index'])
    melted['NODE_ID'] = melted.apply(lambda x: f"{x['variable']}_{x['index']:02d}", axis=1)
    melted = melted[['NODE_ID', 'value']].rename(columns={'value': 'VALUE'})
    
    # Create the final DataFrame with all required columns
    result = pd.DataFrame({
        'AGGREGATION_TREE_ID': 'CPD_TYPE1',
        'NODE_ID': melted['NODE_ID'],
        'PARENT_NODE_ID': '',
        'NODE_DESC': '',
        'AGGREGATION_METHOD': 'calculate_cpty_type1',
        'MATRIX_ID': '',
        'MAX_SCENARIO_BASE': '',
        'BS_TYPE': '',
        'SCENARIO': '',
        'VALUE': melted['VALUE']
    })
    
    return result

# Modify the main function to include the transformation and include it in results
def calculate_cpty_type1(input_file: str, output_folder: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, float, float, float, pd.DataFrame]:
    """
    Main function to process counterparty risk calculations.
    """
    logger.info("Starting counterparty risk calculations")
    
    try:
        # Fetch lookup tables
        cdr_lgd_factors, cdr_rating_pd, cdr_ratio_pd, cdr_pool_ratio = fetch_lookup_tables()
        
        rating_pd_dict = dict(zip(cdr_rating_pd['Rating'], cdr_rating_pd['PD']))
        pool_ratio_dict = dict(zip(cdr_pool_ratio['Rating'], cdr_pool_ratio['Pool SII Ratio']))
        
        # Read and process input file
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

        # Process data
        df = df[[2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29]]
            
        df = df.rename(columns={
            2: 'Counterparty', 3: 'Parent Group', 4: 'LEI Code',
            5: 'Type', 6: 'Rating', 7: 'SCR Ratio', 8: 'MCR Ratio', 
            9: 'Market Value', 10: 'RI Deposits', 11: 'RI > 60% tied up',
            13: 'Risk Mitigating Effect', 15: 'Risk adjustet Mortgage',
            16: 'Morgage Guarantee', 17: 'Market Value Collateral', 
            18: 'Collateral Adjustment', 19: '3rd Party Requirement',
            20: 'Collataral Insolvency', 21: 'Simplified Collateral',
            22: "Pool Name", 23: 'Pool Type', 24: 'Pool SII Scope',
            25: 'Pool EOF', 26: 'Pool SoR', 27: 'Pool USoR',
            28: 'Pool >= 60% Collateral', 29: 'Pool RM Contribution'
        })
        
        # Clean and process records
        df = df.dropna(how='all', subset=['Counterparty', 'Type'])
        logger.info(f"Processing {len(df)} exposure records")
        
        # Calculate Pool SII Ratio for pool exposures
        pool_mask = df['Pool Name'].notna()
        df.loc[pool_mask, 'Pool SII Ratio'] = df[pool_mask].apply(
            lambda row: calculate_pool_sii_ratio(row, pool_ratio_dict), axis=1
        )

        # Calculate Risk Adjusted Collateral and LGD
        df['RACollateral'] = df.apply(calculate_risk_adjusted_collateral, axis=1)
        df['LGD'] = df.apply(lambda row: calculate_lgd(row, cdr_lgd_factors), axis=1)

        # Calculate PD and fill Parent Group
        df['PD'] = df.apply(lambda row: calculate_pd(row, rating_pd_dict, cdr_ratio_pd), axis=1)
        df['Parent Group'] = df['Parent Group'].fillna(df['Counterparty'])
        
        # Apply pool adjustments if applicable
        if 'Pool Name' in df.columns and df['Pool Name'].notna().any():
            logger.info("Calculating pool adjustments")
            df = calculate_pool_metrics(df, cdr_lgd_factors)

        # Aggregate and calculate final values
        logger.info("Performing final calculations")
        aggregated_sne = aggregate_by_parent_group(df)
        distinct_pd, sum_lgd = get_pd_lgd(aggregated_sne)
        
        V_Inter, v_inter_terms = calculate_v_inter(distinct_pd, sum_lgd)
        V_Intra = calculate_v_intra(distinct_pd, sum_lgd)
        sigma = np.sqrt(V_Inter + V_Intra)

        v_inter_table = pd.DataFrame({
            'distinct_pd': distinct_pd,
            'sum_lgd': sum_lgd,
            'v_inter_term': v_inter_terms
        })
        
        # Transform aggregated_sne into cpd_aggregation_tree_enriched format
        logger.info("Creating aggregation tree")
        cpd_aggregation_tree_enriched = transform_to_aggregation_tree(aggregated_sne)
        
        results = (df, aggregated_sne, v_inter_table, V_Inter, V_Intra, sigma, cpd_aggregation_tree_enriched)
        


        return cpd_aggregation_tree_enriched

    except FileNotFoundError:
        logger.error(f"Input file not found: {input_file}")
        raise
    except Exception as e:
        logger.error(f"Error during calculation: {str(e)}")
        raise

if __name__ == "__main__":
    input_file = "/workspaces/SolvMate/input/04.12_SAS_Input_CDR.xlsb"
    output_folder = "/workspaces/SolvMate/outputs"
    
    try:
        cpd_aggregation_tree_enriched = calculate_cpty_type1(input_file, output_folder)
        
    except Exception as e:
        logger.error(f"Failed to complete calculations: {str(e)}")
        raise