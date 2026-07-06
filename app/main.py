"""
main.py
FastAPI entrypoint. Exposes:
  POST /agent            -> runs the full autonomous agent pipeline
  GET  /download/{file}  -> download a generated .docx
  GET  /                 -> serves the demo frontend
  GET  /health           -> simple healthcheck
"""

import os
import traceback
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.config import settings
from app.schemas import AgentRequest, AgentResponse, TaskStep
from app.agent.guardrails import validate_request, GuardrailViolation
from app.agent.planner import create_plan, plan_to_task_steps
from app.agent.executor import execute_plan
from app.agent.reflection import self_check
from app.document.doc_generator import build_document
from app.db.database import init_db, get_db
from app.db.models import RequestLog, ExecutionLog

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}


@app.post("/agent", response_model=AgentResponse)
def run_agent(payload: AgentRequest, db: Session = Depends(get_db)):
    user_request = payload.request

    # --- 1. Guardrails ---
    try:
        validate_request(user_request)
    except GuardrailViolation as e:
        raise HTTPException(status_code=400, detail=str(e))

    request_log = RequestLog(user_request=user_request, success="pending")
    db.add(request_log)
    db.commit()
    db.refresh(request_log)

    try:
        # --- 2. Autonomous planning ---
        plan = create_plan(user_request)
        task_steps = plan_to_task_steps(plan)

        # --- 3. Execution (tool orchestration + content generation) ---
        execution_results, sections = execute_plan(plan, user_request)

        # Persist execution steps
        for result in execution_results:
            db.add(ExecutionLog(
                request_id=request_log.id,
                step_number=result.step_number,
                title=result.title,
                tool_used=result.tool_used,
                output_snippet=result.output,
                status=result.status,
            ))

        # --- 4. Reflection (bonus self-check) ---
        reflection_note = self_check(user_request, sections)

        # --- 5. Document generation ---
        filename = build_document(
            document_title=plan.get("document_title", "Generated Document"),
            document_type=plan.get("document_type", "business_report"),
            assumptions=plan.get("assumptions", []),
            sections=sections,
            user_request=user_request,
        )

        request_log.success = "true"
        request_log.document_type = plan.get("document_type")
        db.commit()

        # Mark steps as done in the returned task list
        result_status_by_step = {r.step_number: r.status for r in execution_results}
        for t in task_steps:
            t.status = result_status_by_step.get(t.step_number, "done")

        return AgentResponse(
            success=True,
            message=f"Document generated successfully: {plan.get('document_title')}",
            document_type=plan.get("document_type"),
            task_list=task_steps,
            execution_log=execution_results,
            engineering_note=(
                "Tool Orchestration: the planner decides per-step which tool to call "
                "(e.g. get_mock_financial_data, get_mock_market_trends) and the executor "
                "dispatches real Python functions, feeding results back into the LLM's "
                "section drafting for grounded, non-hallucinated figures."
            ),
            document_filename=filename,
            download_url=f"/download/{filename}",
            reflection_note=reflection_note,
        )

    except Exception as e:  # noqa: BLE001
        request_log.success = "false"
        db.commit()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {e}")


@app.get("/download/{filename}")
def download_document(filename: str):
    filepath = os.path.join(settings.OUTPUT_DIR, filename)
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        filepath,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename,
    )


# --- Serve the frontend (index.html, style.css, script.js) ---
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.isdir(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
