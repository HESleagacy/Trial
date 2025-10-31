from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableSequence
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

# Initialize the LLM
llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama3-8b-8192",
)

# Load food-drug interaction data
with open("backend/data/drug_food_interactions.json", "r") as f:
    INTERACTIONS = {
        d["name"].lower(): d["food_interactions"] for d in json.load(f)
    }

def get_interactions(drug_name: str):
    """Return list of food interactions for a given drug."""
    return INTERACTIONS.get(drug_name.lower(), ["No known food interactions."])

# Define the prompt
prompt = PromptTemplate(
    input_variables=["drug", "dose", "frequency", "interactions"],
    template="""
You are MVp, a medication food coach.

Drug: {drug} {dose}, {frequency}
Avoid: {interactions}

Generate 3-5 bullet points:
1. Safe time gaps before/after avoided foods
2. Nutritionally similar SAFE replacements
3. Simple, clear language
4. End with: "Stay safe. MVp has your back."

Respond only with bullet points.
"""
)

# Define the modern chain pipeline
chain = RunnableSequence(prompt | llm | StrOutputParser())

def get_ai_plan(drug: str, dose: str, frequency: str) -> str:
    """Generate AI plan using Groq + LangChain."""
    interactions = get_interactions(drug)
    interactions_str = "\n".join(interactions)
    
    result = chain.invoke({
        "drug": drug,
        "dose": dose,
        "frequency": frequency,
        "interactions": interactions_str,
    })
    return result.strip()

