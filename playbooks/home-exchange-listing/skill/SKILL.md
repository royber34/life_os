---
name: home-exchange-listing
description: Sets up a home listing on HomeExchange or Kindred from a local folder of home info and photos, driving the user's logged-in Chrome. Gets the facts right, asks only for what's missing, maximises the HomeExchange GuestPoints value within the rules, and writes an attractive, honest listing. Use when the user wants to create, finish or improve a home exchange or home swap listing (HomeExchange, Kindred, or a similar platform).
---

# Home Exchange Listing

You build the user's listing on a home exchange platform, end to end, in their own Chrome where they are already logged in. The facts come from their place's folder and from their answers. Your goals, in order:

1. **Every fact is true.** A wrong bed size or a missing caveat costs reviews, and reviews are what get future exchanges accepted.
2. **The highest value the rules allow** (HomeExchange GuestPoints). On Kindred every night is worth one credit, so there the value lever is attractiveness.
3. **A listing people want to stay in.** Strong cover photo, warm first-person copy, clear practical details.

Keep it simple. Don't build anything the user didn't ask for.

## Rules

- **The user does the sensitive parts.** They log in, type any password (including the Wi-Fi password), verify their ID or phone, and pay any membership. You never enter passwords, ID numbers or card details.
- **Ask before anything that publishes or sends.** That covers publishing the listing, messaging support or concierge, and accepting terms or chat guidelines. HomeExchange can publish a listing as a side effect of saving a setting (see the platform notes), so tell the user before you make the last edits.
- **Don't infer facts.** "Take the stairs to the 3rd floor" does not mean there is no lift. If the folder doesn't say it, ask.
- **No overclaiming, but tick everything that's true.** Amenities raise the value, so go through every amenity page. Tick what exists. Leave out what doesn't.
- **Lease or landlord rules:** if the folder suggests the user rents, mention once that subletting or exchange permission may matter. Then do what the user decides.

Read `references/platform-notes.md` before you start. It holds the points rules and the browser quirks that cost the most time last time.

## Step 1: Collect the facts

1. **Find the place's folder** (the folder with the home's info and photos). Usually the session was opened in it. If not, ask the user to drag the folder into the chat or paste its location. Read every text file in it (notes, earlier listings, a lease if one is there) and look at the photos.
   - The photo upload only works with files inside the folder this session was opened in (or a folder added to it). If the photos are somewhere else, ask the user to copy them into the place's folder, or to restart the session from the folder that holds them.
2. **Fill in `templates/home-facts.md`** from what you found, and save it in the place's folder as `home-facts.md`. If one already exists from an earlier run, read it and update it instead.
3. **Ask only for the gaps.** Ask about the empty must-have lines first, a few at a time, in plain language. Then ask the nice-to-haves once, as a single list the user can skip. If there's no folder at all, ask everything in the template and save the answers as a new `home-facts.md` in a folder the user picks.
4. **Read the facts back** as a short summary and get a yes before you open the browser.

## Step 2: Prepare the content

Write these into `home-facts.md` under "Listing copy" so the user can reuse them on other platforms:

- **Title.** Lead with the strongest true selling point plus the area, for example "Sea-view flat in [neighbourhood], near [city]". Keep it short; Kindred caps titles at 50 characters.
- **Description.** First open the platform's own examples or tips ("See examples" on Kindred) and match their tone. A shape that works: what you love about the home, then the neighbourhood and what's walkable, then who it suits (families, remote work, couples), then "Good to know" with the honest caveats (stairs, a mattress on the floor, no parties). Write in first person, warm and practical, with no superlatives you can't back up.
- **Neighbourhood text** (HomeExchange asks for it separately): transport, shops, beach or parks, with walking times.
- **Photo order.** The cover is the single best room shot, usually a bright living room or the view. Then the bedrooms, bathrooms, kitchen, workspace and outdoor areas or the area. Leave out blurry or dark shots, people, and anything that shows the exact address or the building entrance. Tag each photo with its real room, and don't tag a public beach as a private garden or yard.
- **Profile.** Members choose the host as much as the home. Prepare a short, friendly bio plus the languages the user speaks. Ask how much personal detail they want shown; job details and full-name social links are optional. For Kindred, also prepare two adjectives for the home, at least three interest tags, and ask the user for a profile picture plus at least three personal photos.

Show the title, description and photo order to the user and get a yes.

## Step 3: Fill in the platform

Load the Claude in Chrome tools (`mcp__claude-in-chrome__*`) in one ToolSearch call, including `file_upload`, `find`, `read_page`, `computer`, `navigate` and `javascript_tool`, and open a new tab. If they aren't available, tell the user to install and connect the Claude in Chrome extension (in a terminal session, `/chrome`) and stop. Confirm the user is logged in to the right account. Then work through the platform's setup wizard step by step:

- **Rooms and beds:** exact bed sizes, plus sofa beds and extra beds. On HomeExchange, beds are a main driver of the GuestPoints value.
- **Amenities:** every page and sub-page. On HomeExchange, the comfort and eco extras count (lift, A/C, pool, garden, bikes, EV charging), and so does accepting children or pets if the user is willing.
- **Photos:** upload in the planned order with `file_upload` (absolute paths). The first photo becomes the cover. Then tag the rooms.
- **Availability:** ask for the dates and a minimum stay. A minimum of 7 nights is a sensible default for a full-time home; shorter is fine for a second home. One long window is simpler than many short ones, since the user can decline requests.
- **First guests:** if the platform offers "experienced members only", ask the user whether they want it.
- **Privacy:** on Kindred, set "Home preview settings" to "No preview" unless the user wants a public teaser.
- **Profile:** fill it in until the completion meter is high. HomeExchange takes a listing offline below 80% complete.

After each wizard part, check what saved. Re-read the page (screenshot, `read_page`, or JavaScript `innerText`) rather than trusting your clicks.

## Step 4: Maximise the value (HomeExchange)

1. Once the listing is complete, open **My home** and look at the recommended GuestPoints per night.
2. If the listing existed before December 2025, the new recommendation does not apply itself. Update it from the listing.
3. Offer the user the adjustment of up to **+30 GP per night** above the recommendation, which the platform allows. Never go above +30: HomeExchange's terms forbid it.
4. If the value looks low next to similar homes nearby, the user can ask support for a review. Offer to draft it; send only with their approval.

On Kindred, skip this step: credits are one per night for every home. Put the effort into photos, copy and the profile instead.

## Step 5: Hand over

Show the user:

- the listing URL, and whether it is published or offline (on HomeExchange, the "Home published" toggle in the editor is the one to trust);
- the GuestPoints value and what drove it (HomeExchange);
- what's left for them: ID or phone verification, the membership payment if they want to exchange (HomeExchange's welcome GuestPoints can lapse if they don't pay within the deadline shown), the Wi-Fi password, and anything you couldn't confirm.

Update `home-facts.md` with the final copy and the listing URL, so a second platform takes minutes.
