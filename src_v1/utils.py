# utils.py

import io
import os
from dataclasses import dataclass

import msoffcrypto
import pandas as pd


@dataclass
class VersionInfo:
    version = "1.0.0"
    description = """`Incentive Processor` version 1.0.0 (simple version for incentive verification and autofilling posting information for easy copy-paste posting)"""  # noqa: E501
    author = "Colby Reyes"
    contact = "colbyr@hs.uci.edu"


def amount_converter(amt_str: str):
    try:
        amt_float = float(amt_str.replace(",", ""))
    except AttributeError:
        amt_float = amt_str
    return amt_float


def npi_to_str(npi: int):
    npi_str = str(npi)
    return npi_str


def load_remitList_spreadsheet(file_path: str, pwd: str):
    # load file to temporary `bytesIO` object and unlock with `msoffcrypto` tool
    temp = io.BytesIO()
    try:
        with open(file_path, "rb") as f:
            excel = msoffcrypto.OfficeFile(f)
            excel.load_key(pwd)
            excel.decrypt(temp)

        # load decrypted excel file into `pandas`
        msg = "Success!"
        df = pd.read_excel(
            temp,
            engine="openpyxl",
            dtype={
                "Tax ID": "category",
                #     "Check #": "category",
                #     "Default Payer": "category",
            },
            converters={"NPI": npi_to_str, "Amount": amount_converter},
        )
    except msoffcrypto.exceptions.FileFormatError as ffe:
        msg = f"""Error decrypting file: {file_path}\n  >>> {ffe}
            Unencrypted file will be read"""
        df = pd.read_excel(
            file_path,
            engine="openpyxl",
            dtype={
                "Tax ID": "category",
                #     "Check #": "category",
                #     "Default Payer": "category",
            },
            converters={"NPI": npi_to_str, "Amount": amount_converter},
        )
    except msoffcrypto.exceptions.InvalidKeyError as ke:
        msg = f""":red[**Error decrypting file** {file_path}:] \n\n                {ke} \n\n PLEASE RE-ENTER PASSWORD"""  # noqa: E501
        df = None
    except Exception as e:
        msg = f"Error decrypting file: :red[{file_path}]\n >>> {e}"
        df = None

    return (msg, df)


def load_reference_info(
    info_path: str = "./resources/Dept_ID_Reference.csv",
) -> pd.DataFrame:
    info_path = os.path.abspath(info_path)
    ref_info_df = pd.read_csv(info_path)
    return ref_info_df


def prep_data_for_verification(df: pd.DataFrame):
    ver_df = df[
        [
            "Process Errors",
            "Check #",
            "Default Payer",
            "Amount",
            "Deposit Date",
            "Tax ID",
            "NPI",
        ]
    ]
    return ver_df


def fill_posting_data(
    decryptedVerified_df: pd.DataFrame, ref_info_df: pd.DataFrame, inc_type="Prop56"
):
    """Function to fill in copy-paste fields upon clicking export button
    after data has been verified"""
    posting_df = decryptedVerified_df.copy()

    for index, row in posting_df.iterrows():
        # drop `PB` and `SUPERPAYOR` terms from payor name to return actual payor name
        payor = (
            row["Payer Name"].replace("PB", "").replace("SUPERPAYOR").strip().title()
        )
        # fill department identifier from `NPI` column value
        dept = ref_info_df[
            ref_info_df.GROUP_NPI == row["NPI"]
        ]  # TODO: confirm that "NPI" is the column name for remittance export
        posting_df.loc[
            index, "Comment1"
        ] = f"{payor} {inc_type} Incentive Payment for {dept}"
