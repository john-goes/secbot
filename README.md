# secbot

This chat bot aims to provide better security procedures at Pagar.me.

## Features

### Chasing

The bot automatically joins any created channel.

### PCI Enforcement

Any time the bot detects a LUHN-valid card posted in public chats, it removes the message and scolds the user.

### Integration

| Service | Status  | Functions |
|---------|---------|-----------|
| 99Taxi | Missing | - |
| AWS | Working | Instance lookup |
| Cabify | Missing| - |
| Email | Missing | - |
| GitHub  | Working | Termination, MFA Enforcement |
| Hubspot | Missing | - |
| Jira/Confluence | Missing |
| Logentries  | Working | Termination |
| Looker | Missing | - |
| Newrelic | Missing | - |
| Readme.io | Working | Change reporting |
| Sentry | Missing | - |
| Slack | Working | Termination, MFA Enforcement |
| Telegram | Missing | - |
| TinyLetter | Working | Subscriber Domain Validation, Subscriber Removal |
| Trello  | Working | Termination |
| Uber | Missing | - |
| VPN | Missing | - |
| Whatsapp | Working | - |
| Zendesk | Missing | - |

### Job logging

Every action is logged for tracing and debugging.

### Authorization

Sensitive actions require pre-authorization from the master user. All is done via chat and settings are persistent.
