import logging
from google import genai
import os

# Initialize the Gemini API client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY")

job_names = [
    "batches/6xc4y7hw53i3bhhby240e9cm7vwyi8de9nq6",
    "batches/ven4nzq7jvpso5eufq4lu7t3zr8yka0gt8jq",
    "batches/gg1oaipzs447b9aqmmahl143dmkh848cntav",
    "batches/osmke14tmdqz0k5ygdbi1u4h2ji60m57het3",
    "batches/pmyrl6brwbtu7zaj4tyuv0ll8kbhsg9rhtrw",
    "batches/en61t8eusomai4fx6x6pyc9l2x0j20d3e1nk",
    "batches/jwrttr9uzc50whcccmt45kou7srbw14j3e1y",
    "batches/xs7mp5or51vgxvdagdcctk78kbvebsm4rahe",
]
# job_name = "batches/gaex64q1z34xx96ucj239i1kyn9bmsoz8d4b"
for job_name in job_names:
    batch_job = client.batches.cancel(name=job_name)
# Cancel a batch job
# client.batches.cancel(name=batch_job.name)