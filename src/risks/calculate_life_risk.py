from src.risks.calculate_risk import (
    InterestRateRiskCalculator,
    RiskCalculator,
    RiskCalculatorFactory,
    SpreadRiskCalculator,
    TypicalRiskCalculator,
)
from src.utils.input_interface import SupabaseDataImporter
from utils import aggregation_tree
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class LifeRiskCalculator:

    def __init__(self, risk_calculator: RiskCalculator):
        self._risk_calculator = risk_calculator

    def calculate_life_risk_all_subrisks(self, input_file: str) -> pd.DataFrame:
        """
        Calculate life risk by aggregating various life risk components.

        Args:
            input_file (str): Path to the input file containing life risk data.

        Returns:
            pd.DataFrame: Aggregated life risk results
        """
        # Load input data
        supabase_data_importer = SupabaseDataImporter()
        data_id_enriched_life = supabase_data_importer.run_import(
            input_file, ["LnH SLT UW"]
        )
        life_risks_list = [
            "LIFE_MOR",
            "LIFE_LON",
            "LIFE_DIS",
            "LIFE_LAP",
            "LIFE_EXP",
            "LIFE_REV",
            "LIFE_CAT",
            "LIFE",
        ]

        aggregation_tree_base_risk_list = []
        for risk in life_risks_list:
            aggregation_tree_base_risk_list.append(
                self._risk_calculator.calculate_risk(data_id_enriched_life, risk)
            )

        # Combine all life risk components into a single DataFrame
        aggregation_tree_life_all_risks = pd.concat(
            aggregation_tree_base_risk_list,
            ignore_index=True,
        )

        # Calculate diversification effects for life risk
        diversification_life_df = self._diversification_life_risk(
            aggregation_tree_life_all_risks
        )
        # Append diversification risk to the aggregated DataFrame
        aggregation_tree_life_all_risks = pd.concat(
            [aggregation_tree_life_all_risks, diversification_life_df],
            ignore_index=True,
        )

        return aggregation_tree_life_all_risks

    def _diversification_life_risk(
        self, aggregation_tree_enriched: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate diversification effects for life risk.

        Args:
            aggregation_tree_enriched: DataFrame containing all life risk components

        Returns:
            pd.DataFrame: DataFrame with diversification values
        """
        # List of data IDs - SCRs necessary to calculate diversifications
        data_id = [
            "LIFE_MOR_SCR_N",
            "LIFE_LON_SCR_N",
            "LIFE_DIS_SCR_N",
            "LIFE_LAP_SCR_N",
            "LIFE_EXP_SCR_N",
            "LIFE_REV_SCR_N",
            "LIFE_CAT_SCR_N",
            "LIFE_SCR_N",
            "LIFE_MOR_SCR_G",
            "LIFE_LON_SCR_G",
            "LIFE_DIS_SCR_G",
            "LIFE_LAP_SCR_G",
            "LIFE_EXP_SCR_G",
            "LIFE_REV_SCR_G",
            "LIFE_CAT_SCR_G",
            "LIFE_SCR_G",
        ]

        # Make dictionary {DATA_ID: VALUE} with data necessary for calculation
        values_series = pd.to_numeric(
            aggregation_tree_enriched.set_index("NODE_ID").loc[data_id, "VALUE"],
            errors="coerce",
        ).dropna()
        values_dict = values_series.to_dict()

        # Calculate value of diversification for LIFE nett and gross as a difference of total SCR and sum of all subrisks SCRs
        values_dict["LIFE_DIV_N"] = values_dict.get("LIFE_SCR_N", 0) - (
            values_dict.get("LIFE_MOR_SCR_N", 0)
            + values_dict.get("LIFE_LON_SCR_N", 0)
            + values_dict.get("LIFE_DIS_SCR_N", 0)
            + values_dict.get("LIFE_LAP_SCR_N", 0)
            + values_dict.get("LIFE_EXP_SCR_N", 0)
            + values_dict.get("LIFE_REV_SCR_N", 0)
            + values_dict.get("LIFE_CAT_SCR_N", 0)
        )
        values_dict["LIFE_DIV_G"] = values_dict.get("LIFE_SCR_G", 0) - (
            values_dict.get("LIFE_MOR_SCR_G", 0)
            + values_dict.get("LIFE_LON_SCR_G", 0)
            + values_dict.get("LIFE_DIS_SCR_G", 0)
            + values_dict.get("LIFE_LAP_SCR_G", 0)
            + values_dict.get("LIFE_EXP_SCR_G", 0)
            + values_dict.get("LIFE_REV_SCR_G", 0)
            + values_dict.get("LIFE_CAT_SCR_G", 0)
        )

        diversification_life_df = pd.DataFrame(
            {
                "AGGREGATION_TREE_ID": "LIFE",
                "NODE_ID": ["LIFE_DIV_N", "LIFE_DIV_G"],
                "PARENT_NODE_ID": "",
                "NODE_DESC": "",
                "AGGREGATION_METHOD": "",
                "MATRIX_ID": "",
                "MAX_SCENARIO_BASE": "",
                "BS_TYPE": "",
                "SCENARIO": "",
                "VALUE": [values_dict["LIFE_DIV_N"], values_dict["LIFE_DIV_G"]],
            }
        )

        return diversification_life_df
