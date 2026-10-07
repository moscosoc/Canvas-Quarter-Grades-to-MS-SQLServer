import csv
import json
from pathlib import Path

import requests
import os
import Step2CanvasActiveCourses

# Retrieve the URL from our Canvas instance and the api key you generated

BASE_URL = os.getenv("CANVAS_URL")
API_KEY = os.getenv("API_KEY")
header = {"Authorization" : "Bearer" + f" {API_KEY}"}

# From Step2CanvasActiveCourses.py, get the list of course ids

course_id_list = Step2CanvasActiveCourses.main()

# https://chappaqua.beta.instructure.com/courses/12545, AP CHEMISTRY - (6040) - Prignano 
# https://chappaqua.beta.instructure.com/courses/12295, ENGLISH 6 - (106) - Daglio
# course_id_list = [12545,12295] 


# For each course id in the list, add it to the course url to toggle off distribution graphs

def hide_distribution_graphs(COURSE_ID):
    """Disable distribution graphs and return a report row for this course."""
    COURSE_URL = BASE_URL + f"/api/v1/courses/{COURSE_ID}/settings"
    result = {
        "course_id": COURSE_ID,
        "http_status": "",
        "result": "Unexpected response",
        "message": "Course did not return an expected response.",
        "response_body": "",
    }

    try:
        response = requests.put(
            COURSE_URL,
            headers=header,
            params={"hide_distribution_graphs": True},
            timeout=60,
        )
        result["http_status"] = response.status_code
        result["response_body"] = response.text

        # Confirm both the HTTP status and the returned setting.
        try:
            settings = response.json()
        except ValueError:
            settings = None

        if (
            200 <= response.status_code < 300
            and isinstance(settings, dict)
            and settings.get("hide_distribution_graphs") is True
        ):
            result["result"] = "Success"
            result["message"] = (
                "Course successfully had grade distribution graphs disabled."
            )
    except requests.RequestException as error:
        # Record request failures and continue with the remaining courses.
        result["result"] = "Request failed"
        result["message"] = (
            f"Course did not return an expected response. Request failed: {error}"
        )

    return result


def create_summary_report(results, report_path=None):
    """Write one row per course, with a column for each response JSON key."""
    if report_path is None:
        report_path = Path(__file__).resolve().parent / "summary.csv"

    fieldnames = ["course_id", "http_status", "result", "message"]
    rows = []
    for result in results:
        row = {key: result.get(key, "") for key in fieldnames[:4]}
        body = result.get("response_body", "")
        try:
            response_data = json.loads(body) if isinstance(body, str) else body
        except (ValueError, TypeError):
            response_data = body

        if isinstance(response_data, dict):
            # Prefix response columns to avoid overwriting report metadata.
            for key, value in response_data.items():
                column = f"response_{key}"
                row[column] = (
                    json.dumps(value, ensure_ascii=False)
                    if isinstance(value, (dict, list)) else value
                )
        elif body != "" and body is not None:
            # Preserve responses that are not JSON objects for troubleshooting.
            row["response_raw"] = (
                body if isinstance(body, str)
                else json.dumps(body, ensure_ascii=False)
            )

        # Include keys returned by any course, even when responses differ.
        for column in row:
            if column not in fieldnames:
                fieldnames.append(column)
        rows.append(row)

    with open(report_path, "w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return Path(report_path)


def main():
    if not BASE_URL or not API_KEY:
        raise ValueError("Set the CANVAS_URL and API_KEY environment variables.")

    results = []
    for course in course_id_list:
        result = hide_distribution_graphs(course)
        results.append(result)
        print(f"Course {course}: {result['message']}")

    report_path = create_summary_report(results)
    success_count = sum(result["result"] == "Success" for result in results)
    print(f"Successfully updated {success_count} of {len(results)} courses.")
    print(f"Summary report saved to: {report_path}")


if __name__ == "__main__":
    main()
