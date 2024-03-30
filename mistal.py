from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.llms import LlamaCpp
from langchain_core.callbacks import CallbackManager, StreamingStdOutCallbackHandler
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import uvicorn
from help import intent_classify
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

# mongo_url = 'mongodb+srv://touqeerqfnetwork:egLjfh7Jlsq69oN6@cluster0.cruq0gs.mongodb.net/?retryWrites=true&w=majority'
# client = AsyncIOMotorClient(mongo_url)
# database = client["test"]
# collection = database["buses"]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# template = """client question is: Question: {question}. What is User Intent in this sentence? Is it general chat? or is it Query? Generate single line answer do not explain details."""
# template = """Recognize the user's intent from the given text delimited by triple quotes. Possible intents are [general query, data query]. Determine the intent with the highest confidence score. Answer in the format [\"intent\"] without any explanation. If no intent is identified with sufficient confidence, then only answer "[]"." ```{question}``` """
# initial_prompt = PromptTemplate.from_template(template)
query_template = """You are a bus travel services customer service bot. Your task is to assess customer query and recognize entities in customer inquiry after <<<>>> one of the following predefined entities:

source
destination
time

If the text doesn't have any of the above entities, reply as:
not found

You will only respond with the entities. Do not include the word "entity". Do not provide explanations or notes.

####
Here are some examples:

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
chat_prompt = PromptTemplate.from_template("""[INST] You are a bus travel services customer service bot, and your task is to create personalized message responses to address customer questions. Answer the customer's inquiry using the provided facts below. Ensure that your response is short, clear, concise, and directly addresses the customer's question. Address the customer in a friendly and professional manner.[/INST] 

# Facts
Hello there: Hi! i hope  you're doing well
karachi to lahore: ticket price 4000, 8 PM to 12 PM
karachi to quetta: ticket price 3000, 6 PM to 9:30 PM
karachi to islamabad: ticket price 5500, 6 PM to 9:30 PM
lahore to karachi: ticket price 4000, 8 PM to 12 PM
quetta to karachi: ticket price 3000, 6 PM to 9:30 PM
islamabad to karachi: ticket price 5500, 6 PM to 9:30 PM
service available only: karachi, quetta, lahore, islamabad 
other location then pakistan: sorry not available
other cities then karachi, quetta, lahore, islamabad: sorry not available
                                           
# Question
{question} """)

queryNot_prompt = PromptTemplate.from_template("""[INST]You are a bus travel services customer service bot, and your task is to create personalized message responses to address customer questions. Answer the customer's inquiry using the provided facts below. Ensure that your response is clear, concise, and directly addresses the customer's question. Address the customer in a friendly and professional manner. Do not include the word "#Response" in start.[/INST]"

# Facts
Hello sir: Hi! my pleasure to assist you
service available only: karachi, quetta, lahore, islamabad 
other location then pakistan: sorry not available
other cities then karachi, quetta, lahore, islamabad: sorry not available
karachi to lahore: ticket price 4000, 8 PM to 12 PM
karachi to quetta: ticket price 3000, 6 PM to 9:30 PM
karachi to islamabad: ticket price 5500, 6 PM to 9:30 PM
lahore to karachi: ticket price 4000, 8 PM to 12 PM
quetta to karachi: ticket price 3000, 6 PM to 9:30 PM
islamabad to karachi: ticket price 5500, 6 PM to 9:30 PM

# Question
{question} """)
# queryNot_prompt = PromptTemplate.from_template("""Customer question is: Question: {question}.Act as bus service customer support, Please answer the customer in a short and informative way, but do not add any emojis and do not add any location name. Generate response to engage customer interactive way.""")
callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])

llm = LlamaCpp(
    model_path="./model/mistral-7b-instruct-v0.2.Q5_K_M.gguf",
    temperature=0.5,
    max_tokens=200,
    top_p=1,
    callback_manager=callback_manager,
    verbose=True,  # Verbose is required to pass to the callback manager
)

# query_chain = query_prompt | llm | StrOutputParser()
initial_chain = query_prompt | llm | StrOutputParser()
chat_chain = chat_prompt | llm | StrOutputParser()
queryNot_chain = queryNot_prompt | llm | StrOutputParser()

@app.get("/ask")
async def ask_question(question: str = Query(..., description="Question to ask")):
    
    answer = initial_chain.invoke(question)
    response = {}
    if "source" in answer.lower() or "destination" in answer.lower() or "time" in answer.lower():
        intent_answer = await intent_classify(chat_chain, question)
        response["answer"] = intent_answer
    
    else:
        chat_answer = chat_chain.invoke(question)
        response["answer"] = chat_answer

    return response

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)

