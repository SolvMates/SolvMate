import pandas as pd
import numpy as np

from src.utils import input_interface


class VariablesInputValues:
    def define_variable(self, input_data: pd.DataFrame, data_id_list: list) -> list:
        variable_values = []

        for data_id in data_id_list:
            filtered_value = input_data.loc[input_data["DATA_ID"] == data_id, "VALUE"]
            if filtered_value.empty:
                print(
                    f"Warning: Value for DATA_ID '{data_id}' not found in input_data. Setting as NaN."
                )
                variable_values.append(np.nan)  # or use None if you prefer
            else:
                variable_values.append(filtered_value.iloc[0])
        if len(variable_values) == 1:
            return variable_values[0]

        return variable_values

    def calculate_fx(self, input_data: pd.DataFrame, fx_data: pd.DataFrame) -> float:
        reporting_currency = self.define_variable(input_data, ["INFO_REPORT_CCY"])
        individual_fx_flag = self.define_variable(input_data, ["INFO_FX_MANUAL_INPUT"])
        if reporting_currency == "EUR":
            fx = 1
        else:
            if individual_fx_flag == "yes":
                fx = 0.88675  # just example, replace with actual logic to get FX rate there will be something using input_data
            else:

                if not fx_data.empty:
                    fx = fx_data.loc[
                        fx_data["TO_CURRENCY"] == reporting_currency, "REGULATORY_RATE"
                    ].iloc[0]
                else:
                    raise ValueError(f"FX rate for {reporting_currency} not found.")

            if fx is None:
                raise ValueError(f"FX rate for {reporting_currency} not found.")
        return fx


class ManMadeRiskCalculator:

    def calculate(self, input_data: pd.DataFrame, risk_id: str):
        # TO DO
        return None

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

    def results_df(
        self, risk_id: str, data_id_list: list, values_list: list
    ) -> pd.DataFrame:
        scr_data = {
            "RISK_ID": risk_id,
            "DATA_ID": data_id_list,
            "VALUE": values_list,
        }

        return pd.DataFrame(scr_data)


class ManMadeMotorRiskCalculator(ManMadeRiskCalculator):

    def calculate(self, input_data: pd.DataFrame, fx_data: pd.DataFrame):
        get_variable_value = VariablesInputValues()
        fx = get_variable_value.calculate_fx(input_data, fx_data)
        (
            no_vehicles_above_24mln,
            no_vehicles_below_24mln,
            reins_prem,
            risk_mitigation,
            reporting_unit,
        ) = get_variable_value.define_variable(
            input_data,
            [
                "NL_MM_MOT_NO_ABOVE",
                "NL_MM_MOT_NO_BELOW",
                "NL_MM_MOT_REINS_PREM",
                "NL_MM_MOT_RM_EFFECT",
                "INFO_REPORT_UNIT",
            ],
        )
        gross_scr = self.calculate_scr_gross(
            no_vehicles_above_24mln, no_vehicles_below_24mln, reporting_unit, fx
        )
        net_scr = self.calculate_scr_net(gross_scr, risk_mitigation)
        total_risk_mitigation = risk_mitigation + reins_prem

        results = self.results_df(
            risk_id="NL_MM_MOT",
            data_id_list=[
                "NL_MM_MOT_SCR_G",
                "NL_MM_MOT_SCR_N",
                "NL_MM_MOT_RM_EFFECT",
                "NL_MM_MOT_TOTAL_RM",
                "NL_MM_MOT_REINS_PREM",
                "NL_MM_MOT_NO_ABOVE",
                "NL_MM_MOT_NO_BELOW",
            ],
            values_list=[
                gross_scr,
                net_scr,
                risk_mitigation,
                total_risk_mitigation,
                reins_prem,
                no_vehicles_above_24mln,
                no_vehicles_below_24mln,
            ],
        )

        return results

    def calculate_scr_gross(
        self, no_vehicles_above_24mln, no_vehicles_below_24mln, reporting_unit, fx
    ) -> float:

        if no_vehicles_above_24mln > 0 or no_vehicles_below_24mln > 0:
            if reporting_unit != 0:
                minimum = 6000000 * fx / reporting_unit
                sqrt_factor = 50000 * fx / reporting_unit
            else:
                minimum = 6000000 * fx
                sqrt_factor = 50000 * fx

            motor_gross_scr = round(
                max(
                    minimum,
                    sqrt_factor
                    * np.sqrt(
                        no_vehicles_above_24mln
                        + 0.05 * no_vehicles_below_24mln
                        + 0.95 * min(no_vehicles_below_24mln, 20000)
                    ),
                ),
                2,
            )
        else:
            motor_gross_scr = 0

        return motor_gross_scr


class ManMadeAviationRiskCalculator(ManMadeRiskCalculator):

    def calculate(self, input_data: pd.DataFrame, fx_data: pd.DataFrame):
        get_variable_value = VariablesInputValues()
        fx = get_variable_value.calculate_fx(input_data, fx_data)
        (
            hull_si_gross,
            hull_si_net,
            liability_si_gross,
            liability_si_net,
            reins_prem,
            aircraft_name,
        ) = get_variable_value.define_variable(
            input_data,
            [
                "NL_MM_AVI_SI_HULL_G",
                "NL_MM_AVI_SI_HULL_N",
                "NL_MM_AVI_SI_LIAB_G",
                "NL_MM_AVI_SI_LIAB_N",
                "NL_MM_AVI_REINS_PREM",
                "NL_MM_AVI_NM",
            ],
        )

        scr_gross = self.calculate_scr_gross()
        loss_net = self.loss(
            [hull_si_gross, liability_si_gross],
            [hull_si_net, liability_si_net],
        )[1]
        risk_mitigation = self.risk_mitigation(scr_gross, loss_net)
        risk_mitigation_incl_reinst = risk_mitigation - reins_prem
        scr_net = self.calculate_scr_net(scr_gross, risk_mitigation_incl_reinst)

        results = self.results_df(
            risk_id="NL_MM_AVI",
            data_id_list=[
                "NL_MM_AVI_SCR_G",
                "NL_MM_AVI_SCR_N",
                "NL_MM_AVI_RM",
                "NL_MM_AVI_RM_INCL_REINST",
                "NL_MM_AVI_REINS_PREM",
                "NL_MM_AVI_SI_HULL_G",
                "NL_MM_AVI_SI_LIAB_G",
            ],
            values_list=[
                scr_gross,
                scr_net,
                risk_mitigation,
                risk_mitigation_incl_reinst,
                reins_prem,
                hull_si_gross,
                liability_si_gross,
            ],
        )

        return pd.DataFrame(results)

    def calculate_scr_gross(
        self, hull_si_gross, liability_si_gross, hull_si_net, liability_si_net
    ) -> float:
        scr_gross = self.loss(
            [hull_si_gross, liability_si_gross],
            [hull_si_net, liability_si_net],
        )[0]
        return round(scr_gross, 2)


class ManMadeFireRiskCalculator(ManMadeRiskCalculator):

    def calculate(self, input_data: pd.DataFrame, fx_data: pd.DataFrame):
        get_variable_value = VariablesInputValues()
        fx = get_variable_value.calculate_fx(input_data, fx_data)
        (
            si_gross,
            si_net,
            reins_prem,
            simplification,
        ) = get_variable_value.define_variable(
            input_data,
            [
                "NL_MM_FIR_SI_G",
                "NL_MM_FIR_SI_N",
                "NL_MM_FIR_REINS_PREM",
                "NL_MM_FIR_SIMPL",
            ],
        )

        scr_gross = self.calculate_scr_gross(si_gross)
        risk_mitigation = self.risk_mitigation(si_gross, si_net)
        risk_mitigation_incl_reinst = self.risk_mitigation(si_gross, si_net, reins_prem)
        scr_net = self.calculate_scr_net(scr_gross, risk_mitigation_incl_reinst)

        results = self.results_df(
            risk_id="NL_MM_FIR",
            data_id_list=[
                "NL_MM_FIR_SCR_G",
                "NL_MM_FIR_SCR_N",
                "NL_MM_FIR_RM",
                "NL_MM_FIR_RM_INCL_REINST",
                "NL_MM_FIR_REINS_PREM",
            ],
            values_list=[
                scr_gross,
                scr_net,
                risk_mitigation,
                risk_mitigation_incl_reinst,
                reins_prem,
            ],
        )

        return pd.DataFrame(results)

    def calculate_scr_gross(self, si_gross) -> float:
        proportion_factor = 1  # is it always 100% ?
        scr_gross = si_gross * proportion_factor
        return round(scr_gross, 2)


class ManMadeCreditRiskCalculator(ManMadeRiskCalculator):

    def calculate(self, input_data, risk_id, fx_data):
        get_variable_value = VariablesInputValues()
        fx = get_variable_value.calculate_fx(input_data, fx_data)
        (
            exposure1,
            exposure2,
            risk_mitigation1,
            risk_mitigation2,
            reins_prem1,
            reins_prem2,
            premium_existing_business,
            premium_new_business,
            rec_reins_prem,
            rec_risk_mitig_incl_nb,
            rec_risk_mitig_exl_nb,
        ) = get_variable_value.define_variable(
            input_data,
            [
                "NL_MM_CRE_DEF_EXP_1",
                "NL_MM_CRE_DEF_EXP_2",
                "NL_MM_CRE_DEF_RM_1",
                "NL_MM_CRE_DEF_RM_2",
                "NL_MM_CRE_DEF_REINS_1",
                "NL_MM_CRE_DEF_REINS_2",
                "NL_MM_CRE_REC_PREM_EARN_G_NY_EB",
                "NL_MM_CRE_REC_PREM_EARN_G_NY_NB",
                "NL_MM_CRE_REC_REINS_PREM",
                "NL_MM_CRE_REC_RM_EFFECT",
                "NL_MM_CRE_REC_RM_EFFECT_WONB",
            ],
        )

        default_scr_gross, recession_scr_gross = self.calculate_scr_gross(
            exposure1,
            exposure2,
            premium_existing_business,
            premium_new_business,
        )
        default_scr_net, recession_scr_net = self.calculate_scr_net(
            exposure1,
            exposure2,
            recession_scr_gross,
            risk_mitigation1,
            risk_mitigation2,
            rec_risk_mitig_incl_nb,
        )

        results = {
            "RISK_ID": risk_id,
            "DATA_ID": [],
            "VALUE": [],
        }

        return pd.DataFrame(results)

    def calculate_scr_gross(
        self,
        exposure1,
        exposure2,
        premium_existing_business,
        premium_new_business,
        run_off="n",
    ) -> float:
        lgd_def_factor = 0.1  # TO DO: define it somewhere outside this file
        lgd_rec_factor = 1
        default_scr_gross = (exposure1 + exposure2) * lgd_def_factor
        if run_off == "y":
            recession_scr_gross = premium_existing_business * lgd_rec_factor
        else:
            recession_scr_gross = (
                premium_existing_business + premium_new_business
            ) * lgd_rec_factor

        return round(default_scr_gross, 2), round(recession_scr_gross, 2)

    def calculate_scr_net(
        self,
        exposure1,
        exposure2,
        recession_scr_gross,
        risk_mitigation1,
        risk_mitigation2,
        rec_risk_mitigation,
    ):
        lgd_def_factor = 0.1
        default_scr_net = max(exposure1 * lgd_def_factor - risk_mitigation1, 0) + max(
            exposure2 * lgd_def_factor - risk_mitigation2, 0
        )
        recession_scr_net = max(recession_scr_gross - rec_risk_mitigation, 0)
        return round(default_scr_net, 2), round(recession_scr_net, 2)


if __name__ == "__main__":

    supabase_data_importer = input_interface.SupabaseDataImporter()
    fx_data = supabase_data_importer.read_from_supabase("exchange_rates")
    data_id_enriched = supabase_data_importer.run_import(
        "/python/SolvMate/input/12.06_SAS_Input_ManMade.xls",
        ["Basic input", "NL man-made"],
    )
    motor_risk = ManMadeMotorRiskCalculator()
    print(motor_risk.calculate(data_id_enriched, fx_data))
