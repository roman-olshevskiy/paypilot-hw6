# ДЗ6 — локальне середовище

Власна копія L07, upstream ce025e3; source hashes у evidence/setup-source.json.
Вихідні S1–S5 збережено в sources/upstream/scenarios. Початковий набір10 сценаріїв і26 expectations змержено в main. Додатковий D11-сценарій ізольовано в supplemental/d11-no-currency; його matchers встановлюються лише на час окремого eval.

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


## Поточний стан після завершення

2026-10-27: пілот і повні серії завершено. Стенд повернуто до anthropic із базового .env; HTTPS_PROXY/SSL_CERT_FILE порожні, HW6 MockServer зупинено, volumes збережено. Реальний health/runtime тест пройшов без генерацій: [доказ](evidence/runtime-restored.json).
Для нового запуску спершу повторити налаштування вище. Environment-тести розраховані на активний OpenRouter/MockServer; у звичайному discovery вони пропускаються. Платні виклики потребують окремого явного запуску.
