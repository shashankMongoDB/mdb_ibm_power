import json
import numpy as np
import faiss
from flask import Flask, render_template, request, session, redirect, jsonify
from flask_session import Session
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.foundation_models.utils.enums import DecodingMethods
from ibm_watsonx_ai.foundation_models.extensions.langchain import WatsonxLLM
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
from bson import ObjectId

# Flask app
app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['SESSION_TYPE'] = 'filesystem'  # Use the filesystem to store session data
app.config["SESSION_PERMANENT"] = True  # Sessions expire when the browser is closed
app.config["SESSION_USE_SIGNER"] = True  # Sign session cookies for added security
Session(app)

# MongoDB connection
MONGO_CONN = "mongodb://localhost:27017/"
client = MongoClient(MONGO_CONN, tls=False, tlsAllowInvalidCertificates=True)

# Define collections
faq_collection = client["banking_quickstart"]["faqs"]
customer_collection = client["banking_quickstart"]["customers_details"]
transaction_collection = client["banking_quickstart"]["transactions_details"]
spending_insight_collection = client["banking_quickstart"]["spending_insight_details"]

# Initialize mpnet Embedding Model
model_path = "all-mpnet-base-v2"
embedding_model = SentenceTransformer(model_path)

# FAISS Index Setup for FAQs
embedding_dim = 768  # Embedding dimension for the model
faq_index = faiss.IndexFlatL2(embedding_dim)

def load_faq_index():
    """Load FAQ embeddings into FAISS index."""
    embeddings = []
    ids = []
    for doc in faq_collection.find():
        embeddings.append(doc["embedding"])
        ids.append(str(doc["_id"]))
    if embeddings:
        faq_index.add(np.array(embeddings, dtype=np.float32))
    return ids

# Load FAQ embeddings on startup
faqs_collection_ids=load_faq_index()

parameters = {
    GenParams.DECODING_METHOD: DecodingMethods.GREEDY,
    GenParams.MIN_NEW_TOKENS: 1,
    GenParams.MAX_NEW_TOKENS: 250,
    GenParams.TEMPERATURE: 0,
    GenParams.STOP_SEQUENCES: ["Human:", "Observation"]

}
llm_model = ModelInference(
    model_id="ibm/granite-3-8b-instruct",
    params=parameters,
    credentials={
        "url": "<API-URL>", #e.g: https://us-south.ml.cloud.ibm.com
        "apikey": "<API-KEY>"
    },
    project_id="<PROJECT-ID>"
)
granite_llm_ibm = WatsonxLLM(model=llm_model)

# -----------------------------
# FAQs Retrieval Function
# -----------------------------
def query_faqs(user_query):
    """Search FAQs using FAISS."""
    query_vector = embedding_model.encode(user_query).reshape(1, -1)
    distances, indices = faq_index.search(query_vector, k=5)

    context = []
    for idx, dist in zip(indices[0], distances[0]):
        if idx < len(faqs_collection_ids):
            doc_id = faqs_collection_ids[idx]
            doc = faq_collection.find_one({"_id": ObjectId(doc_id)})
            if doc:
                content = doc.get("content")
                metadata = doc.get("metadata", {})
                context.append(f"Content: {content}, Metadata: {metadata}")
    if not context:
        print("No relevant information found.")
        return "I'm sorry, I couldn't find relevant information for your query."

    print(f"Retrieved context: {context}")
    return "\n".join(context)


def query_personalized_data(user_query, customer_id):
    """Perform exact match query on a collection."""
    # Collection-to-Index Mapping
    collection_index_mapping = {
        "Customers": {"collection": customer_collection, "index": "customer_details_index"},
        "Transactions": {"collection": transaction_collection, "index": "transaction_detail_index"},
        "Spending Insights": {"collection": spending_insight_collection, "index": "sepending_detail_index"}
    }

    # MongoDB query for vector and text-based search
    def find_similar(collection, top_k=5):
        try:
            exact_match_results = []
            if customer_id:
                exact_match_pipeline = [
                    {
                        "$match": {
                            "customer_id": customer_id  # Use the extracted identifier or logged-in customer ID
                        }
                    },
                    {
                        "$project": {
                            "customer_id": 1,
                            "metadata.name": 1,
                            "metadata.email": 1,
                            "metadata.address": 1,
                            "metadata.account_balance": 1,
                            "metadata.phone": 1,
                            "metadata.description": 1,
                            "metadata.transaction_type": 1,
                            "metadata.most_spent_category": 1,
                            "metadata.last_month_savings": 1,
                            "metadata.monthly_expense": 1,
                            "metadata.monthly_income": 1,
                            "metadata.amount": 1,
                            "metadata.transaction_date": 1,
                            "metadata.answer": 1,
                            "content": 1,
                            "score": {"$literal": 1.0}  # Exact matches have a perfect score
                        }
                    }
                ]
                exact_match_results = list(collection.aggregate(exact_match_pipeline))
                print(f"Exact match retrieved {len(exact_match_results)} documents from {collection.name}")

            combined_results = exact_match_results
            combined_results.sort(key=lambda x: x["score"], reverse=True)  # Sort by descending score

            # Limit to top_k results
            return combined_results[:top_k]

        except Exception as e:
            print(f"Error querying collection {collection.name}: {e}")
            return []

    context = []
    for name, config in collection_index_mapping.items():
        collection = config["collection"]
        docs = find_similar(collection)
        print(docs)
        for doc in docs:
            content = doc.get("customer_id")
            metadata = doc.get("metadata", {})
            context.append(f"Source: {name}, Content: {content}, Metadata: {metadata}")
    if not context:
        print("No relevant information found.")
        return "I'm sorry, I couldn't find relevant information for your query."
    print(f"Retrieved context: {context}")
    return "\n".join(context)


# -----------------------------
# Flask Routes
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page."""
    if request.method == "POST":
        customer_id = request.form.get("customer_id")

        # Validate the customer ID from MongoDB
        customer = customer_collection.find_one({"customer_id": customer_id})
        if customer:
            # Store the customer ID and name in session
            session["customer_id"] = customer_id
            customer_name = customer.get("metadata", {}).get("name", "Customer")
            session["customer_name"] = customer_name
            return redirect("/chatbot")
        else:
            return render_template("login.html", error="Invalid Customer ID")

    return render_template("login.html")


@app.route("/chatbot")
def welcome():
    """Welcome page for logged-in users."""
    if "customer_id" not in session:
        return redirect("/")
    return render_template("chatbot.html", customer_name=session["customer_name"])


# Load keywords from a file
def load_keywords(file_path):
    with open(file_path, "r") as file:
        return json.load(file)


# Detect intent based on user input
def detect_intent(user_input, keywords):
    lower_input = user_input.lower()

    for intent, words in keywords.items():
        if any(keyword in lower_input for keyword in words):
            return intent
    return "unknown"


@app.route("/api/query", methods=["POST"])
def api_query():
    query = request.json.get("query")
    keywords_file = "keywords.json"
    keywords = load_keywords(keywords_file)
    intent = detect_intent(query, keywords)
    if intent != "unknown":
        context = request.json.get("query")
    else:
        """API endpoint for querying the chatbot."""
        customer_id = session.get("customer_id")

        if customer_id:
            # Customer-specific queries
            context = query_personalized_data(query, customer_id)
        else:
            # Only FAQs allowed for unauthenticated users
            if any(word in query.lower() for word in ["transaction", "spending", "my"]):
                return jsonify({"response": "Please log in to query account-related details."})
            context = query_faqs(query)

    prompt_template = """
You are a highly skilled financial assistant. Your role is to answer the user’s financial queries with accuracy, clarity, and professionalism based on the provided context and query. Always prioritize user-friendly, precise responses without introducing unnecessary elements.


Guidelines for Response:
	1.	Context Utilization:
        •	Use the context provided below to craft a coherent response.
        •	Combine related information from multiple sources in the context.
        •	Avoid repeating or duplicating information; summarize overlapping details concisely.
	2.	Recent or Latest Data:
        •	If the query includes terms like “recent” or “latest,” prioritize the most up-to-date data based on transaction_date or other date-related fields.
	3.	Clarity, Relevance, and Additional Information:
        •	Provide clear, human-readable sentences in the response.
        •	Do not include unnecessary formatting, placeholders, or suggestions.
        •	Avoid adding extra questions or answers unrelated to the query.
        •	Ensure added information is relevant and does not detract from the main response.
	4.	Accuracy and Limitations:
        •	Do not speculate, fabricate, or guess information.
        •	If the answer is beyond your scope or unclear, state explicitly that the information is unavailable.
    5. Intent
        - If context is not related to financial queries, find the intent and provide response accordingly.
    6. Query detection
        - If you getting some context with not related to query, find intent of the query and then provide response. 
        - do not provide response directly based on context, analyse query first.


Context:
{context}

Query:
{question}

Output:

Provide a concise, clear, and human-readable answer based on the above instructions. Avoid any additional formatting or unnecessary artifacts in the response.
"""
    prompt = prompt_template.format(context=context, question=query)
    print(prompt)

    # Generate response using Watsonx LLM
    try:
        response = granite_llm_ibm.generate(prompts=[prompt])
        bot_response = response.generations[0][0].text
        print(bot_response)
        print(jsonify({"query": query, "response": bot_response}))
        return jsonify({"query": query, "response": bot_response})
    except Exception as e:
        print(f"Error generating LLM response: {e}")
        return jsonify({"error": "Failed to generate a response. Please try again."}), 500


@app.route("/logout")
def logout():
    """Logout the user."""
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)