# FitFindr

A secondhand shopping assistant that finds thrifted items, suggests outfits based on your wardrobe, and generates a shareable social media caption.

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):

GROQ_API_KEY=your_key_here
Run the app:
```bash
python app.py
```

Then open the URL shown in your terminal (usually http://localhost:7860).

## Tool Inventory

**Tool 1: search_listings**
Searches the mock listings dataset for items matching the user's description, filtered by optional size and price ceiling. Returns a list of matching listing dicts sorted by relevance, or an empty list if nothing matches.
- `description` (str): keywords describing what the user wants. Required.
- `size` (str or None): size to filter by. Optional.
- `max_price` (float or None): maximum price inclusive. Optional.

**Tool 2: suggest_outfit**
Given the top listing from search_listings and the user's wardrobe, suggests 1–2 complete outfits combining the new item with pieces the user already owns. Calls the Groq LLM to generate the suggestion. If the wardrobe is empty, returns general styling advice instead of crashing.
- `new_item` (dict): the top listing dict saved from search_listings.
- `wardrobe` (dict): the user's wardrobe with an 'items' key. May be empty.

**Tool 3: create_fit_card**
Takes the outfit suggestion from suggest_outfit and the new item dict, and generates a 2–4 sentence social media caption. Calls the Groq LLM at higher temperature so the caption sounds different each time. If the outfit string is empty, returns a descriptive error message instead of crashing.
- `outfit` (str): the outfit suggestion string from suggest_outfit.
- `new_item` (dict): the listing dict for the thrifted item.

## Planning Loop

The agent always starts with search_listings() using the user's inputs: description, size, and max_price. If search_listings() returns an empty list, the agent immediately stops and tells the user no matches were found, suggesting they try different keywords, a different size, or a higher budget — it does not proceed to the next step.

If results are returned, the agent saves the top listing and passes it into suggest_outfit() along with the user's wardrobe. If the wardrobe is empty, suggest_outfit() returns general styling advice instead of crashing, and the agent continues as normal.

Finally, create_fit_card() is called with the outfit suggestion from step 2 and the new item. It returns a social media caption about the outfit. Once this function returns, the agent is done — it does not loop back. One query triggers one full pass through all three tools.

## State Management

The agent tracks all state in a session dict for the duration of one interaction. The wardrobe comes from the user upfront — it is not produced by any tool. The session stores the top listing from search_listings() as `selected_item` and passes it directly into suggest_outfit(). The outfit suggestion string returned by suggest_outfit() is saved as `outfit_suggestion` and passed into create_fit_card(). The final caption is saved as `fit_card`. If anything goes wrong, `error` is set and the session is returned early. No state persists between separate queries.

## Error Handling

Each tool handles its failure mode gracefully without crashing the agent.

**search_listings — no results:** If no listings match the query, the tool returns an empty list and the agent stops immediately with a helpful message. Example from testing: `search_listings('designer ballgown', size='XXS', max_price=5)` returned `[]` because no designer dresses under $5 exist in the dataset. The agent told the user to try different keywords, a different size, or a higher budget — it did not proceed to suggest_outfit.

**suggest_outfit — empty wardrobe:** If the user provides no wardrobe, the tool falls back to general styling advice instead of crashing. Example from testing: passing `get_empty_wardrobe()` with a vintage graphic tee returned practical styling suggestions (pair with high-waisted jeans and sneakers, or a flowy skirt and sandals) rather than raising an exception or returning an empty string.

**create_fit_card — empty outfit string:** If the outfit string is empty or missing, the tool returns a descriptive error message instead of crashing. Example from testing: passing an empty string `''` returned "Could not create a fit card: the outfit suggestion was empty. Run suggest_outfit() to get an outfit before creating a caption."

## Spec Reflection

**One way the spec helped during implementation:**
planning.md made it possible to prompt Claude effectively for each tool. By passing in the relevant spec sections (tool inputs, return values, failure modes, and the complete interaction walkthrough) as context, Claude generated functions that matched what I actually needed rather than generic code. Without the spec, the prompts would have been too vague to produce useful output.

**One way implementation diverged from the spec:**
The spec described query parsing as a simple approach but didn't specify the exact method. When implementing run_agent(), Claude added a new helper function _parse_query() using regex to extract max_price (patterns like "under $30"), size (explicit "size M" or standalone tokens like "XS"), and strip filler phrases like "looking for" from the description. This wasn't in the original spec but it was a clean solution so I kept it and documented it in planning.md.

## AI Usage

**Instance 1 — suggest_outfit implementation:**
I gave Claude my Tool 2 spec and the Complete Interaction section from planning.md, and told it to use the existing `_get_groq_client()` helper already in tools.py and not re-implement the Groq client. It produced a function that pairs the new item with clothing the user already owns and returns general styling advice when no wardrobe is provided. One thing I changed: Claude defined `_OUTFIT_MODEL` as a module-level constant inside the function block, so I moved it to the top of tools.py where module-level constants belong.

**Instance 2 — run_agent() implementation:**
I gave Claude my Planning Loop, State Management, and Architecture sections from planning.md. I specifically told it to use a simple approach for query parsing since the queries are short and structured, and to not call suggest_outfit if search_results is empty. Claude added a new helper function `_parse_query()` using regex to extract price, size, and description from the query string,  this wasn't in my spec but was a clean solution. I verified it worked by running both the happy path and the no-results path from the CLI test block in agent.py.