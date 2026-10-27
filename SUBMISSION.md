# ДЗ №6 — навігація здачі

Репозиторій: [paypilot-hw6](https://github.com/roman-olshevskiy/paypilot-hw6).
Статус: **готово до повторної здачі**. Усі три пункти фідбеку ментора виконано; локальний review завершено.

Посилання для LMS: [артефакти ДЗ 6 у main](https://github.com/roman-olshevskiy/paypilot-hw6/blob/main/SUBMISSION.md).

1. [Policy](tool-call-testing-policy.md).
2. [Порожня переносна форма](tool-call-testing-policy-template.md).
3. [10 сценаріїв](scenarios), [команди запуску](README.md#запуск).
4. [Звіт](docs/full-run-summary.md), [первинні докази](evidence/runs).
5. [Прогноз](docs/forecast-before-runs.md), [вартість](evidence/final-billing-reconciliation.json).

Baseline 34/34; usage USD 0.03754609. Межі: D11 masked, D29 forbidden writes 0/5; fresh-clone перевірка — replay, не новий live запуск.

## Доопрацювання за фідбеком ментора

[Виконані правки й додатковий D11 доказ](docs/mentor-revision.md): оцінки затримки в Policy §8, таблиця ризиків у §12; baseline PASS / D11 state FAIL без currency. Додатковий provider cost USD0.00104664; загалом USD0.03859273. Початкові результати34/34 та їхня вартість вище — історична серія. Доопрацювання перевірено; комплект готовий до повторної здачі.
