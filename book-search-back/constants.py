from pydantic import BaseModel


#main
class BookRequest(BaseModel):
    sentence: str

origins = [
    "http://localhost:3000",
    "https://localhost:3000",
    "http://book-search-frontend-vert.vercel.app",
    "https://book-search-frontend-vert.vercel.app",
]

OpenLibraryURL = 'https://openlibrary.org/search.json?'

BATCH_SIZE = 25


#llms
MODEL_NAMES = ["mixtral-8x7b-32768"] #Groq model names

BACKUP_NAME = "hysts/mistral-7b" #huggingface model name

ol_fields = [ #OpenLibrary fields to look for
    'title', 'author', 'subject', 'place', 'person', 'language', 'publisher', 'publish year', 'ddc', 'lcc', 'page', 'sort', 'lang'
]

LIMIT = 50 #max number of books to check at a time

GROQ_KEY = ""
with open("/etc/secrets/groq-key.txt", "r") as file:
    GROQ_KEY = file.read()