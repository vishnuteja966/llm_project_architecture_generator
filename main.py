import os
import glob
import json
from uuid import uuid4
import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.schema import Document
import time  # Added for file generation waiting
from prompt_template import prompt_template

# Set up OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validate API Key
if not OPENAI_API_KEY:
    st.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    st.stop()

# Load the knowledge base and create a vector store for retrieval
def load_vector_store(knowledge_base_path="knowledge_base.json"):
    try:
        with open(knowledge_base_path, "r") as file:
            knowledge = json.load(file)
    except FileNotFoundError:
        st.error(f"Knowledge base file '{knowledge_base_path}' not found.")
        st.stop()
    except json.JSONDecodeError:
        st.error("Error decoding the knowledge base JSON file. Please check its format.")
        st.stop()

    # Create LangChain documents from the knowledge base
    documents = []
    for service, details in knowledge.items():
        content = (
            f"{service}: {details['description']}\n"
            f"Benefits: {', '.join(details['benefits'])}\n"
            f"Use Cases: {', '.join(details['use_cases'])}\n"
            f"Alternatives: {', '.join(details['alternatives'])}\n"
            f"Decision Factors: {', '.join(details['decision_factors'])}"
        )
        metadata = {"service": service}
        documents.append(Document(page_content=content, metadata=metadata))

    # Split and vectorize documents
    text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    split_docs = text_splitter.split_documents(documents)

    # Create a vector store with FAISS
    try:
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        vector_store = FAISS.from_documents(split_docs, embeddings)
    except Exception as e:
        st.error(f"Error creating FAISS vector store: {e}")
        st.stop()

    return vector_store


# Initialize the vector store
vector_store = load_vector_store()

# Retriever for RAG
retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 5})

# Initialize LangChain LLM
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.0,
    openai_api_key=OPENAI_API_KEY
)

# Prompt template for generating Python code dynamically

# Combine prompt template with LangChain
prompt = ChatPromptTemplate.from_template(prompt_template)
llm_chain = LLMChain(llm=llm, prompt=prompt)

# Streamlit app interface
st.title("Advanced Cloud Architecture Generator")
st.write("Enter your requirements. The system will recommend services and generate a diagram.")

# User input
input_text = st.text_area("Describe your architecture:")

# Streamlit logic
if input_text:
    if st.button("Generate Diagram"):
        try:
            # Retrieve relevant knowledge
            retrieved_docs = retriever.get_relevant_documents(input_text)
            service_context = "\n".join([doc.page_content for doc in retrieved_docs])

            if not service_context:
                st.error("No matching services found in the knowledge base.")
            else:
                # Save service descriptions to a separate text file
                service_descriptions = "\n\n".join([doc.page_content for doc in retrieved_docs])
                descriptions_filename = f"service_descriptions_{uuid4().hex}.txt"
                with open(descriptions_filename, "w") as desc_file:
                    desc_file.write(service_descriptions)

                # Display the saved file confirmation
                st.success(f"Service descriptions saved to: {descriptions_filename}")
                st.text_area("Service Descriptions:", service_descriptions, height=300)

                # Generate code with LLM
                response = llm_chain.run({
                    "user_request": input_text,
                    "service_context": service_context
                })

                # Clean up the response to ensure valid Python code
                cleaned_response = response.replace("```python", "").replace("```", "").strip()

                # Save the cleaned code to a file
                with open("complex_architecture.py", "w") as file:
                    file.write(cleaned_response)

                # Display the cleaned code
                st.code(cleaned_response, language="python")
                diagram_filename = f"diagram_{uuid4().hex}.png"

                # Execute the code to create the diagram
                os.system("python complex_architecture.py")

                # Wait for the file to be created
                time.sleep(2)  # Wait to ensure the file is generated
                diagram_path = glob.glob("*.png")

                # Display the generated diagram
                if diagram_path:
                    latest_diagram = max(diagram_path, key=os.path.getctime)
                    st.image(latest_diagram, caption="Generated Architecture Diagram")
                else:
                    st.error("Diagram generation failed. Please check the generated Python code.")
        except Exception as e:
            st.error(f"An error occurred: {e}")

