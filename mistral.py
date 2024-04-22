from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.llms import LlamaCpp
from langchain_core.callbacks import CallbackManager, StreamingStdOutCallbackHandler
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
import uvicorn
import re
from help import data_query
from help import intent_classification
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

mongo_url = 'mongodb+srv://touqeerqfnetwork:egLjfh7Jlsq69oN6@cluster0.cruq0gs.mongodb.net/?retryWrites=true&w=majority'
client = AsyncIOMotorClient(mongo_url)
database = client["test"]
collection = database["buses"]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# template = """Recognize the user's intent from the given text delimited by triple quotes. Possible intents are [general query, data query]. Determine the intent with the highest confidence score. Answer in the format [\"intent\"] without any explanation. If no intent is identified with sufficient confidence, then only answer "[]"." ```{question}``` """
# initial_prompt = PromptTemplate.from_template(template)
query_template = """[INST] You are a bus travel services customer service bot. Your task is to assess customer query and recognize entities. Determine the entities with the highest confidence score in customer inquiry after <<<>>> one of the following predefined entities:

source
destination
time
price

If the text doesn't have any of the above entities, reply as:
not found

You will only respond with the entities. Do not include the word "entity". Do not provide explanations or notes.
[/INST]

####
Here are some examples:
#Example
Inquiry: I'm looking to go from islamabad to karachi. Can you tell me about the available buses and schedules?
Source: islamabad, destination: karachi
Inquiry: I'm planning to travel on 12/3/23 and I'd prefer the morning. What options do you have around 9 AM?
date: 12 march 2023, time: 9 AM
Inquiry: Hi! I'm planning a trip from karachi to Lahore. What are my options for tomorrow?
Source: Karachi, destination: lahore, time: tomorrow
Inquiry: What's the cost for a one-way ticket from karachi to Quetta?
Source: Karachi, destination: lahore
###

<<<
Inquiry: {question}
>>> """
query_prompt = PromptTemplate.from_template(query_template)
chat_prompt = PromptTemplate.from_template("""
[INST]You are a bus travel services customer service bot, and your task is to create single line personalized message responses to address customer questions. Answer the customer's inquiry in single line using the provided facts below. 
Use the fact only when required. Address the customer in a friendly and professional manner. Customer question after <<<>>>:
Generate single line response.[/INST]
                                           
<<<                                                                         
Question: {question}
>>>""")

db_template = """
    [INST]You are a bus travel services customer service bot, and your task is to create single line personalized message responses to address customer questions. After user question data is also provided, answer the customer's inquiry according to provide mongodb document. 
    Use the provided data only when required. Address the customer in a friendly manner and response single line answer. Customer question after <<<>>>:
    Generate single line response according to provided data.[/INST]
                                           
<<<                                                                         
Question: {question}
>>>"""


db_prompt = PromptTemplate.from_template(db_template)


classify_model = 'model/intent_classification.h5'
intent_classification = (classify_model)
callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])

llm = LlamaCpp(
    model_path="./model/mistral-7b-instruct-v0.2.Q5_K_M.gguf",
    temperature=0.2,
    max_tokens=160,
    top_p=0.7,
    callback_manager=callback_manager,
    verbose=True,  # Verbose is required to pass to the callback manager
)

# query_chain = query_prompt | llm | StrOutputParser()
initial_chain = query_prompt | llm | StrOutputParser()
chat_chain = chat_prompt | llm | StrOutputParser()
db_chain = db_prompt | llm | StrOutputParser()

@app.get("/ask")
async def ask_question(question: str = Query(..., description="Question to ask")):
    try:
        print("Question :",question)
        answer = initial_chain.invoke(question)
        
        response = {}
        if  "class" in answer.lower() and len(answer[0]) > 0:
            intent = answer["intents"][0]["name"]
            if  intent == 0:
                intent_answer = await intent_classification(chat_chain, question)
            elif  intent == 1:
                intent_answer = await intent_classification(chat_chain, question)
            elif  intent == 2:
                intent_answer = await intent_classification(chat_chain, question)

        if "source" in answer.lower() or "destination" in answer.lower() or "time" in answer.lower():
            print("This is answer ", answer)
            source_pattern = r"Source: (.*?)(?=,|$)"
            destination_pattern = r"destination: (.*?)(?=,|$)"
            time_pattern = r"Time: (.*?)(?=,|$)"
            price_pattern = r"Price: (\d+)"

            # Initialize extracted data with None values
            extracted_data = [None, None, None, None]

            # Attempt to extract data using regular expressions
            match = re.search(source_pattern, answer, flags=re.IGNORECASE)
            if match:
                extracted_data[0] = match.group(1).strip()
            match = re.search(destination_pattern, answer, flags=re.IGNORECASE)
            if match:
                extracted_data[1] = match.group(1).strip()
        
            match = re.search(time_pattern, answer, flags=re.IGNORECASE)
            if match:
                extracted_data[2] = match.group(1).strip()
            
            match = re.search(price_pattern, answer, flags=re.IGNORECASE)
            if match:
                extracted_data[3] = match.group(1).strip()
                
            checkData = {
                "source": extracted_data[0].capitalize() if extracted_data[0] is not None else None,
                "destination": extracted_data[1].capitalize() if extracted_data[1] is not None else None,
                "time": extracted_data[2],
                "price": extracted_data[3]
            }
            print("check====>it out ",checkData)
            intent_answer = await data_query(db_chain, question, collection, checkData)
            response["answer"] = intent_answer
    
        else:
            chat_answer = chat_chain.invoke(question)
            response["answer"] = chat_answer

        return response
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500)

    
if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)

