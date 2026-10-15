# Connector gotchas

Each of these produced a wrong finding, or nearly did, during weekly runs between July and October 2026. Connectors change, so treat these as things to check rather than permanent facts.

## Email

- **The sent folder is the evidence.** Any claim that the user did not send, reply to or raise something must come from the sent folder and drafts. The inbox only shows what arrived. In one run, a plan claimed an email had not been sent when it had.
- **Count every sending channel.** People send from a second address, a document-sharing tool or a chat app. If a channel is not connected, mark claims about it "send status unverifiable" instead of "not sent".
- **It runs both ways.** A note or session saying "sending now" is not proof of a send. Look for it in the sent folder.
- **Gmail thread search cuts threads short.** The Gmail connector's thread search returned at most 5 messages per thread and dropped the newest ones. One thread showed 5 messages and actually had 11. Use search only to find threads, then open the full thread before claiming "no reply" or "last message". A thread showing exactly 5 messages is probably truncated.
- **Zero results still count.** The truncation happens inside threads, so a search that finds no thread at all is valid evidence of absence.
- **The sent list is a floor.** A 14-day sent search once left out a thread that a 7-day search returned. Do not treat one search as complete.

## Slack

- **Channel search returns no DMs.** Direct messages need a separate search (for example `is:dm`). DMs held the most important message of at least one week.
- **Long posts fail.** The Slack connector rejected messages over 5,000 characters. Keep posts under about 4,900.

## WhatsApp (via a community bridge)

- **Check sync lag as well as connection.** The bridge's connection check reported wrong results; its sync status was reliable. Compute how old the newest message is. The bridge once sat frozen for 13 days while still returning (old) data.

## Meeting transcripts

- **Summaries invent details.** A meeting summary named a person and a city that appear nowhere in the transcript. Never carry a name, place or number out of a summary without checking the transcript.
- **Numbers vanish from non-English audio.** German transcripts kept the sentence and dropped the figure ("... euro per month is enough").
- **Duplicates happen.** The same meeting can appear as two records. Deduplicate before counting.

## Running it unattended

- **Pre-approve read tools by name.** A single permission prompt stalled one scheduled run for 43 minutes. Allow the read tools you need one by one, and never use a wildcard that would also allow send tools.
- **Sources return at very different speeds.** The same source took a few minutes one week and over 3 hours another. Draft once most sources are back and fold in late ones. The past-sessions source is the one most worth waiting for: it knows what is already half-done.
- **A sleeping computer pauses the run.** A Sunday run froze when the computer slept and finished Monday morning. Keep the machine awake at run time, or check the clock and note the gap in the plan.
- **Re-read before writing.** A plan the user seeded mid-run was overwritten by the routine's save. Re-read the target file right before writing.
- **Self-checks are lenient.** A reviewer handed the draft but not the drafting context failed it on 6 of the 11 checks in my fuller version, mostly on claims with no evidence behind them. Checks run inside the drafting context had passed the same kind of error in earlier weeks.
