# Platform notes

What I learned setting up one listing on each platform in October 2026. Platforms change their pages often, so treat this as things to check, not as gospel.

## HomeExchange: how the GuestPoints value works

From the official help centre (checked 2026-10-20):

- The value per night comes from three things: **the number and size of the beds**, **the location** (distance to tourist sites), and **some amenities** (pool and garden are the named examples). Each criterion is capped. ([How is the GuestPoints value calculated?](https://help.homeexchange.com/hc/en-us/articles/360000631257))
- Since the December 2025 recalculation: location is set automatically from the address (big international cities and downtown flats count more); **the number of beds that counts is limited by the size of the home**; and eco extras (bikes, EV charging), comfort extras (lift, pool) and accepting pets or children count more. **The new recommendation was not applied automatically**: the owner has to update it from the listing. ([Why have we made changes?](https://help.homeexchange.com/hc/en-us/articles/31858066974237))
- You can set the value **up to 30 GP per night above the recommendation**. Going higher is forbidden by the terms. ([Can I change the GuestPoint value?](https://help.homeexchange.com/hc/en-us/articles/360000631277))

What one test showed (one listing, so a hint rather than a rule): A/C added 25 GP; ticking "High-speed connection" added nothing; an extra room without a bed added nothing, and floor area and view didn't change the number directly. Beds and the paid-for extras are where the points are.

Other HomeExchange facts:

- Exchanging needs a paid membership. New listings get welcome GuestPoints, and part of them lapses if the membership isn't paid within the deadline shown in the account.
- Below 80% profile completion the listing goes offline. A profile photo, languages and a bio move the meter a lot.

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
