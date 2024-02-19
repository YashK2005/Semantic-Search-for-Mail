from openai import OpenAI
from dotenv import load_dotenv
import os
from pinecone import Pinecone
import webbrowser

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_KEY")
MODEL = "text-embedding-3-small"

client = OpenAI(
    api_key=OPENAI_API_KEY
)

pc = Pinecone(api_key=PINECONE_API_KEY)
INDEX = pc.Index("mail")


def create_embedding(text, model, index): #creates an embedding for the given text
    res = client.embeddings.create(
        input = text, model = model
    )
    # print("\n\n")
    # print(res.data[0].embedding)
    return res.data[0].embedding

def query_embeddings(query, model, index): #creates an embedding for given text and return the 5 most similar results
    embedding = create_embedding(query, model, index)
    res = index.query(vector=embedding, top_k=5, include_metadata=True)
    return res

def get_mail_link(result): #returns the link to the most similar email
    first_id = result["matches"][0]["id"]
    first_score = result["matches"][0]["score"]
    print(first_score) #for information purposes
    link = "https://mail.google.com/mail/u/2/#all/" + first_id
    return link

def open_link(link): #opens the link in the default web browser
    webbrowser.open(link, new=2)

def main():
    #query = "Tell me about how AI is being used in healthcare."
    query = input("Enter your query: ")
    result = query_embeddings(query, MODEL, INDEX)
    link = get_mail_link(result)
    open_link(link)

main()