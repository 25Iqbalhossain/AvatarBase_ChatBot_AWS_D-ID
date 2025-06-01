import os
from dotenv import load_dotenv
from tasks import vectorize_data, design_retriever, implement_chatbot, format_responses
from langchain.vectorstores import Chroma


# Load environment variables
load_dotenv()

JSON_FILE_PATH = r"C:\Users\25ikb\OneDrive\Desktop\timerin_pro\chat_bot\GENZMarketing.json"

def crew_workflow(query):
    print("\n--- Crew Workflow Started ---")
    print("Received Query:", query)

    # Step 1: Vectorize data
    vectorization_result = vectorize_data({"json_file_path": JSON_FILE_PATH})
    if "error" in vectorization_result:
        print("❌ Vectorization Error:", vectorization_result["error"])
        return {"status": "error", "error": vectorization_result["error"]}

    print("✅ Vectorization successful.")

    # Step 2: Design retriever
    retriever_result = design_retriever({"vector_database": vectorization_result["database"]})
    if "error" in retriever_result:
        print("❌ Retriever Error:", retriever_result["error"])
        return {"status": "error", "error": retriever_result["error"]}

    print("✅ Retriever initialized.")

    # Step 3: Implement chatbot
    chatbot_result = implement_chatbot({"retriever": retriever_result["retriever"]})
    if "error" in chatbot_result:
        print("❌ Chatbot Init Error:", chatbot_result["error"])
        return {"status": "error", "error": chatbot_result["error"]}

    print("✅ Chatbot implementation successful.")

    # Query chatbot
    chatbot = chatbot_result["chatbot"]
    response = chatbot(query)

    if not response or "result" not in response:
        print("❌ Chatbot returned no response!")
        return {"status": "error", "error": "Chatbot did not generate a response."}

    print("✅ Chatbot response received.")

    query_type = "list" if "list" in query.lower() else "paragraph"
    formatted_response = format_responses(response["result"], query_type)

    print("Final Response:", formatted_response)

    return {
        "status": "success",
        "response": formatted_response,
        "sources": response.get("sources", [])
    }
