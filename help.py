
async def intent_classify(chat_chain, question):
    print("Database Hit",question)
    intent_answer = chat_chain.invoke(question)
    return intent_answer
