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

from executor import Executor


def main():
    parser = argparse.ArgumentParser(description="Run the ETF Benchmark Green Agent.")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind the server")
    parser.add_argument("--port", type=int, default=9009, help="Port to bind the server")
    parser.add_argument("--card-url", type=str, help="URL to advertise in the agent card")
    args = parser.parse_args()

    # Define what this benchmark tests
    skill = AgentSkill(
        id="etf-data-analysis",
        name="ETF Data Analysis",
        description="Tests an agent's ability to accurately count and filter ETF data across multiple providers and attributes.",
        tags=["benchmark", "etf", "finance", "data-analysis", "counting"],
        examples=[
            "How many Fidelity ETFs have a non-null PriceEarningsRatio value?",
            "How many iShares ETFs have a DividendYield value greater than 0?",
            "How many Vanguard ETFs have DistributionFrequency value equal to 'Quarterly'?"
        ]
    )

    # Define the benchmark identity
    agent_card = AgentCard(
        name="ETF Benchmark",
        description="A benchmark that evaluates agents on 60 ETF data questions. Tests counting, filtering, and analysis across Fidelity, iShares, Schwab, and Vanguard providers. Attributes tested: PriceEarningsRatio, PriceBookRatio, ReturnOnEquity, DividendYield, and DistributionFrequency.",
        url=args.card_url or f"http://{args.host}:{args.port}/",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill]
    )

    # Create request handler with executor
    request_handler = DefaultRequestHandler(
        agent_executor=Executor(),
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