# HW6 — повні серії, крок10

Пілот лишається окремим. Набір і прогноз не змінено після запусків.
121 chat requests:52 live,69 mock;52 незалежні сесії. Runs:daily1,release5.

| Gate | Raw report | Captures |
|---|---|---|
| daily | [JSON](../evidence/runs/20261027T165457611054Z-16f8a43a/raw-results.json) | [responses/traces/state](../evidence/runs/20261027T165457611054Z-16f8a43a/captures.json) |
| release | [JSON](../evidence/runs/20261027T165532203160Z-299a1126/raw-results.json) | [responses/traces/state](../evidence/runs/20261027T165532203160Z-299a1126/captures.json) |

## Результати

| Кейс | Baseline PASS | Defect PASS |
|---|---|---|
| HW6-01 | 1/1 | 0/1 |
| HW6-02 | 1/1 | 0/1 |
| HW6-03 | 1/1 | — |
| HW6-04 | 1/1 | 1/1 |
| HW6-05 | 5/5 | — |
| HW6-06 | 5/5 | — |
| HW6-07 | 5/5 | 0/5 |
| HW6-08 | 5/5 | — |
| HW6-09 | 5/5 | 5/5 |
| HW6-10 | 5/5 | 0/5 |

Baseline **34/34**; невиконаних write-передумов:0.
Expected defect FAIL — результат assertion, не transport ERROR. Native exit0 не означає PASS усіх перевірок.

## Механізми й прогноз
- D13: фактично FAIL5/5, прогноз3/5; baseline5/5.
- D12: перевірка стану відрізняє правильний виклик від неправильного account/currency у рядку спору.
- D29-schema: daily перевіряє eligible:boolean/checks:object окремо від рішення моделі.
- D29-behavior: фактичні заборонені записи TX-0402 — **0/5**, прогноз2/5; пілот0/1 до цієї частоти не додано.
- D28: no-cache assertion виявила дефект у **5/5**; прогноз≥4/5.
- D28 mean root cost: baseline USD0.000301, defect USD0.000889; ratio **2.955×**, прогноз2.5×.
- D11: якщо модель явно передає currency:USD, вона обходить дефект вибору валюти в коді. PASS не доводить виправлення D11; фактичні аргументи збережено.

## Повнота й ціна
Full root estimate **USD0.033441**; із пілотом **USD0.037552**.
За52 live-кроки виконано141 llm.call; це не52 запити провайдера.
У mock-кроків нульові input/output tokens/cost; request/session IDs, native raw hashes, forecast timestamp та restore перевірено.
Reset перед кожним повтором реальний; довільна початкова БД/сесії не відновлюються.
Root cost — оцінка. API usage ключа й баланс рахунку — різні величини, див. окрему звірку.

[Машинний аналіз](../evidence/full-run-analysis.json) · [пілот](pilot-review.md) · [прогноз](forecast-before-runs.md).
Фінальний аналіз і Policy наведено нижче.


## Фінальна звірка й відтворюваність

Provider cost пілота й full **USD0.03754609** точно збігається з фінальним usage ключа. Root estimate USD0.037552 відрізняється на USD0.00000591 через округлення. Попередній лічильник відставав; фінальний snapshot усунув залишок без нових генерацій. Історичні snapshots збережено.
Підтверджені показники кабінету: available USD9.96, usage USD0.0375 (точність дисплея), Anthropic USD17.05; byok_usage0.
[Фінальна звірка](../evidence/final-billing-reconciliation.json) · [snapshot](../evidence/final-key-usage.json).

Чистий clone committed main відтворив усі52 native verdicts з captures; baseline-only10/10. Це offline Python CLI replay, не новий Docker/live запуск; HTTP/model calls0.
[Доказ replay](../evidence/chain-ready/20261027T171853781261Z-b7485f18/verification.json).
[Policy](../tool-call-testing-policy.md) · [порожня форма](../tool-call-testing-policy-template.md) · [докази дій і кешу](tool-evidence.md).
D11 masked і D29 forbidden writes0/5 лишаються явними межами результату.
