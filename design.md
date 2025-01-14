# Book Search Design

## Overview
A book search application is desired that wil allow users to search for books using natural language queries.

## Requirements
Develop a web application that allows users to search for books using natural language queries.
Must make use of an LLM to interpret the user's natural language inputs
Must use the Open Library Web Service 
Will return a list of recommended books, if any exist, or an error message in the event of failure
Each book response should include a list of book recommendations with titles, authors, and brief descriptions, formatted in natural language. 
Must not allow profanity
The final service should be accessible online
Searches should be fast, taking around 1-3 seconds
The project should be free to develop
The UI should handle loading states
The UI should work well on both desktop and mobile devices

## Scope
This should be a relatively small project, essentially containing only 1-2 pages in the frontend, and needing only 1 major endpoint in the backend/

## Components

### Database
No database needed for this application since we aren't storing any kind of data, but are rather relying on the Open Library Web Service.

### Frontend
To create a good looking user interface that can be easily deployed, I plan to use React, since it is fast and has a lot of library support,
allowing me to use material ui, which is a library with a lot of pre-made and easily customizable components, as well as Next.js, which should
allow the project to be easily deployed and should allow for routing if any is needed. Axios to handle queries.

### Backend
The backend will be done in Python and essentially just needs to access the LLM and support one endpoint. For ease of development, I plan to 
use FastAPI to quickly get the backend server and endpoint created, so that more time can be spent on getting the LLM working properly and on the UI.

### LLM
Need to access an LLM online for free somehow. Maybe with this: https://modal.com/pricing 

## Deployment
Maybe on Vercel

## Flow/Sequences

## UI/UX
Initial landing page should contain a title and a search bar, along with a button to confirm the search. This should bring you to the next page, which
will display either the error message, or the formatted search results, along with a button to go back to the search page.

## Risks/Constraints

## Appendix?

gn specification document outlining the design of the end -to-end 
software. Be as detailed and complete as possible. This should include the requirements 
being addressed by the design spec, an overview of the design, scope, the components 
involved, the flow/sequences of the application, UI/UX, risks and constraints, along with clear 
explanatory narratives. Include other areas that you feel should be included. Add your 
alternate designs, if any, as an appendix. 