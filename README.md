# ДЗ №6 — Tool Call Assertion Suite

10 сценаріїв, 3 власні; повна копія L07 ce025e3, стенд shared74f1995. Початковий комплект змержено й надіслано в LMS; доопрацювання за фідбеком ментора підготовлено локально. Для здачі — [покажчик артефактів](SUBMISSION.md).

- [Policy](tool-call-testing-policy.md) і [порожня переносна форма](tool-call-testing-policy-template.md): 12 розділів, по 2 сторінки A4.
- [Результати](docs/full-run-summary.md), [докази дій/стану/кешу](docs/tool-evidence.md), [оракули й ризики 9 інструментів](docs/oracles-and-risk.md).
- [Прогноз до оплати](docs/forecast-before-runs.md), [пілот](docs/pilot-review.md), [фінальна звірка](evidence/final-billing-reconciliation.json).
- [Сценарії](scenarios), [freeze](evidence/dataset-freeze.json), [raw captures](evidence/runs), [налаштування](SETUP.md).

## Результат

Baseline 34/34 PASS; full 52 live +69 mock, 121 chat. З пілотом 58 live/139 chat.
D12-state і D29-contract виявлені; D13 і D28 — по 5/5. D11 замаскований явним USD; заборонених записів D29 —0/5 проти прогнозу 2/5. D28 mean root cost ratio 2.955× проти прогнозу 2.5×.
OpenRouter provider/API usage **USD 0.03754609**, root estimate USD 0.037552; баланс дисплея USD 9.96. Прямий Anthropic не використовувався.

## Запуск

Без мережі й оплати:
~~~powershell
python -m unittest discover -s tests -v
python scripts/verify_chain_ready.py
~~~
Другий запуск відтворює native verdicts з captures у чистій копії committed main; це replay, не нові live результати. Збережений replay підтвердив усі 52 verdicts.

Канонічні команди після налаштування OpenRouter/MockServer за SETUP.md **роблять платні виклики й reset seed-БД**:
~~~powershell
docker compose run --rm eval --gate daily
docker compose run --rm eval --condition baseline
docker compose run --rm eval --gate release
~~~
Daily:4 сценарії/runs 1; release:6/runs 5. Без gate native типово runs 1.
Для нової серії з повними response/trace/state captures:
~~~powershell
$env:HW6_ENABLE_PAID_RUNS='1'
python scripts/run_full.py
Remove-Item Env:HW6_ENABLE_PAID_RUNS
~~~
Native exit 0 не замінює verdicts. Expected defect FAIL відокремлюється від ERROR. Write має передумову досягнення дії та перевірку постстану; текст відповіді не є assertion. Capture не повторює chat автоматично; settings відновлюються, довільна початкова БД/сесії після seed reset не відновлюються.
Вихідні S1–S5 у sources/upstream/scenarios; run_step.py/build_mock.py не змінені. Матриця gate/runs — у scenarios та Policy.

## Доопрацювання за фідбеком ментора

[Виконані правки й додатковий D11 доказ](docs/mentor-revision.md): оцінки затримки в Policy §8, таблиця ризиків у §12; baseline PASS / D11 state FAIL без currency. Додатковий provider cost USD0.00104664; загалом USD0.03859273. Початкові результати34/34 та їхня вартість вище — історична серія. Правки локальні в codex/hw6-mentor-feedback; повторне надсилання ще не виконано.
