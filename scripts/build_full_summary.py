"""Write a full-series summary from measured artifacts, never from predicted scores."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    a=json.loads((ROOT/"evidence/full-run-analysis.json").read_text(encoding="utf-8"))
    lines=["# HW6 — повні серії, крок10","","Пілот лишається окремим. Набір і прогноз не змінено після запусків.",
      "121 chat requests:52 live,69 mock;52 незалежні сесії. Runs:daily1,release5.",
      "","| Gate | Raw report | Captures |","|---|---|---|"]
    for batch in a["selected_batches"]:
        p="../"+batch["folder"]
        lines.append(f"| {batch['gate']} | [JSON]({p}/raw-results.json) | [responses/traces/state]({p}/captures.json) |")
    lines+=["","## Результати","","| Кейс | Baseline PASS | Defect PASS |","|---|---|---|"]
    for n in range(1,11):
        cid=f"HW6-{n:02}"
        vals=[]
        for condition in ["baseline","defect"]:
            item=next((x for x in a["conditions"] if (x["scenario"],x["condition"])==(cid,condition)),None)
            vals.append(f"{item['passed']}/{item['runs']}" if item else "—")
        lines.append("| "+cid+" | "+" | ".join(vals)+" |")
    lines+=["",f"Baseline **{a['baseline_passed']}/{a['baseline_total']}**; невиконаних write-передумов:{a['failed_precondition_repeats']}.",
      "Expected defect FAIL — результат assertion, не transport ERROR. Native exit0 не означає PASS усіх перевірок.",
      "","## Механізми й прогноз",
      f"- D13: фактично FAIL{a['D13_detected_repeats']}/5, прогноз3/5; baseline5/5.",

      "- D12: перевірка стану відрізняє правильний виклик від неправильного account/currency у рядку спору.",
      "- D29-schema: daily перевіряє eligible:boolean/checks:object окремо від рішення моделі.",
      f"- D29-behavior: фактичні заборонені записи TX-0402 — **{a['D29_forbidden_writes']}/{a['D29_behavior_repeats']}**, прогноз2/5; пілот0/1 до цієї частоти не додано.",
      f"- D28: no-cache assertion виявила дефект у **{a['D28_detected_repeats']}/5**; прогноз≥4/5.",
      f"- D28 mean root cost: baseline USD{a['D28_mean_root_cost']['baseline']:.6f}, defect USD{a['D28_mean_root_cost']['defect']:.6f}; ratio **{a['D28_mean_cost_ratio']:.3f}×**, прогноз2.5×.",
      "- D11: якщо модель явно передає currency:USD, вона обходить дефект вибору валюти в коді. PASS не доводить виправлення D11; фактичні аргументи збережено.",
      "","## Повнота й ціна",
      f"Full root estimate **USD{a['full_root_cost_usd']:.6f}**; із пілотом **USD{a['all_root_cost_including_pilot_usd']:.6f}**.",
      f"За52 live-кроки виконано{a['full_model_calls']} llm.call; це не52 запити провайдера.",
      "У mock-кроків нульові input/output tokens/cost; request/session IDs, native raw hashes, forecast timestamp та restore перевірено.",
      "Reset перед кожним повтором реальний; довільна початкова БД/сесії не відновлюються.",
      "Root cost — оцінка. API usage ключа й баланс рахунку — різні величини, див. окрему звірку.",
      "","[Машинний аналіз](../evidence/full-run-analysis.json) · [пілот](pilot-review.md) · [прогноз](forecast-before-runs.md).",
      "Policy і фінальний аналіз ризиків — наступний крок11."]
    (ROOT/"docs/full-run-summary.md").write_bytes(("\n".join(lines)+"\n").encode())
if __name__=="__main__":main()
