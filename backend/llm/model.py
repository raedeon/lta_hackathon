import os 
from dotenv import load_dotenv
from openai import AzureOpenAI

from backend.llm.filter_crowdsource import CrowdsourceFilter
from backend.llm.prioritizer import Prioritizer

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("API_VERSION"),
    azure_endpoint=os.getenv("AZURE_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_DEPLOYMENT")
)

FILTERER = CrowdsourceFilter(client)
PRIORITIZER = Prioritizer(client)