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

def calculate_release_cycle(df, company):
    release_dates = df[df['Organization'] == company]['Release Date'].sort_values()
    if len(release_dates) > 1:
        time_deltas = release_dates.diff().dropna()
        average_cycle = time_deltas.mean()
        months = average_cycle.days // 30
        days = average_cycle.days % 30
        return months, days
    return None, None

df = load_data()

# Custom CSS to widen the container
st.markdown("""
    <style>
    .block-container {
        max-width: 1200px;
        padding: 1rem 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Only proceed if we have data
if not df.empty:
    # Add image at the top
    st.image('geb-logo.png', width=100)
    
    # Set up the Streamlit app
    st.title('LLM Release Explorer')

    # Calculate company-level release cycles
    company_cycles = {company: calculate_release_cycle(df, company) for company in df['Organization'].unique()}
    
    # Compute overall average release cycle across all companies
    average_cycles = [pd.Timedelta(days=months * 30 + days) for months, days in company_cycles.values() if months is not None]
    if average_cycles:
        overall_average_cycle = sum(average_cycles, pd.Timedelta(0)) / len(average_cycles)
        overall_months = overall_average_cycle.days // 30
        overall_days = overall_average_cycle.days % 30
    else:
        overall_months, overall_days = 0, 0

    # Display overall average release cycle prominently
    st.markdown(f"""
        <div style="background-color: #E8F0FE; margin-bottom: 20px; padding: 20px; border-radius: 10px; text-align: center;">
            <div style="font-size: 20px; color: #5F6368;">An Average Company Updates Its Model Every</div>
            <div style="font-size: 40px; color: #1A73E8;">
                <i class="fa fa-clock-o" aria-hidden="true"></i>
                <span style="font-weight: bold;"> {overall_months} months </span> <span> {overall_days} days </span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Create sidebar filters
    st.sidebar.header('Filters')

    # Move "Select data type" and "Select graph type" to the top of the left panel
    data_type = st.sidebar.radio(
        "Select data type:",
        ("Number of Available Models", "Newly Released Models per Month")
    )
    graph_type = st.sidebar.radio(
        "Select graph type:",
        ("Stacked Area", "Line (Total)")
    )

    # Filter by company
    all_companies = df['Organization'].unique()
    selected_companies = st.sidebar.multiselect('Select companies:', all_companies, default=all_companies)
    
    # Filter by date range
    min_date = df['Release Date'].min()
    max_date = df['Release Date'].max()
    start_date, end_date = st.sidebar.date_input('Select date range:', [min_date, max_date], min_value=min_date, max_value=max_date)
    
    # Convert start_date and end_date to datetime
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    # Apply filters
    if selected_companies:
        filtered_df = df[df['Organization'].isin(selected_companies) & (df['Release Date'] >= start_date) & (df['Release Date'] <= end_date)]
    else:
        filtered_df = df[(df['Release Date'] >= start_date) & (df['Release Date'] <= end_date)]
    
    # Create monthly counts by organization
    monthly_counts = filtered_df.groupby(['Year-Month', 'Organization']).size().unstack(fill_value=0)
    
    # Calculate cumulative sums for total available models
    cumulative_counts = monthly_counts.cumsum()

    # Create a color map for companies
    companies = filtered_df['Organization'].unique()
    color_map = px.colors.qualitative.Plotly + px.colors.qualitative.Set1 + px.colors.qualitative.Pastel
    company_colors = {company: color_map[i % len(color_map)] for i, company in enumerate(companies)}

    # Create the selected graph
    if data_type == "Number of Available Models":
        plot_data = cumulative_counts
        title_prefix = 'Total Number of Available LLM Models'
    else:
        plot_data = monthly_counts
        title_prefix = 'Newly Released LLM Models per Month'

    if graph_type == "Stacked Area":
        fig = px.area(plot_data, x=plot_data.index, y=plot_data.columns, 
                      title=f'{title_prefix} by Company (Stacked Area)',
                      labels={'value': 'Number of Models', 'Year-Month': 'Month'},
                      color_discrete_map=company_colors)
        for trace in fig.data:
            trace.hovertemplate = "%{customdata[0]}, %{x} (%{y} models)"
            trace.customdata = list(zip(trace.name for _ in range(len(trace.x))))
    elif graph_type == "Line (Total)":
        plot_data_total = plot_data.sum(axis=1)
        fig = px.line(x=plot_data_total.index, y=plot_data_total.values,
                      title=f'{title_prefix} (Total)',
                      labels={'x': 'Month', 'y': 'Number of Models'},
                      )

    fig.update_layout(
        legend=dict(orientation='h', y=-0.2, xanchor='center', x=0.5),
        hovermode='x unified',
        xaxis_range=['2022-06', (max_date - pd.DateOffset(months=1)).strftime('%Y-%m')]
    )
    
    # Update hover information to include the company
    if graph_type == "Stacked Area":
        for trace in fig.data:
            trace.hovertemplate = "%{customdata[0]}, %{x} (%{y} models)"
            trace.customdata = [[trace.name] for _ in range(len(trace.x))]
    else:
        fig.update_traces(hovertemplate="%{x} (%{y} models)")

    # Remove the legend
    fig.update_layout(showlegend=False)
    
    # Make the graph interactive
    selected_points = plotly_events(fig, click_event=True, hover_event=False)
    
    # Display models for the selected month
    if selected_points:
        selected_month = selected_points[0]['x']

        # Extract year and month from selected_month
        selected_month_str = pd.to_datetime(selected_month).strftime('%Y-%m')
        
        if selected_month_str in filtered_df['Year-Month'].values:
            st.subheader(f"Models released in {selected_month_str}")
            month_df = filtered_df[filtered_df['Year-Month'] == selected_month_str]
            month_df['Release Date'] = month_df['Release Date'].dt.strftime('%Y-%m')
            st.dataframe(month_df[['Model', 'Organization', 'Release Date']])
        else:
            st.write(f"No data for the selected month: {selected_month_str}")
    
    # Horizontal line before per company analysis
    st.markdown('---')
    st.header('Per Company Analysis')
    st.write("This section provides details on the average release cycle and models released by the selected company.")
    
    # Allow exploration by company
    company_model_counts = filtered_df['Organization'].value_counts()
    companies = company_model_counts.index.tolist()
    company_options = [f"{company} ({count} models)" for company, count in zip(companies, company_model_counts)]
    
    selected_company_option = st.selectbox('Select a company:', company_options)
    selected_company = selected_company_option.split(' (')[0]

    company_df = filtered_df[filtered_df['Organization'] == selected_company]
    
    # Show company-level release cycle
    company_months, company_days = company_cycles.get(selected_company, (None, None))
    if company_months is not None:
        st.write(f"**Average release cycle for {selected_company}:** {company_months} months and {company_days} days")
    
    st.write(f"Models released by {selected_company}:")
    company_df['Release Date'] = company_df['Release Date'].dt.strftime('%Y-%m')
    st.dataframe(company_df[['Model', 'Release Date']])
    
    # Horizontal line before per month analysis
    st.markdown('---')
    st.header('Per Month Analysis')
    st.write("This section provides details on models released in the selected month.")
    
    # Allow exploration by month
    months = sorted(filtered_df['Year-Month'].unique(), reverse=True)
    selected_month = st.selectbox('Select a month:', months, index=0)

    month_df = filtered_df[filtered_df['Year-Month'] == selected_month]
    month_df['Release Date'] = month_df['Release Date'].dt.strftime('%Y-%m')
    st.write(f"Models released in {selected_month}:")
    st.dataframe(month_df[['Model', 'Organization', 'Release Date']])

    # Show raw data
    if st.checkbox('Show raw data'):
        st.subheader('Raw data')
        filtered_df['Release Date'] = filtered_df['Release Date'].dt.strftime('%Y-%m')
        st.write(filtered_df)

    # Display data quality issues
    missing_orgs = filtered_df['Organization'].isnull().sum()
    if missing_orgs > 0:
        st.warning(f"There are {missing_orgs} models with missing organization information.")

    missing_dates = filtered_df['Release Date'].isnull().sum()
    if missing_dates > 0):
        st.warning(f"There are {missing_dates} models with missing or invalid release dates.")
else:
    st.error("No data available. Please fix the JSON file and restart the app.")
