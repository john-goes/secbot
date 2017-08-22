# secbot

This chat bot aims to provide better security procedures at Pagar.me.

## Features

### Chasing

The bot automatically joins any created channel.

### PCI Enforcement

Any time the bot detects a LUHN-valid card posted in public chats, it removes the message and scolds the user.

### Termination

The bot also facilitates the termination process by automating numerous actions.

| Service | Status  |
|---------|---------|
| GitHub  | Working |
| Trello  | Working |
| Logentries  | Missing Owner API Key |
| Email | Missing |
| VPN | Missing |
| Slack | Missing |
| Hubspot | Missing |
| Zendesk | Missing |
| Telegram | Missing |
| Looker | Missing|
| Whatsapp | Missing |
| Sentry | Missing |
| Newrelic | Missing |
| Jira/Confluence | Missing |
| Uber | Missing |
| 99Taxi | Missing |
| Cabify | Missing|

### Job logging

Every action is logged for tracing and debugging.

### Authorization

Sensitive actions require pre-authorization from the master user. All is done via chat and settings are persistent.
