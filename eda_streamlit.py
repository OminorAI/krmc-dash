import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import hmac
from plotly.subplots import make_subplots


def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False


if not check_password():
    st.warning("Please enter the password to continue.")
    st.stop()  # Do not continue if check_password is not True.

# Set the title of the dashboard
st.title("KRMC Pharmacy Data Analysis Dashboard")

# Introduction
st.markdown(
    """
This dashboard presents an exploratory data analysis (EDA) on KRMC's Pharmacy Data.
"""
)

# Load the data
df = pd.read_csv(
    "anon_krmc_five_year_data_19_23.csv",
    low_memory=False,
    index_col=0,
)
df["Script Date"] = pd.to_datetime(df["Script Date"]).dt.date
df["Script Date"] = pd.to_datetime(df["Script Date"])
df["Year"] = df["Script Date"].dt.year

st.header("1. Financial Analysis")

# Filtering data
df = df[df["Retail"] < 65000]
df_fa = df.copy()

total_retail_sales = df[df['Year']==2023]["Retail"].sum()
total_cost_sales = df[df['Year']==2023]["Cost"].sum()
st.write(f"Sum of all retail sales: R{total_retail_sales:,.2f} in 2023")
st.write(f"Sum of cost of sales: R{total_cost_sales:,.2f} in 2023")
st.write(f"Total Gross Profit: R{total_retail_sales - total_cost_sales:,.2f} in 2023")
# Updated Distribution of Retail Prices
df_fa['Year'] = df_fa['Year'].astype(str)
fig2 = px.histogram(
    df_fa, x="Retail", nbins=1000, title="Distribution of Retail Prices after Filtering", color="Year"
)
st.plotly_chart(fig2, use_container_width=True)

# Gross profit over the period
gross_profit = df_fa["Retail"].sum() - df_fa["Cost"].sum()
period = (
    df_fa["Script Date"].min().strftime("%d-%b-%Y")
    + " to "
    + df_fa["Script Date"].max().strftime("%d-%b-%Y")
)
st.write(f"Gross profit over the period {period}: R{gross_profit:,.2f}")

# Gross profit over time
df_fa["gross_profit"] = df_fa["Retail"] - df_fa["Cost"]
df_fa_gp = (
    df_fa.groupby("Script Date")[["Cost", "Retail", "gross_profit"]].sum().reset_index()
)
fig3 = px.histogram(
    df_fa_gp, x="Script Date", y="gross_profit", title="Gross Profit over Time", nbins=60
)
st.plotly_chart(fig3, use_container_width=True)

rolling_window = st.number_input(
    "Enter the rolling window for moving average",
    min_value=1,
    max_value=365,
    value=14,
    step=1,
)
df_fa_gp["gross_profit_moving_avg"] = (
    df_fa_gp["gross_profit"].rolling(window=rolling_window).mean()
)
fig = px.line(
    df_fa_gp,
    x="Script Date",
    y="gross_profit_moving_avg",
    title=f"Gross Profit Moving Average over Time with {rolling_window} days window",
)
st.plotly_chart(fig, use_container_width=True)

# Average profit by month
df_fa["Month"] = df_fa["Script Date"].dt.month
df_fa_gp_month = df_fa.groupby("Month")[["gross_profit"]].mean().reset_index()
fig5 = px.bar(
    df_fa_gp_month, x="Month", y="gross_profit", title="Average Profit by Month"
)
st.plotly_chart(fig5, use_container_width=True)

# # Sum and gross profit by sector
# df_fa['Sctno'] = df_fa['Sctno'].astype('str')
# df_fa_s_fa = df_fa.groupby('Sctno')[['Retail', 'Cost', 'gross_profit']].sum().reset_index()
# fig4 = px.bar(df_fa_s_fa, x='Sctno', y='gross_profit', title='Gross Profit by Sector')
# st.plotly_chart(fig4)
df_fa["Sctno"] = df_fa["Sctno"].astype("str")
df_fa_s_fa = (
    df_fa.groupby("Sctno")[["Cost", "Retail", "gross_profit"]].sum().reset_index()
)
fig = go.Figure()
fig.add_trace(go.Box(y=df_fa_s_fa["Cost"], name="Cost"))
fig.add_trace(go.Box(y=df_fa_s_fa["Retail"], name="Retail"))
fig.add_trace(go.Box(y=df_fa_s_fa["gross_profit"], name="Gross Profit"))
fig.update_layout(title="Box and Whisker Plot of Cost, Retail and Gross Profit")
st.plotly_chart(fig, use_container_width=True)

st.header("2. Operational Analysis")

df_disp = (
    df.drop_duplicates(subset=["Sctno"])
    .groupby(["Script Date", "Dispenser"])["Sctno"]
    .count()
    .reset_index()
)
df_disp["Script Date"] = pd.to_datetime(df_disp["Script Date"]).dt.date
# if there are days missing for a dispenser, fill with 0
df_disp_all_days = (
    df_disp.set_index(["Script Date", "Dispenser"])
    .unstack("Dispenser")
    .fillna(0)
    .stack("Dispenser")
    .reset_index()
)
# line plot with a line for each dispenser
fig = px.line(
    df_disp_all_days,
    x="Script Date",
    y="Sctno",
    color="Dispenser",
    title="Number of Scripts per Day",
)
st.plotly_chart(fig, use_container_width=True)

disp_roll_window = st.number_input(
    "Enter the rolling window for moving average for Number of Scripts per Day",
    min_value=1,
    max_value=365,
    value=30,
    step=1,
)
df_disp_all_days["Sctno_moving_avg"] = df_disp_all_days.groupby("Dispenser")[
    "Sctno"
].transform(lambda x: x.rolling(window=disp_roll_window).mean())
fig = px.line(
    df_disp_all_days,
    x="Script Date",
    y="Sctno_moving_avg",
    color="Dispenser",
    title=f"Scripts Moving Average over Time with {disp_roll_window} days window",
)
st.plotly_chart(fig, use_container_width=True)

df_disp_stats = df_disp.groupby("Dispenser")["Sctno"].describe().reset_index()
df_disp_stats["mean_of_means"] = df_disp_stats["mean"].mean()
fig = px.bar(
    df_disp_stats,
    x="Dispenser",
    y="count",
    title="Number of days active at KRMC Dispensary",
)
st.plotly_chart(fig, use_container_width=True)
fig = px.bar(
    df_disp_stats, x="Dispenser", y="mean", title="Mean Scripts per Day per Dispenser"
)
fig.add_trace(
    go.Scatter(
        x=df_disp_stats["Dispenser"],
        y=df_disp_stats["mean_of_means"],
        name="Mean for All",
    )
)
st.plotly_chart(fig, use_container_width=True)
df_disp["Script Date"] = pd.to_datetime(df_disp["Script Date"]).dt.date


def calculate_hours_open(row):
    day_of_week = row["Script Date"].weekday()
    year = row["Script Date"].year

    if day_of_week == 6:  # Sunday
        return 0
    elif day_of_week == 5:  # Saturday
        return 4
    else:  # Weekday
        if year < 2023:
            return 9
        else:
            return 11


# Apply the function to each row
df_disp["no_of_hours_open"] = df_disp.apply(calculate_hours_open, axis=1)
df_disp["rate_of_scripts"] = df_disp["Sctno"] / df_disp["no_of_hours_open"]
df_disp = df_disp[df_disp["no_of_hours_open"] != 0]
df_disp_sr_mean = df_disp.groupby("Dispenser")["rate_of_scripts"].mean().reset_index()
fig = px.bar(
    df_disp_sr_mean,
    x="Dispenser",
    y="rate_of_scripts",
    title="Mean Scripts per Hour per Dispenser",
)
st.plotly_chart(fig, use_container_width=True)

st.header("3. Product Analysis")
df["Year"] = df["Year"].astype(str)
df_product_sales = (
    df.groupby(["Item Description", "Year"])[["Retail", "Cost"]].sum().reset_index()
)
df_product_volume = (
    df.groupby(["Item Description", "Year"])["Sctno"]
    .count()
    .reset_index()
    .rename(columns={"Sctno": "Volume"})
)
df_product_sales_volume = pd.merge(
    df_product_sales, df_product_volume, on=["Item Description", "Year"]
)

df_product_sales_exc_year = (
    df.groupby(["Item Description"])[["Retail", "Cost"]].sum().reset_index()
)
df_product_volume_exc_year = (
    df.groupby(["Item Description"])["Sctno"]
    .count()
    .reset_index()
    .rename(columns={"Sctno": "Volume"})
)
df_product_sales_volume_exc_year = pd.merge(
    df_product_sales, df_product_volume, on=["Item Description"]
)
top_10_products = (
    df_product_sales_volume_exc_year.sort_values(by="Volume", ascending=False)
    .drop_duplicates("Item Description", keep="first")
    .head(10)["Item Description"]
    .tolist()
)

df_product_sales_volume_top_10 = df_product_sales_volume[df_product_sales_volume["Item Description"].isin(top_10_products)]
# make a seperate line for each year

fig = px.bar(
    df_product_sales_volume_top_10,
    y="Volume",
    x="Item Description",
    title="Top 10 Products by Volume",
    color="Year",
    barmode="group",
)
st.plotly_chart(fig, use_container_width=True)

df["Script Date Month"] = (
    pd.to_datetime(df["Script Date"]).dt.to_period("M").astype(str)
)
products = (
    df_product_sales_volume.sort_values(by="Volume", ascending=False)
    .drop_duplicates("Item Description", keep="first")["Item Description"]
    .tolist()
)
df_product_monthly_volume = (
    df.groupby(["Script Date Month", "Item Description"])["Sctno"].count().reset_index()
)

df_products_gross_profit = (
    df.groupby("Item Description")[["Retail", "Cost"]].sum().reset_index()
)
df_products_gross_profit["Gross Profit"] = (
    df_products_gross_profit["Retail"] - df_products_gross_profit["Cost"]
)
df_products_gross_profit_top_10 = df_products_gross_profit.sort_values(
    by="Gross Profit", ascending=False
).head(10)
fig = px.bar(
    df_products_gross_profit_top_10,
    y="Gross Profit",
    x="Item Description",
    title="Top 10 Products by Gross Profit",
    orientation="v",
)
st.plotly_chart(fig, use_container_width=True)
item = st.selectbox("Select Product", products)
# for item in top_10_products:
temp_df = df_product_monthly_volume[
    df_product_monthly_volume["Item Description"] == item
]
fig = px.line(
    temp_df, x="Script Date Month", y="Sctno", title=f"Monthly Volume for {item}"
)
st.plotly_chart(fig, use_container_width=True)


df_product_monthly_volume["Script Date Month"] = pd.to_datetime(
    df_product_monthly_volume["Script Date Month"]
)
df_product_monthly_volume["Month"] = df_product_monthly_volume[
    "Script Date Month"
].dt.month
df_product_only_monthly_volume = (
    df_product_monthly_volume.groupby(["Month", "Item Description"])["Sctno"]
    .mean()
    .reset_index()
)
df_product_only_monthly_volume["Month"] = df_product_only_monthly_volume[
    "Month"
].replace(
    {
        1: "Jan",
        2: "Feb",
        3: "Mar",
        4: "Apr",
        5: "May",
        6: "Jun",
        7: "Jul",
        8: "Aug",
        9: "Sep",
        10: "Oct",
        11: "Nov",
        12: "Dec",
    }
)
df_product_monthly_qty = (
    df.groupby(["Script Date Month", "Item Description"])["Qty"].sum().reset_index()
)
df_product_monthly_qty["Script Date Month"] = pd.to_datetime(
    df_product_monthly_qty["Script Date Month"]
)
df_product_monthly_qty["Month"] = df_product_monthly_qty["Script Date Month"].dt.month
df_product_only_monthly_qty = (
    df_product_monthly_qty.groupby(["Month", "Item Description"])["Qty"]
    .mean()
    .reset_index()
)
df_product_only_monthly_qty["Month"] = df_product_only_monthly_qty["Month"].replace(
    {
        1: "Jan",
        2: "Feb",
        3: "Mar",
        4: "Apr",
        5: "May",
        6: "Jun",
        7: "Jul",
        8: "Aug",
        9: "Sep",
        10: "Oct",
        11: "Nov",
        12: "Dec",
    }
)

df_product_monthly_volume_quantity = df_product_monthly_volume.merge(
    df_product_monthly_qty, on=["Month", "Item Description", "Script Date Month"]
)

temp_df = df_product_monthly_volume_quantity[
    df_product_monthly_volume_quantity["Item Description"] == item
]
temp_df = temp_df[["Month", "Sctno", "Qty"]].groupby("Month").mean().reset_index()

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(
    go.Scatter(x=temp_df["Month"], y=temp_df["Sctno"], name="Volume", mode="lines"),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=temp_df["Month"], y=temp_df["Qty"], name="Quantity", mode="lines"),
    secondary_y=True,
)
fig.update_layout(title=f"Monthly Volume and Quantity for Product {item}")
fig.update_xaxes(title_text="Date")
fig.update_yaxes(title_text="Volume", secondary_y=False)
fig.update_yaxes(title_text="Quantity", secondary_y=True)
st.plotly_chart(fig, use_container_width=True)


df_product_monthly_volume_year = (
    df.groupby(["Script Date Month", "Item Description", "Year"])["Sctno"]
    .count()
    .reset_index()
)
df_product_monthly_volume_year["Month"] = pd.to_datetime(
    df_product_monthly_volume_year["Script Date Month"]
).dt.month
df_product_monthly_volume_year = df_product_monthly_volume_year.sort_values(
    by=["Year", "Month"]
)
df_product_monthly_volume_year["Month"] = df_product_monthly_volume_year[
    "Month"
].replace(
    {
        1: "Jan",
        2: "Feb",
        3: "Mar",
        4: "Apr",
        5: "May",
        6: "Jun",
        7: "Jul",
        8: "Aug",
        9: "Sep",
        10: "Oct",
        11: "Nov",
        12: "Dec",
    }
)

df_product_monthly_qty_year = (
    df.groupby(["Script Date Month", "Item Description", "Year"])["Qty"]
    .sum()
    .reset_index()
)
df_product_monthly_qty_year["Month"] = pd.to_datetime(
    df_product_monthly_qty_year["Script Date Month"]
).dt.month
df_product_monthly_qty_year = df_product_monthly_qty_year.sort_values(
    by=["Year", "Month"]
)
df_product_monthly_qty_year["Month"] = df_product_monthly_qty_year["Month"].replace(
    {
        1: "Jan",
        2: "Feb",
        3: "Mar",
        4: "Apr",
        5: "May",
        6: "Jun",
        7: "Jul",
        8: "Aug",
        9: "Sep",
        10: "Oct",
        11: "Nov",
        12: "Dec",
    }
)

years_to_compare = st.multiselect(
    f"Select Years to Compare for {item}",
    ["2020", "2021", "2022", "2023"],
    ["2022", "2023"],
)
df_product_monthly_volume_quantity_year = df_product_monthly_volume_year.merge(
    df_product_monthly_qty_year,
    on=["Month", "Item Description", "Script Date Month", "Year"],
)
temp_df = df_product_monthly_volume_quantity_year[
    df_product_monthly_volume_quantity_year["Item Description"] == item
]
temp_df = (
    temp_df[["Month", "Sctno", "Qty", "Year"]]
    .groupby(["Month", "Year"])
    .mean()
    .reset_index()
)
fig = make_subplots(specs=[[{"secondary_y": True}]])
for year in years_to_compare:
    temp_df_year = temp_df[temp_df["Year"] == year]
    fig.add_trace(
        go.Scatter(
            x=temp_df_year["Month"],
            y=temp_df_year["Sctno"],
            name=f"Volume {year}",
            mode="lines",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=temp_df_year["Month"],
            y=temp_df_year["Qty"],
            name=f"Quantity {year}",
            mode="lines",
        ),
        secondary_y=True,
    )
fig.update_layout(title=f"Monthly Volume and Quantity for Product {item} by Year")
fig.update_xaxes(title_text="Date")
fig.update_yaxes(title_text="Volume", secondary_y=False)
fig.update_yaxes(title_text="Quantity", secondary_y=True)
st.plotly_chart(fig, use_container_width=True)

df_product_medical_aid = (
    df.groupby(["Medical Aid", "Item Description"])["Sctno"].count().reset_index()
)
medical_aids = (
    df_product_medical_aid.groupby("Medical Aid")["Sctno"]
    .sum()
    .sort_values(ascending=False)
    .index.tolist()
)
medical_aid = st.selectbox("Select Medical Aid", medical_aids)
temp_df = df_product_medical_aid[df_product_medical_aid["Medical Aid"] == medical_aid]
temp_top_5_products = (
    temp_df.groupby("Item Description")["Sctno"]
    .sum()
    .sort_values(ascending=False)
    .head(5)
    .reset_index()
)
fig = px.bar(
    temp_top_5_products,
    x="Sctno",
    y="Item Description",
    title=f"Top 5 Products for {medical_aid} Medical Aid",
)
st.plotly_chart(fig, use_container_width=True)


st.header("4. Doctor Analysis")

# # Gross profit by doctor
krmc_doctors = ["FERNANDES", "CHEUNG", "WISE", "BOSMAN", "OLIVIER", "SMITH", "ASMAL"]

dr_gp_rolling_window = st.number_input(
    "Enter the rolling window for moving average for Gross Profit by Doctor",
    min_value=1,
    max_value=365,
    value=14,
    step=1,
)
df_int_docs = df_fa[df_fa["Doctor"].isin(krmc_doctors)]
df_int_docs_gp = (
    df_int_docs.groupby(["Doctor", "Script Date"])[["gross_profit"]].sum().reset_index()
)
df_int_docs_gp["gross_profit_moving_avg"] = df_int_docs_gp.groupby("Doctor")[
    "gross_profit"
].transform(lambda x: x.rolling(window=dr_gp_rolling_window).mean())
fig6 = px.line(
    df_int_docs_gp,
    x="Script Date",
    y="gross_profit_moving_avg",
    color="Doctor",
    title=f"Gross Profit by KRMC Doctor over Time with {dr_gp_rolling_window} days window",
)
st.plotly_chart(fig6, use_container_width=True)

df_krmc_doctors = df[df["Doctor"].isin(krmc_doctors)]
df_krmc_doctors_monthly_volume = (
    df_krmc_doctors.groupby(["Script Date Month", "Doctor"])["Sctno"]
    .count()
    .reset_index()
)
df_krmc_doctors_monthly_volume["Script Date Month"] = pd.to_datetime(
    df_krmc_doctors_monthly_volume["Script Date Month"]
)
fig = px.line(
    df_krmc_doctors_monthly_volume,
    x="Script Date Month",
    y="Sctno",
    color="Doctor",
    title="Monthly Script Volumes for KRMC Doctors",
)
st.plotly_chart(fig, use_container_width=True)

df_krmc_doctors_monthly_volume["Month"] = df_krmc_doctors_monthly_volume[
    "Script Date Month"
].dt.month
df_krmc_doctors_monthly_volume_only = (
    df_krmc_doctors_monthly_volume.groupby(["Month", "Doctor"])["Sctno"]
    .mean()
    .reset_index()
)
df_krmc_doctors_monthly_volume_only["Month"] = df_krmc_doctors_monthly_volume_only[
    "Month"
].replace(
    {
        1: "Jan",
        2: "Feb",
        3: "Mar",
        4: "Apr",
        5: "May",
        6: "Jun",
        7: "Jul",
        8: "Aug",
        9: "Sep",
        10: "Oct",
        11: "Nov",
        12: "Dec",
    }
)
fig = px.line(
    df_krmc_doctors_monthly_volume_only,
    x="Month",
    y="Sctno",
    color="Doctor",
    title="Monthly Script Volumes for KRMC Doctors",
)
st.plotly_chart(fig, use_container_width=True)


external_doctors = df[~df["Doctor"].isin(krmc_doctors)]["Doctor"].unique().tolist()
external_doctors.remove("KRMC DISPENSARY")
df_external_doctors = df[df["Doctor"].isin(external_doctors)]
df_external_doctors_monthly_volume = (
    df_external_doctors.groupby(["Script Date Month", "Doctor"])["Sctno"]
    .count()
    .reset_index()
)
df_external_doctors_monthly_volume["Script Date Month"] = pd.to_datetime(
    df_external_doctors_monthly_volume["Script Date Month"]
)
top_5_external_doctors = (
    df_external_doctors_monthly_volume.groupby("Doctor")["Sctno"]
    .sum()
    .sort_values(ascending=False)
    .head(5)
    .index.tolist()
)
df_external_doctors_monthly_volume = df_external_doctors_monthly_volume[
    df_external_doctors_monthly_volume["Doctor"].isin(top_5_external_doctors)
]
fig = px.line(
    df_external_doctors_monthly_volume,
    x="Script Date Month",
    y="Sctno",
    color="Doctor",
    title="Monthly Script Volumes for Top 5 External Doctors",
)
st.plotly_chart(fig, use_container_width=True)

df_external_doctors_monthly_volume_2023 = df_external_doctors_monthly_volume[
    df_external_doctors_monthly_volume["Script Date Month"] >= "2023-01-01"
]
df_external_doctors_monthly_volume_2023["Month"] = (
    df_external_doctors_monthly_volume_2023["Script Date Month"].dt.month
)
df_external_doctors_monthly_volume_only = (
    df_external_doctors_monthly_volume_2023.groupby(["Month", "Doctor"])["Sctno"]
    .mean()
    .reset_index()
)
df_external_doctors_monthly_volume_only[
    "Month"
] = df_external_doctors_monthly_volume_only["Month"].replace(
    {
        1: "Jan",
        2: "Feb",
        3: "Mar",
        4: "Apr",
        5: "May",
        6: "Jun",
        7: "Jul",
        8: "Aug",
        9: "Sep",
        10: "Oct",
        11: "Nov",
        12: "Dec",
    }
)
fig = px.line(
    df_external_doctors_monthly_volume_only,
    x="Month",
    y="Sctno",
    color="Doctor",
    title="Monthly Script Volumes for Top 5 External Doctors in 2023",
)
st.plotly_chart(fig, use_container_width=True)


krmc_doctor = st.selectbox("Select KRMC Doctor", krmc_doctors)
# Top 5 Products for Each Doctor
df_krmc_doctors = df[df["Doctor"] == krmc_doctor]
df_krmc_doctors_top_5 = (
    df_krmc_doctors.groupby(["Doctor", "Item Description"])["Sctno"]
    .count()
    .reset_index()
)
doctor_items_dict = {}
for doctor in krmc_doctors:
    temp_df = df_krmc_doctors_top_5[df_krmc_doctors_top_5["Doctor"] == doctor]
    temp_df = (
        temp_df.groupby("Item Description")["Sctno"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .reset_index()
    )
    doctor_items_dict[doctor] = temp_df["Item Description"].tolist()

df_int_docs_ma = df_fa[df_fa["Doctor"].isin(krmc_doctors)]
df_int_docs_ma["Script Date Month"] = (
    pd.to_datetime(df_int_docs_ma["Script Date"]).dt.to_period("M").astype(str)
)
df_int_docs_ma = (
    df_int_docs_ma.groupby(["Script Date Month", "Doctor", "Item Description"])["Sctno"]
    .count()
    .reset_index()
)
df_int_docs_ma["Script Date Month"] = pd.to_datetime(
    df_int_docs_ma["Script Date Month"]
)
df_int_docs_ma["Month"] = df_int_docs_ma["Script Date Month"].dt.month
df_int_docs_ma = (
    df_int_docs_ma.groupby(["Month", "Doctor", "Item Description"])["Sctno"]
    .mean()
    .reset_index()
    .sort_values(by=["Doctor", "Month"])
)
df_int_docs_ma["Month"] = df_int_docs_ma["Month"].replace(
    {
        1: "Jan",
        2: "Feb",
        3: "Mar",
        4: "Apr",
        5: "May",
        6: "Jun",
        7: "Jul",
        8: "Aug",
        9: "Sep",
        10: "Oct",
        11: "Nov",
        12: "Dec",
    }
)

temp_df = df_int_docs_ma[df_int_docs_ma["Doctor"] == krmc_doctor]
temp_df = temp_df.groupby(["Item Description", "Month"])["Sctno"].sum().reset_index()
temp_df = temp_df[
    temp_df["Item Description"].isin(doctor_items_dict.get(krmc_doctor, []))
]
temp_df["Month"] = pd.Categorical(
    temp_df["Month"],
    categories=[
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ],
    ordered=True,
)
fig = px.line(
    temp_df.sort_values(by=["Month"]),
    x="Month",
    y="Sctno",
    color="Item Description",
    title=f"Top 5 Products by Month for {krmc_doctor}",
)
st.plotly_chart(fig, use_container_width=True)

df_krmc_doctors_top_5 = (
    df_krmc_doctors.groupby(["Doctor", "Item Description"])["Sctno"]
    .count()
    .reset_index()
)

temp_df = df_krmc_doctors_top_5[df_krmc_doctors_top_5["Doctor"] == krmc_doctor]
temp_df = (
    temp_df.groupby("Item Description")["Sctno"]
    .sum()
    .sort_values(ascending=False)
    .head(5)
    .reset_index()
)
fig = px.bar(
    temp_df.sort_values(by="Sctno", ascending=False),
    y="Sctno",
    x="Item Description",
    title=f"Top 5 Products by Scipt Volume for {krmc_doctor}",
)
fig.update_layout(xaxis_title="Script Volume")
st.plotly_chart(fig, use_container_width=True)


# Conclusion
st.header("Conclusion")
st.markdown(
    """
This dashboard provides a comprehensive analysis of the KRMC Pharmacy Data, showcasing sales distribution, profit margins, and performance by sectors and doctors over time.
"""
)
