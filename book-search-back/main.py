from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio
#from gradio_client import Client
from groq import Groq
import json
import re

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

MODEL_NAME = "mixtral-8x7b-32768"

GROQ_KEY = ""
with open("groq-key.txt", "r") as file:
    GROQ_KEY = file.read()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=['POST','GET','OPTIONS'],
    allow_headers=["*"]
)

#client = Client("hysts/mistral-7b")
client = Groq(
    api_key=GROQ_KEY,
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
    
async def remove_comments(result):
    #remove comments, llm often adds them and they ruin the json load
    lines = result.split("\n")
    newres = []
    for line in lines:
        if not ("//" in line or "null" in line):
            newres.append(line)
    print("newres: {0}".format(newres))
    if len(newres) > 2: #at least one line other than {}
        if newres[-2].strip()[-1] == ",": #remove extra trailing comma, since it can cause json conversion to fail
            newres[-2] = newres[2].strip()[:-1]
        return "\n".join(newres).strip()
    else:
        return result.strip()
    
async def parse_data(sent): #query llm to get relevant data from user input, and then parse that information in a url fit for the OpenLibrary search API
    prompt = """From the given TEXT, find any information related to the given FIELDS and organize it in a JSON formatted object.\n
    Return only this JSON formatted object, do not provide any additional explanations or comments.\n\n
        FIELDS: 'title', 'author', 'subject', 'place', 'person', 'language', 'publisher', 'publish year', 'ddc', 'lcc', 'page', 'sort', 'lang', 'profanity'\n
        TEXT: {0}""".format(sent) #use sent to create a prompt
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=MODEL_NAME,
        )

        result = chat_completion.choices[0].message.content
        '''result = client.predict( #get llm output from huggingface
            message=prompt,
            param_2=1024,
            param_3=0.6,
            param_4=0.9,
            param_5=50,
            param_6=1.2,
            api_name="/chat"
        ) '''
        print(result)
    except Exception as e:
        return False, "Model usage quota exceeded. Try again in an hour"

    if "{" in result and "}" in result: #postprocess llm output to improve chances of successful json load
        start = result.index("{")
        end = result.rindex("}") + 1
        result = result[start:end]
    else: #can't be json formatted, just attempt to use the original sentence with q input
        return True, "q={0}&page=1".format(sent)

    result = await remove_comments(result)

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
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=MODEL_NAME,
        )

        desc = chat_completion.choices[0].message.content
        '''desc = client.predict( #get llm output from huggingface
            message=prompt,
            param_2=1024,
            param_3=0.6,
            param_4=0.9,
            param_5=50,
            param_6=1.2,
            api_name="/chat"
        ) '''
    except Exception as e: #model usage quota exceeded
        desc = "Model usage quota exceeded. Try again in an hour"

    return desc

def get_descriptions(data): #query LLM to get a descriptions for all books, may be less accurate but should be faster and use up quota less quickly
    prompt = """For each book with specified TITLE and AUTHOR in the given LIST, give a detailed 1-2 sentence description and recommendation of the book.\n
    Return your results in a LIST containing only the descriptions, in the same order as the original list.\n
    Do not include any additional information or explanations.\n\n
        LIST: {0}""".format(data)
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=MODEL_NAME,
        )

        ret = chat_completion.choices[0].message.content
        '''ret = client.predict( #get llm output from huggingface
            message=prompt,
            param_2=256*len(data), #vary length based on number of descriptions
            param_3=0.6,
            param_4=0.9,
            param_5=50,
            param_6=1.2,
            api_name="/chat"
        ) '''
        print(ret)
        if "[" in ret and "]" in ret:
            start = ret.index("[")+1
            end = ret.rindex("]")
            ret = ret[start:end]
            '''str = '",'
            if "'," in ret:
                str = "',"'''
            arr = re.split(r'",|\',|’,', ret)#ret.split(str)
            print(arr)
            for i in range(len(arr)):
                if i >= len(data):
                    break
                val = arr[i].strip()
                if len(val) > 0 and val[0] in ["'", '"', "’"]:
                    val = val[1:]
                data[i]["description"] = val
            return data
        else:
            return data

        '''jsn = '{ "arr": {0}}'.format(ret)
        try:
            obj = json.loads(jsn)
            arr = obj["arr"]
            print(arr)
            
            for i in range(len(arr)):
                if i >= len(data):
                    break
                data[i]["description"] = arr[i]
            return data
        except Exception as e: #json loading failed
            print("array parsing failed")
            return data'''
    except Exception as e: #model usage quota exceeded
        print("model issue")
        return data

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
        print("resps: {0}".format(resps))
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
                    #obj['description'] = get_description(obj)
                    data.append(obj)

                if len(data) > 0: #dont perform needless queries
                    data = get_descriptions(data)
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
        raise HTTPException(status_code=404, detail="Error: Request to OpenLibrary failed for unknown reason. Try submitting the same question again.")
