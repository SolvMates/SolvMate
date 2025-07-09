import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.utils.aggregation_tree import AggregationTree
from utils import input


# HSLT MORTALITY RISK
def calculate_hslt_mortality_risk(data_id_enriched: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate hslt mortality risk.

    Args:
        data_id_enriched: data frame containing enriched input data
    """
    # Read aggregation tree for hslt risk
    aggregation_tree = AggregationTree()
    aggregation_tree_hslt_mor = aggregation_tree.read_aggregation_tree("HSLT_MOR")

    # Aggregate the tree with the enriched data
    aggregation_tree_hslt_mor_enriched = aggregation_tree.aggregate_tree(
        aggregation_tree_hslt_mor, data_id_enriched, "HSLT_MOR"
    )

    return aggregation_tree_hslt_mor_enriched


# HSLT LONGEVITY RISK
def calculate_hslt_longevity_risk(data_id_enriched: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate hslt mortality risk.

    Args:
        data_id_enriched: data frame containing enriched input data
    """
    # Read aggregation tree for hslt risk
    aggregation_tree = AggregationTree()
    aggregation_tree_hslt_lon = aggregation_tree.read_aggregation_tree("HSLT_LON")

    # Aggregate the tree with the enriched data
    aggregation_tree_hslt_lon_enriched = aggregation_tree.aggregate_tree(
        aggregation_tree_hslt_lon, data_id_enriched, "HSLT_LON"
    )

    return aggregation_tree_hslt_lon_enriched


# HSLT DISABILITY-MORBIDITY RISK
def calculate_hslt_disability_risk(data_id_enriched: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate hslt disability risk.

    Args:
        data_id_enriched: data frame containing enriched input data
    """
    # Read aggregation tree for hslt risk
    aggregation_tree = AggregationTree()
    aggregation_tree_hslt_dis = aggregation_tree.read_aggregation_tree("HSLT_DIS")

    # Aggregate the tree with the enriched data
    aggregation_tree_hslt_dis_enriched = aggregation_tree.aggregate_tree(
        aggregation_tree_hslt_dis, data_id_enriched, "HSLT_DIS"
    )

    return aggregation_tree_hslt_dis_enriched


# hslt LAPSE RISK
def calculate_hslt_lapse_risk(data_id_enriched: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate hslt lapse risk.

    Args:
        data_id_enriched: data frame containing enriched input data
    """
    # Read aggregation tree for hslt risk
    aggregation_tree = AggregationTree()
    aggregation_tree_hslt_lap = aggregation_tree.read_aggregation_tree("HSLT_LAP")

    # Aggregate the tree with the enriched data
    aggregation_tree_hslt_lap_enriched = aggregation_tree.aggregate_tree(
        aggregation_tree_hslt_lap, data_id_enriched, "HSLT_LAP"
    )

    return aggregation_tree_hslt_lap_enriched


# HSLT EXPENSE RISK
def calculate_hslt_expense_risk(data_id_enriched: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate hslt expense risk.

    Args:
        data_id_enriched: data frame containing enriched input data
    """
    # Read aggregation tree for hslt risk
    aggregation_tree = AggregationTree()
    aggregation_tree_hslt_exp = aggregation_tree.read_aggregation_tree("HSLT_EXP")

    # Aggregate the tree with the enriched data
    aggregation_tree_hslt_exp_enriched = aggregation_tree.aggregate_tree(
        aggregation_tree_hslt_exp, data_id_enriched, "HSLT_EXP"
    )

    return aggregation_tree_hslt_exp_enriched


# HSLT REVISION RISK
def calculate_hslt_revision_risk(data_id_enriched: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate hslt mrevision risk.

    Args:
        data_id_enriched: data frame containing enriched input data
    """
    # Read aggregation tree for hslt risk
    aggregation_tree = AggregationTree()
    aggregation_tree_hslt_rev = aggregation_tree.read_aggregation_tree("HSLT_REV")

    # Aggregate the tree with the enriched data
    aggregation_tree_hslt_rev_enriched = aggregation_tree.aggregate_tree(
        aggregation_tree_hslt_rev, data_id_enriched, "HSLT_REV"
    )

    return aggregation_tree_hslt_rev_enriched


# TOTAL HSLT RISK
def calculate_total_hslt_risk(data_id_enriched: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate hslt risk.

    Args:
        data_id_enriched: data frame containing enriched input data
    """
    # Read aggregation tree for hslt risk
    aggregation_tree = AggregationTree()
    aggregation_tree_hslt = aggregation_tree.read_aggregation_tree("HSLT")

    # Aggregate the tree with the enriched data
    aggregation_tree_hslt_enriched = aggregation_tree.aggregate_tree(
        aggregation_tree_hslt, data_id_enriched, "HSLT"
    )

    return aggregation_tree_hslt_enriched


def diversification_hslt_risk(aggregation_tree_enriched: pd.DataFrame) -> pd.DataFrame:

    # List of data IDs - SCRs nessessary to calculate diversifications
    data_id = [
        "HSLT_MOR_SCR_N",
        "HSLT_LON_SCR_N",
        "HSLT_DIS_SCR_N",
        "HSLT_LAP_SCR_N",
        "HSLT_EXP_SCR_N",
        "HSLT_REV_SCR_N",
        "HSLT_SCR_N",
        "HSLT_MOR_SCR_G",
        "HSLT_LON_SCR_G",
        "HSLT_DIS_SCR_G",
        "HSLT_LAP_SCR_G",
        "HSLT_EXP_SCR_G",
        "HSLT_REV_SCR_G",
        "HSLT_SCR_G",
    ]

    # Make dictionary {DATA_ID: VALUE} with data necessary for calculation
    values_series = pd.to_numeric(
        aggregation_tree_enriched.set_index("NODE_ID").loc[data_id, "VALUE"],
        errors="coerce",
    ).dropna()
    values_dict = values_series.to_dict()

    # Calculate value of diversification for HSLT nett and gross as a difference of total SCR and sum of all subrisks SCRs
    values_dict["HSLT_DIV_N"] = values_dict.get("HSLT_SCR_N", 0) - (
        values_dict.get("HSLT_MOR_SCR_N", 0)
        + values_dict.get("HSLT_LON_SCR_N", 0)
        + values_dict.get("HSLT_DIS_SCR_N", 0)
        + values_dict.get("HSLT_LAP_SCR_N", 0)
        + values_dict.get("HSLT_EXP_SCR_N", 0)
        + values_dict.get("HSLT_REV_SCR_N", 0)
    )
    values_dict["HSLT_DIV_G"] = values_dict.get("HSLT_SCR_G", 0) - (
        values_dict.get("HSLT_MOR_SCR_G", 0)
        + values_dict.get("HSLT_LON_SCR_G", 0)
        + values_dict.get("HSLT_DIS_SCR_G", 0)
        + values_dict.get("HSLT_LAP_SCR_G", 0)
        + values_dict.get("HSLT_EXP_SCR_G", 0)
        + values_dict.get("HSLT_REV_SCR_G", 0)
    )

    diversification_hslt_df = pd.DataFrame(
        {
            "AGGREGATION_TREE_ID": "HSLT",
            "NODE_ID": ["HSLT_DIV_N", "HSLT_DIV_G"],
            "PARENT_NODE_ID": "",
            "NODE_DESC": "",
            "AGGREGATION_METHOD": "",
            "MATRIX_ID": "",
            "MAX_SCENARIO_BASE": "",
            "BS_TYPE": "",
            "SCENARIO": "",
            "VALUE": [values_dict["HSLT_DIV_N"], values_dict["HSLT_DIV_G"]],
        }
    )

    return diversification_hslt_df


def calculate_hslt_risk_all_subrisks(input_file: str) -> pd.DataFrame:
    """
    Calculate hslt risk by aggregating various hslt risk components.

    Args:
        input_file (str): Path to the input file containing hslt risk data.

    Returns:
        pd.DataFrame: Aggregated hslt risk results
    """
    # Load input data
    data_id_enriched_hslt = input.run_Import(input_file, ["LnH SLT UW"])

    # Calculate individual hslt subrisks
    aggregation_tree_hslt_mor_enriched = calculate_hslt_mortality_risk(
        data_id_enriched_hslt
    )
    aggregation_tree_hslt_lon_enriched = calculate_hslt_longevity_risk(
        data_id_enriched_hslt
    )
    aggregation_tree_hslt_dis_enriched = calculate_hslt_disability_risk(
        data_id_enriched_hslt
    )
    aggregation_tree_hslt_lap_enriched = calculate_hslt_lapse_risk(
        data_id_enriched_hslt
    )
    aggregation_tree_hslt_exp_enriched = calculate_hslt_expense_risk(
        data_id_enriched_hslt
    )
    aggregation_tree_hslt_rev_enriched = calculate_hslt_revision_risk(
        data_id_enriched_hslt
    )
    aggregation_tree_hslt_total_enriched = calculate_total_hslt_risk(
        data_id_enriched_hslt
    )

    # Combine all hslt risk components into a single DataFrame
    aggregation_tree_hslt_all_risks = pd.concat(
        [
            aggregation_tree_hslt_mor_enriched,
            aggregation_tree_hslt_lon_enriched,
            aggregation_tree_hslt_dis_enriched,
            aggregation_tree_hslt_lap_enriched,
            aggregation_tree_hslt_exp_enriched,
            aggregation_tree_hslt_rev_enriched,
            aggregation_tree_hslt_total_enriched,
        ],
        ignore_index=True,
    )

    diversification_hslt_df = diversification_hslt_risk(aggregation_tree_hslt_all_risks)

    # Append diversification risk to the aggregated DataFrame
    aggregation_tree_hslt_all_risks = pd.concat(
        [aggregation_tree_hslt_all_risks, diversification_hslt_df], ignore_index=True
    )

    return aggregation_tree_hslt_all_risks
