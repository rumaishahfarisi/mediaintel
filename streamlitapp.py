import streamlit as st
import pandas as pd
import plotly.express as px
import io
import requests
import json
import os # For environment variables, though Streamlit secrets are preferred

# --- Streamlit Page Configuration ---
st.set_page_config(layout="wide", page_title="Interactive Media Intelligence", page_icon="📊")

# --- Title and Header ---
st.markdown(
    """
    <style>
    .big-font {
        font-size:3rem !important;
        font-weight: bold;
        text-align: center;
        color: #1E40AF; /* blue-700 */
        margin-bottom: 1.5rem;
        padding: 0.5rem;
        border-radius: 0.75rem;
    }
    .stSpinner > div > div {
        color: #2563EB; /* blue-600 */
    }
    .streamlit-expanderHeader {
        background-color: #DBEAFE; /* blue-50 */
        color: #1E40AF; /* blue-700 */
        border-radius: 0.75rem;
        padding: 1rem;
        font-weight: 600;
        font-size: 1.25rem;
    }
    .stSelectbox, .stDateInput, .stTextInput {
        border-radius: 0.5rem;
    }
    .stButton>button {
        border-radius: 0.5rem;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.15s ease-in-out;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<p class="big-font">Interactive Media Intelligence</p>', unsafe_allow_html=True)

# --- LLM API Key Configuration ---
# IMPORTANT: For deployment, use Streamlit Secrets (st.secrets)
# For local testing, you can set it as an environment variable or
# uncomment and replace the placeholder.
# Example: GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
GEMINI_API_KEY = "" # Leave this empty. Canvas will inject the API key at runtime.

# --- File Upload Section ---
st.markdown(
    """
    <div style="background-color: #DBEAFE; /* blue-50 */
                padding: 1.5rem;
                border-radius: 0.75rem;
                box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06);">
        <h3 style="color: #4B5563; /* gray-700 */ margin-bottom: 0.75rem;">Unggah File CSV</h3>
    """,
    unsafe_allow_html=True
)
uploaded_file = st.file_uploader("", type="csv", help="Unggah file CSV Anda di sini.")
st.markdown('</div>', unsafe_allow_html=True)


# --- Data Processing and Cleaning ---
@st.cache_data # Cache data to avoid reprocessing on each rerun
def process_data(file_content):
    """
    Reads CSV, cleans data, and prepares it for analysis.
    - Converts 'Date' to datetime objects.
    - Fills empty 'Engagements' with 0 and converts to int.
    - Fills missing categorical data with 'Unknown'.
    - Drops rows with invalid dates.
    - Sorts data by date.
    """
    try:
        # Read CSV content into a DataFrame
        df = pd.read_csv(io.StringIO(file_content.decode('utf-8')))

        # Data cleaning: Convert 'Date' to datetime
        # errors='coerce' will turn unparseable dates into NaT (Not a Time)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

        # Fill empty 'Engagements' with 0 and convert to integer
        # First, convert to numeric, coercing errors to NaN, then fill and convert to Int64 (supports NaNs)
        df['Engagements'] = pd.to_numeric(df['Engagements'], errors='coerce').fillna(0).astype(int)

        # Fill missing values in categorical columns with 'Unknown'
        categorical_cols = ['Platform', 'Sentiment', 'Media Type', 'Location']
        for col in categorical_cols:
            if col in df.columns:
                df[col].fillna('Unknown', inplace=True)
            else:
                df[col] = 'Unknown' # Add column if not present

        # Filter out rows with invalid dates (NaT)
        df.dropna(subset=['Date'], inplace=True)

        # Create DateString for grouping and display
        df['DateString'] = df['Date'].dt.strftime('%Y-%m-%d')

        # Sort data by Date for engagement trend
        df.sort_values(by='Date', inplace=True)

        return df
    except Exception as e:
        st.error(f"Gagal memproses data: {e}. Harap pastikan format CSV Anda benar dan berisi kolom yang diharapkan.")
        return pd.DataFrame() # Return empty DataFrame on error

df = pd.DataFrame()
if uploaded_file is not None:
    with st.spinner("Memproses data..."):
        df = process_data(uploaded_file.read())

if df.empty and uploaded_file is not None:
    st.warning("Tidak ada data yang valid untuk ditampilkan setelah pemrosesan. Harap periksa file CSV Anda.")
elif df.empty and uploaded_file is None:
    st.info("Unggah file CSV untuk mulai memvisualisasikan data Anda. Kolom yang diharapkan: `Date`, `Engagements`, `Platform`, `Sentiment`, `Media Type`, `Location`")


# --- Filters Section ---
if not df.empty:
    st.markdown(
        """
        <div style="background-color: #DBEAFE; /* blue-50 */
                    padding: 1.5rem;
                    border-radius: 0.75rem;
                    box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06);
                    margin-bottom: 2rem;">
            <h3 style="color: #1E40AF; /* blue-700 */ margin-bottom: 1rem;">Filter Data</h3>
        """,
        unsafe_allow_html=True
    )
    col1, col2, col3 = st.columns(3)

    # Collect unique values for filters
    platforms = ['All'] + list(df['Platform'].unique())
    sentiments = ['All'] + list(df['Sentiment'].unique())
    media_types = ['All'] + list(df['Media Type'].unique())
    locations = ['All'] + list(df['Location'].unique())

    with col1:
        selected_platform = st.selectbox("Platform", platforms)
        selected_sentiment = st.selectbox("Sentimen", sentiments)
    with col2:
        selected_media_type = st.selectbox("Jenis Media", media_types)
        selected_location = st.selectbox("Lokasi", locations)
    with col3:
        min_date = df['Date'].min().to_pydatetime().date()
        max_date = df['Date'].max().to_pydatetime().date()

        start_date = st.date_input("Tanggal Mulai", min_value=min_date, max_value=max_date, value=min_date)
        end_date = st.date_input("Tanggal Akhir", min_value=min_date, max_value=max_date, value=max_date)

    # Apply filters to create filtered_df
    filtered_df = df.copy()

    if selected_platform != 'All':
        filtered_df = filtered_df[filtered_df['Platform'] == selected_platform]
    if selected_sentiment != 'All':
        filtered_df = filtered_df[filtered_df['Sentiment'] == selected_sentiment]
    if selected_media_type != 'All':
        filtered_df = filtered_df[filtered_df['Media Type'] == selected_media_type]
    if selected_location != 'All':
        filtered_df = filtered_df[filtered_df['Location'] == selected_location]

    # Date range filter
    if start_date and end_date:
        filtered_df = filtered_df[(filtered_df['Date'].dt.date >= start_date) & (filtered_df['Date'].dt.date <= end_date)]
    elif start_date:
        filtered_df = filtered_df[filtered_df['Date'].dt.date >= start_date]
    elif end_date:
        filtered_df = filtered_df[filtered_df['Date'].dt.date <= end_date]

    st.markdown('</div>', unsafe_allow_html=True)


    # --- Campaign Strategy Summary Section ---
    st.markdown(
        """
        <div style="background-color: #EEF2FF; /* indigo-50 */
                    padding: 1.5rem;
                    border-radius: 0.75rem;
                    box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06);
                    margin-bottom: 2rem;">
            <h3 style="color: #3730A3; /* indigo-700 */ margin-bottom: 1rem;">Ringkasan Strategi Kampanye</h3>
        """,
        unsafe_allow_html=True
    )
    if st.button("Hasilkan Ringkasan", key="generate_summary_btn"):
        if filtered_df.empty:
            st.warning("Tidak ada data untuk menghasilkan ringkasan. Harap sesuaikan filter Anda.")
        else:
            with st.spinner("Menghasilkan ringkasan..."):
                # Aggregate data for the prompt
                sentiment_counts = filtered_df['Sentiment'].value_counts().to_dict()
                platform_engagements = filtered_df.groupby('Platform')['Engagements'].sum().nlargest(3).to_dict()
                media_type_counts = filtered_df['Media Type'].value_counts().nlargest(3).to_dict()
                location_counts = filtered_df['Location'].value_counts().nlargest(3).to_dict()
                total_engagements = filtered_df['Engagements'].sum()

                min_date_summary = filtered_df['Date'].min().strftime('%Y-%m-%d')
                max_date_summary = filtered_df['Date'].max().strftime('%Y-%m-%d')
                date_range_text = f"{min_date_summary} - {max_date_summary}"


                prompt = f"""
                    Berdasarkan data intelijen media berikut, berikan ringkasan strategi kampanye (ringkasan tindakan utama) yang ringkas dalam bahasa Indonesia.
                    Fokus pada wawasan yang dapat ditindaklanjuti.

                    Poin data:
                    - Rentang Tanggal Data: {date_range_text}
                    - Total Keterlibatan: {total_engagements}
                    - Pecahan Sentimen: {json.dumps(sentiment_counts, ensure_ascii=False)}
                    - Platform Teratas berdasarkan Keterlibatan: {json.dumps(platform_engagements, ensure_ascii=False)}
                    - Jenis Media Teratas: {json.dumps(media_type_counts, ensure_ascii=False)}
                    - Lokasi Teratas: {json.dumps(location_counts, ensure_ascii=False)}

                    Sajikan ringkasan ini dalam format naratif yang mudah dibaca, menyoroti rekomendasi atau poin tindakan utama.
                """

                chat_history = []
                chat_history.append({"role": "user", "parts": [{"text": prompt}]})
                payload = {"contents": chat_history}

                api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

                try:
                    response = requests.post(api_url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
                    response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                    result = response.json()

                    if result and result.get('candidates') and len(result['candidates']) > 0 and \
                       result['candidates'][0].get('content') and result['candidates'][0]['content'].get('parts') and \
                       len(result['candidates'][0]['content']['parts']) > 0:
                        campaign_summary = result['candidates'][0]['content']['parts'][0]['text']
                        st.markdown(
                            f"""
                            <div style="margin-top: 1rem; padding: 1rem; background-color: #EEF2FF; /* indigo-100 */
                                        border: 1px solid #6366F1; /* indigo-400 */
                                        border-radius: 0.5rem;">
                                <p style="white-space: pre-wrap; color: #374151; /* gray-800 */">{campaign_summary}</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        st.error("Gagal menghasilkan ringkasan. Tidak ada respons yang valid dari API.")
                        st.json(result) # Display raw API response for debugging
                except requests.exceptions.RequestException as e:
                    st.error(f"Terjadi kesalahan saat memanggil API Gemini: {e}. Harap periksa kunci API Anda dan koneksi internet.")
                except Exception as e:
                    st.error(f"Terjadi kesalahan yang tidak terduga: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Data Visualizations ---
    if not filtered_df.empty:
        st.subheader("Visualisasi Data")

        # Layout for charts
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            # Pie Chart: Sentiment Breakdown
            sentiment_counts = filtered_df['Sentiment'].value_counts().reset_index()
            sentiment_counts.columns = ['Sentiment', 'Count']
            fig_sentiment = px.pie(
                sentiment_counts,
                values='Count',
                names='Sentiment',
                title='Pecahan Sentimen',
                hole=0.4,
                color='Sentiment',
                color_discrete_map={
                    'Positive': '#4CAF50', # Green
                    'Negative': '#F44336', # Red
                    'Neutral': '#2196F3',  # Blue
                    'Unknown': '#9E9E9E'   # Grey
                }
            )
            fig_sentiment.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#FFFFFF', width=1)))
            fig_sentiment.update_layout(height=400, margin=dict(t=40, b=40, l=40, r=40), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family='Inter, sans-serif'))
            st.plotly_chart(fig_sentiment, use_container_width=True)

        with chart_col2:
            # Line Chart: Engagement Trend over Time
            daily_engagements = filtered_df.groupby('DateString')['Engagements'].sum().reset_index()
            daily_engagements.columns = ['Date', 'Total Engagements']
            fig_engagement_trend = px.line(
                daily_engagements,
                x='Date',
                y='Total Engagements',
                title='Tren Keterlibatan Seiring Waktu',
                markers=True,
                line_shape="linear",
                color_discrete_sequence=['#3F51B5'] # Indigo-500
            )
            fig_engagement_trend.update_layout(height=400, margin=dict(t=40, b=60, l=60, r=40), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family='Inter, sans-serif'), xaxis_title='Tanggal', yaxis_title='Total Keterlibatan')
            st.plotly_chart(fig_engagement_trend, use_container_width=True)

        chart_col3, chart_col4 = st.columns(2)
        with chart_col3:
            # Bar Chart: Platform Engagements
            platform_engagements = filtered_df.groupby('Platform')['Engagements'].sum().reset_index()
            platform_engagements = platform_engagements.sort_values(by='Engagements', ascending=False)
            fig_platform = px.bar(
                platform_engagements,
                x='Platform',
                y='Engagements',
                title='Keterlibatan Platform',
                color_discrete_sequence=['#0EA5E9'] # Sky-600
            )
            fig_platform.update_layout(height=400, margin=dict(t=40, b=60, l=60, r=40), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family='Inter, sans-serif'), xaxis_title='Platform', yaxis_title='Total Keterlibatan')
            st.plotly_chart(fig_platform, use_container_width=True)

        with chart_col4:
            # Pie Chart: Media Type Mix
            media_type_counts = filtered_df['Media Type'].value_counts().reset_index()
            media_type_counts.columns = ['Media Type', 'Count']
            fig_media_type = px.pie(
                media_type_counts,
                values='Count',
                names='Media Type',
                title='Campuran Jenis Media',
                hoverinfo='label+percent',
                color_discrete_sequence=px.colors.sequential.Bluyl
            )
            fig_media_type.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#FFFFFF', width=1)))
            fig_media_type.update_layout(height=400, margin=dict(t=40, b=40, l=40, r=40), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family='Inter, sans-serif'))
            st.plotly_chart(fig_media_type, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True) # Add some space

        # Bar Chart: Top 5 Locations (full width)
        location_counts = filtered_df['Location'].value_counts().nlargest(5).reset_index()
        location_counts.columns = ['Location', 'Count']
        fig_locations = px.bar(
            location_counts,
            x='Location',
            y='Count',
            title='5 Lokasi Teratas',
            color_discrete_sequence=['#14B8A6'] # Teal-500
        )
        fig_locations.update_layout(height=400, margin=dict(t=40, b=60, l=60, r=40), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family='Inter, sans-serif'), xaxis_title='Lokasi', yaxis_title='Jumlah')
        st.plotly_chart(fig_locations, use_container_width=True)

    else:
        st.info("Tidak ada data yang cocok dengan filter yang diterapkan.")

