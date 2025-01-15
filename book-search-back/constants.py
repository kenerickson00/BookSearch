from pydantic import BaseModel


#main
class BookRequest(BaseModel):
    sentence: str

origins = [
    "http://localhost:3000",
    "https://localhost:3000"
]

OpenLibraryURL = 'https://openlibrary.org/search.json?'


#llms
MODEL_NAMES = ["mixtral-8x7b-32768", "llama-3.1-70b-versatile", "llama-guard-3-8b", "llama3-8b-8192"]

BACKUP_NAME = "hysts/mistral-7b"

ol_fields = [
    'title', 'author', 'subject', 'place', 'person', 'language', 'publisher', 'publish year', 'ddc', 'lcc', 'page', 'sort', 'lang'
]

GROQ_KEY = ""
with open("groq-key.txt", "r") as file:
    GROQ_KEY = file.read()