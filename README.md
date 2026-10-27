# ДЗ №6 — Tool Call Assertion Suite

**Пілот завершено; повна серія ще не запускалася.**
Власна копія L07 ce025e3; shared74f1995. Гілка codex/hw6-tool-call-suite, локальний forecast commit89ac39e, без push. Результати пілота незакомічені.
[Локальне середовище](SETUP.md) · [Оракули й ризик9 інструментів](docs/oracles-and-risk.md) ·
[Прогноз до запусків](docs/forecast-before-runs.md) · [Freeze](evidence/dataset-freeze.json).

## Набір

SHA256: **743b4ad2ce80f37d7f5d92d03be0f1c84910499f2c338c394244fab5f2eb2d3d**. Native run_step.py/build_mock.py збережено без змін.
Вихідні S1–S5 — у sources/upstream/scenarios; виконується лише власний scenarios/.
Умови завжди profile:clean,defects явно; clock і summarize_after передаються заголовком на кожен крок.

| ID | Вимірник | Походження | Gate/runs |
|---|---|---|---|
| [HW6-01](scenarios/hw6-01.json) | state | adapted S1 | daily/1 |
| [HW6-02](scenarios/hw6-02.json) | contract | split S3 | daily/1 |
| [HW6-03](scenarios/hw6-03.json) | state | adapted S4 | daily/1 |
| [HW6-04](scenarios/hw6-04.json) | state | own | daily/1 |
| [HW6-05](scenarios/hw6-05.json) | order | split S1 | release/5 |
| [HW6-06](scenarios/hw6-06.json) | parameters | adapted S2 | release/5 |
| [HW6-07](scenarios/hw6-07.json) | tool | own | release/5 |
| [HW6-08](scenarios/hw6-08.json) | tool | own | release/5 |
| [HW6-09](scenarios/hw6-09.json) | tool | split S3 | release/5 |
| [HW6-10](scenarios/hw6-10.json) | cost | adapted S5 | release/5 |


10 сценаріїв,3 власні; daily7 live-кроків, release45. Пілот6 окремо; вартість визначатиметься після нього.
tool_called у daily — передумова, не вибір моделі. Для create_dispute перевіряється також постстан.
Конкретні гроші/частоти в forecast — гіпотези, не вимірювання.

## Offline
~~~powershell
python -m unittest discover -s tests -v
~~~
16 offline passed;9 environment-тестів пропускаються без явного прапорця.
Fixture PASS/FAIL і синтетична cost0.001 в offline console — контрприклади, не живі результати/білінг.

## Preflight без платних запитів
~~~powershell
$env:HW6_RUN_ENVIRONMENT='1'
python -m unittest discover -s tests -p test_environment.py -v
Remove-Item Env:HW6_RUN_ENVIRONMENT
~~~
9 реальних перевірок: health/provider/runtime/CA,26 expectations, D13 descriptions, request-scope, публічний каталог моделі та одна known mock-проба.
Всі неперехоплені запити під час проби заблоковані503, upstream delta0.
Це не перевірка live-маршруту OpenRouter; платного completion немає.

## Пілот — завершено
Перед пілотом створено дозволений локальний forecast commit89ac39e; SHA підтверджено в evidence/forecast-commit.json.
Не встановлювати цей файл вигаданим значенням. Guard перевіряє commit/content до будь-якого HTTP/reset.

Майбутній приклад одного пілотного сценарію (дві умови, два live-кроки, оплата):
~~~powershell
$env:HW6_ENABLE_PAID_RUNS='1'
python scripts/hw6_capture.py --scenario HW6-01 --runs 1
Remove-Item Env:HW6_ENABLE_PAID_RUNS
~~~
Пілот складається з HW6-01,HW6-09,HW6-10 по1 repeat baseline+defect.
Крок9 завершено:6 live/12 mock, root USD0.004111, API usage USD0.00411112.
[Пілот і бюджет](docs/pilot-review.md). Наступний повний прогін ще не дозволено.

## Capture і майбутній CI
Кожен виклик adapter створює evidence/runs/<UTC-ID>, ніколи не перезаписує інший запуск.
Response записується до trace, потім state/proxy counts; attempts лишаються й за невідомого/неповного результату.
Немає chat autoretry; bounded PermissionError retry лише для файлового I/O.
Settings порівнюються й за потреби відновлюються незалежно у finally. Логи mock очищає native runner.
Seed reset реальний; довільна початкова БД/сесії не відновлюються.
Native CLI exit0 може містити quality FAIL — CI має читати verdicts; manifest зберігає quality_passed.
Офіційні raw results відокремлено від completed-conditions/partial captures. API-ключі не копіюються.

Для майбутніх повних серій --gate daily використовує1 repeat, --gate release використовує5.
Без --gate native runner типово виконує1, навіть якщо сценарій має runs5.
Chain-ready baseline/gate докази ще не зібрано: вони потребують живої моделі після пілота.
Policy у двох формах — кроки11–12 плану, не заявляється завершеною зараз.

[Підсумок підготовки до пілота](evidence/preparation-summary.json):16 offline +9 environment checks passed. Підготовка завершена, пілот описано вище.
