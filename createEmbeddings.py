#this file is used to create embeddings for the email text and upload them to Pinecone.

from openai import OpenAI
from dotenv import load_dotenv
import os
import pandas as pd
import tiktoken
import matplotlib.pyplot as plt
from pinecone import Pinecone

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_KEY")
MODEL = "text-embedding-3-small"

client = OpenAI(
    api_key=OPENAI_API_KEY
)

pc = Pinecone(api_key=PINECONE_API_KEY)
INDEX = pc.Index("mail")


def token_counter(df): #counting tokens for the email text so I don't spend too much money
    tokenizer = tiktoken.get_encoding("cl100k_base")
    df['n_tokens'] = df.body.apply(lambda x: len(tokenizer.encode(x)))
    df.n_tokens.hist()
    print(df.n_tokens.describe())
    plt.show()

def remove_newlines(serie): #cleaning up some data
    serie = serie.str.replace('\n', ' ')
    serie = serie.str.replace('\\n', ' ')
    serie = serie.str.replace('  ', ' ')
    serie = serie.str.replace('  ', ' ')
    return serie

def read_csv(): #reading the csv file
    df = pd.read_csv('email.csv')
    df['body'] = remove_newlines(df.body)
    df = df.fillna('nan') #filling in missing values
    return df

def create_embeddings(df, model, index): #creating embeddings for the email text and uploading to pinecone
    BATCH_SIZE = 50
    for i in range(0, len(df), BATCH_SIZE):
        print(f"Processing {i} to {i+BATCH_SIZE}...")
        res = client.embeddings.create(
            input=df.body[i:i+BATCH_SIZE], model=model
        )
        embeds = [record.embedding for record in res.data]
        ids = df.id[i:i+BATCH_SIZE]
        meta = df[['subject', 'from', 'to']][i:i+BATCH_SIZE].to_dict(orient='records')
        to_upsert = zip(ids, embeds, meta)
        index.upsert(vectors=list(to_upsert))
        print("tokens used: ", res.usage.total_tokens)
    print("DONE!")


df = read_csv()

#create_embeddings(df[1400:2000], MODEL, INDEX) #so far I've created embeddings for first 2000 emails out of approx. 10000 in the dataset


#a sample query to check if the embeddings are working 
res = client.embeddings.create(
    input="How can I learn about how artificial intelligence is impacting the healthcare field?", model=MODEL    
)
print("\n\n")
print(res.data[0].embedding)

