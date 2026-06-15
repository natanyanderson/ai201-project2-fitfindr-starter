
"""
agent.py
 
The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.
 
Complete tools.py and test each tool in isolation before implementing this file.
 
Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe
 
    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""
 
import re
 
from tools import search_listings, suggest_outfit, create_fit_card
 
 
# ── query parsing ─────────────────────────────────────────────────────────────
 
# Filler phrases stripped from the front of a query so the leftover text reads
# as a clean item description (e.g. "looking for a vintage tee" -> "vintage tee").
_LEAD_FILLER = [
    "i'm looking for", "im looking for", "i am looking for",
    "looking for", "i want", "i need", "show me", "find me",
    "searching for", "search for", "do you have",
]
 
# Common clothing size tokens we'll recognize when they appear on their own
# (i.e. without an explicit "size" prefix), longest-first so "XXL" wins over "XL".
_SIZE_TOKENS = ["xxs", "xxl", "xs", "xl", "s", "m", "l"]
 
 
def _parse_query(query: str) -> dict:
    """
    Extract a description, optional size, and optional max_price from a short,
    structured query string using simple regex/string splitting.
 
    Returns a dict: {"description": str, "size": str|None, "max_price": float|None}.
    Designed to be forgiving — anything it can't confidently match is left as None,
    and the remaining text becomes the description.
    """
    text = query.strip()
    size = None
    max_price = None
 
    # ── max_price ────────────────────────────────────────────────────────────
    # Matches "under $30", "below 30", "max $29.99", "less than $40", "<$25".
    price_match = re.search(
        r"(?:under|below|less than|max(?:imum)?|at most|<=?)\s*\$?\s*(\d+(?:\.\d+)?)",
        text,
        flags=re.IGNORECASE,
    )
    if price_match:
        max_price = float(price_match.group(1))
        text = text[: price_match.start()] + text[price_match.end() :]
    else:
        # Bare "$30" with no qualifier — treat as a budget ceiling.
        bare = re.search(r"\$\s*(\d+(?:\.\d+)?)", text)
        if bare:
            max_price = float(bare.group(1))
            text = text[: bare.start()] + text[bare.end() :]
 
    # ── size ──────────────────────────────────────────────────────────────────
    # Preferred form: an explicit "size M" / "size: XXS" prefix.
    size_match = re.search(r"\bsize:?\s*([A-Za-z0-9]+)", text, flags=re.IGNORECASE)
    if size_match:
        size = size_match.group(1).upper()
        text = text[: size_match.start()] + text[size_match.end() :]
    else:
        # Fallback: a standalone size token (e.g. "... tee XS ...").
        for token in _SIZE_TOKENS:
            standalone = re.search(rf"\b{token}\b", text, flags=re.IGNORECASE)
            if standalone:
                size = standalone.group(0).upper()
                text = text[: standalone.start()] + text[standalone.end() :]
                break
 
    # ── description ────────────────────────────────────────────────────────────
    # Clean up leftover punctuation/whitespace, then strip leading filler phrases.
    description = re.sub(r"\s+", " ", text.replace(",", " ")).strip(" ,.-").strip()
    lowered = description.lower()
    for filler in _LEAD_FILLER:
        if lowered.startswith(filler):
            description = description[len(filler) :].strip(" ,.-").strip()
            break
    # Trim a dangling leading article left behind ("a vintage tee" -> "vintage tee").
    description = re.sub(r"^(?:a|an|the)\s+", "", description, flags=re.IGNORECASE).strip()
 
    # If parsing stripped everything, fall back to the original query text.
    if not description:
        description = query.strip()
 
    return {"description": description, "size": size, "max_price": max_price}
 
 
# ── session state ─────────────────────────────────────────────────────────────
 
def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.
 
    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.
 
    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }
 
 
# ── planning loop ─────────────────────────────────────────────────────────────
 
def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.
 
    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py
 
    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.
 
    TODO — implement this function using the planning loop you designed in planning.md:
 
        Step 1: Initialize the session with _new_session().
 
        Step 2: Parse the user's query to extract a description, size, and
                max_price. You can use regex, string splitting, or ask the LLM
                to parse it — document your choice in planning.md.
                Store the result in session["parsed"].
 
        Step 3: Call search_listings() with the parsed parameters.
                Store results in session["search_results"].
                If no results: set session["error"] to a helpful message and
                return the session early. Do NOT proceed to suggest_outfit
                with empty input.
 
        Step 4: Select the item to use (e.g., the top result).
                Store it in session["selected_item"].
 
        Step 5: Call suggest_outfit() with the selected item and wardrobe.
                Store the result in session["outfit_suggestion"].
 
        Step 6: Call create_fit_card() with the outfit suggestion and selected item.
                Store the result in session["fit_card"].
 
        Step 7: Return the session.
 
    Before writing code, complete the Planning Loop and State Management sections
    of planning.md — your implementation should match what you described there.
    """
    # Step 1: fresh session — the single source of truth for this interaction.
    session = _new_session(query, wardrobe)
 
    # Step 2: parse the query into description / size / max_price.
    session["parsed"] = _parse_query(query)
    parsed = session["parsed"]
 
    # Step 3: search listings with the parsed parameters.
    session["search_results"] = search_listings(
        description=parsed["description"],
        size=parsed["size"],
        max_price=parsed["max_price"],
    )
 
    # Early termination: nothing matched. Do NOT call suggest_outfit with empty
    # input — set a helpful error and return the session as-is.
    if not session["search_results"]:
        session["error"] = (
            "No listings matched your search. Try different keywords, "
            "a different size, or a higher budget."
        )
        return session
 
    # Step 4: select the top (most relevant) result.
    session["selected_item"] = session["search_results"][0]
 
    # Step 5: suggest an outfit pairing the new item with the user's wardrobe.
    # suggest_outfit handles an empty wardrobe internally (general styling advice)
    # and always returns a non-empty string, so we continue regardless.
    session["outfit_suggestion"] = suggest_outfit(
        new_item=session["selected_item"],
        wardrobe=session["wardrobe"],
    )
 
    # Step 6: turn the outfit into a shareable fit-card caption.
    session["fit_card"] = create_fit_card(
        outfit=session["outfit_suggestion"],
        new_item=session["selected_item"],
    )
 
    # Step 7: done — single pass complete, no looping back.
    return session
 
 
# ── CLI test ──────────────────────────────────────────────────────────────────
 
if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe
 
    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")
 
    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")