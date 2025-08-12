import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from src.utils import input_interface


class SupabaseDataFrameReader:
    def __init__(self):
        load_dotenv()
        self.supabase: Client = create_client(
            os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY")
        )

    def read_from_supabase(self, table_name) -> pd.DataFrame:
        response = self.supabase.table(table_name).select("*").execute()
        data = response.data
        df_supabase = pd.DataFrame(data)
        return df_supabase


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
                fx = 0.88675  # just example, replace with actual logic to get FX rate
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


class ManMadeRiskCalculator:
    def __init__(self, input_data: pd.DataFrame, risk_id: str):
        self.risk_id = risk_id
        self.input_data = input_data
        self.get_variable_value = VariablesInputValues(input_data)
        self.fx = self.get_variable_value.calculate_fx("INFO_REPORT_CCY")

    def loss(
        self, sum_insured_gross: list, sum_insured_net: list, threshold: float = None
    ) -> tuple:

        total_sum_insured_gross = sum(sum_insured_gross)
        total_sum_insured_net = sum(sum_insured_net)

        if threshold is not None and total_sum_insured_gross > threshold:
            total_sum_insured_gross = 0
            total_sum_insured_net = 0

        return total_sum_insured_gross, total_sum_insured_net

    def risk_mitigation(
        self, loss_g: float, loss_n: float, reins_prem: float = None
    ) -> float:
        if reins_prem is not None:
            return loss_g - loss_n - reins_prem
        else:
            return loss_g - loss_n

    def calculate_scr_net(
        self, scr_g: float, mitigation_incl_reinst_prem: float
    ) -> float:
        return (
            round(max(scr_g - mitigation_incl_reinst_prem, 0), 2) if scr_g != 0 else 0
        )

    def diversification(
        self, sub_scr_g: list, sub_scr_n: list, total_scr_g: float, total_scr_n: float
    ) -> tuple:
        div_gross = total_scr_g - sum(sub_scr_g)
        div_net = total_scr_n - sum(sub_scr_n)
        return div_gross, div_net

    def scr_df(self) -> pd.DataFrame:
        scr_data = {
            "RISK_ID": self.risk_id,
            "DATA_ID": [self.risk_id + "SCR_G", self.risk_id + "SCR_N"],
            "VALUE": [self.calculate_scr_gross(), self.calculate_scr_net()],
        }

        return pd.DataFrame(scr_data)


class ManMadeMotorRiskCalculator(ManMadeRiskCalculator):
    def __init__(self, input_data: pd.DataFrame, risk_id: str):
        super().__init__(input_data, risk_id)

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

    def results_df(self) -> pd.DataFrame:
        gross_scr = self.calculate_scr_gross()
        net_scr = self.calculate_scr_net(gross_scr, self.risk_mitigation)
        total_risk_mitigation = self.risk_mitigation + self.reins_prem

        results = {
            "RISK_ID": self.risk_id,
            "DATA_ID": [
                "NL_MM_MOT_SCR_G",
                "NL_MM_MOT_SCR_N",
                "NL_MM_MOT_RM_EFFECT",
                "NL_MM_MOT_TOTAL_RM",
                "NL_MM_MOT_REINS_PREM",
                "NL_MM_MOT_NO_ABOVE",
                "NL_MM_MOT_NO_BELOW",
            ],
            "VALUE": [
                gross_scr,
                net_scr,
                self.risk_mitigation,
                total_risk_mitigation,
                self.reins_prem,
                self.no_vehicles_above_24mln,
                self.no_vehicles_below_24mln,
            ],
        }

        return pd.DataFrame(results)

    def calculate_scr_gross(self) -> float:

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
        else:
            motor_gross_scr = 0

        return motor_gross_scr


class ManMadeAviationRiskCalculator(ManMadeRiskCalculator):
    def __init__(self, input_data: pd.DataFrame, risk_id: str):
        super().__init__(input_data, risk_id)
        self.hull_si_gross = self.get_variable_value.define_variable(
            "NL_MM_AVI_SI_HULL_G"
        )
        self.hull_si_net = self.get_variable_value.define_variable(
            "NL_MM_AVI_SI_HULL_N"
        )
        self.liability_si_gross = self.get_variable_value.define_variable(
            "NL_MM_AVI_SI_LIAB_G"
        )
        self.liability_si_net = self.get_variable_value.define_variable(
            "NL_MM_AVI_SI_LIAB_N"
        )
        self.reins_prem = self.get_variable_value.define_variable(
            "NL_MM_AVI_REINS_PREM"
        )
        self.aircraft_name = self.get_variable_value.define_variable("NL_MM_AVI_NM")

    def calculate_scr_gross(
        self,
    ) -> float:
        scr_gross = self.loss(
            [self.hull_si_gross, self.liability_si_gross],
            [self.hull_si_net, self.liability_si_net],
        )[0]
        return round(scr_gross, 2)

    def results_df(self) -> pd.DataFrame:
        scr_gross = self.calculate_scr_gross()
        loss_net = self.loss(
            [self.hull_si_gross, self.liability_si_gross],
            [self.hull_si_net, self.liability_si_net],
        )[1]
        risk_mitigation = self.risk_mitigation(scr_gross, loss_net)
        risk_mitigation_incl_reinst = risk_mitigation - self.reins_prem
        scr_net = self.calculate_scr_net(scr_gross, risk_mitigation_incl_reinst)

        results = {
            "RISK_ID": self.risk_id,
            "DATA_ID": [
                "NL_MM_AVI_SCR_G",
                "NL_MM_AVI_SCR_N",
                "NL_MM_AVI_RM",
                "NL_MM_AVI_RM_INCL_REINST",
                "NL_MM_AVI_REINS_PREM",
                "NL_MM_AVI_SI_HULL_G",
                "NL_MM_AVI_SI_LIAB_G",
            ],
            "VALUE": [
                scr_gross,
                scr_net,
                risk_mitigation,
                risk_mitigation_incl_reinst,
                self.reins_prem,
                self.hull_si_gross,
                self.liability_si_gross,
            ],
        }

        return pd.DataFrame(results)


class ManMadeFireRiskCalculator(ManMadeRiskCalculator):
    def __init__(self, input_data: pd.DataFrame, risk_id: str):
        super().__init__(input_data, risk_id)
        self.si_gross = self.get_variable_value.define_variable("NL_MM_FIR_SI_G")
        self.si_net = self.get_variable_value.define_variable("NL_MM_FIR_SI_N")
        self.reins_prem = self.get_variable_value.define_variable(
            "NL_MM_FIR_REINS_PREM"
        )
        self.simplification = self.get_variable_value.define_variable("NL_MM_FIR_SIMPL")

    def calculate_scr_gross(self) -> float:
        proportion_factor = 1
        scr_gross = self.si_gross * proportion_factor
        return round(scr_gross, 2)

    def results_df(self) -> pd.DataFrame:
        scr_gross = self.calculate_scr_gross()
        loss_net = self.loss([self.si_gross], [self.si_net])[1]
        risk_mitigation = self.risk_mitigation(scr_gross, loss_net, self.reins_prem)
        risk_mitigation_incl_reinst = risk_mitigation - self.reins_prem
        scr_net = self.calculate_scr_net(scr_gross, risk_mitigation_incl_reinst)

        results = {
            "RISK_ID": self.risk_id,
            "DATA_ID": [
                "NL_MM_FIR_SCR_G",
                "NL_MM_FIR_SCR_N",
                "NL_MM_FIR_RM",
                "NL_MM_FIR_RM_INCL_REINST",
                "NL_MM_FIR_REINS_PREM",
                "NL_MM_FIR_SI_G",
            ],
            "VALUE": [
                scr_gross,
                scr_net,
                risk_mitigation,
                risk_mitigation_incl_reinst,
                self.reins_prem,
                self.si_gross,
            ],
        }

        return pd.DataFrame(results)


if __name__ == "__main__":

    supabase_data_importer = input_interface.SupabaseDataImporter()
    data_id_enriched = supabase_data_importer.run_import(
        "/python/SolvMate/input/12.06_SAS_Input_ManMade.xls",
        ["Basic input", "NL man-made"],
    )
    motor_risk = ManMadeMotorRiskCalculator(
        risk_id="MAN_MADE_MOT_RISK", input_data=data_id_enriched
    )
    print(motor_risk.results_df())
