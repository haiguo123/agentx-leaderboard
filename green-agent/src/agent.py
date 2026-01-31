import json
import re
from pathlib import Path
from typing import Any
import logging

from pydantic import BaseModel, HttpUrl, ValidationError
from a2a.server.tasks import TaskUpdater
from a2a.types import Message, TaskState, Part, TextPart, DataPart
from a2a.utils import get_message_text, new_agent_text_message

from messenger import Messenger

logger = logging.getLogger(__name__)


class EvalRequest(BaseModel):
    """Request format sent by the AgentBeats platform to green agents."""
    participants: dict[str, HttpUrl]  # role -> agent URL
    config: dict[str, Any]


def extract_number(text: str):
    """
    Extract the first number (integer or float) from text.
    Supports:
    - integers (e.g., "22")
    - floats (e.g., "22.5", "-3.14")
    Returns:
        float if a number is found
        -1 if no number is found
    """
    match = re.search(r'-?\d+(?:\.\d+)?', str(text))
    return float(match.group()) if match else -1

class Agent:
    # Purple Agent role
    required_roles: list[str] = ["agent"]
    # No config needed
    required_config_keys: list[str] = []

    def __init__(self):
        self.messenger = Messenger()
        
        # Load questions
        qa_file = Path(__file__).parent / "qa_pairs.json"
        with open(qa_file) as f:
            self.qa_pairs = json.load(f)["qa_pairs"]

    def validate_request(self, request: EvalRequest) -> tuple[bool, str]:
        missing_roles = set(self.required_roles) - set(request.participants.keys())
        if missing_roles:
            return False, f"Missing roles: {missing_roles}"

        missing_config_keys = set(self.required_config_keys) - set(request.config.keys())
        if missing_config_keys:
            return False, f"Missing config keys: {missing_config_keys}"

        return True, "ok"

    async def run(self, message: Message, updater: TaskUpdater) -> None:
        """Run ETF benchmark evaluation.

        Args:
            message: The incoming assessment request
            updater: Report progress and results
        """
        input_text = get_message_text(message)

        # Validate request
        try:
            request: EvalRequest = EvalRequest.model_validate_json(input_text)
            ok, msg = self.validate_request(request)
            if not ok:
                await updater.reject(new_agent_text_message(msg))
                return
        except ValidationError as e:
            await updater.reject(new_agent_text_message(f"Invalid request: {e}"))
            return

        # Get Purple Agent URL
        agent_url = str(request.participants["agent"])
        
        # Track results
        results = []
        correct = 0
        total = len(self.qa_pairs)

        # Loop through questions
        for qa in self.qa_pairs:
            qid = qa["id"]
            question = qa["question"]
            ground_truth = qa["answer"]
            
            # Update status
            await updater.update_status(
                TaskState.working,
                new_agent_text_message(f"Question {qid}/{total}...")
            )

            # Send question to Purple Agent
            try:
                logger.info(f"Sending to Purple Agent at: {agent_url}")
                response = await self.messenger.talk_to_agent(question, agent_url)
                logger.info(f"Got response: {response}")
                agent_answer = extract_number(response)
            except Exception as e:
                logger.error(f"Error talking to agent: {e}", exc_info=True)
                agent_answer = -1

            # Check if correct with ±10% tolerance
            if ground_truth != 0:
                relative_error = abs(agent_answer - ground_truth) / abs(ground_truth)
                is_correct = relative_error <= 0.10
            else:
                # Ground truth is zero → must be exactly zero
                is_correct = agent_answer == 0

            if is_correct:
                correct += 1


            # Store result
            results.append({
                "question_id": qid,
                "question": question,
                "correct": is_correct,
                "agent_answer": agent_answer,
                "ground_truth": ground_truth
            })

        # Calculate pass rate
        pass_rate = (correct / total) * 100 if total > 0 else 0

        # Return final results as artifact
        await updater.add_artifact(
            parts=[
                Part(root=TextPart(text=f"Score: {correct}/{total} ({pass_rate:.1f}%)")),
                Part(root=DataPart(data={
                    "score": correct,
                    "total": total,
                    "pass_rate": round(pass_rate, 2),
                    "results": results
                }))
            ],
            name="Result",
        )