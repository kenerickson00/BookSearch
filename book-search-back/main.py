from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio
from constants import BookRequest, origins, OpenLibraryURL
from llms import parse_data, get_descriptions


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=['POST', 'OPTIONS'],
    allow_headers=["*"]
)


async def request(client, url):
    response = await client.get(url)
    return response

async def perform_requests(urls):
    async with httpx.AsyncClient() as client:
        reqs = list(map(lambda u: request(client, u) ,urls))
        results = await asyncio.gather(*reqs)
        return results
    
    
@app.post("/search-books")
async def search_books(req: BookRequest):
    sent = req.sentence #user input
    success, val = await parse_data(sent) #parse sentence into useful input for OpenLibrary query
    if not success:
        if val is None: #try again in case it was just due to a model quota issue
            success, val = await parse_data(sent) #call huggingface space to parse out data
            if not success:
                return val
        else:
            return val
        
    olURL = "{0}{1}".format(OpenLibraryURL, val) #form actual query string
    try:
        resps = await perform_requests([olURL]) #get data from OpenLibrary
        if len(resps) < 1:
            return "No books found matching that description. Try modifying your search criteria."
        
        status = resps[0].status_code
        body = resps[0].json()

        if status == 200: #success
            if body["num_found"] == 0:
                return "No books found matching that description. Try modifying your search criteria."
            else: #books found
                data = []
                for item in body["docs"]: #organize title and author names
                    try:
                        obj = {
                            "title": item["title"],
                            "author": item["author_name"][0]
                        }
                        data.append(obj)
                    except Exception as e:
                        pass

                if len(data) > 0: #dont perform needless queries
                    ret, data = get_descriptions(data) #use llm to get descriptions for all the books
                    while not ret: #try again in case of quota issues
                        ret, data = get_descriptions(data)
                return data #return books with title, author, description
        elif status == 400:
            raise HTTPException(status_code=status, detail="Error: Unable to find searchable data in your question: {0}".format(body))
        elif status == 403:
            raise HTTPException(status_code=status, detail="Error: Forbidden, you don't have the permissions to access this resource: {0}".format(body))
        elif status == 404:
            raise HTTPException(status_code=status, detail="Error: Unable to access Open Library, resource may be down: {0}".format(body))
        elif status == 500:
            raise HTTPException(status_code=status, detail="Error: Request caused internal errors at Open Library, your question may need to be modified: {0}".format(body))
        else:
            raise HTTPException(status_code=status, detail="Error: Unknown issue: {0}".format(body))
    except Exception as e:
        raise HTTPException(status_code=405, detail="Error: Request to OpenLibrary failed for unknown reason. Try submitting the same question again.")
