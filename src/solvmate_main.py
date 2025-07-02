# Import required libraries and modules
from src.risks import calculate_market_risk, calculate_life_risk, calculate_hslt_risk, calculate_cpty_type1, calculate_cpty_type_2_risk
from src.utils import input, output
import os
import shutil
from dotenv import load_dotenv
from supabase import create_client, Client
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import openpyxl
from pathlib import Path
import random
from IPython.display import display
import ipywidgets as widgets

# Initialize Supabase client
load_dotenv()
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)

# Input files and worksheet requirements
REQUIRED_WORKSHEETS = [
    "Basic input",
    "MarketR",
    "ConcR",
    "CurrR",
    "CDR",
    "LnH SLT UW"
    ]

# Utility to update run status in Supabase
def update_run_status(run_id: int, status: str, end_time: datetime = None):
    data = {"run_status": status}
    if end_time:
        data["run_end"] = end_time.isoformat()
    supabase.table("run_status").update(data).eq("run_id", run_id).execute()

def run_calculation(input_file_path, run_id):
    output_base = Path("/workspaces/SolvMate/outputs")
    run_output_path = output_base / str(run_id)
    run_output_path.mkdir(parents=True, exist_ok=True)
    # Copy input files to run directory
    input_file = Path(input_file_path)
    if input_file.exists():
        shutil.copy2(input_file, run_output_path / input_file.name)
    else:
        print(f"Warning: Input file {input_file} not found")
    try:
        # Load input data
        data_id_enriched = input.run_Import(input_file, REQUIRED_WORKSHEETS)

        # Market risk calculations
        aggregation_tree_market_ir_enriched = calculate_market_risk.calculate_interest_rate_risk(data_id_enriched)
        aggregation_tree_market_eq_enriched = calculate_market_risk.calculate_equity_risk(data_id_enriched)
        aggregation_tree_market_pro_enriched = calculate_market_risk.calculate_property_risk(data_id_enriched)
        aggregation_tree_market_spr_enriched = calculate_market_risk.calculate_spread_risk(data_id_enriched)
        aggregation_tree_market_enriched = calculate_market_risk.calculate_total_market_risk(data_id_enriched)

        # Combine market risks
        aggregation_tree_market_all_risks = pd.concat([
            aggregation_tree_market_enriched,
            aggregation_tree_market_ir_enriched,
            aggregation_tree_market_eq_enriched,
            aggregation_tree_market_pro_enriched,
            aggregation_tree_market_spr_enriched
        ], ignore_index=True)

        # Life risk calculations
        aggregation_tree_life_mor_enriched = calculate_life_risk.calculate_life_mortality_risk(data_id_enriched)
        aggregation_tree_life_lon_enriched = calculate_life_risk.calculate_life_longevity_risk(data_id_enriched)
        aggregation_tree_life_dis_enriched = calculate_life_risk.calculate_life_disability_risk(data_id_enriched)
        aggregation_tree_life_lap_enriched = calculate_life_risk.calculate_life_lapse_risk(data_id_enriched)
        aggregation_tree_life_exp_enriched = calculate_life_risk.calculate_life_expense_risk(data_id_enriched)
        aggregation_tree_life_rev_enriched = calculate_life_risk.calculate_life_revision_risk(data_id_enriched)
        aggregation_tree_life_cat_enriched = calculate_life_risk.calculate_life_catastrophe_risk(data_id_enriched)

        # Combine life risks
        aggregation_tree_life_all = pd.concat([
            aggregation_tree_life_mor_enriched,
            aggregation_tree_life_lon_enriched,
            aggregation_tree_life_dis_enriched,
            aggregation_tree_life_lap_enriched,
            aggregation_tree_life_exp_enriched,
            aggregation_tree_life_rev_enriched,
            aggregation_tree_life_cat_enriched
        ], ignore_index=True)

        # HSLT risk calculations
        aggregation_tree_hslt_mor_enriched = calculate_hslt_risk.calculate_hslt_mortality_risk(data_id_enriched)
        aggregation_tree_hslt_lon_enriched = calculate_hslt_risk.calculate_hslt_longevity_risk(data_id_enriched)
        aggregation_tree_hslt_dis_enriched = calculate_hslt_risk.calculate_hslt_disability_risk(data_id_enriched)
        aggregation_tree_hslt_lap_enriched = calculate_hslt_risk.calculate_hslt_lapse_risk(data_id_enriched)
        aggregation_tree_hslt_exp_enriched = calculate_hslt_risk.calculate_hslt_expense_risk(data_id_enriched)
        aggregation_tree_hslt_rev_enriched = calculate_hslt_risk.calculate_hslt_revision_risk(data_id_enriched)

        # Combine HSLT risks
        aggregation_tree_hslt_all = pd.concat([
            aggregation_tree_hslt_mor_enriched,
            aggregation_tree_hslt_lon_enriched,
            aggregation_tree_hslt_dis_enriched,
            aggregation_tree_hslt_lap_enriched,
            aggregation_tree_hslt_exp_enriched,
            aggregation_tree_hslt_rev_enriched
        ], ignore_index=True)

        # Counterparty Type 1 Risk calculations
        aggregation_tree_cpty_type1 = calculate_cpty_type1.calculate_cpty_type1(data_id_enriched)

        # Counterparty Type 2 Risk calculations
        aggregation_tree_cpty_type2 = calculate_cpty_type_2_risk.calculate_cpty_type2(data_id_enriched)

        # Combine all risk components
        aggregation_tree_enriched = pd.concat([
            aggregation_tree_market_all_risks,
            aggregation_tree_life_all,
            aggregation_tree_hslt_all,
            aggregation_tree_cpty_type1,
            aggregation_tree_cpty_type2
        ], ignore_index=True)

        # Fill QRT from the aggregated DataFrame
        Path(run_output_path).mkdir(parents=True, exist_ok=True)
        output.fill_QRT_from_dataframe(aggregation_tree_enriched, output_dir=run_output_path)
        update_run_status(run_id, "finished", datetime.now(timezone.utc))

        print(f"Run completed successfully. Results saved in: {run_output_path}")
        return True
    except Exception as e:
        update_run_status(run_id, "failed", datetime.now(timezone.utc))
        print(f"Error during run: {str(e)}")
        raise

# --- Widgets for user input ---
def main_widget():
    description_widget = widgets.Text(
        description='Description:',
        placeholder='Enter a short description for this run'
    )
    scope_widget = widgets.Dropdown(
        options=['SCR, MCR', 'Risk margin only'],
        description='Scope:',
        value='SCR, MCR'
    )
    run_button = widgets.Button(
        description='Run Calculation',
        button_style='success'
    )
    output_widget = widgets.Output()

    def on_run_button_clicked(b):
        with output_widget:
            output_widget.clear_output()
            if not description_widget.value.strip():
                print("Please enter a description before running.")
                return
            run_id = random.randint(1, 1000000)
            input_file = Path("/workspaces/SolvMate/input/04.12_SAS_Input_CDR.xlsb")
            # Create initial run status entry
            start_time = datetime.now(timezone.utc)
            run_data = {
                "run_id": run_id,
                "short_description": description_widget.value,
                "run_start": start_time.isoformat(),
                "run_status": "running",
                "scope_of_run": scope_widget.value,
                "user_id": os.environ.get("USER", "unknown")
            }
            supabase.table("run_status").insert(run_data).execute()
            print(f"Starting calculation with run ID: {run_id}")
            run_button.disabled = True
            description_widget.disabled = True
            scope_widget.disabled = True
            try:
                run_calculation(str(input_file), run_id)
            except Exception as e:
                print(f"Calculation failed: {str(e)}")
            finally:
                run_button.disabled = False
                description_widget.disabled = False
                scope_widget.disabled = False

    run_button.on_click(on_run_button_clicked)

    display(description_widget)
    display(scope_widget)
    display(run_button)
    display(output_widget)
    print("Fill in the description and scope, then click 'Run Calculation' to start the process.")

# Only run widget UI if run directly (not on import)
if __name__ == "__main__":
    main_widget()
