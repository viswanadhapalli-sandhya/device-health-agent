import os
from groq import Groq
from core.actions import clear_temp_files, kill_high_cpu_process
from dotenv import load_dotenv
from utils.helpers import append_json_log
load_dotenv()

VALID_ACTIONS = {"kill_process", "clear_temp", "do_nothing"}
DEFAULT_GROQ_MODELS = [
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
]


def get_groq_models():
    raw = os.getenv("GROQ_MODEL", "").strip()
    if raw:
        return [raw]

    raw_candidates = os.getenv("GROQ_MODEL_CANDIDATES", "").strip()
    if raw_candidates:
        models = [model.strip() for model in raw_candidates.split(",") if model.strip()]
        if models:
            return models

    return DEFAULT_GROQ_MODELS


def normalize_action(raw_action):
    if not raw_action:
        return None

    text = str(raw_action).strip().lower().replace("-", "_").replace(" ", "_")
    text = text.replace("`", "").replace(".", "")

    if text in VALID_ACTIONS:
        return text

    for action in VALID_ACTIONS:
        if action in text:
            return action

    return None


def enforce_action_policy(action, issues):
    if action not in VALID_ACTIONS:
        return "do_nothing", "Policy: Invalid action blocked"

    issue_types = {issue.get("type") for issue in issues}

    if action == "kill_process" and "cpu" not in issue_types:
        return "do_nothing", "Policy: kill_process allowed only for CPU anomaly"

    if action == "clear_temp" and "disk" not in issue_types:
        return "do_nothing", "Policy: clear_temp allowed only for Disk anomaly"

    if not issues and action != "do_nothing":
        return "do_nothing", "Policy: No anomalies, action blocked"

    return action, "Policy: action accepted"


def _infer_severity(issues, final_action):
    issue_types = {issue.get("type") for issue in issues}

    if not issues:
        return "low"

    if final_action == "kill_process" or "cpu" in issue_types or "disk" in issue_types:
        return "high"

    if "ram" in issue_types:
        return "medium"

    return "low"


def _infer_confidence(source, fallback_used, error):
    if source == "system":
        return 0.95

    if source == "ai" and not fallback_used:
        return 0.85

    if source == "ai_policy_override":
        return 0.55

    if error == "GROQ_API_KEY missing":
        return 0.70

    if error == "unparseable_ai_output":
        return 0.60

    if source == "fallback":
        return 0.65

    return 0.50


def _log_decision(source, raw_action, final_action, reason, issues, fallback_used=False, error=None):
    severity = _infer_severity(issues, final_action)
    confidence = _infer_confidence(source, fallback_used, error)

    append_json_log(
        "logs/agent_decisions.jsonl",
        {
            "source": source,
            "raw_action": raw_action,
            "final_action": final_action,
            "reason": reason,
            "fallback_used": fallback_used,
            "error": error,
            "severity": severity,
            "confidence": confidence,
            "issue_count": len(issues),
        },
    )

def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return None  # don't crash

    return Groq(api_key=api_key)


def decide_action_ai(stats, issues):
    client = get_groq_client()

    # 🔴 If no API key → fallback immediately
    if client is None:
        fallback_action, fallback_reason = decide_action(issues)
        reason = f"{fallback_reason} | cause=missing_api_key"
        _log_decision(
            source="fallback",
            raw_action=None,
            final_action=fallback_action,
            reason=reason,
            issues=issues,
            fallback_used=True,
            error="GROQ_API_KEY missing",
        )
        return fallback_action, reason

    if not issues:
        _log_decision(
            source="system",
            raw_action="do_nothing",
            final_action="do_nothing",
            reason="System is healthy",
            issues=issues,
            fallback_used=False,
            error=None,
        )
        return "do_nothing", "System is healthy"

    prompt = f"""
    You are a device health agent.

    System Stats:
    CPU: {stats['cpu']}%
    RAM: {stats['ram']}%
    Disk: {stats['disk']}%
    Battery: {stats['battery']}

    Issues:
    {issues}

    Choose ONLY ONE action from:
    - kill_process
    - clear_temp
    - do_nothing

    Respond ONLY with action name.
    """

    try:
        response = None
        used_model = None
        last_error = None

        for model_name in get_groq_models():
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    max_tokens=8,
                )
                used_model = model_name
                break
            except Exception as model_error:
                last_error = model_error
                continue

        if response is None:
            raise last_error if last_error else RuntimeError("No Groq model available")

        raw_action = response.choices[0].message.content.strip().lower()
        normalized_action = normalize_action(raw_action)

        if normalized_action is None:
            fallback_action, fallback_reason = decide_action(issues)
            reason = f"{fallback_reason} | cause=unparseable_ai_output:{raw_action}"
            _log_decision(
                source="fallback",
                raw_action=raw_action,
                final_action=fallback_action,
                reason=reason,
                issues=issues,
                fallback_used=True,
                error="unparseable_ai_output",
            )
            return fallback_action, reason

        final_action, policy_reason = enforce_action_policy(normalized_action, issues)

        if final_action != normalized_action:
            reason = f"Policy override. ai={normalized_action}; final={final_action}. {policy_reason}"
            _log_decision(
                source="ai_policy_override",
                raw_action=raw_action,
                final_action=final_action,
                reason=reason,
                issues=issues,
                fallback_used=True,
                error="policy_override",
            )
            return final_action, reason

        reason = f"Decided by AI ({policy_reason}) | model={used_model}"
        _log_decision(
            source="ai",
            raw_action=raw_action,
            final_action=final_action,
            reason=reason,
            issues=issues,
            fallback_used=False,
            error=None,
        )
        return final_action, reason

    except Exception as e:
        fallback_action, fallback_reason = decide_action(issues)
        reason = f"{fallback_reason} | cause=ai_error"
        _log_decision(
            source="fallback",
            raw_action=None,
            final_action=fallback_action,
            reason=reason,
            issues=issues,
            fallback_used=True,
            error=str(e),
        )
        return fallback_action, reason


# ✅ Fallback rule-based system
def decide_action(issues):
    if not issues:
        return "do_nothing", "System is healthy"

    for issue in issues:
        if issue["type"] == "cpu":
            return "kill_process", "Fallback: High CPU"

        elif issue["type"] == "disk":
            return "clear_temp", "Fallback: Low disk"

    return "do_nothing", "Fallback used"


def execute_action(action):
    if action == "kill_process":
        return kill_high_cpu_process()

    elif action == "clear_temp":
        return clear_temp_files()

    return "No action executed"