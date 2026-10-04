Algorithm: Student & Teacher Performance Analytics

Step 1: Start. Import the required libraries (pandas, SQLAlchemy, python-dotenv, matplotlib, Streamlit).

Step 2: Configure. Read the database host, user, password and name from the .env file.

Step 3: Connect. Create a MySQL engine using SQLAlchemy (PyMySQL driver) and test the connection.

Step 4: Load data. Read the 7 database tables (students, teachers, subjects, marks, attendance, feedback, etc.) into pandas DataFrames.

Step 5: Clean data. Remove duplicate rows using drop_duplicates(), convert numeric columns using pd.to_numeric(), and standardise text columns using str.strip() and str.capitalize().

Step 6: Compute metrics.
- Marks % = marks obtained / total marks x 100, then the average marks % per student and per subject.
- Attendance % = sessions present / total sessions x 100 per student.
- Pass percentage = share of marks records at or above the 40% pass mark.
- Average teacher rating from the feedback table.

Step 7: Merge and aggregate. Join marks and attendance per student, join marks with subjects and teachers, and join feedback with teachers.

Step 8: Flag risk. A student is marked "At risk" if average marks are below 40% or attendance is below 75%. Students with missing marks or attendance are labelled "Incomplete data".

Step 9: Visualise. Draw the attendance vs marks hexbin chart with 40% and 75% reference lines, and produce subject-wise and teacher-wise summaries.

Step 10: Display dashboard. Use Streamlit to switch between the Student Report and Teacher Insights views, search for a student or teacher, and show metric tiles and comparison charts.

Step 11: End. Close the database connection and terminate the program.