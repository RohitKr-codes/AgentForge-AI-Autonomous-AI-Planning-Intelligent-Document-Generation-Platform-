"""
test_case_2_complex.py
Ambiguous, under-specified request with conflicting/missing information —
exercises the agent's ability to make and STATE reasonable assumptions
rather than fail or ask a clarifying question.

Run this AFTER starting the server:
    uvicorn app.main:app --reload
Then in a second terminal:
    python tests/test_case_2_complex.py
"""

import requests

BASE_URL = "http://127.0.0.1:8000"

COMPLEX_REQUEST = (
    "We need something for leadership about the new thing we're building. "
    "Keep it business-y and make sure it sounds impressive, cover impact, "
    "some numbers would be nice, and whatever else matters — you decide, "
    "we haven't even fully scoped it yet."
)


def run():
    print("Sending complex / ambiguous request...\n")
    response = requests.post(f"{BASE_URL}/agent", json={"request": COMPLEX_REQUEST})
    print(f"Status code: {response.status_code}")

    data = response.json()
    print(f"\nDocument type chosen by agent: {data.get('document_type')}")
    print(f"Message: {data.get('message')}")

    print("\n--- Task List (agent's own plan) ---")
    for step in data.get("task_list", []):
        tool = f" (tool: {step['tool_used']})" if step.get("tool_used") else ""
        print(f"  [{step['status']}] Step {step['step_number']}: {step['title']}{tool}")

    print("\n--- Reflection ---")
    print(data.get("reflection_note"))

    print(f"\nDownload URL: {BASE_URL}{data.get('download_url')}")
    print(
        "\nNote: open the generated .docx and check the 'Assumptions Made by "
        "the Agent' section — this is where the agent states how it filled "
        "in the missing information."
    )


if __name__ == "__main__":
    run()
