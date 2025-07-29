import pandas as pd
import os
from dotenv import load_dotenv
from supabase import create_client, Client


class SupabaseDataFrameReader:
    def __init__(self):
        load_dotenv()
        self.supabase: Client = create_client(
            os.environ.get("SUPABASE_URL"),
            os.environ.get("SUPABASE_KEY")
        )

    def read_from_supabase(self, table_name) -> pd.DataFrame:
        response = self.supabase.table(table_name).select("*").execute()
        data = response.data
        df = pd.DataFrame(data)
        return df
        

class ExternalAssetsCalculator:
    def __init__(self, external_assets: pd.DataFrame):
        self.external_assets = external_assets

    def quarterly_assets_values_all_entities(self, closing_quarter: str) -> pd.DataFrame:
        entity_ids = self.external_assets['ENTITY_ID'].unique().tolist()
        results = []

        for entity_id in entity_ids:
            result_df = self.quarterly_assets_values(closing_quarter, entity_id)
            results.append(result_df)

        external_assets_df = pd.concat(results, ignore_index=True)

        return external_assets_df


    def quarterly_assets_values(self, closing_quarter: str, entity_id: str) -> pd.DataFrame:

        assets_values = []
        entity_ids = []
        reporting_dates = []

        #TO DO: put this table also to supabase 
        helper_frame = SupabaseDataFrameReader().read_from_supabase("external_assets_mapping")

        for _, row in helper_frame.iterrows():
            value_col = row['VALUE_COL']
            flag_col = row['FLAG_COL']
            flag_value = row['FLAG_VALUE']

            assets_value = self.external_assets.loc[(self.external_assets[flag_col] == flag_value) & (self.external_assets['ENTITY_ID'] == entity_id), value_col].sum()
            assets_values.append(assets_value)

            entity_ids.append(entity_id)
            reporting_dates.append(closing_quarter)

        columns_for_external_assets_df = ['DATA_ID']  
        external_assets_df = helper_frame[columns_for_external_assets_df].copy()

        external_assets_df['VALUE'] = assets_values
        external_assets_df['ENTITY_ID'] = entity_ids
        external_assets_df['REPORTING_DT'] = reporting_dates

        columns_order = ['REPORTING_DT', 'ENTITY_ID', 'DATA_ID', 'VALUE'] 
        external_assets_df = external_assets_df[columns_order]
        
        return external_assets_df
    

class ExternalAssetsUploader:
    def __init__(self):
        load_dotenv()
        self.supabase: Client = create_client(
            os.environ.get("SUPABASE_URL"),
            os.environ.get("SUPABASE_KEY")
        )

        self.response = self.supabase.table("external_market_risk_input").select("*").execute()
        self.external_market_risk_data = self.response.data
        self.external_market_risk_df = pd.DataFrame(self.external_market_risk_data)

    def upload_external_assets(self, external_assets: pd.DataFrame) -> None:
        try:
            self.supabase.table("external_market_risk_input").insert(external_assets.to_dict(orient="records")).execute()
        except Exception as e:
            print(f"Error uploading external assets: {e}")

    def update_external_assets(self, external_assets: pd.DataFrame) -> None:
        try:
            self.supabase.table("external_market_risk_input").upsert(external_assets.to_dict(orient="records")).execute()
        except Exception as e:
            print(f"Error updating external assets: {e}")


class ExternalAssetsValuesToInput:
    def __init__(self, input_values_df, exchange_rates, external_assets):
        self.input_values_df = input_values_df
        self.exchange_rates = exchange_rates
        self.external_assets = external_assets
    

    def external_assets_values_upload(self):
        (mkt_assets_manual_input_flg_value, conc_assets_manual_input_flg_value,
         currency_assets_manual_input_flg_value, reporting_date_value, reporting_currency_value,
         entity_id_value) = self.read_flags()

        if mkt_assets_manual_input_flg_value == 'no':
            input_values_df = self.market_risk_input(reporting_date_value, reporting_currency_value, entity_id_value)
        if conc_assets_manual_input_flg_value == 'no':
            input_values_df = self.concentration_risk_input()
        if currency_assets_manual_input_flg_value == 'no':
            input_values_df = self.currency_risk_input()

        return input_values_df
  
    def read_flags(self):
        mkt_assets_manual_input_flg_value = self.input_values.loc[self.input_values_df['DATA_ID'] == mkt_assets_manual_input, 'VALUE'].iloc[0]
        conc_assets_manual_input_flg_value = self.input_values.loc[self.input_values_df['DATA_ID'] == conc_assets_manual_input, 'VALUE'].iloc[0]
        currency_assets_manual_input_flg_value = self.input_values.loc[self.input_values_df['DATA_ID'] == currency_assets_manual_input, 'VALUE'].iloc[0]
        reporting_date_value = self.input_values.loc[self.input_values_df['DATA_ID'] == reporting_date, 'VALUE'].iloc[0]
        reporting_currency_value = self.input_values.loc[self.input_values_df['DATA_ID'] == reporting_currency, 'VALUE'].iloc[0]
        entity_id_value = self.input_values.loc[self.input_values_df['DATA_ID'] == entity_id, 'VALUE'].iloc[0]


        return (mkt_assets_manual_input_flg_value, conc_assets_manual_input_flg_value,
                currency_assets_manual_input_flg_value, reporting_date_value, reporting_currency_value,
                entity_id_value)


    def market_risk_input(self, reporting_date, reporting_currency, entity_id, market_external_assets_data_id):
        
        filtered_external_assets = self.external_assets[(self.external_assets['REPORTING_DT'] == reporting_date) &
                                                    (self.external_assets['ENTITY_ID'] == entity_id)]
        
        assets_values_to_insert = []
        for data_id in market_external_assets_data_id:
            external_asset = filtered_external_assets[filtered_external_assets['DATA_ID'] == data_id][['DATA_ID', 'VALUE']]
            assets_values_to_insert.append(external_asset)

        assets_values_to_insert_df = pd.concat(assets_values_to_insert, ignore_index=True) 

        if reporting_currency != 'EUR':
            assets_values_to_insert_df = self.change_currency(reporting_currency, reporting_date, assets_values_to_insert_df, self.exchange_rates)  

        input_values_df = self.input_values_df.copy()
        input_values_df.set_index('DATA_ID', inplace=True)
        assets_values_to_insert_df.set_index('DATA_ID', inplace=True)

        input_values_df.loc[assets_values_to_insert_df.index, 'VALUE'] = assets_values_to_insert_df['VALUE']

        input_values_df.reset_index(inplace=True)
        
        return input_values_df

    def concentration_risk_input(self):
        return None

    def currency_risk_input(self):
        return None

    def change_currency(self, reporting_currency, reporting_date, assets_values, exchange_rates):
        spot_rate = exchange_rates.loc[(exchange_rates['REPORTING_DT'] == reporting_date) & 
                                (exchange_rates['TO_CURRENCY'] == reporting_currency), 'SPOT_RATE'].iloc[0]
        
        assets_values = assets_values.copy()
        assets_values['VALUE'] = assets_values['VALUE'] * spot_rate

        return assets_values
    
    
mkt_assets_manual_input = 'INFO_MKT_ASSETS_MANUAL_INPUT'
conc_assets_manual_input = 'INFO_CONC_ASSETS_MANUAL_INPUT'
currency_assets_manual_input = 'INFO_CURRENCY_MANUAL_INPUT'
reporting_date = 'INFO_REPORT_DT'
reporting_currency = 'INFO_REPORT_CCY'
entity_id = 'INFO_ECON_NO'

external_input_flags_dict = {
    mkt_assets_manual_input: ['INFO_MKT_ASSETS_MANUAL_INPUT'],
    conc_assets_manual_input: ['INFO_CONC_ASSETS_MANUAL_INPUT'],
    currency_assets_manual_input: ['INFO_CURRENCY_MANUAL_INPUT'],
    reporting_date: ['INFO_REPORT_DT'],
    reporting_currency: ['INFO_REPORT_CCY'],
    entity_id: ['INFO_ECON_NO']
}
 
market_external_assets_data_id = ['MKT_INT_A_BC',
'MKT_INT_DN_A_SH',
'MKT_INT_UP_A_SH',
'MKT_EQU_T1_ST_A_BC',
'MKT_EQU_T2_ST_A_BC',
'MKT_EQU_QI_CORP_OTH_A_BC',
'MKT_EQU_T1_EQ_A_BC',
'MKT_EQU_T2_EQ_A_BC',
'MKT_EQU_QI_NONCORP_OTH_A_BC',
'MKT_EQU_T1_ST_A_SH',
'MKT_EQU_T1_EQ_A_SH',
'MKT_EQU_T2_ST_A_SH',
'MKT_EQU_T2_EQ_A_SH',
'MKT_EQU_QI_CORP_OTH_A_SH',
'MKT_EQU_QI_NONCORP_OTH_A_SH',
'MKT_EQU_QI_CORP_ST_A_BC',
'MKT_EQU_QI_CORP_ST_A_SH',
'MKT_EQU_QI_NONCORP_ST_A_BC',
'MKT_EQU_QI_NONCORP_ST_A_SH',
'MKT_PRO_A_BC',
'MKT_PRO_A_SH',
'MKT_SPR_BD_QI_CORP_A_BC',
'MKT_SPR_BD_QI_NONCORP_A_BC',
'MKT_SPR_BD_OT_A_BC',
'MKT_SPR_BD_QI_CORP_A_SH',
'MKT_SPR_BD_QI_NONCORP_A_SH',
'MKT_SPR_BD_OT_A_SH',
'MKT_SPR_SE_S_STS_A_BC',
'MKT_SPR_SE_NS_STS_A_BC',
'MKT_SPR_SE_R_A_BC',
'MKT_SPR_SE_OTH_A_BC',
'MKT_SPR_SE_TT1_A_BC',
'MKT_SPR_SE_G_STS_A_BC',
'MKT_SPR_SE_S_STS_A_SH',
'MKT_SPR_SE_NS_STS_A_SH',
'MKT_SPR_SE_R_A_SH',
'MKT_SPR_SE_OTH_A_SH',
'MKT_SPR_SE_TT1_A_SH',
'MKT_SPR_SE_G_STS_A_SH',
'MKT_SPR_CD_A_BC',
'MKT_SPR_CD_UP_A_SH',
'MKT_SPR_CD_DN_A_SH'
] 