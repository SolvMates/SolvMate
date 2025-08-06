import sys

sys.path.insert(0, "/workspaces/SolvMate")
import pandas as pd
import numpy as np
import os
import logging
from typing import Tuple, Dict, List, Optional
from dotenv import load_dotenv
from supabase import create_client, Client
from src.utils.input import get_dataframe, run_Import
from src.utils.get_Value import get_value, get_valueExt
from pathlib import Path


class CurRisk:

    def __init__(self):

        self.__inputColumns = None
        self.__localCurrency = None
        self.__lacTPAbsValShockUp = None
        self.__lacTPAbsValShockDown = None
        self.__lacTPRelGrossShockUp = None
        self.__lacTPRelGrossShockDown = None
        self.__assetFlag = None
        self.__liabFlag = None
        self.__currencyShocks = None
        self.__currrencyShockStd = 0.25
        self.__lacTPAbsValShockUp = 0.0
        self.__lacTPAbsValShockDown = 0.0
        self.__lacTPRelGrossShockUp = 0.0
        self.__lacTPRelGrossShockDown = 0.0

        # output is equelant to Column A: Y in the Excel kernel of sheet Currency
        self.output = pd.DataFrame(
            columns=[
                "ForeignCurrency",
                "Asset_Input",
                "Liab_Input",
                "AssetShockUp_Input",
                "LiabShockUpAfterLACTP_Input",
                "LiabShockUp_Input",
                "AssetShockDown_Input",
                "LiabShockDown_Input",
                "LiabShockDownAfterLACTP_Input",
                "RiskFactor",
                "ForeignCurrencyPeggedLocalCur",
                "AssetSCRGross",
                "LiabSCRGross",
                "AssetShockDown",
                "AssetShockUp",
                "LiabDownGross",
                "LiabUpGross",
                "SCRDownGross",
                "SCRUpGross",
                "LiabDownNet",
                "LiabUpNet",
                "SCRDownNet",
                "SCRUpNet",
                "RelevantShock",
            ]
        )
        for column in self.output.columns:
            if column not in [
                "ForeignCurrency",
                "RelevantShock",
                "ForeignCurrencyPeggedLocalCur",
            ]:
                self.output[column] = self.output[column].astype(float)

        # aggOutput is equelant to the output in the QRT
        self.aggOutput = pd.DataFrame(
            columns=[
                "Shock",
                "Assets",
                "Liabilities",
                "AssetsShocked",
                "LiabilitiesShockedNet",
                "LiabilitiesShockedGross",
            ]
        )
        for column in self.aggOutput.columns:
            if column not in ["Shock"]:
                self.aggOutput[column] = self.aggOutput[column].astype(float)

    def __readInput(self, input_file: str):

        # Initialize Supabase client
        load_dotenv()
        supabase: Client = create_client(
            os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY")
        )

        # Load input dataframe of input columns
        data_id_enriched = run_Import(input_file, ["CurrR"])
        data_id_enriched_Basic = run_Import(input_file, ["Basic input"])
        inputColumns = get_dataframe(data_id_enriched, "MARKET_FX")

        # For further calculations, empty fields get filled with a Null instead of carrying care of empty fields
        # The required columns of Input get handled in a global Error-Concept to treat it with an Error message.
        # It will not get checked in this file.

        pd.set_option("future.no_silent_downcasting", True)
        inputColumns = inputColumns.replace("", np.nan)
        inputColumns = inputColumns.fillna(0)
        inputColumns = inputColumns.infer_objects(copy=False)
        cols_to_convert = [
            col for col in inputColumns.columns if col != "FX_FOREIGN_CCY_"
        ]
        try:
            inputColumns[cols_to_convert] = inputColumns[cols_to_convert].astype(float)
        except Exception as e:
            raise ValueError(f"Conversion of inputColumns to float failed: {e}")
        self.__inputColumns = inputColumns

        # Load simple input data
        self.__localCurrency = get_value("FX_LOCAL_CCY", data_id_enriched)
        if self.__localCurrency is None:
            raise ValueError("Local currency not found in the CurrR sheet.")

        self.__lacTPAbsValShockUp = get_valueExt("FX_UP_LAC", data_id_enriched)
        self.__lacTPAbsValShockDown = get_valueExt("FX_DN_LAC", data_id_enriched)
        self.__lacTPRelGrossShockUp = get_valueExt("FX_UP_LAC_REL", data_id_enriched)
        self.__lacTPRelGrossShockDown = get_valueExt("FX_DN_LAC_REL", data_id_enriched)

        # print("FX_UP_LAC_REL:" + self.__lacTPRelGrossShockUp + " FX_DN_LAC_REL:" + self.__lacTPRelGrossShockDown)

        # Input Method
        inputMethod = get_value("INFO_CURR_ASSETS_MANUAL_INPUT", data_id_enriched_Basic)
        if inputMethod is None:
            raise ValueError(
                "Error: Input Method for currency risk not found in the Basic input sheet."
            )
        start_index = inputMethod.find(" ", 0)
        end_index = inputMethod.find("-", start_index)
        self.__assetFlag = inputMethod[start_index + 1 : end_index - 1]
        start_index = inputMethod.find("Liab: ", 0)
        self.__liabFlag = inputMethod[start_index + 6 :]

        print("assetFlag:" + self.__assetFlag + " liabFlag:" + self.__liabFlag)

        if not self.__assetFlag:
            raise ValueError(
                "Error: assetFlag must not be empty or unfilled. Check inputMethod for Currency Risk."
            )
        if not self.__liabFlag:  # Überprüft, ob assetFlag leer oder None ist
            raise ValueError(
                "Error: liabFlag must not be empty or unfilled. Check inputMethod for Currency Risk."
            )

        # Load currency shock percentage values
        currencyShocks_response = supabase.table("currency_shock").select("*").execute()
        self.__currencyShocks = pd.DataFrame(currencyShocks_response.data)
        if self.__currencyShocks.empty:
            raise ValueError(
                "Error: currency shock table of percentages could not be loaded or is empty."
            )

    # Main Function to calculate the market risk for foreign exchange
    def calculate(self, input_file: str):

        self.__readInput(input_file)
        self.__copyInputColumns()
        self.__calcRiskFactor()
        self.__calcGrossValues()
        self.__calcNetValues()
        self.__identifyRelevantShocks()
        self.__calcAggOutput()

    def __copyInputColumns(self):

        self.output["ForeignCurrency"] = self.__inputColumns["FX_FOREIGN_CCY_"]

        # For local currency there is no shock and values have to be set to 0
        for idx, row in self.output.iterrows():
            if row["ForeignCurrency"] == self.__localCurrency:
                self.output.at[idx, "Asset_Input"] = 0.0
                self.output.at[idx, "Liab_Input"] = 0.0
                self.output.at[idx, "AssetShockUp_Input"] = 0.0
                self.output.at[idx, "LiabShockUpAfterLACTP_Input"] = 0.0
                self.output.at[idx, "LiabShockUp_Input"] = 0.0
                self.output.at[idx, "AssetShockDown_Input"] = 0.0
                self.output.at[idx, "LiabShockDown_Input"] = 0.0
                self.output.at[idx, "LiabShockDownAfterLACTP_Input"] = 0.0
            else:
                if (
                    self.__assetFlag == "Manual BC+SH"
                    or self.__assetFlag == "Manual BC"
                ):
                    self.output.at[idx, "Asset_Input"] = self.__inputColumns.at[
                        idx, "FX_A_BC_"
                    ]
                else:
                    # ToDo: Add code for MEAG BC+SH and MEAG BC
                    self.output.at[idx, "Asset_Input"] = 0.0

                self.output.at[idx, "Liab_Input"] = self.__inputColumns.at[
                    idx, "FX_L_BC_"
                ]

                if self.__assetFlag == "Manual BC+SH":
                    self.output.at[idx, "AssetShockUp_Input"] = self.__inputColumns.at[
                        idx, "FX_A_UP_"
                    ]
                    self.output.at[idx, "AssetShockDown_Input"] = (
                        self.__inputColumns.at[idx, "FX_A_DN_"]
                    )
                else:
                    # ToDo: Add code for MEAG BC+SH
                    self.output.at[idx, "AssetShockUp_Input"] = 0.0
                    self.output.at[idx, "AssetShockDown_Input"] = 0.0

                if self.__liabFlag == "Manual BC+SH":
                    self.output.at[idx, "LiabShockUp_Input"] = self.__inputColumns.at[
                        idx, "FX_L_UP_B_"
                    ]
                    self.output.at[idx, "LiabShockUpAfterLACTP_Input"] = (
                        self.__inputColumns.at[idx, "FX_L_UP_A_"]
                    )
                    self.output.at[idx, "LiabShockDown_Input"] = self.__inputColumns.at[
                        idx, "FX_L_DN_B_"
                    ]
                else:
                    self.output.at[idx, "LiabShockUp_Input"] = 0.0
                    self.output.at[idx, "LiabShockUpAfterLACTP_Input"] = 0.0
                    self.output.at[idx, "LiabShockDown_Input"] = 0.0

                self.output.at[idx, "LiabShockDownAfterLACTP_Input"] = (
                    self.__inputColumns.at[idx, "FX_L_DN_A_"]
                )

    def __calcRiskFactor(self):

        # Boolean-Spalte erzeugen: True, wenn Wert in den Spaltennamen von currencyShocks vorkommt
        self.output["ForeignCurrencyPeggedLocalCur"] = self.output[
            "ForeignCurrency"
        ].apply(lambda x: x in self.__currencyShocks.columns)

        self.output["RiskFactor"] = 0.0
    
        for idx, row in self.output.iterrows():
            if row["ForeignCurrencyPeggedLocalCur"]:
                columnCur = self.output.at[idx,"ForeignCurrency"]
                
                self.output.at[idx, "RiskFactor"] = self.__currrencyShockStd
                
                # Iterate through the rows of __currencyShocks to find the matching currency 
                for idxShocks, rowShocks in self.__currencyShocks.iterrows():
                    if rowShocks["Currency"] == self.__localCurrency:
                        self.output.at[idx, "RiskFactor"] = rowShocks[columnCur]
                        break                 
            else:
                self.output.at[idx, "RiskFactor"] = self.__currrencyShockStd

    def __calcGrossValues(self):

        for idx, row in self.output.iterrows():

            if self.__assetFlag == "Manual BC+SH" or self.__assetFlag == "MEAG BC+SH":
                self.output.at[idx, "AssetSCRGross"] = 0.0
                self.output.at[idx, "AssetShockDown"] = self.output.at[
                    idx, "AssetShockDown_Input"
                ]
                self.output.at[idx, "AssetShockUp"] = self.output.at[
                    idx, "AssetShockUp_Input"
                ]
            else:
                self.output.at[idx, "AssetSCRGross"] = (
                    self.output.at[idx, "RiskFactor"]
                    * self.output.at[idx, "Asset_Input"]
                )
                self.output.at[idx, "AssetShockDown"] = (
                    self.output.at[idx, "Asset_Input"]
                    - self.output.at[idx, "AssetSCRGross"]
                )
                self.output.at[idx, "AssetShockUp"] = (
                    self.output.at[idx, "Asset_Input"]
                    + self.output.at[idx, "AssetSCRGross"]
                )

            if self.__liabFlag == "Manual BC+SH":
                self.output.at[idx, "LiabSCRGross"] = 0.0
                self.output.at[idx, "LiabDownGross"] = self.output.at[
                    idx, "LiabShockDown_Input"
                ]
                self.output.at[idx, "LiabUpGross"] = self.output.at[
                    idx, "LiabShockUp_Input"
                ]
            else:
                self.output.at[idx, "LiabSCRGross"] = (
                    self.output.at[idx, "RiskFactor"]
                    * self.output.at[idx, "Liab_Input"]
                )
                self.output.at[idx, "LiabDownGross"] = (
                    self.output.at[idx, "Liab_Input"]
                    - self.output.at[idx, "LiabSCRGross"]
                )
                self.output.at[idx, "LiabUpGross"] = (
                    self.output.at[idx, "Liab_Input"]
                    + self.output.at[idx, "LiabSCRGross"]
                )

            # SCR = Max (0, (Asset Basis -Liabilities Basis)-(Asset Shocked -Liabilities Shocked))
            self.output.at[idx, "SCRDownGross"] = max(
                0,
                (self.output.at[idx, "Asset_Input"] - self.output.at[idx, "Liab_Input"])
                - (
                    self.output.at[idx, "AssetShockDown"]
                    - self.output.at[idx, "LiabDownGross"]
                ),
            )
            self.output.at[idx, "SCRUpGross"] = max(
                0,
                (self.output.at[idx, "Asset_Input"] - self.output.at[idx, "Liab_Input"])
                - (
                    self.output.at[idx, "AssetShockUp"]
                    - self.output.at[idx, "LiabUpGross"]
                ),
            )

    def __calcNetValues(self):

        # Calculate net values
        # Net value = Gross value - Part of Lac TP
        for idx, row in self.output.iterrows():
            if self.__liabFlag == "Manual BC+SH":
                self.output.at[idx, "LiabDownNet"] = self.output.at[
                    idx, "LiabShockDownAfterLACTP_Input"
                ]
                self.output.at[idx, "LiabUpNet"] = self.output.at[
                    idx, "LiabShockUpAfterLACTP_Input"
                ]
            else:
                if self.output["SCRDownGross"].sum() == 0:
                    self.output.at[idx, "LiabDownNet"] = self.output.at[
                        idx, "LiabDownGross"
                    ]
                else:
                    self.output.at[idx, "LiabDownNet"] = (
                        self.output.at[idx, "LiabDownGross"]
                        - self.__lacTPAbsValShockDown
                        * self.output.at[idx, "SCRDownGross"]
                        / self.output["SCRDownGross"].sum()
                        - self.__lacTPRelGrossShockDown
                        * self.output.at[idx, "SCRDownGross"]
                    )

                if self.output["SCRUpGross"].sum() == 0:
                    self.output.at[idx, "LiabUpNet"] = self.output.at[
                        idx, "LiabUpGross"
                    ]
                else:
                    self.output.at[idx, "LiabUpNet"] = (
                        self.output.at[idx, "LiabUpGross"]
                        - self.__lacTPAbsValShockUp
                        * self.output.at[idx, "SCRUpGross"]
                        / self.output["SCRUpGross"].sum()
                        - self.__lacTPRelGrossShockUp
                        * self.output.at[idx, "SCRUpGross"]
                    )

            # SCR = Max (0, (Asset Basis -Liabilities Basis)-(Asset Shocked -Liabilities Shocked Net))
            self.output.at[idx, "SCRDownNet"] = max(
                0,
                (self.output.at[idx, "Asset_Input"] - self.output.at[idx, "Liab_Input"])
                - (
                    self.output.at[idx, "AssetShockDown"]
                    - self.output.at[idx, "LiabDownNet"]
                ),
            )
            self.output.at[idx, "SCRUpNet"] = max(
                0,
                (self.output.at[idx, "Asset_Input"] - self.output.at[idx, "Liab_Input"])
                - (
                    self.output.at[idx, "AssetShockUp"]
                    - self.output.at[idx, "LiabUpNet"]
                ),
            )

    def __identifyRelevantShocks(self):

        # Find relevant shocks (Up or Down)
        for idx, row in self.output.iterrows():
            if self.output.at[idx, "SCRDownNet"] == self.output.at[idx, "SCRUpNet"]:
                if (
                    self.output.at[idx, "SCRUpGross"]
                    < self.output.at[idx, "SCRDownGross"]
                ):
                    self.output.at[idx, "RelevantShock"] = "Downward"
                else:
                    self.output.at[idx, "RelevantShock"] = "Upward"
            else:
                if self.output.at[idx, "SCRUpNet"] < self.output.at[idx, "SCRDownNet"]:
                    self.output.at[idx, "RelevantShock"] = "Downward"
                else:
                    self.output.at[idx, "RelevantShock"] = "Upward"

    def __calcAggOutput(self):

        # Aggregate values selected by RelevantShock
        filtered_output = self.output[self.output["RelevantShock"] == "Upward"]

        self.aggOutput.loc[1, "Shock"] = "Upward"
        self.aggOutput.loc[1, "Assets"] = filtered_output["Asset_Input"].sum()
        self.aggOutput.loc[1, "Liabilities"] = filtered_output["Liab_Input"].sum()
        self.aggOutput.loc[1, "AssetsShocked"] = filtered_output["AssetShockUp"].sum()
        self.aggOutput.loc[1, "LiabilitiesShockedNet"] = filtered_output[
            "LiabUpNet"
        ].sum()
        self.aggOutput.loc[1, "SCRNet"] = filtered_output["SCRUpNet"].sum()
        self.aggOutput.loc[1, "LiabilitiesShockedGross"] = filtered_output[
            "LiabUpGross"
        ].sum()
        self.aggOutput.loc[1, "SCRGross"] = filtered_output["SCRUpGross"].sum()

        filtered_output = self.output[self.output["RelevantShock"] == "Downward"]

        self.aggOutput.loc[2, "Shock"] = "Downward"
        self.aggOutput.loc[2, "Assets"] = filtered_output["Asset_Input"].sum()
        self.aggOutput.loc[2, "Liabilities"] = filtered_output["Liab_Input"].sum()
        self.aggOutput.loc[2, "AssetsShocked"] = filtered_output["AssetShockDown"].sum()
        self.aggOutput.loc[2, "LiabilitiesShockedNet"] = filtered_output[
            "LiabDownNet"
        ].sum()
        self.aggOutput.loc[2, "SCRNet"] = filtered_output["SCRDownNet"].sum()
        self.aggOutput.loc[2, "LiabilitiesShockedGross"] = filtered_output[
            "LiabDownGross"
        ].sum()
        self.aggOutput.loc[2, "SCRGross"] = filtered_output["SCRDownGross"].sum()


if __name__ == "__main__":
    input_file = Path("/workspaces/SolvMate/input/02.10_SAS_Input_CurrR.xls")

    curRisk = CurRisk()
    curRisk.calculate(str(input_file))
    output_path = Path.cwd() / "outputs"

    curRisk.output.to_excel(str(output_path / "Output_CurrR_2_10.xlsx"), index=False)
    curRisk.aggOutput.to_excel(str(output_path / "AggOutput_CurrR_2_10.xlsx"), index=False)
    print(curRisk.aggOutput)