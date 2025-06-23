import pandas as pd
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Initialize Supabase client
load_dotenv()
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)

def read_aggregation_tree(tree_id: str) -> pd.DataFrame:
    """
    Read aggregation tree data from Supabase.
    
    Args:
        tree_id (str): Aggregation tree identifier
    
    Returns:
        pd.DataFrame: Aggregation tree data
    """
    response = (supabase.table('aggregation_tree') # Tree only set up for market risk as of now
               .select('*')
               .eq('AGGREGATION_TREE_ID', tree_id)
               .execute())
    return pd.DataFrame(response.data)

def calculate_value(node_id, aggregation_tree, data_id_enriched):
    # Check if the value has already been calculated
    node_info = aggregation_tree[aggregation_tree["NODE_ID"] == node_id]

    if node_info.empty:
        return " "  # Node ID not found

    node = node_info.iloc[0]
    aggregation_method_cd = node["AGGREGATION_METHOD_CD"]

    # If the value is already calculated, return it
    if "VALUE" in node and pd.notnull(node["VALUE"]):
        return node["VALUE"]

    if aggregation_method_cd == "external":
        # Retrieve value from data_id_enriched
        value_row = data_id_enriched[data_id_enriched["DATA_ID"] == node_id]
        if not value_row.empty:
            return value_row["VALUE"].values[0]
        else:
            return "DATA_ID not found"

    # For non-external nodes, calculate values for child nodes
    child_nodes = aggregation_tree[aggregation_tree["PARENT_NODE_ID"] == node_id]

    if child_nodes.empty:
        return "Input insufficient"  # No child nodes

    # Recursive calculation for child nodes
    child_values = []
    for _, child in child_nodes.iterrows():
        child_value = calculate_value(
            child["NODE_ID"], aggregation_tree, data_id_enriched
        )
        if isinstance(child_value, str):  # If it's an error message
            return child_value
        child_values.append(child_value)

    # Apply the aggregation method
    if aggregation_method_cd == "sum":
        calculated_value = sum(child_values)
    elif aggregation_method_cd == "max":
        calculated_value = max(child_values)
    elif aggregation_method_cd == "min":
        calculated_value = min(child_values)
    elif aggregation_method_cd == "dnav":
        # Calculate base case values
        base_case_assets = sum(
            value
            for value, bs_type, scenario in zip(
                child_values, child_nodes["BS_TYPE"], child_nodes["SCENARIO"]
            )
            if bs_type == "ASSET" and scenario == "BC"
        )
        base_case_liabilities = sum(
            value
            for value, bs_type, scenario in zip(
                child_values, child_nodes["BS_TYPE"], child_nodes["SCENARIO"]
            )
            if bs_type == "LIAB" and scenario == "BC"
        )

        # Calculate shocked values
        shocked_assets = sum(
            value
            for value, bs_type, scenario in zip(
                child_values, child_nodes["BS_TYPE"], child_nodes["SCENARIO"]
            )
            if bs_type == "ASSET" and scenario == "SH"
        )
        shocked_liabilities = sum(
            value
            for value, bs_type, scenario in zip(
                child_values, child_nodes["BS_TYPE"], child_nodes["SCENARIO"]
            )
            if bs_type == "LIAB" and scenario == "SH"
        )

        # Final calculation for dnav
        calculated_value = max(0,((base_case_assets - base_case_liabilities) - (
            shocked_assets - shocked_liabilities)))
    elif aggregation_method_cd == "max_scen":

        max_scenario_base_id = aggregation_tree["MAX_SCENARIO_BASE"]
        master_child_nodes = aggregation_tree[aggregation_tree["PARENT_NODE_ID"] == max_scenario_base_id]
        master_child_values = []
        master_child_scneraios = []
        for _, child in master_child_nodes.iterrows():
            master_child_value = calculate_value(
                child["NODE_ID"], aggregation_tree, data_id_enriched
            )
            if isinstance(master_child_value, str):  # If it's an error message
                return master_child_value
            master_child_values.append(master_child_value)
        
        #master_child_scneraio = filter tree by master_child_nodes with largest value
        #Choose the maximum value from the master child nodes
        calculated_value = max(child_values)
    else:
        return "Method not defined"

    # Store the calculated value in the aggregation tree
    aggregation_tree.loc[aggregation_tree["NODE_ID"] == node_id, "VALUE"] = (
        calculated_value
    )
    return calculated_value


def aggregate_tree(aggregation_tree, data_id_enriched, aggregation_tree_id):
    # Step 1: Filter the aggregation tree for the specified aggregation_tree_id
    filtered_tree = aggregation_tree[
        aggregation_tree["AGGREGATION_TREE_ID"] == aggregation_tree_id
    ].copy()

    # Step 2: Initialize the VALUE column
    if 'VALUE' not in aggregation_tree.columns:
        aggregation_tree['VALUE'] = None  # Initialize the VALUE column


    # Step 3: Calculate values recursively for each node
    for index, row in filtered_tree.iterrows():
        node_id = row["NODE_ID"]
        filtered_tree.at[index, "VALUE"] = calculate_value(
            node_id, filtered_tree, data_id_enriched
        )

    return filtered_tree


# Example usage:
# aggregation_tree_df = pd.DataFrame({...})  # Your aggregation tree data
# data_id_enriched_df = pd.DataFrame({...})  # Your data id enriched data
# result = aggregate_tree(aggregation_tree_df, data_id_enriched_df, 'your_aggregation_tree_id')
