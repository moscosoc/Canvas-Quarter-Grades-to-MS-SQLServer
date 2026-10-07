# Canvas Quarter Grades Import to MS SQL Server database

## Intent

These series of scripts were created with the goal of migrating the in progress quarterly grades from the Canvas LMS to a SQL Server database. 

## Prerequisites

Before running the file, be sure to install the following external libraries in your environment:

  1. requests
  2. dotenv
  3. pyodbc
  4. msal

In addition, be sure to have the following variables defined in your .env file:

  1. API_KEY = You can generate a key if you are listed as an administrator in Canvas, more information can be found [here](https://developerdocs.instructure.com/services/canvas/oauth2/file.oauth#manual-token-generation)
  2. CANVAS_URL = The URL to the Canvas site. The structure of the URL should be "https://{YOUR DOMAIN NAME HERE}.instructure.com"

## Description of data and file structure

Each file is denoted with a prefix of "Step#" to help the reader contextualize the order of operations throughout this procedure.

The sequence of code execution is summarized as follows:


  1. For every term active within a defined quarter, return the term data.
  2. Using the term data from Step 1, use it to return the course ids.
  3. From the course data returned in Step 2, use it to send a POST command for every course. This will disable the "Hide grade      distribution graphs from students" checkbox. 
