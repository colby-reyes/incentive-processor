# dashboard.py (main file)

# import packages
import os
import shutil
import time
import warnings
from datetime import datetime

import pandas as pd
import streamlit as st

# import local functions
import utils

warnings.simplefilter(
    "ignore",
)

uci_logo_link = (
    "https://www.logolynx.com/images/logolynx/4f/4f42c461be2388aca949521bbb6a64f1.gif"
)

vinfo = utils.VersionInfo()

st.set_page_config(
    page_title="Incentive Preprocessor",
    page_icon=uci_logo_link,
    layout="wide",
    menu_items={
        "Report a Bug": "mailto:colbyr@hs.uci.edu",
        "About": vinfo.description,
    },
)

## sidebar
# Sidebar Configuration
st.sidebar.image(
    uci_logo_link,
    use_column_width=True,
)
st.sidebar.markdown("# Incentive Posting Preprocessor")
st.sidebar.markdown(
    "Use exported PB Remittance data to create templates for copy-paste posting of Prop56 and CalOptima Incentive payments"  # noqa: E501
)
st.sidebar.markdown(f"Version: `{vinfo.version}`")
st.sidebar.divider()

st.sidebar.markdown("##### Standard Dept ID's")
ref_info_df = utils.load_reference_info()

# transform number cols to str for easier reading
ref_info_df["TIN"] = ref_info_df["TIN"].astype(str)
ref_info_df["GROUP_NPI"] = ref_info_df["GROUP_NPI"].astype(str)

# display ID ref df
st.sidebar.dataframe(ref_info_df[["TIN", "GROUP_NPI", "ID"]], hide_index=True)

st.divider()
st.sidebar.write("Developed by Colby Reyes")
st.sidebar.write("Contact at colbyr@hs.uci.edu")


## main body
st.title("Incentive Posting Pre-Processor")


# select incentive type
inc_type = st.selectbox("Incentive Type:", ["Prop56", "N419", "N423"], index=0)
# initialize session state variables
if "run_button_clicked" not in st.session_state:
    st.session_state.run_button_clicked = False
# st.write(f"Run button clicked: `{st.session_state.run_button_clicked}`")

if "file_uploaded" not in st.session_state:
    st.session_state.file_uploaded = False
# st.write(f"File uploaded: `{st.session_state.file_uploaded}`")

if "pwd" not in st.session_state:
    st.session_state.pwd = None
# st.write(f"pwd: `{st.session_state.pwd}`")

if "logMsgs" not in st.session_state:
    st.session_state.logMsgs = None
# st.write(f"log msgs: `{st.session_state.logMsgs}`")

if "remits_df" not in st.session_state:
    st.session_state.remits_df = None
# st.write(f"remits_df: `{st.session_state.remits_df}`")

if "report_file" not in st.session_state:
    st.session_state.report_file = None
# st.write(f"report file: `{st.session_state.report_file}`")

if "load_msg" not in st.session_state:
    st.session_state.load_msg = ""
# st.write(f"load msg: {st.session_state.load_msg}")

if "export_button_clicked" not in st.session_state:
    st.session_state.export_button_clicked = False

if "final_output_df" not in st.session_state:
    st.session_state.final_output_df = None


def new_upload():
    st.session_state.file_uploaded = True
    st.session_state.load_msg = ""
    st.session_state.remits_df = None
    st.session_state.logMsgs = None


st.session_state.report_file = st.file_uploader(
    "Upload report file here",
    type=["xlsx"],
    accept_multiple_files=False,
    on_change=new_upload,
)

user_input_cont = st.empty()


def load_and_process():
    os.makedirs("./tempDir", exist_ok=True)
    with open(os.path.join("./tempDir", st.session_state.report_file.name), "wb") as f:
        f.write(st.session_state.report_file.getbuffer())

    report_file_path = os.path.join("./tempDir", st.session_state.report_file.name)

    with st.spinner("Analyzing...."):
        st.session_state.load_msg, df = utils.load_remitList_spreadsheet(
            report_file_path, st.session_state.pwd
        )
    
    if df is not None:
        st.session_state.remits_df = utils.prep_data_for_verification(df)
        # st.write(st.session_state.remits_df.dtypes)

    try:
        shutil.rmtree("./tempDir", ignore_errors=False)
    except PermissionError as pe:
        st.warning(f"Permission Denied: {pe}")
    except OSError as oe:
        st.warning(f"OS Error: {oe}")


load_msg_ctr = st.empty()
if st.session_state.load_msg == "":
    pass
elif st.session_state.load_msg == "Success!":
    user_input_cont.empty()
    st.session_state.run_button_clicked = True
    st.session_state.file_uploaded = False
    # load_msg_ctr.success(st.session_state.load_msg)
    # time.sleep(0.5)
    # load_msg_ctr.empty()

elif "PLEASE RE-ENTER PASSWORD" in st.session_state.load_msg:
    st.session_state.run_button_clicked = False
    st.session_state.file_uploaded = True
    st.session_state.logMsgs = None
    st.session_state.remits_df = None
    df = None
    load_msg_ctr.warning(st.session_state.load_msg)

elif "Unencrypted file" in st.session_state.load_msg:
    user_input_cont.empty()
    st.session_state.run_button_clicked = True
    st.session_state.file_uploaded = False
    load_msg_ctr.success(st.session_state.load_msg)
    time.sleep(3)
    load_msg_ctr.empty()

elif "could not infer" in st.session_state.load_msg:
    user_input_cont.empty()
    st.session_state.run_button_clicked = True
    st.session_state.file_uploaded = False
    load_msg_ctr.success(st.session_state.load_msg)
    

else:
    st.session_state.run_button_clicked = False
    st.session_state.file_uploaded = True
    st.session_state.logMsgs = None
    st.session_state.remits_df = None
    df = None
    load_msg_ctr.error(st.session_state.load_msg)

if "dataEditor_expanded" not in st.session_state:
    st.session_state.dataEditor_expanded = True

c1, c2, c3, c4 = st.columns([1, 2, 2, 1])


if st.session_state.file_uploaded:
    with user_input_cont:
        st.session_state.pwd = c2.text_input(
            "Enter spreadsheet password: ", type="password"
        )
        c3.markdown("")
        c3.markdown("")
        c3.button("Run", on_click=load_and_process, type="primary")
        # c3.button("Run",on_click=run_and_clear_container)
        user_input_cont.empty()


# @st.cache_data
def export_to_csv(df: pd.DataFrame):
    # IMORTANT: cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode("utf-8")


if st.session_state.run_button_clicked and st.session_state.remits_df is not None:
    with st.expander(":white_check_mark: Data to Verify", expanded=st.session_state.dataEditor_expanded):
        st.subheader(":white_check_mark: Data to Verify")
        # st.table(st.session_state.remits_df)
        if "No" not in st.session_state.remits_df.columns:
            st.session_state.remits_df.insert(loc=0, column="No", value=False)
        if "Yes" not in st.session_state.remits_df.columns:
            st.session_state.remits_df.insert(loc=0, column="Yes", value=False)
        num_rows = len(st.session_state.remits_df)
        editor_height = 100 + (35 * (num_rows - 1))
        edited_df = st.data_editor(
            st.session_state.remits_df,
            use_container_width=True,
            num_rows="fixed",
            height=editor_height,
            disabled=[
                "Check #",
                "Process Errors",
                "Amount",
                "Deposit Date",
                "Tax ID",
                "NPI",
            ],
            column_config={
                "Amount": st.column_config.NumberColumn(
                    "Amount (USD)", help="Total check amount", format="$%2f"
                ),
                "Yes": st.column_config.CheckboxColumn(
                    "Yes",
                    help="Check box to indicate that check has been verified as an incentive payment",
                    default=False,
                ),
                "No": st.column_config.CheckboxColumn(
                    "No",
                    help="Check box to indicate that check has is *NOT* an incentive payment",
                    default=False,
                ),
                "Tax ID": st.column_config.NumberColumn("Tax ID", format="%s"),
                "NPI": st.column_config.NumberColumn("NPI", format="%s"),
            },
        )
        # st.write(st.session_state.remits_df.dtypes)

        s = edited_df[edited_df["Yes"] == True]["Amount"].sum().round(2)  # noqa: E712
        df_for_export = edited_df[edited_df["Yes"] == True]  # noqa: E712
        # st.write(f"Total Amount: ${s}")
        st.markdown("Total Incentive Amount: :green[**${:,}**]".format(s))

        def fill_and_export():
            st.session_state.final_output_df: pd.DataFrame = utils.fill_posting_data(
                df_for_export, inc_type
            )
            st.session_state.export_button_clicked = True
            st.session_state.run_button_clicked = False
            st.session_state.dataEditor_expanded = False
            return st.session_state.final_output_df

        st.button(
            "Process and Export for Posting",
            help="Once you are done verifying which checks are incentives, click this button to export the data to a spreadsheet that is ready for quick copy-paste posting",  # noqa: E501
            on_click=fill_and_export,
            type="primary",
            use_container_width=True,
        )
dt_now = datetime.today().date().isoformat()
if st.session_state.export_button_clicked:
    st.divider()
    dlc1, dlc2, dlc3 = st.columns([2, 9, 2])
    dlc1.subheader("File is ready!")

    fname = f"{inc_type}_PostingSheet_{dt_now}.csv"
    csv = export_to_csv(
        st.session_state.final_output_df[
            ["Check #", "Comment1", "Clearing Account", "Amount", "Comment2", "Posted?"]
        ]
    )

    dlc3.download_button(
        label="Download as CSV", data=csv, file_name=fname, mime="text/csv"
    )

    st.data_editor(
        st.session_state.final_output_df,
        use_container_width=True,
        num_rows="fixed",
        hide_index=True,
    )
