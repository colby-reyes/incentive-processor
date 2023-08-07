# dashboard.py (main file)

# import packages
import os
import shutil
import time

import pandas as pd
import streamlit as st

# import local functions
import utils

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
    "Use exported PB Remittance data to create templates for copy-paste posting of Prop56 and CalOptima Incentive payments"
)
st.sidebar.markdown(f"Version: `{vinfo.version}`")
st.sidebar.divider()

st.sidebar.write("Developed by Colby Reyes")
st.sidebar.write("Contact at colbyr@hs.uci.edu")


## main body
st.title("Incentive Posting Pre-Processor")


# select incentive type
inc_type = st.selectbox(
    "Incentive Type:", ["Prop56", "Caloptima N419", "Caloptima N423"], index=0
)
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

else:
    st.session_state.run_button_clicked = False
    st.session_state.file_uploaded = True
    st.session_state.logMsgs = None
    st.session_state.remits_df = None
    df = None
    load_msg_ctr.error(st.session_state.load_msg)

c1, c2, c3, c4 = st.columns([1, 2, 2, 1])


if st.session_state.file_uploaded:
    with user_input_cont:
        st.session_state.pwd = c2.text_input(
            "Enter spreadsheet password: ", type="password"
        )
        c3.markdown("")
        c3.button("Run", on_click=load_and_process)
        # c3.button("Run",on_click=run_and_clear_container)
        user_input_cont.empty()


def verify_rows(df: pd.DataFrame):
    checkboxes = {}
    cc1, cc2 = st.columns([1, 8])
    for index, row in df.iterrows():
        ky = f"checkbox_{index}"
        checkboxes[ky] = cc1.checkbox("", key=ky)
        cc2.dataframe(row.T)


if st.session_state.run_button_clicked and st.session_state.remits_df is not None:
    st.subheader(":white_check_mark: Data to Verify")
    # st.table(st.session_state.remits_df)
    if "Verified?" not in st.session_state.remits_df.columns:
        st.session_state.remits_df.insert(loc=0, column="Verified?", value=False)
    edited_df = st.data_editor(
        st.session_state.remits_df,
        use_container_width=True,
        num_rows="fixed",
        height=1000,
    )
    st.write(st.session_state.remits_df.dtypes)

    s = edited_df["Amount"].sum()
    st.write(f"Total Amount: {s}")
