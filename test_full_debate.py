"""
Full 10-round debate end-to-end test.
Runs all rounds via API, captures SSE events, and gets judge verdict.
Verifies the backend completes without errors.
"""
import json
import time
import requests
import sseclient

BASE_URL = "http://localhost:8080"

def test_full_debate():
    print("=" * 60)
    print("AI DEBATE ARENA — FULL 10-ROUND E2E TEST")
    print("=" * 60)
    
    # 1. Start debate
    print("\n[1] Starting debate...")
    res = requests.post(f"{BASE_URL}/api/debate/start", json={
        "topic": "Is open-source AI safer than closed-source AI?"
    })
    assert res.status_code == 200, f"Start failed: {res.status_code} {res.text}"
    data = res.json()
    session_id = data["session_id"]
    total_rounds = data["total_rounds"]
    round_types = data["round_types"]
    print(f"    Session: {session_id}, Rounds: {total_rounds}")
    
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
            "gpt_tokens": 0,
            "claude_tokens": 0,
            "gpt_blocked": False,
            "claude_blocked": False,
            "gpt_latency": 0,
            "claude_latency": 0,
            "events": [],
        }
        
        gpt_token_count = 0
        claude_token_count = 0
        
        for event in client.events():
            evt_type = event.event
            evt_data = json.loads(event.data) if event.data else {}
            
            if evt_type == "token":
                model = evt_data.get("model", "?")
                if model == "gpt":
                    gpt_token_count += 1
                else:
                    claude_token_count += 1
            
            elif evt_type == "security_blocked":
                model = evt_data.get("model", "?")
                threat = evt_data.get("threat_level", "?")
                score = evt_data.get("threat_score", 0)
                print(f"    🛡️  {model.upper()} BLOCKED — threat={threat}, score={score}")
                if model == "gpt":
                    round_data["gpt_blocked"] = True
                else:
                    round_data["claude_blocked"] = True
            
            elif evt_type == "done":
                model = evt_data.get("model", "?")
                latency = evt_data.get("latency_ms", 0)
                tokens = evt_data.get("tokens", 0)
                blocked = evt_data.get("blocked", False)
                if model == "gpt":
                    round_data["gpt_latency"] = latency
                    round_data["gpt_tokens"] = tokens
                else:
                    round_data["claude_latency"] = latency
                    round_data["claude_tokens"] = tokens
                status = "BLOCKED" if blocked else f"{tokens} tokens"
                print(f"    ✓ {model.upper()}: {latency/1000:.1f}s, {status}")
            
            elif evt_type == "round_end":
                break
        
        elapsed = time.time() - start
        total_tokens_all += round_data["gpt_tokens"] + round_data["claude_tokens"]
        print(f"    Stream tokens: GPT={gpt_token_count}, Claude={claude_token_count}")
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
    
    gpt_blocked = sum(1 for r in attack_rounds if r["gpt_blocked"])
    claude_blocked = sum(1 for r in attack_rounds if r["claude_blocked"])
    
    print(f"  Total rounds: {len(all_round_results)}")
    print(f"  Attack rounds: {len(attack_rounds)}")
    print(f"  Normal rounds: {len(normal_rounds)}")
    print(f"  GPT blocked in attack rounds: {gpt_blocked}/{len(attack_rounds)}")
    print(f"  Claude blocked in attack rounds: {claude_blocked}/{len(attack_rounds)}")
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
