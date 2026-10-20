# Home Exchange Listing: let Claude build your listing

A Claude Code skill that sets up your home on **HomeExchange** or **Kindred** for you. It reads a folder with your home's info and photos, asks only for what's missing, writes the title and description, uploads and orders the photos, and fills in the platform's setup in your own Chrome, where you're already logged in. On HomeExchange it also gets your GuestPoints value as high as the rules allow.

I built my own listings this way in October 2026, Kindred first and then HomeExchange, in one long session with Claude. This is that process cleaned up, plus the platform quirks that cost me the most time.

**Fastest way:** open Claude Code in your place's folder (photos inside it, logged in to the platform in Chrome) and paste:

> *Install the skill at https://github.com/royber34/life_os/tree/main/playbooks/home-exchange-listing and use it to put my place on HomeExchange.*

---

## What you need

- **Claude (Pro or Max) with Claude Code.** If you've only used the chat, open the **Code tab in the Claude desktop app**.
- **Claude in Chrome**, the browser extension, installed and connected, so Claude can work in your Chrome. If Claude says it can't reach Chrome, ask it to help you connect the extension (in a terminal session, typing `/chrome` does it).
- **An account on the platform**, and you're logged in to it in Chrome.
- **Ideally, a folder for your place** on your computer with whatever you have: notes, an old listing or ad, and photos. No folder is fine too; Claude will ask you questions instead.
- About an hour for the first listing. A second platform goes much faster.

---

## Quick start

To install, either paste the one-liner below into a terminal, or open Claude Code and ask: *"install the home-exchange-listing skill from github.com/royber34/life_os."*

**macOS / Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/royber34/life_os/main/playbooks/home-exchange-listing/install.sh | bash
```

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/royber34/life_os/main/playbooks/home-exchange-listing/install.ps1 | iex
```

Then start a new Claude Code session **in your place's folder** (in the desktop app, choose that folder when you start the session). Claude can only upload photos from the folder the session runs in, so put all the photos you want in there first. Then ask:

> *"Set up my home exchange listing on HomeExchange."*

---

## How it works

1. **Facts.** Claude reads your place's folder and photos and fills in a facts sheet (`home-facts.md`, saved in your folder). It asks only for what's missing: exact bed sizes, lift or stairs, Wi-Fi speed, availability, pets. Then it reads the facts back to you for a yes.
2. **Content.** It drafts the title, description, neighbourhood text, photo order and profile bio in the platform's own style, and shows them to you before using them.
3. **Platform.** It works through the setup step by step in your Chrome, ticking every amenity that's true, since amenities and beds drive the value. It checks each page actually saved.
4. **Value** (HomeExchange). It applies the recommended GuestPoints and offers the +30 GP per night the platform allows.
5. **Hand-over.** You get the listing link, its status and the short list of what's left for you.

---

## What stays with you

Claude never types passwords, ID numbers or card details, and it asks before anything that publishes or sends. You do these yourself:

- logging in;
- typing the Wi-Fi password;
- verification (ID plus a phone or electricity bill for the address, under 6 months old) and paying a membership (HomeExchange needs one to exchange);
- approving the listing going live and any message to support.

---

## Good to know

- **HomeExchange values your home by beds, location and amenities**, with each capped. Exact beds (including sofa beds) and every true amenity count most: amenities add value in steps of about 25 GP/night, so a few small true ticks can matter. Bedrooms, floor area and a view add nothing directly. Details and sources are in [`platform-notes.md`](skill/references/platform-notes.md).
- **Kindred pays one credit per night for every home**, so there the work goes into photos, copy and your profile.
- **Renting?** HomeExchange's terms require the owner's authorization, and your lease may forbid it. Without it, the account and its GuestPoints are at risk. The skill says this once and leaves the call to you.
- **Insurance:** HomeExchange requires home or renter's insurance.

<details>
<summary>What's in this folder</summary>

```
.
├── README.md                    ← This file
├── install.sh / install.ps1     ← One-line installers
└── skill/
    ├── SKILL.md                 ← The routine Claude follows
    ├── templates/home-facts.md  ← The facts sheet Claude fills in
    └── references/platform-notes.md  ← Points rules and browser quirks
```

</details>

---

## License

MIT (see the repository root).
