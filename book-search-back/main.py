from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio
from gradio_client import Client
import json

class BookRequest(BaseModel):
    sentence: str

ol_fields = [
    'title', 'author', 'subject', 'place', 'person', 'language', 'publisher', 'publish year', 'ddc', 'lcc', 'page', 'sort', 'lang'
]

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

client = Client("hysts/mistral-7b")


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
    
async def parse_data(sent): #query llm to get relevant data from user input, and then parse that information in a url fit for the OpenLibrary search API
    prompt = """From the given TEXT, find any information related to the given FIELDS and organize it in a JSON formatted object.\n
    Return only this JSON formatted object, do not provide any additional explanations.\n\n
        FIELDS: 'title', 'author', 'subject', 'place', 'person', 'language', 'publisher', 'publish year', 'ddc', 'lcc', 'page', 'sort', 'lang', 'profanity'\n
        TEXT: {0}""".format(sent) #use sent to create a prompt
    
    try:
        result = client.predict( #get llm output from huggingface
            message=prompt,
            param_2=1024,
            param_3=0.6,
            param_4=0.9,
            param_5=50,
            param_6=1.2,
            api_name="/chat"
        ) 
        print(result)
    except Exception as e:
        return False, "Model usage quota exceeded. Try again in an hour"

    if "{" in result and "}" in result: #postprocess llm output to improve chances of successful json load
        start = result.index("{")
        end = result.rindex("}") + 1
        result = result[start:end]
    else: #can't be json formatted, just attempt to use the original sentence with q input
        return True, "q={0}&page=1".format(sent)

    try:
        obj = json.loads(result.lower()) #try to organize string into data
        print(obj)
        if "profanity" in obj:
            prof = obj["profanity"]
            if prof in [None, False] or "null" in prof or "false" in prof or len(prof) < 1: #not actual profanity
                del obj["profanity"]
            else:
                return False, "Your question was flagged for profanity and was rejected, please try a different question."
        
        url = ""
        first = True
        for key in ol_fields: #check which of the useable fields ended up in the json object
            if key in obj:
                val = obj[key]
                if isinstance(val, list):
                    val = " ".join(val)

                if val in [None, False] or "null" in val or len(val) < 1:
                    continue #not a useful value

                if not (key in ['title', 'author'] or key in sent.lower()):
                    continue #including too much information can break queries

                if first:
                    first = False
                else:
                    url += "&"
                url += "{0}={1}".format(key, val)
        
        if first: #no fields were found/added
            url = "q={0}".format(sent)

        if "page" not in url:
            url += "&page=1"

        return True, url
    except ValueError: #failed to decode it properly, just attempt to use the original sentence with q input
        return True, "q={0}&page=1".format(sent)

def get_description(data): #query LLM to get a description for a given book
    prompt = """Give a one sentence description of the book '{0}' by author '{1}'.\n
        Return only the book description, do not give any additional explanations.""".format(data['title'], data['author'])
    
    desc = ""
    try:
        desc = client.predict( #get llm output from huggingface
            message=prompt,
            param_2=1024,
            param_3=0.6,
            param_4=0.9,
            param_5=50,
            param_6=1.2,
            api_name="/chat"
        ) 
    except Exception as e: #model usage quota exceeded
        desc = "Model usage quota exceeded. Try again in an hour"

    return desc

@app.post("/search-books")
async def search_books(req: BookRequest):
    sent = req.sentence
    print("sentence: {0}".format(sent))
    success, val = await parse_data(sent) #call huggingface space to parse out data
    print("success: {0}, val: {1}".format(success, val))
    if not success:
        return val
    olURL = "{0}{1}".format(OpenLibraryURL, val)
    print(olURL)
    try:
        resps = await perform_requests([olURL])
        if len(resps) < 1:
            return "No books found matching that description. Try modifying your search criteria."
        status = resps[0].status_code
        body = resps[0].json()
        print("body: {0}".format(body))
        if status == 200: #success
            if body["num_found"] == 0:
                return "No books found matching that description. Try modifying your search criteria."
            else:
                data = []
                for item in body["docs"]:
                    obj = {
                        "title": item["title"],
                        "author": item["author_name"][0]
                    }
                    obj['description'] = get_description(obj)
                    data.append(obj)

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
        raise HTTPException(status_code=404, detail="Error: Unknown issue: {0}".format(e))
