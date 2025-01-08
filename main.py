# https://kleiber.me/blog/2024/08/04/demystifying-vector-stores-lanchain-vector-store-from-scratch/
# https://www.datacamp.com/tutorial/llama-3-1-rag

print("Downloading nltk data...")
import nltk
nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger_eng')

import os
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import SKLearnVectorStore
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from rl_vecstore import RisingLightVectorStore

print("Loading documents...")

docs = []
for file in os.listdir("../docs"):
    if file.endswith(".md"):
        print(f"Loading {file}...")
        docs.append(UnstructuredMarkdownLoader("../docs/" + file).load())
docs_list = [item for sublist in docs for item in sublist]
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=250, chunk_overlap=0
)
doc_splits = text_splitter.split_documents(docs_list)

print("Creating embeddings...")

# Create embeddings for documents and store them in a vector store
vectorstore = RisingLightVectorStore.from_documents(
    documents=doc_splits,
    embedding=OllamaEmbeddings(model="llama3.2"),
)
retriever = vectorstore.as_retriever(k=4)

print("Creating model...")

prompt = PromptTemplate(
    template="""You are an assistant for question-answering tasks.
    Use the following documents to answer the question.
    If you don't know the answer, just say that you don't know.
    Use three sentences maximum and keep the answer concise:
    Question: {question}
    Documents: {documents}
    Answer:
    """,
    input_variables=["question", "documents"],
)

llm = ChatOllama(
    model="llama3.2",
    temperature=0,
)

rag_chain = prompt | llm | StrOutputParser()

class RAGApplication:
    def __init__(self, retriever, rag_chain):
        self.retriever = retriever
        self.rag_chain = rag_chain
    def run(self, question):
        # Retrieve relevant documents
        documents = self.retriever.invoke(question)
        # Extract content from retrieved documents
        doc_texts = "\\n".join([doc.page_content for doc in documents])
        # Get the answer from the language model
        answer = self.rag_chain.invoke({"question": question, "documents": doc_texts})
        return answer

rag_application = RAGApplication(retriever, rag_chain)

while True:
    question = input("Enter a question: ")
    answer = rag_application.run(question)
    print("Answer:", answer)
