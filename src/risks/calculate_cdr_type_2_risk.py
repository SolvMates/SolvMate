import pandas as pd
import numpy as np


# Read input file
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
    
    # Process data
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
    mortgage_loans = df[df['Type'] == 'Mortgage loan'].copy()

    # Calculate LGD for each row
    mortgage_loans['LGD'] = (
        mortgage_loans['Market Value'] - (0.8 * mortgage_loans['Risk adjustet Mortgage'] + mortgage_loans['Guarantee'])
    ).clip(lower=0)

    # Calculate total LGD
    total_LGD = mortgage_loans['LGD'].sum()

    return total_LGD