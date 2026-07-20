# Canvas Quarter Grades Import to Infinite Campus Gradebook

## Intent

These series of scripts were created with the goal of migrating the in progress quarterly grades from the Canvas LMS to a SQL Server database. 

## Prerequisites

Before running the file, be sure to install the following external libraries in your environment:

  1. requests
  2. dotenv
  3. pyodbc

In addition, be sure to have the following variables defined in your .env file:

  1. API_KEY = You can generate a key if you are listed as an administrator in Canvas, more information can be found [here](https://developerdocs.instructure.com/services/canvas/oauth2/file.oauth#manual-token-generation)
  2. CANVAS_URL = The URL to the Canvas site. The structure of the URL should be "https://{YOUR DOMAIN NAME HERE}.instructure.com"
  3. SQL_SERVER = The server name used in your work environment.
  4. SQL_DATABASE = The name of of the database that will receive the completed dataset.
  5. SQL_USERNAME = The username of the SQL Server user account.
  6. SQL_PASSWORD = The password of the SQL Server user account. 

## Description of data and file structure

Each file is denoted with a prefix of "Step#" to help the reader contextualize the order of operations throughout this procedure. As of May 22nd, 2026, there are 5 files or "steps" in this repository. 

The sequence of code execution is summarized as follows:

  1. Define the quarter to pull data from (Q1, Q2, etc.)
  2. For every term active within a defined quarter, return the term data.
  3. Using the term data from Step 2, use it to return the course data in Step 3.
  4. From the course data returned in Step 3, use it to find the grading period data, merge the course data from step 3 and the grading period data from the current step (step 4).
  5. Finally, once the course data and grading period data is merged, use it to find the current quarter scores and grades for every student in those courses. Import the     final data set into the canvas_quarter_grades table. 
