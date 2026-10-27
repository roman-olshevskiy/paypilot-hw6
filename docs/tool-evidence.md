# ДЗ6 — докази дій і кешу

Додаток до [Policy](../tool-call-testing-policy.md). Джерело: незмінні captures двох full-серій; пілот не входить у частоти.

## Намір і постстан

### HW6-01 · baseline
request_id: 6c80975e9ba14374; session_id: 6ca3d58d2939.
~~~json
{
  "tools": [
    {
      "name": "tool.check_dispute_eligibility",
      "arguments": {
        "transaction_id": "TX-0202",
        "reason_code": "unauthorized_debit"
      },
      "result": {
        "eligible": true,
        "reason_code": "unauthorized_debit",
        "window_days": 56,
        "tx_date": "2026-09-08",
        "as_of": "2026-09-15",
        "deadline": "2026-11-03",
        "checks": {
          "reason_code": "pass",
          "tx_status": "pass",
          "window": "pass",
          "compliance_hold": "pass"
        }
      }
    },
    {
      "name": "tool.create_dispute",
      "arguments": {
        "transaction_id": "TX-0202",
        "reason_code": "unauthorized_debit"
      },
      "result": {
        "dispute_id": 1,
        "status": "open"
      }
    }
  ],
  "disputes": [
    {
      "id": 1,
      "transaction_id": "TX-0202",
      "account_id": "ACC-1003",
      "reason_code": "unauthorized_debit",
      "amount": 89.99,
      "currency": "USD",
      "status": "open",
      "created_at": "2026-09-15T10:00:00+00:00"
    }
  ]
}
~~~

### HW6-01 · defect
request_id: f0ff186973e746fe; session_id: a9f9a78a80a3.
~~~json
{
  "tools": [
    {
      "name": "tool.check_dispute_eligibility",
      "arguments": {
        "transaction_id": "TX-0202",
        "reason_code": "unauthorized_debit"
      },
      "result": {
        "eligible": true,
        "reason_code": "unauthorized_debit",
        "window_days": 56,
        "tx_date": "2026-09-08",
        "as_of": "2026-09-15",
        "deadline": "2026-11-03",
        "checks": {
          "reason_code": "pass",
          "tx_status": "pass",
          "window": "pass",
          "compliance_hold": "pass"
        }
      }
    },
    {
      "name": "tool.create_dispute",
      "arguments": {
        "transaction_id": "TX-0202",
        "reason_code": "unauthorized_debit"
      },
      "result": {
        "dispute_id": 1,
        "status": "open"
      }
    }
  ],
  "disputes": [
    {
      "id": 1,
      "transaction_id": "TX-0202",
      "account_id": "ACC-1002",
      "reason_code": "unauthorized_debit",
      "amount": 89.99,
      "currency": "EUR",
      "status": "open",
      "created_at": "2026-09-15T10:00:00+00:00"
    }
  ]
}
~~~

### HW6-03 · baseline
request_id: 9a841ebec85a427c; session_id: f246fe6c7908.
~~~json
{
  "tools": [],
  "disputes": [
    {
      "id": 1,
      "transaction_id": "TX-0401",
      "account_id": "ACC-1005",
      "reason_code": "duplicate_charge",
      "amount": 240.0,
      "currency": "EUR",
      "status": "open",
      "created_at": "2026-09-15T10:00:00+00:00"
    }
  ]
}
~~~

### HW6-04 · baseline
request_id: 50695590f6594c52; session_id: 772d9aebf71f.
~~~json
{
  "tools": [
    {
      "name": "tool.check_dispute_eligibility",
      "arguments": {
        "transaction_id": "TX-0801",
        "reason_code": "unauthorized_debit"
      },
      "result": {
        "eligible": true,
        "reason_code": "unauthorized_debit",
        "window_days": 56,
        "tx_date": "2026-09-09",
        "as_of": "2026-09-15",
        "deadline": "2026-11-04",
        "checks": {
          "reason_code": "pass",
          "tx_status": "pass",
          "window": "pass",
          "compliance_hold": "pass"
        }
      }
    },
    {
      "name": "tool.create_dispute",
      "arguments": {
        "transaction_id": "TX-0801",
        "reason_code": "unauthorized_debit",
        "amount": 120.0,
        "currency": "USD"
      },
      "result": {
        "dispute_id": 1,
        "status": "open"
      }
    }
  ],
  "disputes": [
    {
      "id": 1,
      "transaction_id": "TX-0801",
      "account_id": "ACC-1009",
      "reason_code": "unauthorized_debit",
      "amount": 120.0,
      "currency": "USD",
      "status": "open",
      "created_at": "2026-09-15T10:00:00+00:00"
    }
  ]
}
~~~

### HW6-04 · defect
request_id: 68572780b0744d4b; session_id: 0d1a4079cf6d.
~~~json
{
  "tools": [
    {
      "name": "tool.check_dispute_eligibility",
      "arguments": {
        "transaction_id": "TX-0801",
        "reason_code": "unauthorized_debit"
      },
      "result": {
        "eligible": true,
        "reason_code": "unauthorized_debit",
        "window_days": 56,
        "tx_date": "2026-09-09",
        "as_of": "2026-09-15",
        "deadline": "2026-11-04",
        "checks": {
          "reason_code": "pass",
          "tx_status": "pass",
          "window": "pass",
          "compliance_hold": "pass"
        }
      }
    },
    {
      "name": "tool.create_dispute",
      "arguments": {
        "transaction_id": "TX-0801",
        "reason_code": "unauthorized_debit",
        "amount": 120,
        "currency": "USD"
      },
      "result": {
        "dispute_id": 1,
        "status": "open"
      }
    }
  ],
  "disputes": [
    {
      "id": 1,
      "transaction_id": "TX-0801",
      "account_id": "ACC-1009",
      "reason_code": "unauthorized_debit",
      "amount": 120.0,
      "currency": "USD",
      "status": "open",
      "created_at": "2026-09-15T10:00:00+00:00"
    }
  ]
}
~~~

## D29 — контракт окремо від поведінки

| Кейс/умова/повтор | Request ID | Результат eligibility | Спори в стані |
|---|---|---|---|
| HW6-02/baseline/1 | fb7aa709258a49f6 | {"eligible": false, "reason_code": "duplicate_charge", "window_days": 60, "tx_date": "2026-07-14", "as_of": "2026-09-15", "deadline": "2026-09-12", "checks": {"reason_code": "pass", "tx_status": "pass", "window": "fail: window of 60 days expired on 2026-09-12", "compliance_hold": "pass"}} | 0 |
| HW6-02/defect/1 | 488ce69707d542a0 | {"ok": true, "r": "N", "c": [3], "w": 60} | 0 |
| HW6-09/baseline/1 | 69ea734f35924599 | {"eligible": false, "reason_code": "duplicate_charge", "window_days": 60, "tx_date": "2026-07-14", "as_of": "2026-09-15", "deadline": "2026-09-12", "checks": {"reason_code": "pass", "tx_status": "pass", "window": "fail: window of 60 days expired on 2026-09-12", "compliance_hold": "pass"}} | 0 |
| HW6-09/baseline/2 | 7f13a93f752a45c9 | {"eligible": false, "reason_code": "duplicate_charge", "window_days": 60, "tx_date": "2026-07-14", "as_of": "2026-09-15", "deadline": "2026-09-12", "checks": {"reason_code": "pass", "tx_status": "pass", "window": "fail: window of 60 days expired on 2026-09-12", "compliance_hold": "pass"}} | 0 |
| HW6-09/baseline/3 | f5c5d3df10ae4726 | {"eligible": false, "reason_code": "duplicate_charge", "window_days": 60, "tx_date": "2026-07-14", "as_of": "2026-09-15", "deadline": "2026-09-12", "checks": {"reason_code": "pass", "tx_status": "pass", "window": "fail: window of 60 days expired on 2026-09-12", "compliance_hold": "pass"}} | 0 |
| HW6-09/baseline/4 | 6b2fb7b0a0e8474c | {"eligible": false, "reason_code": "duplicate_charge", "window_days": 60, "tx_date": "2026-07-14", "as_of": "2026-09-15", "deadline": "2026-09-12", "checks": {"reason_code": "pass", "tx_status": "pass", "window": "fail: window of 60 days expired on 2026-09-12", "compliance_hold": "pass"}} | 0 |
| HW6-09/baseline/5 | 34e19b11cd4e4577 | {"eligible": false, "reason_code": "duplicate_charge", "window_days": 60, "tx_date": "2026-07-14", "as_of": "2026-09-15", "deadline": "2026-09-12", "checks": {"reason_code": "pass", "tx_status": "pass", "window": "fail: window of 60 days expired on 2026-09-12", "compliance_hold": "pass"}} | 0 |
| HW6-09/defect/1 | b37dde62afbf420e | {"ok": true, "r": "N", "c": [3], "w": 60} | 0 |
| HW6-09/defect/2 | 01593e7ced5b4548 | {"ok": true, "r": "N", "c": [3], "w": 60} | 0 |
| HW6-09/defect/3 | a62eb48a05b24cbe | {"ok": true, "r": "N", "c": [3], "w": 60} | 0 |
| HW6-09/defect/4 | 6cbb296d8e484a75 | {"ok": true, "r": "N", "c": [3], "w": 60} | 0 |
| HW6-09/defect/5 | 89cace5b47da40a2 | {"ok": true, "r": "N", "c": [3], "w": 60} | 0 |

## D13 — підмінена специфікація

Описи до/після D13: [snapshot](../evidence/tool-contracts.json).

| Умова/повтор | Request ID | Інструменти |
|---|---|---|
| baseline/1 | 934e41ffd99a4015 | tool.get_account, tool.check_limits |
| baseline/2 | fdab41b8f9ef4790 | tool.get_account, tool.check_limits |
| baseline/3 | ba2dedbda5454945 | tool.get_account, tool.check_limits |
| baseline/4 | d60df61cb17e4f5c | tool.get_account, tool.check_limits |
| baseline/5 | b145c524ef4840a2 | tool.get_account, tool.check_limits |
| defect/1 | 177c23af63ee4e2c | tool.get_account, tool.get_transactions, tool.search_knowledge_base, tool.quote_fx |
| defect/2 | 4ab5db87c0b94a69 | tool.get_account, tool.get_transactions, tool.search_knowledge_base, tool.quote_fx, tool.quote_fx |
| defect/3 | 0d68e0ed5a8244ec | tool.get_account, tool.get_transactions, tool.search_knowledge_base |
| defect/4 | 24a7ce7cd80245f5 | tool.get_account, tool.get_transactions, tool.search_knowledge_base |
| defect/5 | 9f37000bb09a4248 | tool.get_account, tool.get_transactions, tool.quote_fx, tool.search_knowledge_base |

## D28 — кожен виклик живого кроку

Нумерація call починається з1; from_call1 у JSON означає другий. Пропущене поле показувалося б як n/a, не0.

| Умова | Run | Call | Input | Output | Cache read | Cache write | Provider USD |
|---|---|---|---|---|---|---|---|
| baseline | 1 | 1 | 3226 | 56 | 2514 | 0 | 0.00012434 |
| baseline | 1 | 2 | 3408 | 130 | 2514 | 0 | 0.00017954 |
| baseline | 2 | 1 | 3226 | 56 | 2514 | 0 | 0.00012434 |
| baseline | 2 | 2 | 3408 | 130 | 2514 | 0 | 0.00017954 |
| baseline | 3 | 1 | 3226 | 56 | 2514 | 0 | 0.00012434 |
| baseline | 3 | 2 | 3408 | 125 | 2514 | 0 | 0.00017704 |
| baseline | 4 | 1 | 3226 | 56 | 2514 | 0 | 0.00012434 |
| baseline | 4 | 2 | 3408 | 106 | 2514 | 0 | 0.00016754 |
| baseline | 5 | 1 | 3226 | 56 | 2514 | 0 | 0.00012434 |
| baseline | 5 | 2 | 3408 | 129 | 2514 | 0 | 0.00017904 |
| defect | 1 | 1 | 3240 | 56 | 0 | 2528 | 0.0004152 |
| defect | 1 | 2 | 3424 | 147 | 0 | 2530 | 0.00047915 |
| defect | 2 | 1 | 3239 | 56 | 0 | 2527 | 0.000415075 |
| defect | 2 | 2 | 3423 | 131 | 0 | 2529 | 0.000471025 |
| defect | 3 | 1 | 3240 | 56 | 0 | 2528 | 0.0004152 |
| defect | 3 | 2 | 3421 | 127 | 0 | 2527 | 0.000468775 |
| defect | 4 | 1 | 3239 | 56 | 0 | 2527 | 0.000415075 |
| defect | 4 | 2 | 3422 | 130 | 0 | 2528 | 0.0004704 |
| defect | 5 | 1 | 3242 | 56 | 0 | 2530 | 0.00041545 |
| defect | 5 | 2 | 3420 | 152 | 0 | 2526 | 0.00048115 |

## Межі
Результат у span показує заявлений результат інструмента; остаточний наслідок звірено зі state snapshot.
Backend-дублювання відправки, SMTP, повний MCP і production state тут не тестувалися.
[Raw reports і captures](full-run-summary.md) · [машинні поля](../evidence/full-run-analysis.json).
