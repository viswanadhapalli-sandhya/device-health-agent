from core.agent import decide_action, execute_action

issues = [
    {"type": "cpu", "message": "High CPU usage"}
]

action, reason = decide_action(issues)
result = execute_action(action)

print("Decision:", action)
print("Reason:", reason)
print("Result:", result)