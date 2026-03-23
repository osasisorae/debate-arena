"""
Full 10-round debate end-to-end test.
Runs all rounds via API, captures SSE events, and gets judge verdict.
Verifies the backend completes without errors.
"""
import json
import os
import time
import requests
import sseclient

BASE_URL = os.getenv("DEBATE_BASE_URL", "http://localhost:8080")
DEFAULT_MODEL_CONFIG = {
    "left": os.getenv("DEBATE_LEFT_MODEL", "gpt-4o-mini"),
    "right": os.getenv("DEBATE_RIGHT_MODEL", "gpt-4.1-mini"),
    "judge": os.getenv("DEBATE_JUDGE_MODEL", "gpt-4.1-mini"),
}

def test_full_debate():
    print("=" * 60)
    print("AI DEBATE ARENA — FULL 10-ROUND E2E TEST")
    print("=" * 60)
    
    # 1. Start debate
    print("\n[1] Starting debate...")
    res = requests.post(f"{BASE_URL}/api/debate/start", json={
        "topic": "Is open-source AI safer than closed-source AI?",
        "model_config": DEFAULT_MODEL_CONFIG,
    })
    assert res.status_code == 200, f"Start failed: {res.status_code} {res.text}"
    data = res.json()
    session_id = data["session_id"]
    total_rounds = data["total_rounds"]
    round_types = data["round_types"]
    slot_models = data["slot_models"]
    left_name = slot_models["gpt"]["name"]
    right_name = slot_models["claude"]["name"]
    judge_name = slot_models["judge"]["name"]
    print(f"    Session: {session_id}, Rounds: {total_rounds}")
    print(f"    Left: {left_name} | Right: {right_name} | Judge: {judge_name}")
    
    # 2. Run all 10 rounds
    all_round_results = []
    total_tokens_all = 0
    
    for round_num in range(1, total_rounds + 1):
        rt = round_types.get(str(round_num), {})
        is_attack = rt.get("attack", False)
        label = rt.get("label", f"Round {round_num}")
        attack_type = rt.get("attack_type", "")
        
        marker = " ⚠️  ATTACK" if is_attack else ""
        print(f"\n[Round {round_num}/10] {label}{marker}")
        if is_attack:
            print(f"    Attack type: {attack_type}")
        
        start = time.time()
        
        # Stream the round via SSE
        response = requests.get(
            f"{BASE_URL}/api/debate/{session_id}/round/{round_num}",
            stream=True,
            headers={"Accept": "text/event-stream"}
        )
        assert response.status_code == 200, f"Round {round_num} failed: {response.status_code}"
        
        client = sseclient.SSEClient(response)
        
        round_data = {
            "round": round_num,
            "label": label,
            "is_attack": is_attack,
            "left_tokens": 0,
            "right_tokens": 0,
            "left_blocked": False,
            "right_blocked": False,
            "left_latency": 0,
            "right_latency": 0,
            "events": [],
        }

        left_token_count = 0
        right_token_count = 0
        
        for event in client.events():
            evt_type = event.event
            evt_data = json.loads(event.data) if event.data else {}
            
            if evt_type == "token":
                model = evt_data.get("model", "?")
                if model == "gpt":
                    left_token_count += 1
                else:
                    right_token_count += 1

            elif evt_type == "security_blocked":
                model = evt_data.get("model", "?")
                threat = evt_data.get("threat_level", "?")
                score = evt_data.get("threat_score", 0)
                blocked_name = left_name if model == "gpt" else right_name
                print(f"    🛡️  {blocked_name} BLOCKED — threat={threat}, score={score}")
                if model == "gpt":
                    round_data["left_blocked"] = True
                else:
                    round_data["right_blocked"] = True

            elif evt_type == "done":
                model = evt_data.get("model", "?")
                latency = evt_data.get("latency_ms", 0)
                tokens = evt_data.get("tokens", 0)
                blocked = evt_data.get("blocked", False)
                model_name = evt_data.get("model_name", left_name if model == "gpt" else right_name)
                if model == "gpt":
                    round_data["left_latency"] = latency
                    round_data["left_tokens"] = tokens
                else:
                    round_data["right_latency"] = latency
                    round_data["right_tokens"] = tokens
                status = "BLOCKED" if blocked else f"{tokens} tokens"
                print(f"    ✓ {model_name}: {latency/1000:.1f}s, {status}")
            
            elif evt_type == "round_end":
                break
        
        elapsed = time.time() - start
        total_tokens_all += round_data["left_tokens"] + round_data["right_tokens"]
        print(f"    Stream tokens: {left_name}={left_token_count}, {right_name}={right_token_count}")
        print(f"    Round time: {elapsed:.1f}s")
        
        all_round_results.append(round_data)
    
    # 3. Get judge verdict
    print(f"\n{'=' * 60}")
    print("[JUDGE] Getting verdict...")
    start = time.time()
    res = requests.post(f"{BASE_URL}/api/debate/{session_id}/judge")
    assert res.status_code == 200, f"Judge failed: {res.status_code} {res.text}"
    verdict = res.json()
    elapsed = time.time() - start
    print(f"    Verdict latency: {elapsed:.1f}s")
    print(f"    Tokens: {verdict.get('tokens', '?')}")
    print(f"\n    VERDICT:\n    {verdict['content'][:300]}...")
    
    # 4. Summary
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    
    attack_rounds = [r for r in all_round_results if r["is_attack"]]
    normal_rounds = [r for r in all_round_results if not r["is_attack"]]
    
    left_blocked = sum(1 for r in attack_rounds if r["left_blocked"])
    right_blocked = sum(1 for r in attack_rounds if r["right_blocked"])
    
    print(f"  Total rounds: {len(all_round_results)}")
    print(f"  Attack rounds: {len(attack_rounds)}")
    print(f"  Normal rounds: {len(normal_rounds)}")
    print(f"  {left_name} blocked in attack rounds: {left_blocked}/{len(attack_rounds)}")
    print(f"  {right_name} blocked in attack rounds: {right_blocked}/{len(attack_rounds)}")
    print(f"  Total tokens: {total_tokens_all}")
    print(f"\n  ✅ ALL 10 ROUNDS + JUDGE VERDICT COMPLETED SUCCESSFULLY")
    
    # 5. Check debate status
    res = requests.get(f"{BASE_URL}/api/debate/{session_id}/status")
    status = res.json()
    print(f"\n  Final status: {status['status']}")
    print(f"  Rounds completed: {status['rounds_completed']}")
    assert status["rounds_completed"] == 10, f"Expected 10 rounds, got {status['rounds_completed']}"
    assert status["status"] == "complete", f"Expected complete, got {status['status']}"
    
    print(f"\n{'=' * 60}")
    print("🎉 E2E TEST PASSED — No crashes, all rounds streamed successfully")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    test_full_debate()
