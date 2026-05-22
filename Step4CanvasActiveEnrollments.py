import requests
import os
import Step3CanvasActiveGradingPeriods
from datetime import date
import pyodbc

# Retrieve the URL from our Canvas instance and the api key you generated

BASE_URL = os.getenv("CANVAS_URL")
API_KEY = os.getenv("API_KEY")
header = {"Authorization" : "Bearer" + f" {API_KEY}"}


# course_list is a list of dictionaries, which will need to be unpacked to be used 

def get_enrollments_for_course(course):
    course_id = course["course_id"]
    grading_period_id = course["grading_period_id"]

    url = BASE_URL + f"/api/v1/courses/{course_id}/enrollments"

    params = {
        "per_page": 100,
        "type[]": ["StudentEnrollment"],
        "state[]": ["active"],
        "grading_period_id": grading_period_id,
        "include[]": ["user"]
    }

    while url:
        response = requests.get(url, headers=header, params=params, timeout=30)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            if response.status_code == 400:
                print(f"Skipping course {course_id} - no grading periods")
                return
            raise

        data = response.json()

        for enrollment in data:
            grades = enrollment.get("grades", {})
            user = enrollment.get("user", {})

            yield {
                "course_id": course_id,
                "course_name": course["course_name"],
                "term_id": course["term_id"],
                "term_name": course["term_name"],
                "grading_period_id": grading_period_id,
                "grading_period_title": course["grading_period_title"],

                "user_id": enrollment.get("user_id"),
                "student_name": user.get("name"),
                "sis_user_id": user.get("sis_user_id"),

                "type": enrollment.get("type"),
                "sis_course_id": enrollment.get("sis_course_id"),
                "sis_section_id": enrollment.get("sis_section_id"),

                "html_url": grades.get("html_url"),
                "current_grade": grades.get("current_grade"),
                "current_score": grades.get("current_score"),

                "load_date": date.today()
            }

        url = response.links.get("next", {}).get("url")
        params = None
        

def list_current_grade_records():

    current_periods = Step3CanvasActiveGradingPeriods.main()

    enrollments = []

    for course in current_periods:
        enrollments.extend(get_enrollments_for_course(course))

    return enrollments


def load_enrollments_to_sqlserver():
    server = os.getenv("SQL_SERVER")
    database = os.getenv("SQL_DATABASE")
    username = os.getenv("SQL_USERNAME")
    password = os.getenv("SQL_PASSWORD")

    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes"
    )

    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.fast_executemany = True

    truncate_sql = """
        TRUNCATE TABLE dbo.canvas_in_progress_grades
    
    """

    insert_sql = """

        INSERT INTO dbo.canvas_in_progress_grades (
            type,
            sis_course_id,
            course_id,
            user_id,
            sis_section_id,
            html_url,
            current_score,
            current_grade,
            name,
            sis_user_id,
            load_date
         )
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """


    enrollments = list_current_grade_records()

    rows = [
        (
            e.get("type"),
            e.get("sis_course_id"),
            e.get("course_id"),
            e.get("user_id"),
            e.get("sis_section_id"),
            e.get("html_url"),
            e.get("current_score"),
            e.get("current_grade"),
            e.get("name"),
            e.get("sis_user_id"),
            e.get("load_date")
        )
        for e in enrollments
    ]

    if rows:
        cursor.execute(truncate_sql)
        cursor.executemany(insert_sql, rows)
        conn.commit()
        print(f"Inserted {len(rows)} rows into dbo.canvas_in_progress_grades")
    else:
        print("No enrollments to load.")

    cursor.close()
    conn.close()


if __name__ == "__main__":
   
    print("Running Python File!")
    load_enrollments_to_sqlserver()

