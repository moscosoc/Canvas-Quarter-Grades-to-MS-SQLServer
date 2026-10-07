import requests
import os
import Step1CanvasActiveTerms
import csv


# Retrieve the URL from our Canvas instance and the api key you generated

BASE_URL = os.getenv("CANVAS_URL")
API_KEY = os.getenv("API_KEY")
header = {"Authorization" : "Bearer" + f" {API_KEY}"}

# From Step1CanvasActiveTerms.py, get the dictionary of terms we filtered out

term_dict_list = Step1CanvasActiveTerms.main()

# Function to put term ids in a list

def unpack_term_dict():

    term_ids = [term["id"] for term in term_dict_list]
    
    return term_ids


# Uses the term_ids list to make a request to the Canvas API once more
 
def get_courses_for_term(TERM_ID):

    ACCOUNT_ID = "1" # Chappaqua Central School District
    COURSE_URL = BASE_URL + f"/api/v1/accounts/{ACCOUNT_ID}/courses"
    headers = header
    params = {"per_page" : "100",
              "include[]": ["term"], 
              "enrollment_term_id": TERM_ID
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

    terms = unpack_term_dict()
    
    course_list = []

    for id in terms:
        course_list.extend(get_courses_for_term(id))

    course_ids = [course["id"] for course in course_list]

    return course_ids

if __name__ == "__main__":
    main()


"""
# For running output file of courses
def main(): 

    terms = unpack_term_dict()
    
    course_list = []

    for id in terms:
        course_list.extend(get_courses_for_term(id))

    course_ids = [course["name"] for course in course_list]

    with open ("course_names.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        for course in course_ids:
            writer.writerow([course])
"""