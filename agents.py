from langchain.agents import create_agent
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import web_search, scrap_url
import os
from dotenv import load_dotenv

load_dotenv()


#model setup
llm = ChatMistralAI(model="mistral-small-latest",temperature=0)

#1st agent

def build_search_agent():
    return create_agent(
        model= llm,
        tools= [web_search]
    )

#2nd agent

def build_reader_agent():
    return create_agent(

        model= llm,
        tools= [scrap_url]
    )


# wruter chain

write_prompt = ChatPromptTemplate([
    ("system", "You are an expert research writer. Write clear, structured and insighful reports"),
    ("human", """Wrute detailed research report on the topic below.
    
    Topic: {topic}
    
    Resaech Gathered:
    {research}
    
    Structure the report as:
    - Introduction
    - key Findings (minimum 3 well-explained points)
    - Conclusion
    - Sources (list all the URLs found in research)
    
    Be detailed, factual and professional."""),
])

writer_chain = write_prompt | llm | StrOutputParser()

#Critic_chain

critic_prompt = ChatPromptTemplate([
    ("system", "You are sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.
    
    Report: 
    {report}
    
    Respond in exact format:
    
    Score: X/10
    
    Strengths:
    - ...
    - ...
    
    Areas to Improve:
    - ...
    - ...
    
    One line verdict:
    ...""")
])

critic_chain = critic_prompt | llm | StrOutputParser()
