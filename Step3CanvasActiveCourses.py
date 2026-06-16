import requests
import os
import Step2CanvasActiveTerms


# Retrieve the URL from our Canvas instance and the api key you generated

BASE_URL = os.getenv("CANVAS_URL")
API_KEY = os.getenv("API_KEY")
header = {"Authorization" : "Bearer" + f" {API_KEY}"}

# From Step1CanvasActiveTerms.py, get the dictionary of terms we filtered out

term_dict = Step2CanvasActiveTerms.main()

# Function to pull out all term names and term ids 

def unpack_term_dict():

    active_term_list = []

    # First I want to get the lists of active term dicts from every school

    all_lists = term_dict.values()

    # Then from each list of active term dicts, I want to add each dict to a new list

    for terms in all_lists:
        for term in terms:
            active_term_list.append(term)

    term_keys_to_keep = ["name", "grading_period_group_id", "id"]

    # I don't want all key/value pairs from the term_dict so I will use list/dict comprehension to filter out the pairings I want
          
    active_term_list_clean = [{k: v for k,v in d.items() if k in term_keys_to_keep} for d in active_term_list]
    
    return(active_term_list_clean) 


# Uses the term_id list to make a request to the Canvas API once more
 
def get_courses_for_term(TERM_ID):

    ACCOUNT_ID = "1" # Chappaqua Central School District
    COURSE_URL = BASE_URL + f"/api/v1/accounts/{ACCOUNT_ID}/courses"
    headers = header
    params = {"per_page" : "100",
              "include[]": ["term"], 
              "enrollment_term_id": TERM_ID,
              "state[]": "available"
    } 

    while COURSE_URL: 
        
        response = requests.get(COURSE_URL, headers=headers, params=params) 

        #Checks the HTTP status code of the response and raises an exception if the request failed

        response.raise_for_status() 
            
        data = response.json()

        # Produces one value at a time, pausing the function between values

        for course in data:

        # From the Courses API, request the following resources from the object
        # More info can be found here: https://developerdocs.instructure.com/services/canvas/resources/courses

            yield {
                "id": course.get("id"),
                "name": course.get("name"),
                "term_id": course.get("term", {}).get("id")
            }

        COURSE_URL = response.links.get("next", {}).get("url")
        params = None 


# For each term id that we got from our first file, pass it into the main() function
# Each time main() function is ran, it will return the values we requested in get_courses_for_term()
# Put the values of get_courses_for_term into a list called course list, we will use this list in Step 3

def main(): 

    term_dict = unpack_term_dict()

    terms = []
    
    for term in term_dict:
        terms.append(term["id"])
    
    course_list = []

    for id in terms:
        course_list.extend(get_courses_for_term(id))

    return course_list 
    
if __name__ == "__main__":
    main()


