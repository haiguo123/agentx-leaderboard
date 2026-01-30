import argparse
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)

from executor import PurpleExecutor


def main():
    parser = argparse.ArgumentParser(description="Run the Purple Finance Agent.")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind the server")
    parser.add_argument("--port", type=int, default=9010, help="Port to bind the server")
    parser.add_argument("--card-url", type=str, help="URL to advertise in the agent card")
    args = parser.parse_args()

    # Define what the purple agent does
    skill = AgentSkill(
        id="etf-question-answering",
        name="ETF Question Answering",
        description="Answers ETF-related finance questions using structured ETF data and an LLM.",
        tags=["etf", "finance", "qa", "llm"],
        examples=[
            "What is the PriceEarningsRatio of VOO?",
            "What is the DividendYield of SCHD?",
            "What is the ReturnOnEquity for an iShares ETF?"
        ]
    )

    # Define agent identity
    agent_card = AgentCard(
        name="Purple Finance Agent",
        description="A finance agent that answers ETF data questions by querying structured ETF data and a Gemini LLM.",
        url=args.card_url or f"http://{args.host}:{args.port}/",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["json"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[skill]
    )

    # Create request handler with PurpleExecutor
    request_handler = DefaultRequestHandler(
        agent_executor=PurpleExecutor(),
        task_store=InMemoryTaskStore(),
    )

    # Create and run server
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    uvicorn.run(server.build(), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
