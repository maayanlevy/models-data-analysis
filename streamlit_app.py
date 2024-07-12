import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import json

# Load the data
@st.cache_data
def load_data():
    try:
        with open('models.json', 'r') as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        df['Release Date'] = pd.to_datetime(df['Release Date'], format='%Y-%m-%d', errors='coerce')
        df = df.dropna(subset=['Release Date'])
        return df
    except json.JSONDecodeError as e:
        st.error(f"Error parsing JSON file: {str(e)}")
        st.error("Please check your models.json file for syntax errors.")
        st.error(f"Error occurs near line {e.lineno}, column {e.colno}")
        with open('models.json', 'r') as f:
            lines = f.readlines()
        st.code("".join(lines[max(0, e.lineno-3):e.lineno+2]), language="json")
        return pd.DataFrame()

df = load_data()

# Only proceed if we have data
if not df.empty:
    # Set up the Streamlit app
    st.title('LLM Release Explorer')

    # Create a monthly graph of released models
    df['Year-Month'] = df['Release Date'].dt.to_period('M')
    monthly_counts = df.groupby('Year-Month').size().reset_index(name='Count')
    monthly_counts['Year-Month'] = monthly_counts['Year-Month'].astype(str)

    fig = px.bar(monthly_counts, x='Year-Month', y='Count',
                 title='Number of LLM Releases per Month',
                 labels={'Year-Month': 'Month', 'Count': 'Number of Releases'})
    st.plotly_chart(fig)

    # Allow exploration by company
    companies = sorted(df['Organization'].unique())
    selected_company = st.selectbox('Select a company:', companies)

    company_df = df[df['Organization'] == selected_company]
    st.write(f"Models released by {selected_company}:")
    st.dataframe(company_df[['Model', 'Release Date']])

    # Allow exploration by month
    months = sorted(df['Year-Month'].unique())
    selected_month = st.selectbox('Select a month:', months)

    month_df = df[df['Year-Month'] == selected_month]
    st.write(f"Models released in {selected_month}:")
    st.dataframe(month_df[['Model', 'Organization', 'Release Date']])

    # Show raw data
    if st.checkbox('Show raw data'):
        st.subheader('Raw data')
        st.write(df)
else:
    st.error("No data available. Please fix the JSON file and restart the app.")