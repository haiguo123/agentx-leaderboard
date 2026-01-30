"""
ETF Purple Agent - Basic shell for ETF benchmark.

This is the agent being tested. It:
1. Receives questions from the Green Agent
2. Passes to LLM
3. Returns answer


"""
import argparse
import uvicorn
from dotenv import load_dotenv

load_dotenv()

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    Task,
    TaskState,
    InvalidRequestError,
    UnsupportedOperationError,
)
from a2a.utils import new_agent_text_message, new_task
from a2a.utils.errors import ServerError
from litellm import completion
from loguru import logger


def prepare_agent_card(url: str) -> AgentCard:
    """Create the agent card for the ETF purple agent."""
    skill = AgentSkill(
        id="etf_analysis",
        name="ETF Data Analysis",
        description="Answers questions about ETF data from Fidelity, iShares, Schwab, and Vanguard",
        tags=["etf", "finance", "data-analysis"],
        examples=[
            "How many Fidelity ETFs have a non-null PriceEarningsRatio value?",
            "How many iShares ETFs have a DividendYield value greater than 0?",
        ],
    )
    return AgentCard(
        name="ETF Agent",
        description="An agent that answers questions about ETF data across multiple providers.",
        url=url,
        version="1.0.0",
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(),
        skills=[skill],
    )


SYSTEM_PROMPT = """You are an ETF data analyst. You will receive questions about ETF data from providers like Fidelity, iShares, Schwab, and Vanguard.

Your task is to answer questions about ETF attributes such as:
- PriceEarningsRatio
- PriceBookRatio
- ReturnOnEquity
- DividendYield
- DistributionFrequency

IMPORTANT: Return ONLY a single number as your answer. No explanations, no text, just the number.

Example:
Question: "How many Fidelity ETFs have a non-null PriceEarningsRatio value?"
Answer: 18
"""


TERMINAL_STATES = {
    TaskState.completed,
    TaskState.canceled,
    TaskState.failed,
    TaskState.rejected
}


class ETFAgentExecutor(AgentExecutor):
    """Executor for the ETF purple agent."""

    def __init__(self, model: str):
        self.model = model
        self.ctx_id_to_messages: dict[str, list[dict]] = {}

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        msg = context.message
        if not msg:
            raise ServerError(error=InvalidRequestError(message="Missing message in request"))

        task = context.current_task
        if task and task.status.state in TERMINAL_STATES:
            raise ServerError(error=InvalidRequestError(message=f"Task {task.id} already processed"))

        if not task:
            task = new_task(msg)
            await event_queue.enqueue_event(task)

        context_id = task.context_id
        updater = TaskUpdater(event_queue, task.id, context_id)
        
        await updater.start_work()
        
        try:
            user_input = context.get_user_input()
            logger.info(f"Received question: {user_input[:200]}...")

            # Initialize or get conversation history
            if context_id not in self.ctx_id_to_messages:
                self.ctx_id_to_messages[context_id] = [
                    {"role": "system", "content": SYSTEM_PROMPT}
                ]

            messages = self.ctx_id_to_messages[context_id]
            messages.append({"role": "user", "content": user_input})

            # Call LLM
            try:
                response = completion(
                    messages=messages,
                    model=self.model,
                    temperature=0.0,
                )
                assistant_content = response.choices[0].message.content
                logger.info(f"LLM response: {assistant_content}")
            except Exception as e:
                logger.error(f"LLM error: {e}")
                assistant_content = "-1"

            # Add assistant response to history
            messages.append({"role": "assistant", "content": assistant_content})

            # Complete the task with the response
            await updater.complete(new_agent_text_message(assistant_content, context_id=context_id))
            
        except Exception as e:
            logger.error(f"Task failed: {e}")
            await updater.failed(new_agent_text_message(f"Error: {e}", context_id=context_id, task_id=task.id))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise ServerError(error=UnsupportedOperationError())


def main():
    parser = argparse.ArgumentParser(description="Run the ETF Purple Agent.")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind the server")
    parser.add_argument("--port", type=int, default=9019, help="Port to bind the server")
    parser.add_argument("--card-url", type=str, help="External URL for the agent card")
    parser.add_argument("--model", type=str, default="openai/gpt-4o-mini", help="LLM model to use")
    args = parser.parse_args()

    logger.info("Starting ETF Purple Agent...")
    card = prepare_agent_card(args.card_url or f"http://{args.host}:{args.port}/")

    request_handler = DefaultRequestHandler(
        agent_executor=ETFAgentExecutor(model=args.model),
        task_store=InMemoryTaskStore(),
    )

    app = A2AStarletteApplication(
        agent_card=card,
        http_handler=request_handler,
    )

    uvicorn.run(
        app.build(),
        host=args.host,
        port=args.port,
        timeout_keep_alive=300,
    )


if __name__ == "__main__":
    main()