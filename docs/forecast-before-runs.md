# HW6 — прогноз до пілота

Дата2026-10-27. Набір SHA256 **743b4ad2ce80f37d7f5d92d03be0f1c84910499f2c338c394244fab5f2eb2d3d**.
Це власні гіпотези до платних прогонів, а не результати викладача чи виконаних тестів.
OpenRouter/anthropic/claude-haiku-5.5 через MockServer, clean; дефекти лише у request settings.
Статус: локальна чернетка для review; окремого forecast commit ще немає.
Пілот не дозволено запускати, доки commit/proof не зафіксовані.

## Два числа

1. **2 із5** release-повторів HW6-09 із D29 створять заборонений спір.
   Гіпотеза: opaque ok:true послаблює відмову, але модель може відновити правило з історії/KB.
   Це низька впевненість, не оцінка ймовірності із власних даних.
2. **2.5×** — відношення середньої root cost live-кроку HW6-10 D28 до baseline у повній серії.
   Механізм: змінний початковий префікс ламає cache reuse; output/tool loop можуть змінити множник.
   Якщо baseline cost відсутня/нульова, множник не визначений; невідомий usage не прирівнювати до0.

Пілот по1 повтору на умову не підтверджує частоту із5 і не замінює повну серію.
Після пілота прогноз не переписувати під результат; фінально порівняти всі відхилення.

## По сценаріях

| Сценарій | Baseline — гіпотеза | Defect — гіпотеза |
|---|---|---|
| HW6-01 D12-state | PASS за досягнутого write | FAIL account/currency; правильний tool_called не рятує state |
| HW6-02 D29-contract | PASS, eligible:boolean/checks:object | FAIL контракту незалежно від реакції агента |
| HW6-03 repeat | PASS, один рядок | — |
| HW6-04 D11-state | PASS,USD120 | FAIL якщо model не передасть currency; явний USD може маскувати дефект |
| HW6-05 order | PASS5/5 за досягнутого create_dispute | — |
| HW6-06 parameters | PASS5/5, TX-0202 з історії | — |
| HW6-07 D13-tool | PASS5/5 | орієнтир FAIL3/5: вибір стохастичний |
| HW6-08 forbidden write | PASS5/5, create_dispute0 | — |
| HW6-09 D29-behavior | PASS5/5 | FAIL2/5; schema не входить у цей verdict |
| HW6-10 D28-cache | PASS5/5 від другого llm.call | no-cache assertion FAIL щонайменше4/5, один можливий PASS не стирати |

Передумова write/eligibility не виконана — окрема діагностична категорія, не доказ backend-захисту.
У partial/transport error немає права домальовувати verdicts або добирати повтори до бажаного результату.

## Незмінні умови й обсяг

10 сценаріїв,4 daily/1 та6 release/5;26 mock expectations.
Короткі англомовні історії, clock2026-09-15T10:00:00Z, summarize_after8.
Тексти/args очікування взяті з seed, engine, інструкцій клієнта й контрактів до trace.
52 live-кроки у повній серії; окремий пілот HW6-01/09/10 на baseline+defect —6.
121 chat requests full,18 pilot; разом139 chat,58 live,81 mock за поточним дизайном.
Це не58 provider calls: один live-крок може мати кілька llm.call.
USD-резерв оцінюється після пілота. Повідомлений рахунок10 USD, ліміт ключа20 USD — різні величини.

## Що має спростувати очікування

Зберегти baseline FAIL, D11 PASS із явною currency, відсутній write prerequisite,
D29 без жодного forbidden-write, baseline cache0 після другого виклику, D28 cache hit.
Текст відповіді не використовується жодною assertion.
При ERROR capture припиняє запуск без автоматичного повтору chat; витрати partial обліковуються окремо.

## Review перед оплатою

Окремий commit має містити цей forecast, frozen scenarios та mock/expectations.json.
Лише після окремої вказівки на commit записати справжній повний SHA в evidence/forecast-commit.json.
Не вигадувати commit і не обходити guard. На момент підготовки жодного paid model call.
