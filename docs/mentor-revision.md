# ДЗ6 — доопрацювання за фідбеком ментора

## Що змінено

1. **Policy §8:** create_dispute — оцінка додаткових **2–10 мс** (2 DB читання +1 локальний виклик disputes engine); send_statement — **1–5 мс** (1 DB join власника/email + звірка в коді). Прогріта локальна БД, без contention; це інженерний бюджет запропонованих бар’єрів, не benchmark. Новий email потребує окремого підтвердження людиною; цей час не входить у мс. Додаткових LLM-викликів немає.
2. **Policy §12:** рядки ризику за L03: що не покрито, наслідок, прийняти/відкласти й умова перегляду. Рішення стосуються навчального комплекту.
3. **D11:** окрема цільова пара без optional currency/amount. Старі10 сценаріїв, freeze і докази не змінено.

## Реальний D11 eval

Новий запит явно просить використати збережені defaults і передати тільки transaction_id/reason_code. Це перевірка конкретного шляху, не вимір спонтанної поведінки.
[Сценарій](../supplemental/d11-no-currency/scenario.json) · [freeze до запуску](../supplemental/d11-no-currency/before-run.json).

| Умова | Аргументи create_dispute | Постстан | Verdict |
|---|---|---|---|
| baseline | TX-0801, unauthorized_debit; без amount/currency | ACC-1009,120.0 USD,count1 | PASS |
| D11 | TX-0801, unauthorized_debit; без amount/currency | ACC-1009,120.0 EUR,count1 | FAIL state_row: expected USD |

Baseline request_id: eee9be787a134be8; D11 request_id: 8ed8fe52691f4aff.
По1 repeat,2 live +2 mock =4 chat,2 незалежні сесії. По3 live llm.call на умову. Передумова write пройшла в обох умовах; capture/restore без помилок. Повторів для бажаного результату не було.
[Native raw](../evidence/runs/20261027T210028506397Z-dd5eb0ec/raw-results.json) · [responses/traces/state](../evidence/runs/20261027T210028506397Z-dd5eb0ec/captures.json) · [аналіз аргументів і стану](../supplemental/d11-no-currency/analysis.json).

Початковий HW6-04 залишає історичний masked PASS. Додаток демонструє D11 при пропуску currency; не стверджує виправлення D11 чи частоту5/5. Початковий прогноз89ac39e не переписано; новий сценарій локально frozen до викликів, нового коміту перед ним не було.

## Вартість і відтворення

Додаток: provider **USD0.00104664**, root estimate USD0.001047. Usage ключа0.03754609→0.03859273: delta **USD0.00104664**, різниця0. Ранній after snapshot відставав; обидва snapshots збережено. Із початковими прогонами: provider **USD0.03859273**, root USD0.038599. Новий available balance кабінету не підтверджувався; прямий Anthropic не використовувався.
[Звірка](../supplemental/d11-no-currency/billing-reconciliation.json).

Запуск виконував scripts/run_d11_supplement.py через native CLI/Capture з явним HW6_ENABLE_PAID_RUNS=1. Доповнення ізольовано від стандартного scenarios/, тому історичні canonical результати34/34 не перейменовуються на нову серію. Script відмовляється повторно запускати вже зафіксовану спробу; для майбутньої повторної серії потрібен новий ID/каталог, старі докази не видаляти. Runtime після завершення повертається до базового режиму.

[Оновлена Policy](../tool-call-testing-policy.md) зберігає12 розділів і2 сторінки. Порожня форма вже містить потрібні колонки, її зміст не змінено.
