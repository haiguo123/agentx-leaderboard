"""
Test script to run ETF benchmark assessment.

Run with: 
  uv run pytest test_assessment.py -v -s
"""
import asyncio
import json
import pytest
import httpx
from uuid import uuid4

from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import Message, Part, Role, TextPart


@pytest.mark.asyncio
async def test_assessment(green_agent, purple_agent):
    """Run the full ETF benchmark assessment."""
    
    print()
    print("=" * 50)
    print("ETF Benchmark Assessment")
    print("=" * 50)
    print(f"Green Agent: {green_agent}")
    print(f"Purple Agent: {purple_agent}")
    print("=" * 50)
    print()
    
    # Create assessment request
    assessment_request = json.dumps({
        "participants": {"agent": purple_agent},
        "config": {}
    })
    
    results = None
    
    async with httpx.AsyncClient(timeout=300) as httpx_client:
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=green_agent)
        agent_card = await resolver.get_agent_card()
        config = ClientConfig(httpx_client=httpx_client, streaming=True)
        factory = ClientFactory(config)
        client = factory.create(agent_card)

        msg = Message(
            kind="message",
            role=Role.user,
            parts=[Part(TextPart(text=assessment_request))],
            message_id=uuid4().hex,
        )

        print("Running assessment...")
        print()
        
        async for event in client.send_message(msg):
            match event:
                case (task, update):
                    # Print status updates
                    if task.status and task.status.message:
                        for part in task.status.message.parts:
                            if hasattr(part.root, 'text'):
                                print(f"  {part.root.text}")
                    
                    # Get final results
                    if task.artifacts:
                        print()
                        print("=" * 50)
                        print("RESULTS")
                        print("=" * 50)
                        for artifact in task.artifacts:
                            for part in artifact.parts:
                                if hasattr(part.root, 'text'):
                                    print(f"\n{part.root.text}")
                                if hasattr(part.root, 'data'):
                                    results = part.root.data
                                    print(f"\nScore: {results.get('score')}/{results.get('total')}")
                                    print(f"Pass Rate: {results.get('pass_rate')}%")
                                    print()
                                    
                                    # Show first 5 results
                                    result_list = results.get('results', [])
                                    print("Sample Results (first 5):")
                                    print("-" * 40)
                                    for r in result_list[:5]:
                                        status = "✓" if r['correct'] else "✗"
                                        print(f"  {status} Q{r['question_id']}: {r['agent_answer']} (expected: {r['ground_truth']})")
                
                case Message() as msg:
                    for part in msg.parts:
                        if hasattr(part.root, 'text'):
                            print(part.root.text)
    
    # Assertions
    assert results is not None, "Assessment should return results"
    assert "score" in results, "Results should have score"
    assert "total" in results, "Results should have total"
    assert "pass_rate" in results, "Results should have pass_rate"
    assert results["total"] == 60, "Should have 60 questions"
    
    print(f"\n✓ Assessment completed: {results['score']}/{results['total']} ({results['pass_rate']}%)")