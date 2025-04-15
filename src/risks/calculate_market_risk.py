import os
from dotenv import load_dotenv
from supabase import create_client, Client
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import openpyxl
from pathlib import Path

# Initialize Supabase client
load_dotenv()
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)

def read_market_risk_input(input_path: str) -> pd.DataFrame:
    """
    Read the market risk input data from the xlsb file.
    
    Args:
        input_path (str): Path to the input xlsb file
    
    Returns:
        pd.DataFrame: DataFrame containing the market risk data
    """
    try:
        return pd.read_excel(input_path, sheet_name='MarketR', header=0, engine='pyxlsb')
    except Exception as e:
        raise Exception(f"Error reading input file: {str(e)}")

def get_cell_value(df: pd.DataFrame, rc_code: str) -> float:
    """
    Extract value from DataFrame based on RC_CODE.
    
    Args:
        df (pd.DataFrame): Input DataFrame
        rc_code (str): RC_CODE in format 'R{row}C{col}'
    
    Returns:
        float: Cell value or None if invalid
    """
    if not rc_code:
        return None
    
    try:
        row_num = int(rc_code.split('C')[0][1:]) - 1  # Convert to 0-based index
        col_num = int(rc_code.split('C')[1]) - 1
        
        if 0 <= row_num < len(df) and 0 <= col_num < len(df.columns):
            return df.iat[row_num, col_num]
        return None
    except:
        return None

def aggregate_tree(tree_data: pd.DataFrame, correlation_matrix: pd.DataFrame = None, max_iterations: int = 1000) -> pd.DataFrame:
    """
    Aggregate the market SCR values based on the aggregation tree.

    Args:
        tree_data (pd.DataFrame): Aggregation tree data
        correlation_matrix (pd.DataFrame): Correlation matrix for calculations
        max_iterations (int): Maximum number of iterations before raising an error

    Returns:
        pd.DataFrame: Aggregated results
    """
    def calculate_correlated_value(node, children_values, correlation_matrix):
        matrix_id = node['MATRIX_ID']
        relevant_correlations = correlation_matrix[
            correlation_matrix['CORRELATION_MATRIX_ID'] == matrix_id
        ]

        total = 0
        child_ids = children_values.index

        for i in child_ids:
            for j in child_ids:
                if i != j:
                    try:
                        corr = relevant_correlations[
                            (relevant_correlations['VAR1_NM'] == i) & 
                            (relevant_correlations['VAR2_NM'] == j)
                        ]['CORRELATION_VALUE_NO'].iloc[0]
                        total += corr * children_values[i] * children_values[j]
                    except IndexError:
                        return "missing correlation values"

        return np.sqrt(total)

    def calculate_dnav(children):
        try:
            base_assets = children[
                (children['BS_TYPE'] == 'asset') & 
                (children['SCENARIO'] == 'BC')
            ]['VALUE'].sum()

            base_liab = children[
                (children['BS_TYPE'] == 'liab') & 
                (children['SCENARIO'] == 'BC')
            ]['VALUE'].sum()

            shocked_assets = children[
                (children['BS_TYPE'] == 'asset') & 
                (children['SCENARIO'] == 'SH')
            ]['VALUE'].sum()

            shocked_liab = children[
                (children['BS_TYPE'] == 'liab') & 
                (children['SCENARIO'] == 'SH')
            ]['VALUE'].sum()

            return (base_assets - base_liab) - (shocked_assets - shocked_liab)
        except KeyError:
            return "missing dnav data"

    # Create results DataFrame
    results = pd.DataFrame(index=tree_data['NODE_ID'])
    results['VALUE'] = np.nan
    results['VALUE'] = results['VALUE'].astype(object)  # Allow mixed types (numeric and string)

    iteration_count = 0
    prev_null_count = float('inf')

    # Process nodes from bottom up
    while results['VALUE'].isnull().any():
        iteration_count += 1
        current_null_count = results['VALUE'].isnull().sum()

        # Check for infinite loop conditions
        if iteration_count > max_iterations:
            print(f"Maximum iterations ({max_iterations}) reached. Possible circular dependency in tree.")
            break
        if current_null_count >= prev_null_count:
            stuck_nodes = results.index[results['VALUE'].isnull()].tolist()
            print(f"Stuck nodes: {stuck_nodes}")
            break

        prev_null_count = current_null_count

        # Process level by level
        for node_id in results.index[results['VALUE'].isnull()]:
            node = tree_data[tree_data['NODE_ID'] == node_id].iloc[0]
            children = tree_data[tree_data['PARENT_NODE_ID'] == node_id]

            # Handle leaf nodes (nodes without children)
            if len(children) == 0:
                if node['AGGREGATION_METHOD_CD'] == 'external':
                    # Use the VALUE column directly for external nodes
                    results.loc[node_id, 'VALUE'] = node['VALUE']
                else:
                    results.loc[node_id, 'VALUE'] = 0  # Default value for non-external leaf nodes
                continue

            # Skip if children's values are not calculated yet
            if not all(results.loc[children['NODE_ID']]['VALUE'].notna()):
                results.loc[node_id, 'VALUE'] = "missing children values"
                continue

            method = node['AGGREGATION_METHOD_CD']

            try:
                if method == 'sum':
                    results.loc[node_id, 'VALUE'] = results.loc[children['NODE_ID'], 'VALUE'].sum()
                elif method in ('max', 'max_scen'):
                    results.loc[node_id, 'VALUE'] = results.loc[children['NODE_ID'], 'VALUE'].max()
                elif method == 'correlated':
                    results.loc[node_id, 'VALUE'] = calculate_correlated_value(
                        node, 
                        results.loc[children['NODE_ID'], 'VALUE'],
                        correlation_matrix
                    )
                elif method == 'dnav':
                    results.loc[node_id, 'VALUE'] = calculate_dnav(children)
                else:
                    results.loc[node_id, 'VALUE'] = f"unknown method: {method}"
            except Exception as e:
                results.loc[node_id, 'VALUE'] = f"error: {str(e)}"

    return results

def process_output_mapping(results: pd.DataFrame, mapping_template_path: str) -> pd.DataFrame:
    """
    Process the output mapping based on the template.
    
    Args:
        results (pd.DataFrame): Aggregation results
        mapping_template_path (str): Path to the mapping template
    
    Returns:
        pd.DataFrame: Processed output data
    """
    # Read mapping template
    mapping = pd.read_excel(
        mapping_template_path,
        sheet_name='Output mapping',
        usecols="C:K",
        skiprows=11,
        nrows=52
    )
    
    # Clean column names
    mapping.columns = [
        str(col).replace(" ", "").replace(",", "_").replace(";", "_")
        .replace("(", "_").replace(")", "_").replace("\n", "_")
        for col in mapping.columns
    ]
    
    # Replace values in relevant columns
    value_columns = [f"C00{i}" for i in range(20, 81, 10)]
    for col in value_columns:
        mapping[col] = mapping[col].map(lambda x: results.loc[x, 'VALUE'] if x in results.index else x)
    
    return mapping

def read_aggregation_tree(tree_id: str) -> pd.DataFrame:
    """
    Read aggregation tree data from Supabase.
    
    Args:
        tree_id (str): Aggregation tree identifier
    
    Returns:
        pd.DataFrame: Aggregation tree data
    """
    response = (supabase.table('aggregation_tree_market') # Tree only set up for market risk as of now
               .select('*')
               .eq('AGGREGATION_TREE_ID', tree_id)
               .execute())
    return pd.DataFrame(response.data)

def read_correlation_matrix(matrix_id: str) -> pd.DataFrame:
    """
    Read correlation matrix from Supabase.
    
    Args:
        matrix_id (str): Correlation matrix identifier
    
    Returns:
        pd.DataFrame: Correlation matrix data
    """
    response = (supabase.table('correlation_matrix')
               .select('*')
               .eq('CORRELATION_MATRIX_ID', matrix_id)
               .execute())
    return pd.DataFrame(response.data)

def read_data_id_values(worksheet: str = 'MarketR') -> pd.DataFrame:
    """
    Read data_id values from Supabase.
    
    Args:
        worksheet (str): Worksheet name to filter by
    
    Returns:
        pd.DataFrame: Data ID values
    """
    response = (supabase.table('data_id')
               .select('*')
               .eq('WORKSHEET', worksheet)
               .execute())
    return pd.DataFrame(response.data)


def main(run_id: str = None):
    """
    Main function to run the market risk calculations.

    Args:
        run_id (str, optional): Run identifier for output files
    """
    # Setup paths
    input_path = Path("/workspaces/SolvMate/input/02.01_SAS_Input_MarketR.xlsb")
    template_path = Path("/workspaces/SolvMate/templates/Output_Template.xlsx")
    output_dir = Path("/workspaces/SolvMate/outputs")

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate run_id if not provided
    if not run_id:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Read input data from Excel
    market_risk_input = read_market_risk_input(input_path)

    # Read data from Supabase
    tree_data = read_aggregation_tree('MARKET_INT')
    correlation_data = read_correlation_matrix('corrmatrix_mkt_up')
    data_id_values = read_data_id_values()

    # Validate input data
    if tree_data.empty:
        raise ValueError("Aggregation tree data is empty.")
    if correlation_data.empty:
        raise ValueError("Correlation matrix data is empty.")

    # Step 1: Create data_id_values DataFrame
    print("Inspecting data_id_values before processing:")
    print(data_id_values[['WORKSHEET', 'CELL_REF']].head())

    data_id_values['VALUE'] = data_id_values.apply(
        lambda row: get_cell_value(market_risk_input, row['RC_CODE']) 
        if row['WORKSHEET'] == 'MarketR' and pd.notnull(row['RC_CODE']) else None,
        axis=1
    )

    print("Inspecting data_id_values after processing:")
    print(data_id_values[['WORKSHEET', 'CELL_REF', 'VALUE']].head())

    # Step 2: Update tree_data with external values from data_id_values
    for _, node in tree_data[tree_data['AGGREGATION_METHOD_CD'] == 'external'].iterrows():
        matching_data = data_id_values[data_id_values['DATA_ID'] == node['NODE_ID']]
        if not matching_data.empty:
            tree_data.loc[tree_data['NODE_ID'] == node['NODE_ID'], 'VALUE'] = matching_data['VALUE'].iloc[0]

    # Process tree data and get results
    try:
        results = aggregate_tree(tree_data, correlation_data, max_iterations=1000)
        print("\nAggregation successful!")
    except Exception as e:
        print(f"\nAggregation failed: {str(e)}")
        raise

    # Process output mapping
    output_data = process_output_mapping(results, template_path)

    # Prepare output file
    output_path = output_dir / f"Output_{run_id}.xlsx"

    # Load the template workbook
    template = openpyxl.load_workbook(template_path)

    # Ensure at least one sheet is visible
    if not any(sheet.sheet_state == 'visible' for sheet in template.worksheets):
        template.active.sheet_state = 'visible'

    # Write the output data to the specified sheet
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Write the output data to the specified sheet
        output_data.to_excel(
            writer,
            sheet_name='Output mapping',
            startrow=12,
            startcol=2,
            index=False,
            header=False
        )

    # Save the workbook
    template.save(output_path)

    # Save intermediate DataFrames to a separate Excel file for debugging
    debug_output_path = output_dir / f"Debug_{run_id}.xlsx"
    with pd.ExcelWriter(debug_output_path, engine='openpyxl') as debug_writer:
        market_risk_input.to_excel(debug_writer, sheet_name='Market Risk Input', index=False)
        tree_data.to_excel(debug_writer, sheet_name='Tree Data', index=False)
        correlation_data.to_excel(debug_writer, sheet_name='Correlation Data', index=False)
        data_id_values.to_excel(debug_writer, sheet_name='Data ID Values', index=False)
        output_data.to_excel(debug_writer, sheet_name='output_data', index=False)
        results.to_excel(debug_writer, sheet_name='Results', index=True)

    print(f"Debug file saved to: {debug_output_path}")


if __name__ == "__main__":
    # Run the main function with default run_id
    main()