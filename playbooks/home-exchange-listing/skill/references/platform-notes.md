# Platform notes

What I learned setting up one listing on each platform in October 2026. Platforms change their pages often, so treat this as things to check, not as gospel.

## HomeExchange: how the GuestPoints value works

From the official help centre (checked 2026-10-20):

- The value per night comes from three things: **the number and size of the beds**, **the location**, and **some amenities** (pool and garden are the named examples). Each criterion is capped. ([How is the GuestPoints value calculated?](https://help.homeexchange.com/hc/en-us/articles/360000631257))
- Since the December 2025 recalculation: location is set automatically from the address (big international cities and downtown flats count more); **the number of beds that counts is limited by the size of the home**; and eco extras (bikes, EV charging), comfort extras (lift, pool) and accepting pets or children count more. **The new recommendation was not applied automatically**: the owner has to update it from the listing. ([Why have we made changes?](https://help.homeexchange.com/hc/en-us/articles/31858066974237))
- You can set the value **up to 30 GP per night above the recommendation**. Going higher is forbidden by the terms. **Editing the listing can undo the +30**, so set it last and re-check it. ([Can I change the GuestPoint value?](https://help.homeexchange.com/hc/en-us/articles/360000631277))

What controlled tests showed (one account, unpublished drafts, October 2026; HomeExchange can change this any time). Roughly: **value = location factor x (beds + about 25 per amenity step)**, then up to +30.

- **Beds:** about +11 per extra double (size beyond double doesn't matter) and +6 per single or sofa bed. Bedrooms, bathrooms, floor area, house vs flat and main vs second home added nothing.
- **Amenities count in steps, 0 to 4, each worth about 25 GP/night** (more in pricier locations). A/C, a pool or a garden alone reach the first step; several together still make one step. A broad "fully equipped" set reaches the second. A few small items on top (energy-efficient appliances, public transport, waste sorting) reached the third. Many single items add nothing alone (wifi, high-speed connection, lift, balcony, parking, kids' items).
- **Location** comes from the postcode and is coarse: a city centre and a suburb nearby scored the same; big international cities score higher. "Coastal" or "countryside" surroundings and a view added nothing.

Other HomeExchange facts:

- Exchanging needs a paid membership. Welcome GuestPoints: 50 for the account, 750 for the first completed listing (they lapse unless you subscribe within 3 months), 500 on first subscribing. ([How can I obtain GuestPoints?](https://help.homeexchange.com/hc/en-us/articles/360000631317))
- 80% completion is needed to see full listings, contact members and verify; aim for 100%. A profile photo, languages and a bio move the meter a lot.
- Search ranking favours hosts who are active, reply fast, update the calendar and complete exchanges. Reply to every request, even with a no. ([How are search results ordered?](https://help.homeexchange.com/hc/en-us/articles/360000730577))
- Minimum stay is a preference: guests can still ask for shorter stays.

## HomeExchange: rules that get accounts closed

- **Renting:** a tenant must have the owner's authorization to list (Terms, listings warranty). Without it the account and all its GuestPoints are at risk.
- **Fees:** the only fee allowed is a checkout cleaning fee (or a required tourist tax), reasonable and agreed in advance. ([Can hosts ask for extra fees?](https://help.homeexchange.com/hc/en-us/articles/360009466098))
- **Insurance:** every member must carry home or renter's insurance. HomeExchange's guarantees cover guest damage to contents; your own insurer comes first for structural damage. ([Guarantees vs home insurance](https://help.homeexchange.com/hc/en-us/articles/360000619417))
- **Host present:** a whole-home listing means the guest has the home. If the user stays home, they need a separate private-room listing with the room's own size and only the amenities the guest can use. ([Can I host guests while I'm staying at home?](https://help.homeexchange.com/hc/en-us/articles/360019707377))
- **Verification:** email and phone, then ID plus proof of address within 6 months (phone or electricity bill for the listed home, in the account holder's name). ([What is the verification process?](https://help.homeexchange.com/hc/en-us/articles/360000611557))
- **One account per household**, with all its homes on it. Check that a partner doesn't already have one.

## HomeExchange: browser quirks

- The wizard runs at `/homes/create/part/N/step/M`, in five parts: home, amenities (about ten sub-pages), title and descriptions, photos, availability. Size in m² is mandatory.
- `get_page_text` returns nothing on the wizard. Use screenshots, `read_page` or JavaScript `innerText`.
- **The listing published itself** when a setting (the minimum stay) was saved after the wizard, with no separate publish step. Warn the user before the last edits. The "Home published" toggle in the editor is the truth; pop-ups and menus disagreed with it.
- The availability calendar shows four months at a time. Paging or "See the following months" resets your start date, and the calendar scrolls on its own, so clicks can land on the wrong day. Reload, expand to all the months you need, then click the start and end dates without expanding again. Check the result.
- Escape closes a whole dialog without saving.
- The profile allows one photo.

## Kindred

- **Credits are flat:** you earn one credit per night you host and spend one per night you stay, at any home. Credits can't be bought, so there's no value to maximise. Attractiveness gets requests accepted. ([livekindred.com](https://livekindred.com/community/hosting))
- The setup wizard (`/profile/home/setup`) covers address, layout, beds, amenities, Wi-Fi speed (in bands), workspaces, stairs, pets, first guests, two adjectives, title (50 characters max) and description. Photos come after the wizard, at `/profile/home/photos`, and each photo gets a room tag. Kindred then reviews the photos.
- The address and city lock after the first step. Correcting them means a message to Concierge, which needs the user's approval because the chat makes you accept its guidelines first.
- **Home preview settings** default to "Limited preview" (some photos, the city and availability visible to logged-out visitors). Switch to "No preview" unless the user wants a public teaser.
- **The minimum stay resets to 2 nights** whenever an availability window is re-saved. Check it after every calendar edit.
- The Wi-Fi network name only saves together with a password, which the user types.
- Kindred may re-tag photos on its own (a beach photo became "Backyard", which implies a private garden). Check the tags after saving.
- The photo-tagging carousel can jam after scrolling. Reloading the page fixes it.
- Hosts need a member profile: an avatar, a short bio, at least three interest tags and at least three personal photos. ID verification is needed before taking a trip; the user does that themselves.
- Screenshots sometimes time out on Kindred. `read_page` still works.

## Both platforms

- **Photo upload:** find the hidden `input[type=file]` (with `find`, or JavaScript `document.querySelectorAll('input[type=file]')`), then use `file_upload` with absolute paths. Upload in batches of about six. It only takes files from the session's folder, so the photos need to be in the place's folder.
- If a click on a text field doesn't take the typing, click by coordinate rather than by reference, and check the field afterwards.
- Grids of amenity tiles shift as you click. Re-read the page and confirm each tick stuck.
