Algorithm: Student & Teacher Performance Analytics

Step 1: Start
    Import required libraries (pandas, mysql.connector, plotly.express, streamlit).

Step 2: Connect to Database
    Establish connection with MySQL using host, user, password, and database.

Step 3: Load Data
    Execute SQL queries to fetch tables:
        - students
        - teachers
        - subjects
        - marks
        - attendance
        - feedback
    Store each table in a pandas DataFrame.

Step 4: Clean Data
    - Remove missing values using dropna().
    - Remove duplicates using drop_duplicates().
    - Convert data types using pd.to_numeric().
    - Standardize text using str.strip() and str.capitalize().

Step 5: Analyze Data
    - Compute average marks per student.
    - Compute average marks per subject.
    - Calculate pass percentage.
    - Summarize attendance (count of “Present” per student).
    - Calculate average teacher ratings.

Step 6: Merge and Aggregate
    - Merge attendance and marks for correlation analysis.
    - Merge teacher ratings with subjects for performance overview.

Step 7: Visualize Data
    - Create histogram for marks distribution.
    - Create bar chart for average marks per subject.
    - Create line chart for marks and attendance trends.
    - Create scatter plot for attendance vs marks.
    - Create pie chart for pass vs fail ratio.
    - Create heatmap for subject vs teacher performance.

Step 8: Display Dashboard
    - Use Streamlit to show student and teacher lists.
    - Display pandas tables and Plotly charts.
    - Allow user interaction with filters and selections.

Step 9: Export Data (Optional)
    - Save cleaned or analyzed data to CSV or Excel files.

Step 10: End
    Close database connection and terminate the program.
