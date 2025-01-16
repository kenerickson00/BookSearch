from gradio_client import Client
from groq import Groq
import json
import re
from constants import MODEL_NAMES, BACKUP_NAME, GROQ_KEY, ol_fields, LIMIT


BACKUP = False
MODEL_INDEX = 0

client = Groq( #load groq client
    api_key=GROQ_KEY,
)


async def remove_comments(result): #remove comments, llm often adds them and they ruin the json load. Helper for parse_data
    lines = result.split("\n")
    newres = []
    for line in lines:
        if not ("//" in line or "null" in line): #remove comment lines or null lines. Commentted lines are typically null anyway, and the llm is justifying the null value
            newres.append(line)

    if len(newres) > 2: #at least one line other than {}
        if newres[-2].strip()[-1] == ",": #remove extra trailing comma, since it can cause json conversion to fail
            newres[-2] = newres[2].strip()[:-1]
        return "\n".join(newres).strip()
    else:
        return result.strip() #just return original, nothing found
    
    
async def parse_data(sent): #query llm to get relevant data from user input, and then parse that information in a url fit for the OpenLibrary search API
    global BACKUP, MODEL_INDEX, client
    prompt = """From the given TEXT, find any information related to the given FIELDS and organize it in a JSON formatted object.\n
    Return only this JSON formatted object, do not provide any additional explanations or comments.\n\n
        FIELDS: 'title', 'author', 'subject', 'place', 'person', 'language', 'publisher', 'publish year', 'ddc', 'lcc', 'page', 'sort', 'lang', 'profanity'\n
        TEXT: {0}""".format(sent) #use sent to create a prompt
    
    try:
        if BACKUP:
            result = client.predict( #get llm output from huggingface
                message=prompt,
                param_2=128, 
                param_3=0.6,
                param_4=0.9,
                param_5=50,
                param_6=1.2,
                api_name="/chat"
            )
        else: #use groq if possible, faster
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=MODEL_NAMES[MODEL_INDEX],
                max_completion_tokens=128
            )
            result = chat_completion.choices[0].message.content

    except Exception as e:
        if BACKUP: #Backup used up too, just use no descriptions
            return False, "Model usage quota exceeded. Try again tomorrow"
        else:
            MODEL_INDEX += 1 #use next model that hasn't been exceeded yet
            if MODEL_INDEX >= len(MODEL_NAMES): #switch to huggingface backup option
                BACKUP = True
                client = Client(BACKUP_NAME)
            return False, None
        
    if "{" in result and "}" in result: #postprocess llm output to improve chances of successful json load
        start = result.index("{")
        end = result.rindex("}") + 1
        result = result[start:end]
    else: #can't be json formatted, just attempt to use the original sentence with q input
        return True, "q={0}&limit={1}".format(sent, LIMIT)

    result = await remove_comments(result) #remove comments since they cause json loading issues and the llm includes them sometimes

    try:
        obj = json.loads(result.lower()) #try to organize string into data
        if "profanity" in obj:
            prof = obj["profanity"]
            if prof in [None, False] or "null" in prof or "false" in prof or "no" in prof or len(prof) < 1: #not actual profanity
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

                if key == "page":
                    try:
                        pagenum = int(val)*LIMIT
                        if first:
                            first = False
                        else:
                            url += "&"
                        url += "offset={0}".format(pagenum)
                    except Exception as e:
                        pass
                    continue

                if not (key in ['title', 'author'] or key in sent.lower()):
                    continue #including too much information can cause nothing to be returned, only include extra fields if explicitly asked for

                if first:
                    first = False
                else:
                    url += "&"
                url += "{0}={1}".format(key, val)
        
        if first: #no fields were found/added
            url = "q={0}".format(sent)

        if "limit" not in url:
            url += "&limit={0}".format(LIMIT)

        return True, url
    except ValueError: #failed to decode it properly, just attempt to use the original sentence with q input
        return True, "q={0}&limit={1}".format(sent, LIMIT)
    

def get_descriptions(data): #query LLM to get a descriptions for all books, may be less accurate but should be faster and use up quota less quickly
    global BACKUP, MODEL_INDEX, client
    
    prompt = """For each book with specified TITLE and AUTHOR in the given LIST, give a detailed 1-2 sentence description and recommendation of the book.\n
    Return your results in a LIST containing only the descriptions, in the same order as the original list.\n
    Do not include any additional information or explanations.\n\n
        LIST: {0}""".format(data)
    
    try:
        if BACKUP: #use huggingface otherwise as an alternative
            ret = client.predict( #get llm output from huggingface
                message=prompt,
                param_2=128*len(data), #vary length based on number of descriptions
                param_3=0.6,
                param_4=0.9,
                param_5=50,
                param_6=1.2,
                api_name="/chat"
            )
        else: #use groq if possible, faster
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=MODEL_NAMES[MODEL_INDEX],
                max_completion_tokens=128*len(data) #vary length based on number of descriptions
            )
            ret = chat_completion.choices[0].message.content

        if "[" in ret and "]" in ret: #turn string to array
            start = ret.index("[")+1 #remove braces
            end = ret.rindex("]")
            ret = ret[start:end]

            arr = re.split(r'",|\',|’,', ret) #split into list
            for i in range(len(arr)):
                if i >= len(data):
                    break
                val = arr[i].strip()
                if len(val) > 0 and val[0] in ["'", '"', "’"]: #remove extra str markers
                    val = val[1:]
                data[i]["description"] = val #add to data
        
        return True, data
    except Exception as e: #model usage quota exceeded
        if BACKUP: #Backup used up too, just use no descriptions
            return True, data
        else:
            MODEL_INDEX += 1 #use next model that hasn't been exceeded yet
            if MODEL_INDEX >= len(MODEL_NAMES): #switch to huggingface backup option
                BACKUP = True
                client = Client(BACKUP_NAME)
            return False, data