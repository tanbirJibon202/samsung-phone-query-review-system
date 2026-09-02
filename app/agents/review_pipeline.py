"""Two-agent pipeline built with plain LangChain: a tool-calling Data
Specialist agent retrieves specs from Postgres, then a Review Generator
chain turns them into a structured product review.

Built once (see app.api.main's lifespan) and reused across requests.
"""

from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate

from app.agents.llm_config import get_groq_llm
from app.agents.tools import get_phone_specs_tool

DATA_SPECIALIST_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a meticulous Samsung phone data specialist. Your only job is to "
            "retrieve complete, accurate technical specifications for the requested "
            "phone using the tool provided, then present them clearly - display, "
            "camera, battery, processor, memory and any other available details.",
        ),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)

REVIEW_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a veteran tech-journalist review agent. Using only the supplied "
            "specifications, write a balanced Markdown review with exactly these "
            "sections: Summary, Pros, Cons, and Rating. The rating must be 1-5 stars "
            "with a short justification. Never invent missing facts.",
        ),
        ("human", "Review {phone_name}.\n\nSpecifications:\n{specs}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)


class ReviewPipeline:
    def __init__(self) -> None:
        llm = get_groq_llm()
        tools = [get_phone_specs_tool]
        agent = create_tool_calling_agent(llm, tools, DATA_SPECIALIST_PROMPT)
        self.data_specialist = AgentExecutor(agent=agent, tools=tools, verbose=False)

        review_agent = create_tool_calling_agent(llm, [], REVIEW_PROMPT)
        self.review_generator = AgentExecutor(agent=review_agent, tools=[], verbose=False)

    def run(self, phone_name: str) -> str:
        specialist_result = self.data_specialist.invoke(
            {"input": f"Retrieve the full technical specifications for the Samsung phone '{phone_name}'."}
        )
        specs_text = specialist_result["output"]
        review_result = self.review_generator.invoke({"phone_name": phone_name, "specs": specs_text})
        return review_result["output"]


def build_review_pipeline() -> ReviewPipeline:
    return ReviewPipeline()
