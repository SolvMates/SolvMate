import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from src.utils import input_interface


# class can be useful to other modules too
class SupabaseDataFrameReader:
    def __init__(self):
        load_dotenv()
        self.supabase: Client = create_client(
            os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY")
        )

    def read_from_supabase(self, table_name) -> pd.DataFrame:
        response = self.supabase.table(table_name).select("*").execute()
        data = response.data
        df_from_supabase = pd.DataFrame(data)
        return df_from_supabase


# class can be useful to other modules too
class VariablesInputValues:
    def __init__(self, input_data: pd.DataFrame):
        self.input_data = input_data

    def define_variable(self, data_id: str):
        variable_value = self.input_data.loc[
            self.input_data["DATA_ID"] == data_id, "VALUE"
        ].iloc[0]
        return variable_value

    def calculate_fx(self, input_data: pd.DataFrame) -> float:
        reporting_currency = self.define_variable("INFO_REPORT_CCY")
        individual_fx_flag = self.define_variable("INFO_FX_MANUAL_INPUT")
        if reporting_currency == "EUR":
            fx = 1
        else:
            if individual_fx_flag == "yes":
                fx = 0.88675  # Example value, replace with actual logic to get FX rate
            else:
                supabase_reader = SupabaseDataFrameReader()
                fx_data = supabase_reader.read_from_supabase("exchange_rates")
                if not fx_data.empty:
                    fx = fx_data.loc[
                        fx_data["TO_CURRENCY"] == reporting_currency,
                        "REGULATORY_RATE",  # TO DO: check if regulatory or spot rate
                    ].iloc[0]
                else:
                    raise ValueError(f"FX rate for {reporting_currency} not found.")

            if fx is None:
                raise ValueError(f"FX rate for {reporting_currency} not found.")
        return fx


class ManMadeMotorRiskCalculator:
    def __init__(self, risk_id: str, input_data: pd.DataFrame):
        self.risk_id = risk_id
        self.get_variable_value = VariablesInputValues(input_data)
        self.no_vehicles_above_24mln = self.get_variable_value.define_variable(
            "NL_MM_MOT_NO_ABOVE"
        )
        self.no_vehicles_below_24mln = self.get_variable_value.define_variable(
            "NL_MM_MOT_NO_BELOW"
        )
        self.reins_prem = self.get_variable_value.define_variable(
            "NL_MM_MOT_REINS_PREM"
        )
        self.risk_mitigation = self.get_variable_value.define_variable(
            "NL_MM_MOT_RM_EFFECT"
        )
        self.reporting_unit = self.get_variable_value.define_variable(
            "INFO_REPORT_UNIT"
        )
        self.fx = self.get_variable_value.calculate_fx("INFO_REPORT_CCY")

    def calculate_motor_risk(self) -> tuple:

        if self.no_vehicles_above_24mln > 0 or self.no_vehicles_below_24mln > 0:
            if self.reporting_unit != 0:
                minimum = 6000000 * self.fx / self.reporting_unit
                sqrt_factor = 50000 * self.fx / self.reporting_unit
            else:
                minimum = 6000000 * self.fx
                sqrt_factor = 50000 * self.fx

            motor_gross_scr = round(
                max(
                    minimum,
                    sqrt_factor
                    * np.sqrt(
                        self.no_vehicles_above_24mln
                        + 0.05 * self.no_vehicles_below_24mln
                        + 0.95 * min(self.no_vehicles_below_24mln, 20000)
                    ),
                ),
                2,
            )
            motor_net_scr = round(motor_gross_scr - self.risk_mitigation, 2)
        else:
            motor_gross_scr = 0
            motor_net_scr = 0

        return (motor_gross_scr, motor_net_scr)

    # TO DO: method for getting table: risk id | data_ id | value
    # method for getting all output values to fill QRT
    # fill output mapping file

    def scr_df(self) -> pd.DataFrame:
        scr_data = {
            "RISK_ID": self.risk_id,
            "DATA_ID": [
                "NL_MM_MOT_SCR_G",
                "NL_MM_MOT_SCR_N",
            ],
            "VALUE": [
                self.calculate_motor_risk()[0],
                self.calculate_motor_risk()[1],
            ],
        }
        return pd.DataFrame(scr_data)

    def qrt_values_df(self) -> pd.DataFrame:
        qrt_data = {
            "RISK_ID": self.risk_id,
            "DATA_ID": [
                "NL_MM_MOT_SCR_G",
                "NL_MM_MOT_RM_EFFECT",
                "NL_MM_MOT_SCR_N",
                "NL_MM_MOT_NO_ABOVE",
                "NL_MM_MOT_NO_BELOW",
                "NL_MM_MOT_REINS_PREM",
            ],
            "VALUE": [
                self.calculate_motor_risk()[0],
                self.risk_mitigation,
                self.calculate_motor_risk()[1],
                self.no_vehicles_above_24mln,
                self.no_vehicles_below_24mln,
                self.reins_prem,
            ],
        }
        return pd.DataFrame(qrt_data)


if __name__ == "__main__":

    supabase_data_importer = input_interface.SupabaseDataImporter()
    data_id_enriched = supabase_data_importer.run_import(
        "/python/SolvMate/input/12.06_SAS_Input_ManMade.xls",
        ["Basic input", "NL man-made"],
    )
    motor_risk = ManMadeMotorRiskCalculator(
        risk_id="MAN_MADE_MOTOR_RISK", input_data=data_id_enriched
    )

    motor_scr = motor_risk.scr_df()
    output_df = motor_risk.qrt_values_df()

    print(motor_scr)
    print(output_df)
