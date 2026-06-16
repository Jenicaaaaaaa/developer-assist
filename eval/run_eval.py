import json
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from devassist.agent import ask

def score_answer(answer, expected_keywords):
    answer_lower = answer.lower()
    matched = [kw for kw in expected_keywords if kw.lower() in answer_lower]
    score = len(matched) / len(expected_keywords)
    return {
        "matched": matched,
        "missed": [kw for kw in expected_keywords if kw.lower() not in answer_lower],
        "score": score
    }

def run_eval(questions_path):
    with open(questions_path, "r") as f:
        questions = json.load(f)

    results = []
    total_score = 0

    print("\n" + "="*60)
    print("  DEVASSIST EVAL HARNESS")
    print("="*60 + "\n")

    for i, item in enumerate(questions):
        question = item["question"]
        expected = item["expected_keywords"]
        print(f"[{i+1}/{len(questions)}] {question}")

        try:
            answer = ask(question)
            scored = score_answer(answer, expected)
            total_score += scored["score"]
            status = "PASS" if scored["score"] >= 0.5 else "FAIL"
            print(f"  {status} - {scored['score']*100:.0f}% keywords matched")
            if scored["missed"]:
                print(f"  Missing: {scored['missed']}")
            results.append({
                "question": question,
                "score": scored["score"],
                "matched": scored["matched"],
                "missed": scored["missed"],
                "status": status
            })
        except Exception as e:
            print(f"  ERROR - {e}")
            results.append({
                "question": question,
                "score": 0,
                "error": str(e),
                "status": "ERROR"
            })
        print()

    avg_score = total_score / len(questions)
    passed = sum(1 for r in results if r["status"] == "PASS")

    print("="*60)
    print("  RESULTS")
    print("="*60)
    print(f"  Questions:  {len(questions)}")
    print(f"  Passed:     {passed}/{len(questions)}")
    print(f"  Accuracy:   {avg_score*100:.1f}%")
    print("="*60 + "\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"eval/results_{timestamp}.json"
    with open(output_path, "w") as f:
        json.dump({
            "timestamp": timestamp,
            "accuracy": avg_score,
            "passed": passed,
            "total": len(questions),
            "results": results
        }, f, indent=2)

    print(f"Results saved to {output_path}\n")
    return avg_score

if __name__ == "__main__":
    run_eval("eval/questions.json")