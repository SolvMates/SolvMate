import pandas as pd
from abc import ABC, abstractmethod
from dependency_injector import containers, providers
from dependency_injector.wiring import inject, Provide
from typing import List

from utils import aggregation_tree


class CalculateRiskInterface(ABC):

    @abstractmethod
    def applies_to(self) -> List[str]:
        pass

    @abstractmethod
    def calculate_risk(
        self, data_id_enriched: pd.DataFrame, risk_type: str
    ) -> pd.DataFrame:
        pass


class TypicalRiskCalculator(CalculateRiskInterface):

    def applies_to(self) -> List[str]:
        return [
            "MARKET_EQU",
            "MARKET_PRO",
            "MARKET",
            "HSLT_MOR",
            "HSLT_LON",
            "HSLT_DIS",
            "HSLT_LAP",
            "HSLT_EXP",
            "HSLT_REV",
            "HSLT",
            "LIFE_MOR",
            "LIFE_LON",
            "LIFE_DIS",
            "LIFE_LAP",
            "LIFE_EXP",
            "LIFE_REV",
            "LIFE_CAT",
            "LIFE",
        ]

    def calculate_risk(
        self, data_id_enriched: pd.DataFrame, risk_type: str
    ) -> pd.DataFrame:
        # Read aggregation tree for life risk
        aggregation_tree = aggregation_tree.read_aggregation_tree(risk_type)

        # Aggregate the tree with the enriched data
        aggregation_tree_enriched = aggregation_tree.aggregate_tree(
            aggregation_tree, data_id_enriched, risk_type
        )

        return aggregation_tree_enriched


class InterestRateRiskCalculator(CalculateRiskInterface):

    def applies_to(self) -> List[str]:
        return [
            "MARKET_INT",
        ]

    def calculate_risk(
        self, data_id_enriched: pd.DataFrame, risk_type: str
    ) -> pd.DataFrame:
        # Read aggregation tree for interest rate risk
        aggregation_tree_market_ir = aggregation_tree.read_aggregation_tree(risk_type)

        # Aggregate the tree with the enriched data
        aggregation_tree_market_ir_enriched = aggregation_tree.aggregate_tree(
            aggregation_tree_market_ir, data_id_enriched, risk_type
        )

        # For the output liabilities subordinated loans are added to liabilities w/o sub loans
        sub_loan_value = data_id_enriched.loc[
            data_id_enriched["DATA_ID"] == "MKT_INT_SUB_LOAN_L_BC", "VALUE"
        ].sum()
        aggregation_tree_market_ir_enriched.loc[
            aggregation_tree_market_ir_enriched["NODE_ID"] == "MKT_INT_L_BC", "VALUE"
        ] += sub_loan_value

        sub_loan_dn_value = data_id_enriched.loc[
            data_id_enriched["DATA_ID"] == "MKT_INT_SUB_LOAN_DN_L_SH_N", "VALUE"
        ].sum()
        aggregation_tree_market_ir_enriched.loc[
            aggregation_tree_market_ir_enriched["NODE_ID"] == "MKT_INT_DN_L_SH_N",
            "VALUE",
        ] += sub_loan_dn_value
        aggregation_tree_market_ir_enriched.loc[
            aggregation_tree_market_ir_enriched["NODE_ID"] == "MKT_INT_DN_L_SH_G",
            "VALUE",
        ] += sub_loan_dn_value

        sub_loan_up_value = data_id_enriched.loc[
            data_id_enriched["DATA_ID"] == "MKT_INT_SUB_LOAN_UP_L_SH_N", "VALUE"
        ].sum()
        aggregation_tree_market_ir_enriched.loc[
            aggregation_tree_market_ir_enriched["NODE_ID"] == "MKT_INT_UP_L_SH_N",
            "VALUE",
        ] += sub_loan_up_value
        aggregation_tree_market_ir_enriched.loc[
            aggregation_tree_market_ir_enriched["NODE_ID"] == "MKT_INT_UP_L_SH_G",
            "VALUE",
        ] += sub_loan_up_value

        return aggregation_tree_market_ir_enriched


class SpreadRiskCalculator(CalculateRiskInterface):

    def applies_to(self) -> List[str]:
        return [
            "MARKET_SPR",
        ]

    def calculate_risk(
        self, data_id_enriched: pd.DataFrame, risk_type: str
    ) -> pd.DataFrame:
        # Read aggregation tree for spread risk
        aggregation_tree_market_spr = aggregation_tree.read_aggregation_tree(risk_type)

        # Aggregate the tree with the enriched data
        aggregation_tree_market_spr_enriched = aggregation_tree.aggregate_tree(
            aggregation_tree_market_spr, data_id_enriched, risk_type
        )

        # Update specific scr values
        scr_to_update = [
            "MKT_SPR_BD_QI_CORP_SCR_N",
            "MKT_SPR_BD_QI_CORP_SCR_G",
            "MKT_SPR_BD_QI_NONCORP_SCR_N",
            "MKT_SPR_BD_QI_NONCORP_SCR_G",
            "MKT_SPR_BD_OT_SCR_N",
            "MKT_SPR_BD_OT_SCR_G",
            "MKT_SPR_SE_S_STS_SCR_N",
            "MKT_SPR_SE_S_STS_SCR_G",
            "MKT_SPR_SE_NS_STS_SCR_N",
            "MKT_SPR_SE_NS_STS_SCR_G",
            "MKT_SPR_SE_R_SCR_N",
            "MKT_SPR_SE_R_SCR_G",
            "MKT_SPR_SE_OTH_SCR_N",
            "MKT_SPR_SE_OTH_SCR_G",
            "MKT_SPR_SE_TT1_SCR_N",
            "MKT_SPR_SE_TT1_SCR_G",
            "MKT_SPR_SE_G_STS_SCR_N",
            "MKT_SPR_SE_G_STS_SCR_G",
        ]  # list of nodes to update

        for node in scr_to_update:
            # Selecting liabilities for SCRs from, BS_TYPE == 'LIAB'
            relevant_liab = (
                aggregation_tree_market_spr_enriched["PARENT_NODE_ID"] == node
            ) & (aggregation_tree_market_spr_enriched["BS_TYPE"] == "LIAB")
            # Checking if found liabilities are empty - if yes, set SCR value also empty
            if (
                aggregation_tree_market_spr_enriched.loc[relevant_liab, "VALUE"] == ""
            ).all():  # empty cells are recognised as empty strings
                relevant_node = aggregation_tree_market_spr_enriched["NODE_ID"] == node
                aggregation_tree_market_spr_enriched.loc[relevant_node, "VALUE"] = (
                    " "  # set empty string to the node value
                )

        return aggregation_tree_market_spr_enriched


class RiskCalculatorFactory:

    def __init__(self, calculators: List[CalculateRiskInterface]):
        self.calculators = calculators

    def get_calculator(self, risk_type: str) -> CalculateRiskInterface:
        calculators = [
            calculators
            for calculators in self.calculators
            if risk_type in calculators.applies_to()
        ]
        return calculators[0]


class RiskCalculator:

    def __init__(self, factory: RiskCalculatorFactory):
        self.factory = factory

    def calculate_risk(self, data_id_enriched: pd.DataFrame, risk_type: str):
        calculator = self.factory.get_calculator(risk_type)
        return calculator.calculate_risk(data_id_enriched, risk_type)
