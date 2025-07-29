class ColumnRenamingDictionaryCptyType2Risk:
    RENAMING_DICT = {
        "CPTY_LGD_CPTY_NAME_": "Counterparty",
        "CPTY_LGD_CPTY_PARENT_NAME_": "Parent Group",
        "CPTY_LGD_CPTY_CODE_": "LEI Code",
        "CPTY_LGD_EXP_TYPE_": "Type",
        "CPTY_LGD_CPTY_RATING_": "Rating",
        "CPTY_LGD_CPTY_SCR_RATIO_": "SCR Ratio",
        "CPTY_LGD_CPTY_MCR_RATIO_": "MCR Ratio",
        "CPTY_LGD_EXP_MVAL_": "Market Value",
        "CPTY_LGD_EXP_DEPO_": "RI Deposits",
        "CPTY_LGD_CPTY_RI_TIED_UP_": "RI > 60% tied up",
        "CPTY_LGD_EXP_RM_FLG_": "Risk Mitigation Flag",
        "CPTY_LGD_RM_EFFECT_": "Risk Mitigating Effect",
        "CPTY_LGD_RM_SIMPL_FLG_": "Simplified Risk Mitigation Flag",
        "CPTY_LGD_MORT_RISK_ADJ_VAL_": "Risk adjusted Mortgage",
        "CPTY_LGD_MORT_GUARANTEE_": "Morgage Guarantee",
        "CPTY_LGD_COLL_MVAL_": "Market Value Collateral",
        "CPTY_LGD_COLL_ADJ_MKT_": "Collateral Adjustment",
        "CPTY_LGD_COLL_3RD_REQ_MET_": "3rd Party Requirement",
        "CPTY_LGD_COLL_INSOLV_FLG_": "Collataral Insolvency",
        "CPTY_LGD_COLL_SIMPL_": "Simplified Collateral",
        "CPTY_LGD_POOL_NAME_": "Pool Name",
        "CPTY_LGD_POOL_TYPE_": "Pool Type",
        "CPTY_LGD_POOL_S2_SCOPE_": "Pool SII Scope",
        "CPTY_LGD_POOL_EOF_": "Pool EOF",
        "CPTY_LGD_POOL_C_SHARE_RISK_": "Pool SoR",
        "CPTY_LGD_POOL_U_SHARE_RISK_": "Pool USoR",
        "CPTY_LGD_POOL_COLL_FLG_": "Pool >= 60% Collateral",
        "CPTY_LGD_POOL_CONTR_RM_": "Pool RM Contribution",
    }


class ColumnNameFinalResultCptyType2Risk:
    CPTY_TYPE2_SCR_G = "CPTY_TYPE2_SCR_G"
    CPTY_TYPE2_EXP_INTER_DUE = "CPTY_TYPE2_EXP_INTER_DUE"
