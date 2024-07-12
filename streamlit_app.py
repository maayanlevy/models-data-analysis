import streamlit as st
import pandas as pd
import plotly.express as px
import json
from streamlit_plotly_events import plotly_events

# Load the data
@st.cache_data
def load_data():
    try:
        with open('models.json', 'r') as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        df['Release Date'] = pd.to_datetime(df['Release Date'], format='%Y-%m-%d', errors='coerce')
        df = df.dropna(subset=['Release Date'])
        df['Organization'] = df['Organization'].fillna('Unknown')
        df['Year-Month'] = df['Release Date'].dt.to_period('M').astype(str)
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
    
    # Create monthly counts by organization
    monthly_counts = df.groupby(['Year-Month', 'Organization']).size().unstack(fill_value=0)
    
    # Calculate cumulative sums for total available models
    cumulative_counts = monthly_counts.cumsum()

    # Create a color map for companies
    companies = df['Organization'].unique()
    color_map = px.colors.qualitative.Plotly + px.colors.qualitative.Set1 + px.colors.qualitative.Pastel
    company_colors = {company: color_map[i % len(color_map)] for i, company in enumerate(companies)}

    # Add options to switch between new releases and total available models, and graph types
    col1, col2 = st.columns(2)
    with col1:
        data_type = st.radio(
            "Select data type:",
            ("Number of Available Models", "Newly Released Models per Month")
        )
    with col2:
        graph_type = st.radio(
            "Select graph type:",
            ("Stacked Area", "Line (Total)", "Line (Stacked)")
        )

    if data_type == "Number of Available Models":
        plot_data = cumulative_counts
        title_prefix = 'Total Number of Available LLM Models'
    else:
        plot_data = monthly_counts
        title_prefix = 'Newly Released LLM Models per Month'

    # Create the selected graph
    if graph_type == "Stacked Area":
        fig = px.area(plot_data, x=plot_data.index, y=plot_data.columns, 
                      title=f'{title_prefix} by Company (Stacked Area)',
                      labels={'value': 'Number of Models', 'Year-Month': 'Month'},
                      color_discrete_map=company_colors)
    elif graph_type == "Line (Total)":
        plot_data_total = plot_data.sum(axis=1)
        fig = px.line(x=plot_data_total.index, y=plot_data_total.values,
                      title=f'{title_prefix} (Total)',
                      labels={'x': 'Month', 'y': 'Number of Models'},
                      )
    else:  # Line (Stacked)
        fig = px.line(plot_data, x=plot_data.index, y=plot_data.columns, 
                      title=f'{title_prefix} by Company (Line)',
                      labels={'value': 'Number of Models', 'Year-Month': 'Month'},
                      color_discrete_map=company_colors)

    fig.update_layout(legend_title_text='Company')
    
    # Make the graph interactive
    selected_points = plotly_events(fig, click_event=True, hover_event=False)
    
    # Debug: Display selected points
    st.write("Selected points:", selected_points)

    # Display models for the selected month
    if selected_points:
        selected_month = selected_points[0]['x']
        st.write("Selected month:", selected_month)  # Debug: Display selected month

        # Extract year and month from selected_month
        selected_month_str = pd.to_datetime(selected_month).strftime('%Y-%m')
        
        if selected_month_str in df['Year-Month'].values:
            st.subheader(f"Models released in {selected_month_str}")
            month_df = df[df['Year-Month'] == selected_month_str]
            st.dataframe(month_df[['Model', 'Organization', 'Release Date']])
        else:
            st.write(f"No data for the selected month: {selected_month_str}")

    # Allow exploration by company
    company_model_counts = df['Organization'].value_counts()
    companies = company_model_counts.index.tolist()
    company_options = [f"{company} ({count} models)" for company, count in zip(companies, company_model_counts)]
    
    selected_company_option = st.selectbox('Select a company:', company_options)
    selected_company = selected_company_option.split(' (')[0]

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

    # Display data quality issues
    missing_orgs = df['Organization'].isnull().sum()
    if missing_orgs > 0:
        st.warning(f"There are {missing_orgs} models with missing organization information.")

    missing_dates = df['Release Date'].isnull().sum()
    if missing_dates > 0:
        st.warning(f"There are {missing_dates} models with missing or invalid release dates.")
else:
    st.error("No data available. Please fix the JSON file and restart the app.")
