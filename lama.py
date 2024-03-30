import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langserve import add_routes
from langchain_community.llms import LlamaCpp
from llama_cpp import Llama
from langchain_core.callbacks import CallbackManager, StreamingStdOutCallbackHandler
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

# Callbacks support token-wise streaming
callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])

model_path = "model/llama-2-7b-chat.Q5_K_M.gguf"
llm = LlamaCpp(
    model_path=model_path,
    temperature=0.75,
    max_tokens=512,
    top_p=1,
    callback_manager=callback_manager,
    verbose=True,
)

intent_classification_template = """You are a classification expert who classify text, classify the user intent from message. The user message is: {msg}. Is the user looking for a live update or information about the bus services (live_query) or is it a general question (general_chat)? Generate one word response"""
intent_classification_chain = PromptTemplate.from_template(intent_classification_template) | llm

def _parse_intent(response):
    print("_parse_intent line 29 ", response)
    if "live update" in response.lower() or "information" in response.lower():
        print("if live_query line 31 ")
        return "live_query"
    else:
        print("else general 34 ")
        return "general_chat"

def parse_intent(info): 
    print("Information type is 37:", type(info))
    print("Content in info is 39: ", info)
    # intent = _parse_intent(info) 
    # return {"intent": intent, "msg": info["msg"]}
    # response = info["output"] 
    return _parse_intent(info)

def _generate_response(msg):
    print("_generate_response line 43: ",msg)
    if msg == "live_query":
        print("line 46: ",msg)
        # prompt = PromptTemplate.from_template(f"The user is asking a live query. Please identify the entities (locations, timings) from the user message: {msg}") | llm
    else:
        print("line 49: ",msg)
        # prompt = PromptTemplate.from_template(f"The user is asking a general question. Please answer the user in a short and informative way, but don't add any emojis. User question: {msg}") | llm
    return msg


def generate_response(info):
    print("Information type is line 55:", type(info))
    print("Content in info is line 56: ", info)
    # intent = info['intent']
    # msg = info['msg']
    return _generate_response(info)
    
  

initial_chain = {"msg": lambda x: x["msg"]}    
# print("fur  N ",initial_chain) 
# full_chain = initial_chain |intent_classification_chain| RunnableLambda(parse_intent) | RunnableLambda(generate_response)
intent_classification_chain = initial_chain | intent_classification_chain | RunnableLambda(parse_intent)
full_chain =  intent_classification_chain | RunnableLambda(generate_response)


app = FastAPI(title="LangChain", version="1.0", description="The fast server!")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

response = add_routes(app, full_chain, path="/chain")

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
