"""
test_case_1_standard.py
Standard, clearly-specified business request — exercises the happy path:
planning -> tool calls -> section drafting -> document generation.

Run this AFTER starting the server:
    uvicorn app.main:app --reload
Then in a second terminal:
    python tests/test_case_1_standard.py
"""

import requests

BASE_URL = "http://127.0.0.1:8000"

STANDARD_REQUEST = (
    "Create a project proposal for building an internal chatbot that answers "
    "employee HR questions. Include budget, timeline, and expected ROI."
)


def run():
    print("Sending standard request...\n")
    response = requests.post(f"{BASE_URL}/agent", json={"request": STANDARD_REQUEST})
    print(f"Status code: {response.status_code}")

    data = response.json()
    print(f"\nDocument type: {data.get('document_type')}")
    print(f"Message: {data.get('message')}")

    print("\n--- Task List ---")
    for step in data.get("task_list", []):
        tool = f" (tool: {step['tool_used']})" if step.get("tool_used") else ""
        print(f"  [{step['status']}] Step {step['step_number']}: {step['title']}{tool}")

    print("\n--- Engineering Note ---")
    print(data.get("engineering_note"))

    print("\n--- Reflection ---")
    print(data.get("reflection_note"))

    print(f"\nDownload URL: {BASE_URL}{data.get('download_url')}")


if __name__ == "__main__":
    run()
