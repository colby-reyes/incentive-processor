# utils.py

import io
import os
import warnings
from dataclasses import dataclass

import msoffcrypto
import pandas as pd

warnings.simplefilter("always")

pd.options.future.infer_string = True


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
                "Tax ID": "int64[pyarrow]",
                "Check #": "str",
                "NPI": "int64[pyarrow]"
                #     "Default Payer": "category",
            },
            converters={"Amount": amount_converter}, #"NPI": npi_to_str,
            dtype_backend="pyarrow",
        )
    except msoffcrypto.exceptions.FileFormatError as ffe:
        msg = f"""Error decrypting file: {file_path}\n  >>> {ffe}
            Unencrypted file will be read"""
        df = pd.read_excel(
            file_path,
            engine="openpyxl",
            dtype={
                "Tax ID": "int64[pyarrow]",
                "NPI": "int64[pyarrow]"
                #     "Check #": "category",
                #     "Default Payer": "category",
            },
            converters={"NPI": npi_to_str, "Amount": amount_converter},
            dtype_backend="pyarrow",
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
    ref_info_df = pd.read_csv(
        info_path,
        dtype={
            "TIN": "int64[pyarrow]",
            "GROUP_NPI": "int64[pyarrow]",
            "ACCT_ID": "category",
        },
        dtype_backend="pyarrow",
        engine="pyarrow",
    )
    return ref_info_df


def prep_data_for_verification(df: pd.DataFrame):
    # load reference info
    ref_info = load_reference_info()

    # insert Department column for editing pre-export
    df.insert(0, column="Dept", value="")

    for index, row in df.iterrows():
        # dept = ref_info[ref_info.GROUP_NPI == row["NPI"]]["ID"].tolist()[0]
        try:
            print(f"type of row[npi]: {type(row['NPI'])}")
            print(f"type of refinfo.GROUP_NPI[1]: {type(ref_info.GROUP_NPI[1])}")
            dept = ref_info.loc[ref_info.GROUP_NPI == row["NPI"], "ID"].item()
        except ValueError:
            try:
                print("<<< TRYING FIND BY TAX ID >>>>")
                print(f"Type of row[tax_ID]: {type(row['Tax ID'])}")
                print(f"Type refinfo row: {type(ref_info.TIN[1])}")

                dept = ref_info.loc[ref_info.TIN == row["Tax ID"], "ID"].item()
            except ValueError:
                print(" +++++++++++  Could not find by TAX ID or NPI +++++++++++ ")
                dept = "<look up in OnBase>"
        df.loc[index, "Dept"] = dept

    # return ordered df
    ver_df = df[
        [
            "Process Errors",
            "Check #",
            "Dept",
            "Default Payer",
            "Amount",
            "Deposit Date",
            "Tax ID",
            "NPI",
        ]
    ]

    return ver_df


def fill_posting_data(decryptedVerified_df: pd.DataFrame, inc_type="Prop56"):
    """Function to fill in copy-paste fields upon clicking export button
    after data has been verified"""
    ref_info_df = load_reference_info()
    posting_df = decryptedVerified_df.copy()

    posting_df.insert(0, column="Comment1", value="")
    posting_df.insert(0, column="Comment2", value="")
    posting_df.insert(0, column="Clearing Account", value="")
    # posting_df.insert(0, column="Dept", value="") ## fill Department from `posting_df`
    posting_df.insert(0, column="Posted?", value=False)

    for index, row in posting_df.iterrows():
        # drop `PB` and `SUPERPAYOR` terms from payor name to return actual payor name
        payor = (
            row["Default Payer"]
            .replace("PB", "")
            .replace("SUPERPAYOR", "")
            .strip()
            .title()
        )
        # fill department identifier from `NPI` column value
        # dept = ref_info_df[ref_info_df.GROUP_NPI == row["NPI"]]["ID"].tolist()[0]
        ### change to filling Department from "Dept" column in `posting_df`
        dept = row["Dept"]
        posting_df.loc[index, "Dept"] = dept

        # fill comments columns
        posting_df.loc[
            index, "Comment1"
        ] = f"{payor} {inc_type} Incentive Payment for {dept}"  # noqa: E501
        posting_df.loc[
            index, "Comment2"
        ] = f"{payor} {inc_type} Incentive Payment for {dept}"  # noqa: E501

        # fill account number columns
        acct = ref_info_df[ref_info_df.ID == row["Dept"]]["ACCT_ID"].tolist()[0]
        posting_df.loc[index, "Clearing Account"] = str(acct)

    return posting_df[
        [
            "Process Errors",
            "Check #",
            "Comment1",
            "Clearing Account",
            "Amount",
            "Dept",
            "Comment2",
            "Posted?",
        ]
    ]
