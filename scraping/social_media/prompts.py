import json
import os

TEMPLATE = "You are acting as both a data scientist and a financial domain expert.
I will give you one sample containing these fields:
Context


Question


Source


Category


Your task:
Read and understand the Context.


If the Context is more than 300 words, summarize it while preserving all information directly relevant to the investment topic.


Replace the Question with a custom yes/no question about investing that explicitly names the investment opportunity discussed in the Context.
   • If multiple opportunities are mentioned, choose the most suitable.
   • Interpret 'investment opportunity' broadly (stocks, bonds, ETFs, companies, commodities, currencies, cryptocurrencies, etc.).


Judge whether the answer should be 'Yes' or 'No' based only on the Context (ignore any outside knowledge).
   • Do not add explanations or reasoning in the Answer field.


Return the updated sample as a JSON object with this exact structure:


{
  'Context': '[shortened or original context]',
  'Question': '[custom yes/no question mentioning the investment opportunity]',
  'Answer': 'Yes' or 'No',
  'Source': '[unchanged]',
  'Category': '[unchanged]'
}

Do not use keyword-based rules or generic summarization—manually interpret and understand the content before deciding.

Sample to process:



"
# Step 1: Load your data from a JSON file
with open("social_media_samples.json", "r", encoding="utf-8") as f:
    data = json.load(f)