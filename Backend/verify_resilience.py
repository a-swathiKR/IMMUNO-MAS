from agents.agent_manager import AgentManager

agents = ['PM-01', 'MA-01', 'RA-01']
anomaly_types = [
    ('PRIVILEGE_ESCALATION',  'CRITICAL'),
    ('UNKNOWN_ACTION',        'CRITICAL'),
    ('UNAUTHORIZED_TARGET',   'HIGH'),
    ('SEQUENCE_VIOLATION',    'HIGH'),
    ('RUN_STRUCTURE_ANOMALY', 'HIGH'),
    ('TIMING_ANOMALY',        'MEDIUM'),
]

results = []
overall = True

for agent_id in agents:
    for anomaly_type, expected_level in anomaly_types:
        mg = AgentManager(warn_threshold=2, recovery_cooldown_s=60.0)
        sim = mg.simulate_anomaly(anomaly_type=anomaly_type, agent_id=agent_id)
        health = sim['agent_health'].get(agent_id, {})
        status_after = health.get('status', 'N/A')

        if expected_level == 'CRITICAL':
            p1 = (status_after == 'QUARANTINED')
            expected_status = 'QUARANTINED'
        elif expected_level == 'HIGH':
            p1 = (status_after in ('WARNED', 'QUARANTINED'))
            expected_status = 'WARNED/QUARANTINED'
        else:
            p1 = (status_after == 'HEALTHY')
            expected_status = 'HEALTHY'

        rec_result = 'N/A'
        rec_ok = True
        if status_after in ('QUARANTINED', 'RECOVERING', 'WARNED'):
            rec = mg.recover_agent(agent_id)
            final = mg.get_system_status()['agent_health'].get(agent_id, {}).get('status')
            rec_ok = (final == 'HEALTHY')
            rec_result = f"{rec.get('action')} -> {final}"

        row_ok = p1 and rec_ok
        if not row_ok:
            overall = False

        results.append({
            'agent': agent_id,
            'anomaly': anomaly_type,
            'level': expected_level,
            'expected': expected_status,
            'got': status_after,
            'sim_ok': p1,
            'rec': rec_result,
            'rec_ok': rec_ok,
            'row_ok': row_ok,
        })

# Print table
print('=' * 95)
print(f"{'Agent':<8} {'Anomaly Type':<25} {'Level':<8} {'Expected':<22} {'Got':<14} {'Sim':>4} {'Recovery':<28} {'OK':>4}")
print('-' * 95)
for r in results:
    sim_tag = 'PASS' if r['sim_ok'] else 'FAIL'
    ok_tag  = 'PASS' if r['row_ok'] else 'FAIL'
    print(f"{r['agent']:<8} {r['anomaly']:<25} {r['level']:<8} {r['expected']:<22} {r['got']:<14} {sim_tag:>4} {r['rec']:<28} {ok_tag:>4}")

print('=' * 95)
fails = [r for r in results if not r['row_ok']]
if fails:
    print(f"FAILURES: {len(fails)}")
    for f in fails:
        print(f"  - {f['agent']} | {f['anomaly']} | got={f['got']} rec={f['rec']}")
else:
    print("ALL TESTS PASSED")
print(f"OVERALL: {'PASS' if overall else 'FAIL'}")
print('=' * 95)
