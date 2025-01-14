from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio

class BookRequest(BaseModel):
    sentence: str

origins = [
    "http://localhost:3000",
    "https://localhost:3000"
]

OpenLibraryURL = 'https://openlibrary.org/search.json?'

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=['POST','GET','OPTIONS'],
    allow_headers=["*"]
)


@app.get("/")
async def index():
    return {"message": "Hello World"}

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
    print(req)
    sent = req.sentence
    print(sent)
    prompt = """From the given text, return any information related to the given fields in a JSON formatted object:\n
        fields: 'title', 'author', 'subject', 'place', 'person', 'language', 'publisher', 'publish year', 'ddc', 'lcc', 'page', 'profanity'\n
        text: {0}""".format(sent) #use sent to create a prompt
    #call huggingface space to parse out data
    dummy_data = "{0}q=stormlight archives".format(OpenLibraryURL)
    try:
        resps = await perform_requests([dummy_data])
        if len(resps) < 1:
            return "No books found matching that description. Try modifying your search criteria."
        status = resps[0].status_code
        body = resps[0].json()
        if status == 200: #success
            if body["num_found"] == 0:
                return []#"No books found matching that description. Try modifying your search criteria."]
            else:
                data = []
                for item in body["docs"]:
                    data.append({
                        "title": item["title"],
                        "author": item["author_name"][0],
                        "description": "testing testing 123"
                    })
                    #data += '"{0}" by {1}\n\n'.format(item["title"], item["author_name"][0])
                return data
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
        raise HTTPException(status_code=status, detail="Error: Unknown issue: {0}".format(body))
    return []
    #return data/error message
