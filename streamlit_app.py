import streamlit as st
import pandas as pd
import plotly.express as px

st.title('FitBit Fitness Tracker Data Exploration',
         help='Sourced from a publicly-available dataset in Kaggle that contains activity,' \
         ' steps, sleep, calorie, and intensity data from 30 consenting ' \
         'users of Fitbit trackers, collected via a distributed survey between April–May 2016.')


st.set_page_config(layout='wide')

def get_user_df(user, date, df):
    user_df = df[df['Id'] == user]
    day_df = user_df[user_df['ActivityHour'].dt.date == pd.to_datetime(date).date()]
    return day_df

@st.cache_data
def load_data():
    daily_activity = pd.read_csv('data/dailyActivity_merged.csv')
    daily_sleep = pd.read_csv('data/sleepDay_merged.csv')
    hourly_steps = pd.read_csv('data/hourlySteps_merged.csv')
    hourly_intensity = pd.read_csv('data/hourlyIntensities_merged.csv')
    hourly_calories = pd.read_csv('data/hourlyCalories_merged.csv')

    # Clean column names and format for merging
    daily_sleep = daily_sleep.rename(columns={'SleepDay': 'ActivityDate'})
    daily_sleep['SleepHours'] = daily_sleep['TotalMinutesAsleep'] / 60

    # Convert date columns to datetime
    daily_activity['ActivityDate'] = pd.to_datetime(daily_activity['ActivityDate'])
    daily_sleep['ActivityDate'] = pd.to_datetime(daily_sleep['ActivityDate'])
    hourly_calories['ActivityHour'] = pd.to_datetime(hourly_calories['ActivityHour'])
    hourly_steps['ActivityHour'] = pd.to_datetime(hourly_steps['ActivityHour'])
    hourly_intensity['ActivityHour'] = pd.to_datetime(hourly_intensity['ActivityHour'])

    # Merge daily steps and calories
    daily_combined = pd.merge(daily_activity, daily_sleep, on=['Id', 'ActivityDate'], how='left')

    # Rename columns for clarity
    daily_combined = daily_combined.rename(columns={'SleepHours': 'Sleeping Hours',
                                                    'TotalSteps': 'Steps',
                                                    'TotalDistance': 'Distance',
                                                    'Calories': 'Calories Burned'})

    return daily_activity, daily_sleep, hourly_steps, hourly_intensity, hourly_calories, daily_combined

daily_activity, daily_sleep, hourly_steps, hourly_intensity, hourly_calories, daily_combined= load_data()


st.dataframe(daily_combined.head())

st.subheader('Daily Activity Overview')
with st.container(border=True):
    empty_df = pd.DataFrame()
    avg_steps = daily_combined['Steps'].mean()
    avg_distance = daily_combined['Distance'].mean()
    avg_calories = daily_combined['Calories Burned'].mean()
    avg_sleep = daily_combined['Sleeping Hours'].mean()

    c1, c2, c3, c4= st.columns(4)
    c1.metric('Average Daily Steps', f"{avg_steps:,.0f}", border=True)
    c2.metric('Average Daily Distance (KM)', f"{avg_distance:,.2f}", border=True)
    c3.metric('Average Daily Calories Burned', f"{avg_calories:,.0f}", border=True)
    c4.metric('Average Daily Sleeping Hours', f"{avg_sleep:,.2f}", border=True)

    # Histogram for activity distribution
    st.subheader("Activity Distribution")
    options = ['Steps', 'Distance', 'Calories Burned', 'Sleeping Hours']
    metric = st.segmented_control(options=options, 
                                  label="Select metric to visualize:",
                                  selection_mode="single")
    
    if metric:
        his_fig = px.histogram(daily_combined, x=metric, nbins=50,
                       title=f'Distribution of {metric} Across All Users')
    else:
        his_fig = px.histogram(empty_df, x=[], nbins=50)
    st.plotly_chart(his_fig)

    # Correlation scatter plot
    st.subheader("Correlation Between Metrics")
    cx, cy = st.columns(2)
    x = cx.selectbox('Select X-axis metric:', options=options, 
                     placeholder='Choose X-axis metric', index=None)
    y = cy.selectbox('Select Y-axis metric:', options=options,
                     placeholder='Choose Y-axis metric', index=None)
    if x and y:
        scat_fig = px.scatter(daily_combined, x=x, y=y,
                       title=f'Correlation between {x} and {y}')
    else:
        scat_fig = px.scatter(empty_df, x=None, y=None)

    st.plotly_chart(scat_fig)


# Individual User Data Exploration
st.subheader('Explore Individual User Data')
c1, c2 = st.columns(2)

user = c1.selectbox('Select user:', daily_activity['Id'].unique(), index=None, placeholder='Choose a user ID to see more details')
if user:
    user_df = daily_activity[daily_activity['Id'] == user]
    user_min_date = user_df["ActivityDate"].min()
    user_max_date = user_df["ActivityDate"].max()
    date = c2.date_input("Select date:", value=None, min_value=pd.to_datetime(user_min_date), max_value=pd.to_datetime(user_max_date))


    if date:
        day_df = user_df[user_df['ActivityDate'] == pd.to_datetime(date)]
        st.subheader(f"User's Activity Data on {date}")
        c1, c2, c3 = st.columns(3)
        c1.metric('Total Steps', day_df["TotalSteps"], border=True)
        c2.metric('Total Distance (KM)', day_df["TotalDistance"].round(2), border=True)
        c3.metric('Calories Burned', day_df["Calories"], border=True)

        total_minutes = day_df[["VeryActiveMinutes", "FairlyActiveMinutes",
                                "LightlyActiveMinutes", "SedentaryMinutes"]].sum()
        distances = day_df[["VeryActiveDistance", "ModeratelyActiveDistance",
                                "LightActiveDistance", "SedentaryActiveDistance"]].sum()
        
        st.subheader("Activity Minutes Breakdown")
        with st.container(border=True):
            cc1, cc2, cc3 = st.columns([1, 3, 3])
            cc1.metric('Total Minutes Tracked', total_minutes.sum())

            # Pie Chart for Activity Minutes
            pie1 = px.pie(values=total_minutes.values,
                        names=total_minutes.index,
                        labels={'names': 'Activity Type', 'values': 'Minutes'})
            
            cc2.plotly_chart(pie1)
            # Pie Chart for Distances
            pie2 = px.pie(values=distances.values,
                        names=distances.index,
                        labels={'names': 'Activity Type', 'values': 'Distance (KM)'})
            cc3.plotly_chart(pie2)

        st.subheader("Hourly Data")
        with st.container(border=True):

            hour_calories = get_user_df(user, date, hourly_calories)
            hour_steps = get_user_df(user, date, hourly_steps)
            hour_intensity = get_user_df(user, date, hourly_intensity)

            l1, l2 , l3= st.columns(3)
            # Combine data for line chart
            hourly_data = hour_calories.merge(hour_intensity[['ActivityHour', 'TotalIntensity']], on="ActivityHour")

            line1 = px.line(hour_steps, x='ActivityHour', y='StepTotal', 
                            labels={'StepTotal': 'Steps', 'ActivityHour': 'Hour'},
                            title='Steps')
            line1.update_layout(title_x=0.5)
            l1.plotly_chart(line1)

            line2 = px.line(hour_calories, x='ActivityHour', y='Calories', 
                            labels={'Calories': 'Calories', 'ActivityHour': 'Hour'},
                            title='Calories Burned')
            line2.update_layout(title_x=0.5)
            l2.plotly_chart(line2)

            line3 = px.line(hour_intensity, x='ActivityHour', y='TotalIntensity', 
                            labels={'TotalIntensity': 'Intensity', 'ActivityHour': 'Hour'},
                            title='Intensity Level')
            line3.update_layout(title_x=0.5)
            l3.plotly_chart(line3)

