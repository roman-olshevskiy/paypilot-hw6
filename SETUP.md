# ДЗ6 — локальне середовище

Власна копія L07, upstream ce025e3; source hashes у evidence/setup-source.json.
Вихідні S1–S5 збережено в sources/upstream/scenarios. Власний набір10 сценаріїв і26 expectations підготовлено; forecast commit ще очікує review.
Усі зміни локальні, без staging/commit/push. Main у цьому новому репозиторії поки без комітів.

## Запустити mock
З кореня paypilot-hw6: docker compose up -d llm-mock.
Після зміни сценаріїв: docker compose run --rm --entrypoint python eval build_mock.py,
потім docker compose restart llm-mock.

## Стенд через proxy
У PowerShell з D:/neoversity/paypilot-stand-shared:

~~~powershell
$env:L07_DIR='D:/neoversity/paypilot-hw6'
$env:L07_PROVIDER='openrouter'
$env:PROFILE='clean'
$env:DEFECTS=''
$env:LLM_MODEL='anthropic/claude-haiku-5.5'
docker compose -f docker-compose.yml -f ../paypilot-hw6/mock/stand.override.yml up -d --build --force-recreate stand
Remove-Item Env:L07_DIR,Env:L07_PROVIDER,Env:PROFILE,Env:DEFECTS,Env:LLM_MODEL
~~~

Секрет береться з .env стенду; ключ сюди не копіюється. API виклики моделі ще не виконувати.
Сертифікат mock/mockserver-ca.pem — публічний CA для локального proxy, не API-ключ.

## Повернути попередній режим
З D:/neoversity/paypilot-stand-shared: docker compose up -d --force-recreate stand.
Потім з paypilot-hw6: docker compose stop llm-mock.
Це відтворює provider/model з .env стенду, без proxy override; дані volumes не видаляються.


## Поточний результат
2026-10-27:6/6 реальних environment-тестів passed.
[Конфігурація без ключів](evidence/environment-runtime.json),
[мок-маршрут із trace](evidence/environment-mock-route.json),
[підсумок](evidence/environment-ready.json).
Платних model calls0; один mock chat виконав лише get_account, таблиці дій не змінені.
Live-маршрут до OpenRouter ще не тестувався; підготовка suite/forecast попереду.

Повторення перевірки:
~~~powershell
$env:HW6_RUN_ENVIRONMENT='1'
python -m unittest discover -s tests -p test_environment.py -v
Remove-Item Env:HW6_RUN_ENVIRONMENT
~~~
Мок-проба тимчасово блокує всі неперехоплені запити503 і прибирає guard у finally.
Звичайне unittest discovery пропускає environment-тести.
