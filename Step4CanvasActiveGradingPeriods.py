import requests
import os
import Step1DefineQuarter
import Step2CanvasActiveTerms
import Step3CanvasActiveCourses

BASE_URL = os.getenv("CANVAS_URL")
API_KEY = os.getenv("API_KEY")

header = {
    "Authorization": f"Bearer {API_KEY}"
}


TARGET_QUARTER = Step1DefineQuarter.define_quarter()

# Returns all terms from Step 1, place it into a list

def flatten_step1_terms():

    grouped_terms = Step2CanvasActiveTerms.main()

    terms = []

    for school, school_terms in grouped_terms.items():
        for term in school_terms:
            terms.append(term)

    return terms

# from the terms list made in flatten_step1_terms function, 
# make a lookup dictionary of dictionaries containing all term ids as keys
# mapped to their respective names and grading period group ids

def build_active_quarter_term_map():

    active_quarter_terms = flatten_step1_terms()

    return {
        term["id"]: {
            "term_name": term["name"],
            "grading_period_group_id": term["grading_period_group_id"]
        }
        for term in active_quarter_terms
    }

# Makes grading period matching more flexible
# Examples:
# "Quarter 1" -> matches Q1
# "Q1" -> matches Q1
# "Quarter 1 2025-2026" -> matches Q1

def grading_period_matches_quarter(title, target_quarter):

    if not title:
        return False

    # Creates consistency "Quarter 1" --> "QUARTER1"
    normalized_title = title.upper().replace(" ", "")

    # Creates consistency "q1" --> "Q1"
    normalized_target = target_quarter.upper()

    quarter_map = {
        "Q1": ["Q1", "QUARTER1"],
        "Q2": ["Q2", "QUARTER2"],
        "Q3": ["Q3", "QUARTER3"],
        "Q4": ["Q4", "QUARTER4"]
    }

    valid_patterns = quarter_map.get(normalized_target, [])

    return any(pattern in normalized_title for pattern in valid_patterns)


def get_grading_periods(course_id, target_quarter):

    url = BASE_URL + f"/api/v1/courses/{course_id}/grading_periods"

    while url:

        response = requests.get(url, headers=header)
        response.raise_for_status()

        data = response.json()

        for gp in data.get("grading_periods", []):

            gp_title = gp.get("title")

            # Only keep grading periods for the selected quarter
            if not grading_period_matches_quarter(
                gp_title,
                target_quarter
            ):
                continue

            yield {
                "id": gp.get("id"),
                "title": gp_title,
                "start_date": gp.get("start_date"),
                "end_date": gp.get("end_date")
            }

        url = response.links.get("next", {}).get("url")


def combine_course_and_grading_periods():

    course_list = Step3CanvasActiveCourses.main()

    active_quarter_term_map = build_active_quarter_term_map()

    grading_period_cache = {}

    final_list = []

    for course in course_list:

        course_id = course["id"]
        course_name = course["name"]
        term_id = course["term_id"]

        # Skip courses not in the active quarter
        if term_id not in active_quarter_term_map:
            continue

        term_info = active_quarter_term_map[term_id]

        grading_period_group_id = term_info[
            "grading_period_group_id"
        ]

        # Cache grading periods by grading period group
        if grading_period_group_id not in grading_period_cache:

            grading_period_cache[
                grading_period_group_id
            ] = list(
                get_grading_periods(
                    course_id,
                    TARGET_QUARTER
                )
            )

        # Add grading periods to final dataset
        for gp in grading_period_cache[
            grading_period_group_id
        ]:

            final_list.append({
                "course_id": course_id,
                "course_name": course_name,
                "term_name": term_info["term_name"],
                "grading_period_group_id": grading_period_group_id,
                "grading_period_id": gp["id"],
                "grading_period_title": gp["title"]
            })

    return final_list


def main():

    return combine_course_and_grading_periods()

if __name__ == "__main__":
    main()





