class PurpleExecutor:
    async def execute(self, task):
        """
        Handles a single A2A task.
        Expects a question and returns a numeric answer.
        """

        question = task.input.get("question")

        if not question:
            return {"error": "No question provided"}

        # TODO: replace this with your real Gemini call
        answer = ask_gemini_and_extract_number(question)

        return {
            "answer": answer
        }


def ask_gemini_and_extract_number(question: str):
    """
    Stub for now — replace with your real Gemini logic.
    """
    # Example placeholder
    return 0
