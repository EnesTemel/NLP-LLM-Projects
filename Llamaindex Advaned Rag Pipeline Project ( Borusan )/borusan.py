import utils
from dotenv import load_dotenv, find_dotenv
import os 
import streamlit as st
from llama_index import VectorStoreIndex, ServiceContext, Document, SimpleDirectoryReader
from llama_index.llms import OpenAI
from llama_index import SimpleDirectoryReader
from dotenv import load_dotenv, find_dotenv
import os 



# the function for getting the openai api key 
def get_openai_api_key():
    _ = load_dotenv(find_dotenv())
    
    return os.getenv("OPENAI_API_KEYY")
documents = SimpleDirectoryReader(
    input_files=["Main_Data.pdf"]
).load_data()

key=get_openai_api_key()
print(key)


def main():
    st.title("Borusan AutoHack")
    user_query = st.text_input("Enter your query:")
    submit_button = st.button('Submit Query')  # Add this line for the button

    if submit_button and user_query:
        response = query_engine.query(user_query)
        st.text("Response:")
        st.write(str(response))


from llama_index import Document

document = Document(text="\n\n".join([doc.text for doc in documents]))


from llama_index import VectorStoreIndex
from llama_index import ServiceContext
from llama_index.llms import OpenAI

llm = OpenAI(model="gpt-3.5-turbo", temperature=0.2)
service_context = ServiceContext.from_defaults(
    llm=llm, embed_model="local:BAAI/bge-small-en-v1.5"
)
index = VectorStoreIndex.from_documents([document],
                                        service_context=service_context)


query_engine = index.as_query_engine(similarity_top_k=10)

# response = query_engine.query("What are the new features in the Mini Countryman 2021 compared to its previous year's model?")



def main():
    st.title("Borusan Chatbot")
    user_query = st.text_input("What are the new features in the Mini Countryman 2021 compared to its previous year's model?")

    if user_query:
        response = query_engine.query(user_query)
        st.text("Response:")
        st.write(str(response))

if __name__ == "__main__":
    main()

