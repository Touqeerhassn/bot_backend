from fastapi import HTTPException
import json

async def data_query(db_chain, question, collection, checkData):
    try:
        source = checkData["source"]
        destination = checkData["destination"]
        price = checkData["price"]
        if source and destination and price:
            result = await collection.find_one({"pickup_address": source,"drop_address": destination})
            if result:
                filtered_result = {
                    "pickup_address": result.get("pickup_address", ""),
                    "drop_address": result.get("drop_address", ""),
                    "pick_up_time": result.get("pick_up_time", ""),
                    "drop_time": result.get("drop_time", ""),
                    "price": result.get("price", "")
                    }
                # Convert filtered_result dictionary to a JSON-formatted string
                result_string = json.dumps(filtered_result)
                response = db_chain.invoke(question + result_string)
                return response
            else:
                response = db_chain.invoke(question + "No data available")
                return response

        elif source and destination:
            result = await collection.find_one({"pickup_address": source,"drop_address": destination})
            if result:
                filtered_result = {
                    "pickup_address": result.get("pickup_address", ""),
                    "drop_address": result.get("drop_address", ""),
                    "pick_up_time": result.get("pick_up_time", ""),
                    "drop_time": result.get("drop_time", ""),
                    "price": result.get("price", "")
                    }
                # Convert filtered_result dictionary to a JSON-formatted string
                result_string = json.dumps(filtered_result)
                response = db_chain.invoke(question + result_string)
                return response
            else:
                response = db_chain.invoke(question + "No data available")
                return response

        else:
            response = db_chain.invoke(question)
            return response
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500)

    
def responses(user,val):
    print(f"User said : {user}")
    response=''
    
    id1=val.argsort()[0][-2]
    #print(idx)
    flat = val.flatten()
    flat.sort()
    req = flat[-2]


    
GREETING_INPUTS = ("hello", "hi", "greetings", "sup", "what's up","hey","how are you")
GREETING_RESPONSES = ["hi", "hey", "hi there", "hello", "I am glad! You are talking to me"]
def greeting(sentence):

    for word in sentence.split():
        if word.lower() in GREETING_INPUTS:
            return GREETING_RESPONSES

async def intent_classification(user_input, question):
    predict_class ={}
    extract_entities={}
    GREETING_INPUTS= {}
    for word in response.split():
        if word.lower() in GREETING_INPUTS:
            return predict_class

    for word in response.split():
        if word.lower() in ["nice","good","good job","okay","cool","great"]:
            return "smile.."

    if(predict_class == 0):
        response = responses(str(user_input))
        return response     

    elif(predict_class == 1):
        response = extract_entities(user_input)
        return response

    elif(predict_class == 2):
        response = extract_entities(user_input)
        return response
    
    elif(predict_class == 3):
        response = extract_entities(user_input)
        return response

    return response