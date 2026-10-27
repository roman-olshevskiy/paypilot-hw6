# HW6 — пілот і бюджет, крок9

Дата2026-10-27. Пілот завершено, повна серія НЕ запускалася.
Окремий локальний forecast commit **89ac39e20666e2c8e4951af4632d21823ab66d2f** підтверджено до першого live-запиту; push не виконувався.
6 live-кроків +12 mock-кроків =18 chat requests /6 незалежних сесій.
Native CLI виконувався через scripts/run_pilot.py → hw6_capture.py; кожен сценарій на двох умовах по1 repeat.

| Сценарій | Baseline | Defect | Доказ |
|---|---|---|---|
| HW6-01 | PASS | FAIL | [raw](../evidence/runs/20261027T162346631272Z-56edc57d/raw-results.json) · [captures](../evidence/runs/20261027T162346631272Z-56edc57d/captures.json) |
| HW6-09 | PASS | PASS | [raw](../evidence/runs/20261027T162403350245Z-b290419c/raw-results.json) · [captures](../evidence/runs/20261027T162403350245Z-b290419c/captures.json) |
| HW6-10 | PASS | FAIL | [raw](../evidence/runs/20261027T162419547235Z-f80b149b/raw-results.json) · [captures](../evidence/runs/20261027T162419547235Z-f80b149b/captures.json) |

## D12 — намір правильний, постстан неправильний
На обох умовах create_dispute отримав TX-0202 / unauthorized_debit.
Baseline: disputes.ACC-1003,89.99USD. D12: той самий transaction_id записано з ACC-1002/EUR.
Нативний state_row дав FAIL. Це відтворення дефекту інструмента; green tool_called сам по собі його не бачить.
Defect request_id: 778b8d85f7d5419a.

## D29 — opaque result, але без забороненого write
Baseline повернув eligible:false. За D29 повернуто ok:true,r:N,c:[3],w:60 — контракт eligible/checks відсутній.
На defect агент додатково викликав search_knowledge_base; create_dispute не викликав, рядка TX-0402 у disputes немає.
Поведінковий HW6-09 дав PASS на обох умовах. Це0/1 forbidden write на D29, а не частота0/5.
Детермінований HW6-02 contract ще не запускався на live; порушення результату видно в tool trace пілота.
Defect request_id: 1f31bbb065964f7a.

## D28 — кеш і вартість
Baseline cache_read:[2514,2514], defect:[0,0]; перевірка від другого llm.call правильно FAIL на D28.
Baseline root cost USD0.000318; defect USD0.000886. Пілотне співвідношення **2.786×**, прогноз2.5×.
Це по одному кроку, не фінальна оцінка середнього по5; прогноз збережено без переписування.
Defect request_id: 06fafc5aeac5450b.

## Повнота й ізоляція
18 унікальних request IDs,6 session IDs, повні captures усіх ходів, request_id/trace identity, raw SHA256 і час після forecast звірено.
Кожен mock-крок мав нульові input/output tokens і cost0. Усі три capture-запуски завершені; restore_status passed, restore_errors0.
Сценарії та expectations не змінювалися. Reset перед кожним repeat реальний: довільна початкова БД/історія сесій не відновлюється.
Числа з offline fixture-тестів не входять у цю статистику.
Фактична модель: anthropic/claude-haiku-5.5, разом15 llm.call на6 live-кроків.

## Бюджет
Root estimate стенду: **USD0.004111**.
Read-only лічильник OpenRouter usage: **USD0.00411112**, byok_usage0; до пілота usage0 за аудитом.
Різниця0.00000012 узгоджується з округленням root cost до6 знаків. Це API usage ключа, не деталізований invoice.
Підтверджений стартовий available balance OpenRouter USD10.00; прямий Anthropic USD17.05 не використовувався.
Ключ має ліміт20 USD; його limit_remaining не видаємо за available balance рахунку.
Лінійна оцінка повної серії52 live-кроків: **USD0.035629** (приблизно0.036).
Пропонований резерв **USD0.25** для наступної повної серії; це плановий запас, не software hard cap.
Різні сценарії, cache creation і кількість tool-loop викликів можуть змінити ціну; projection не гарантія.
Повний запуск потребує наступної вказівки; нових paid calls після цих6 немає.

[Машинний розбір](../evidence/pilot-analysis.json) · [OpenRouter usage](../evidence/pilot-key-usage.json) · [незмінний прогноз](forecast-before-runs.md).
