import requests
from dotenv import load_dotenv
import os
from datetime import datetime, timezone
import Step0DefineQuarter

load_dotenv()

quarter = Step0DefineQuarter.define_quarter()

# Retrieve the URL from our Canvas instance and the api key you generated

BASE_URL = os.getenv("CANVAS_URL")
API_KEY = os.getenv("API_KEY")
header = {"Authorization" : "Bearer" + f" {API_KEY}"}

def get_term_ids():

    ACCOUNT_ID = "1" # Chappaqua Central School District
    TERMS_URL = BASE_URL + f"/api/v1/accounts/{ACCOUNT_ID}/terms"
    headers = header
    params = {"per_page" : "10"} 

    # From the Enrollment Terms API, request the following resources from the object
    # More info can be found here: https://developerdocs.instructure.com/services/canvas/resources/enrollment_terms

    TERM_KEYS = {
    "id",
    "name",
    "start_at",
    "end_at",
    "grading_period_group_id",
    "sis_term_id"
    }

    while TERMS_URL:
         
        response = requests.get(TERMS_URL, headers=headers, params=params) 

        #Checks the HTTP status code of the response and raises an exception if the request failed

        response.raise_for_status() 

        # put the data into a json object for readability

        data = response.json()

        # Produces one value at a time, pausing the function between values

        for term in data.get("enrollment_terms", []):
            yield {k: term.get(k) for k in TERM_KEYS} 

        # Extract the next page URL 

        next_link = response.links.get("next", {}).get("url")
       
        TERMS_URL = next_link

        # set params = None so that only the first request sends a param. Sending the same param in later requests breaks pagination.

        params = None  

# Grabs response from API call and puts it into a list. 

def list_terms(terms): 

    term_list = []
    
    for term in terms:
        term_list.append(term)  

    return term_list

# This function converts Canvas start_at and end_at strings (2026-06-27T03:59:00Z) into datetime elements (2026-06-27T03:59:00:00:00)

def parse_canvas_dt(dt_str: str | None) -> datetime | None:

    # if the date is None or empty, return None instead of crashing

    if not dt_str:
        return None
    
    # If there is a date, drop the Z at the end and add +00:00 at the end

    if dt_str.endswith("Z"):
        dt_str = dt_str[:-1] + "+00:00"
    return datetime.fromisoformat(dt_str)

# This function filters by terms that exist in the current school year, meaning the start date exists and the end date has not passed yet. 

def term_starts_in_window(term: dict, window_start: datetime) -> bool:

    start = parse_canvas_dt(term.get("start_at"))
    end = parse_canvas_dt(term.get("end_at"))
    today = datetime.now(timezone.utc)

    if start is None and end < today:
        return False
    return window_start <= start and (end is None or end >= today)

# Returns terms that have a populated start date a and grading period group id

def is_real_grading_term(t: dict) -> bool:

    return t.get("start_at") is not None and t.get("grading_period_group_id") is not None # All terms


# Filters terms in the term_list() function so only terms in the current school year are returned 

def filter_terms(term_list):

    today = datetime.today()

    if today.month >= 7:
        school_year = today.year
    else:
        school_year = today.year - 1

    ts = datetime(school_year, 7, 1, tzinfo=timezone.utc) 

    # Get terms where they exist in the current school year and they are a term associated with grading
    filtered = [t for t in term_list  if is_real_grading_term(t) and term_starts_in_window(t, ts)]

    return filtered

# Get every sis_term_id (key) : canvas term id (value) for term in all terms IF there is an sis_term_id for the term.

def build_sis_to_id_map(terms: list[dict]) -> dict:

    return {t["sis_term_id"]: t["id"] for t in terms if t.get("sis_term_id")}

def get_quarters_from_term_name(term_name: str) -> list[str]:

    quarter_order = ["Q1", "Q2", "Q3", "Q4"]

    # Gets the quarter portion from the name
    # Example: "2026-HG-Q1-Q4" -> ["2026", "HG", "Q1", "Q4"]

    parts = term_name.split("-")

    # if the part in the term name is Q1-Q4 then keep, otherwise ignore

    quarters_in_name = [p for p in parts if p in quarter_order]

    # if there is no name in the parts then return an empty list

    if not quarters_in_name:
        return []

    # Single quarter term, example: Q2

    if len(quarters_in_name) == 1:
        return quarters_in_name

    # Quarter range, example: Q1-Q4
    
    start_q = quarters_in_name[0]
    end_q = quarters_in_name[-1]

    start_index = quarter_order.index(start_q)
    end_index = quarter_order.index(end_q)

    return quarter_order[start_index:end_index + 1]

def group_terms_by_term_name(terms: list[dict]) -> dict:
    grouped = {
        "Q1": {"BS": [], "SB": [], "HG": []},
        "Q2": {"BS": [], "SB": [], "HG": []},
        "Q3": {"BS": [], "SB": [], "HG": []},
        "Q4": {"BS": [], "SB": [], "HG": []},
    }

    for term in terms:
        name = term.get("name")

        if not name:
            continue

        parts = name.split("-")

        if len(parts) < 3:
            continue

        school = parts[1]  # BS, SB, HG

        if school not in grouped["Q1"]:
            continue

        active_quarters = get_quarters_from_term_name(name)

        for quarter in active_quarters:
            grouped[quarter][school].append(term)


    return grouped

def main():
    
    terms_response = get_term_ids()

    terms_listed = list_terms(terms_response)

    terms_filtered = filter_terms(terms_listed)

    terms_grouped = group_terms_by_term_name(terms_filtered)

    return(terms_grouped[quarter]) 


if __name__ == "__main__":
    main()



