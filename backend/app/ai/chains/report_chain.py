"""
LangChain report generation chain.
Produces structured output from machine data.
"""
import json
from typing import Any, Dict
from langchain.schema import HumanMessage, SystemMessage
from app.ai.provider import get_llm
from app.ai.prompts.report_prompts import SYSTEM_PROMPT, ENGINEER_REPORT_PROMPT
from app.core.logging import logger


class AIReportResult:
    def __init__(self, data: dict):
        self.summary = data.get("summary", "")
        self.condition = data.get("condition", "UNKNOWN")
        self.likely_fault = data.get("likely_fault", "Unknown")
        self.confidence = float(data.get("confidence", 0))
        self.risk_level = data.get("risk_level", "LOW")
        self.evidence = data.get("evidence", [])
        self.recommended_actions = data.get("recommended_actions", [])
        self.maintenance_notes = data.get("maintenance_notes", "")

    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "condition": self.condition,
            "likely_fault": self.likely_fault,
            "confidence": self.confidence,
            "risk_level": self.risk_level,
            "evidence": self.evidence,
            "recommended_actions": self.recommended_actions,
            "maintenance_notes": self.maintenance_notes,
        }


def run_report_chain(
    machine_data: str,
    telemetry_stats: str,
    baseline_deviations: str,
    alerts: str,
    fft_data: str,
    maintenance_history: str,
    engineer_recommendations: str,
) -> AIReportResult:
    """Run the LangChain report chain and return structured result."""
    try:
        llm = get_llm()

        user_content = ENGINEER_REPORT_PROMPT.format(
            machine_data=machine_data,
            telemetry_stats=telemetry_stats,
            baseline_deviations=baseline_deviations,
            alerts=alerts,
            fft_data=fft_data,
            maintenance_history=maintenance_history,
            engineer_recommendations=engineer_recommendations,
        )

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ]

        response = llm.invoke(messages)
        raw = response.content.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        data = json.loads(raw)
        return AIReportResult(data)

    except Exception as e:
        logger.error(f"Report chain failed: {e}")
        # Return a safe fallback so the report pipeline doesn't break
        return AIReportResult({
            "summary": "AI analysis unavailable — please review telemetry manually.",
            "condition": "UNKNOWN",
            "likely_fault": "Unable to determine",
            "confidence": 0,
            "risk_level": "UNKNOWN",
            "evidence": [],
            "recommended_actions": ["Manual inspection recommended"],
            "maintenance_notes": f"AI chain error: {str(e)}",
        })
