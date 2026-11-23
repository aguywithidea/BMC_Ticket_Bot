# Online BookMyShow alerts to Telegram

This uses GitHub Actions as a scheduled runner and Telegram for phone notifications. GitHub permits scheduled workflows as often as every five minutes, though runs can be delayed during busy periods. This workflow checks every 15 minutes. Standard runners are free for public repositories; private repositories use the monthly Actions allowance for the account plan. See [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions) and [schedule event behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).

## 1. Create a Telegram bot

1. In Telegram, message `@BotFather`, send `/newbot`, and follow its steps.
2. Copy the bot token it gives you. Treat it like a password.
3. Open your new bot's chat and press **Start** (or send `/start`).
4. To get your chat ID, open `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser after sending `/start`. Find `message.chat.id` in the response. Do not share the URL or token.

## 2. Create a GitHub repository

Upload these files preserving their paths:

```text
bms_ticket_watcher.py
.github/workflows/bookmyshow-alert.yml
```

For GitHub-hosted runners with no usage charge, use a public repository. The code is then public, but repository secrets remain private. A private repository uses the Actions allowance for your account plan.

## 3. Add the secrets

In the repository, open **Settings → Secrets and variables → Actions → New repository secret** and create:

- `TELEGRAM_BOT_TOKEN` — the token from BotFather
- `TELEGRAM_CHAT_ID` — your Telegram chat ID

## 4. Enable and start it

Open the **Actions** tab, enable workflows if prompted, then choose **BookMyShow ticket alert → Run workflow** to check it immediately. The scheduled workflow checks every 15 minutes. GitHub may delay scheduled runs, so this is not an instant alert service.

The workflow sends one Telegram message when it first detects booking controls and showtimes. It waits for the page to show no availability before it can alert again. It does not buy tickets. BookMyShow page changes may require updating the detection rules.
