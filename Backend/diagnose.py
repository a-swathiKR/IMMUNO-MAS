from agents.agent_manager import AgentManager

# Focused test: what happens when PM-01 gets WARNED from HIGH anomaly + then we recover
mg = AgentManager(warn_threshold=2, recovery_cooldown_s=60.0)

# Simulate UNAUTHORIZED_TARGET on PM-01 (HIGH -> WARN)
sim = mg.simulate_anomaly(anomaly_type='UNAUTHORIZED_TARGET', agent_id='PM-01')
health = sim['agent_health'].get('PM-01', {})
print("After UNAUTHORIZED_TARGET on PM-01:")
print("  status:", health.get('status'))
print("  actions_taken:", [a['action'] for a in sim['actions_taken']])

# Try recovery
rec = mg.recover_agent('PM-01')
print("Recovery result:", rec)

final = mg.get_system_status()['agent_health'].get('PM-01', {}).get('status')
print("Final status:", final)

print()

# Now test TIMING_ANOMALY on PM-01 (MEDIUM -> should stay HEALTHY, recovery N/A)
mg2 = AgentManager(warn_threshold=2, recovery_cooldown_s=60.0)
sim2 = mg2.simulate_anomaly(anomaly_type='TIMING_ANOMALY', agent_id='PM-01')
health2 = sim2['agent_health'].get('PM-01', {})
print("After TIMING_ANOMALY on PM-01:")
print("  status:", health2.get('status'))   # Expected: HEALTHY

print()

# Test PRIVILEGE_ESCALATION on PM-01 (CRITICAL -> QUARANTINED)
mg3 = AgentManager(warn_threshold=2, recovery_cooldown_s=60.0)
sim3 = mg3.simulate_anomaly(anomaly_type='PRIVILEGE_ESCALATION', agent_id='PM-01')
health3 = sim3['agent_health'].get('PM-01', {})
print("After PRIVILEGE_ESCALATION on PM-01:")
print("  status:", health3.get('status'))   # Expected: QUARANTINED
rec3 = mg3.recover_agent('PM-01')
print("  Recovery:", rec3.get('action'), "->", mg3.get_system_status()['agent_health']['PM-01']['status'])
