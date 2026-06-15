# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Searches the mock listings dataset for items matching the user's description, filtered by optional size and price ceiling. Returns results sorted by relevance with the best match first.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): Keywords describing what the user is looking for (e.g. "vintage graphic tee"). Required.
- `size` (str): Size string to filter by. Optional — if None, size filtering is skipped.
- `max_price` (float): Maximum price inclusive. Optional — if None, price filtering is skipped.

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
A list of matching listing dicts sorted by relevance. Each dict contains: id, title, description, category, style_tags (list), size, condition, price (float), colors (list), brand, platform. Returns an empty list if nothing matches.
**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
If the list is empty, FitFindr tells the user no listings matched their search and suggests they try different keywords, a different size, or a higher budget. The agent stops and does not call suggest_outfit with empty input.
---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Given a thrifted item the user is considering and their existing wardrobe, suggests 1–2 complete outfits that combine the new item with pieces the user already owns. Calls the Groq LLM to generate the suggestion.
**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): A listing dict for the item the user is considering buying. Contains fields like title, category, style_tags, colors, condition, price, platform.
- `wardrobe` (dict): A wardrobe dict with an 'items' key containing a list of wardrobe item dicts. May be empty.

**What it returns:**
<!-- Describe the return value -->
A non-empty string with outfit suggestions. If the wardrobe has items, the suggestion names specific pieces from the wardrobe. If the wardrobe is empty, returns general styling advice for the new item instead.
**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->
If the wardrobe is empty, the tool does not raise an exception.It falls back to general styling advice for the item. The agent continues to create_fit_card with whatever suggestion was returned.
---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Generates a short, shareable social media caption (2–4 sentences) for the thrifted outfit. Combines the outfit suggestion and the new item's details into something that reads like a real Instagram or TikTok OOTD post -casual, authentic, and specific about the vibe.
**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): The outfit suggestion string returned by suggest_outfit().
- `new_item` (dict): The listing dict for the thrifted item. Used to pull the item name, price, and platform into the caption naturally.

**What it returns:**
<!-- Describe the return value -->
A 2–4 sentence string usable as a social media caption. Mentions the item name, price, and platform once each. Sounds different each time for different inputs. If outfit is empty or missing, returns a descriptive error message string instead of raising an exception.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
If the outfit string is empty or whitespace-only, the tool returns an error message string describing the problem rather than crashing. The agent can surface this message to the user.

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->
The agent always starts with search_listings(), using the description, size, and max_price from the user's input. If search_listings() returns an empty list, the agent stops immediately, tells the user no matches were found, and suggests they try different keywords, a different size, or a higher budget, it does not proceed to the next step. If search_listings() returns results, the agent picks the top result and calls suggest_outfit() with that item and the user's wardrobe. If the wardrobe is empty, suggest_outfit() falls back to general styling advice and still returns a non-empty string — the agent continues regardless. The agent then calls create_fit_card() with the outfit suggestion from step 2 and the new item. Once create_fit_card() returns a caption, the agent is done and returns the final output to the user. The agent does not loop back, each user query triggers one full pass through the three tools.
---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->
The agent tracks three pieces of state across the interaction:

1. **Top listing:** search_listings() returns a list of matching items. The agent saves the top result (index 0) as a single listing dict and passes it to suggest_outfit() as new_item.

2. **Outfit suggestion:** suggest_outfit() returns an outfit suggestion string. The agent saves that string and passes it to create_fit_card() as outfit, along with the same listing dict from step 1 as new_item.

3. **Wardrobe:** The user provides their wardrobe upfront before the interaction starts. It is not produced by any tool, it is passed directly into suggest_outfit() as the wardrobe input and held in session state for the duration of the interaction.

No data persists between separate user sessions, state is held in memory for one query cycle only.

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | Tells the user no matches were found and suggests trying different keywords, size, or budget. Stops — does not call suggest_outfit. |
| suggest_outfit | Wardrobe is empty | Returns general styling advice, calls create_fit_card as normal |
| create_fit_card | Outfit input is missing or incomplete | If outfit is empty or missing, returns a descriptive error message string, does not raise an exception.|

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->
User Input (description, size, max_price, wardrobe)
          │
          ▼
┌─────────────────────┐
│   search_listings   │──── returns empty ──→ Tell user, STOP
│  (description, size,│
│    max_price)       │
└─────────┬───────────┘
          │ top listing dict
          ▼
┌─────────────────────┐
│   suggest_outfit    │←── wardrobe (from user)
│  (new_item,         │
│   wardrobe)         │──── wardrobe empty ──→ general styling advice (continue)
└─────────┬───────────┘
          │ outfit suggestion string
          ▼
┌─────────────────────┐
│   create_fit_card   │──── outfit empty ──→ return error message string
│  (outfit, new_item) │
└─────────┬───────────┘
          │
          ▼
   Final caption → User
---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**
*search_listings:* I'll give Claude my Tool 1 spec and the Complete Interaction section, then ask it to implement search_listings() using load_listings() from the data loader. I'll verify by running three test cases: (1) a query that should return results sorted by relevance, (2) a query that should return an empty list with no exception, and (3) a price-filtered query where every result has price ≤ max_price.

*suggest_outfit:* I'll give Claude my Tool 2 spec and the Complete Interaction section, then ask it to implement suggest_outfit() using the Groq API. I'll verify by testing with get_empty_wardrobe() to confirm it returns general styling advice instead of crashing, and with get_example_wardrobe() to confirm it references specific wardrobe items in the suggestion.

*create_fit_card:* I'll give Claude my Tool 3 spec and the Complete Interaction section, then ask it to implement create_fit_card() using the Groq API with higher temperature. I'll verify by running it several times on the same input to confirm the output varies, and by passing an empty outfit string to confirm it returns an error message instead of crashing.

**Milestone 4 — Planning loop and state management:**
I'll give Claude my Planning Loop, State Management, and Architecture sections, then ask it to implement the agent loop in agent.py that wires the three tools together. I'll verify by running a complete end-to-end query and checking that: (1) the top listing from search_listings gets passed correctly to suggest_outfit, (2) the outfit string gets passed correctly to create_fit_card, and (3) an empty search result stops the agent without calling the other tools.
---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
Call search_listings() with a string description of the wanted clothing, a string of clothing size, and a float that represents the users budget. Returns a list of matching listings based and sorted by relevance. If empty, fitfindr tells user what to do differently and stops completely.

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
Call suggest_outfit() receives the top listing from step 1 plus the user's wardrobe. Returns a possible outfit description with the new clothing item and existing clothing item in users wardrobe.

**Step 3:**
<!-- Continue until the full interaction is complete -->
Call create_fit_card() with the suggest outfit from step 2 and the item of clothing the user wanted. Returns a social media caption about the new outfit.

**Final output to user:**
<!-- What does the user actually see at the end? -->
Social media suggested caption about new outfit