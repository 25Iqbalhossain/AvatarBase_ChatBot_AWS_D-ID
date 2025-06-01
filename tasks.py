from tools import create_vector_database, setup_retriever, build_chatbot

# Task: Vectorize data
def vectorize_data(inputs):
    json_file_path = inputs.get("json_file_path")
    if not json_file_path:
        return {"error": "No JSON file path provided."}

    try:
        vector_db = create_vector_database(json_file_path)
        return {"database": vector_db}
    except Exception as e:
        return {"error": f"Vectorization error: {str(e)}"}

# Task: Design retriever
def design_retriever(inputs):
    vector_database = inputs.get("vector_database")
    if not vector_database:
        return {"error": "No vector database provided."}

    try:
        retriever = setup_retriever(vector_database)
        return {"retriever": retriever}
    except Exception as e:
        return {"error": f"Retriever design error: {str(e)}"}

# Task: Implement chatbot
def implement_chatbot(inputs):
    retriever = inputs.get("retriever")
    if not retriever:
        return {"error": "No retriever provided."}

    try:
        chatbot = build_chatbot(retriever)
        return {"chatbot": chatbot}
    except Exception as e:
        return {"error": f"Chatbot implementation error: {str(e)}"}

# Utility: Format responses
def format_responses(response, query_type):
    """
    Format the chatbot response based on query type.

    Args:
        response (str): The raw response from the chatbot.
        query_type (str): The type of query ('list' or 'paragraph').

    Returns:
        str: The formatted response.
    """
    if query_type == "list":
        return "\n".join(f"- {item.strip()}" for item in response.split("\n") if item.strip())
    elif query_type == "paragraph":
        return response.strip()
    return response
