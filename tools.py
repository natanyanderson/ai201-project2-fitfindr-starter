"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

_OUTFIT_MODEL = "llama-3.3-70b-versatile"

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.
    ...
    """
    listings = load_listings()

    # Step 2: Filter by max_price and size
    filtered = []
    for listing in listings:
        if max_price is not None and listing["price"] > max_price:
            continue
        if size is not None:
            if size.lower() not in listing["size"].lower():
                continue
        filtered.append(listing)

    # Step 3: Score by keyword overlap with description
    keywords = set(description.lower().split())

    def score(listing):
        text = " ".join([
            listing["title"],
            listing["description"],
            " ".join(listing["style_tags"]),
        ]).lower()
        return sum(1 for word in keywords if word in text)

    # Step 4 & 5: Drop score=0, sort by score descending
    scored = [(score(l), l) for l in filtered]
    scored = [(s, l) for s, l in scored if s > 0]
    scored.sort(key=lambda x: x[0], reverse=True)

    return [l for _, l in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────
 
def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.
 
    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handled gracefully.
 
    Returns:
        A non-empty string with outfit suggestions. If the wardrobe has items,
        the suggestion names specific pieces from it. If the wardrobe is empty,
        returns general styling advice for the new item instead.
    """
    client = _get_groq_client()
 
    # Summarize the new item for the prompt, tolerating missing fields.
    item_summary = (
        f"Title: {new_item.get('title', 'Unknown item')}\n"
        f"Category: {new_item.get('category', 'unknown')}\n"
        f"Style tags: {', '.join(new_item.get('style_tags', [])) or 'none listed'}\n"
        f"Colors: {', '.join(new_item.get('colors', [])) or 'none listed'}\n"
        f"Condition: {new_item.get('condition', 'unknown')}\n"
        f"Price: ${new_item.get('price', 'unknown')}\n"
        f"Platform: {new_item.get('platform', 'unknown')}"
    )
 
    items = wardrobe.get("items", []) if isinstance(wardrobe, dict) else []
 
    system_msg = (
        "You are FitFindr, a sharp thrift-and-styling assistant. You suggest "
        "wearable, specific outfits and keep your answers concise (under ~150 "
        "words). Never invent items the user does not have."
    )
 
    if not items:
        # Empty wardrobe → general styling advice, no exception.
        user_msg = (
            "A user is considering buying this thrifted item:\n\n"
            f"{item_summary}\n\n"
            "They have not shared their existing wardrobe. Suggest 1–2 complete "
            "outfit ideas built around this item. For each, describe the kinds of "
            "pieces (tops, bottoms, shoes, layers, accessories) that pair well "
            "with it and the overall vibe it creates. Keep it practical and "
            "specific so they can picture wearing it."
        )
    else:
        # Format the wardrobe so the model can reference pieces by name.
        wardrobe_lines = []
        for w in items:
            name = w.get("title") or w.get("name") or "unnamed piece"
            descriptors = []
            if w.get("category"):
                descriptors.append(str(w["category"]))
            if w.get("colors"):
                descriptors.append(", ".join(w["colors"]))
            if w.get("style_tags"):
                descriptors.append(", ".join(w["style_tags"]))
            detail = f" ({'; '.join(descriptors)})" if descriptors else ""
            wardrobe_lines.append(f"- {name}{detail}")
        wardrobe_text = "\n".join(wardrobe_lines)
 
        user_msg = (
            "A user is considering buying this thrifted item:\n\n"
            f"{item_summary}\n\n"
            "Here is what they already own:\n\n"
            f"{wardrobe_text}\n\n"
            "Suggest 1–2 complete outfits that combine the new item with pieces "
            "from their wardrobe. Name the specific wardrobe pieces you use in "
            "each outfit, and briefly explain why the combination works."
        )
 
    response = client.chat.completions.create(
        model=_OUTFIT_MODEL,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.7,
    )
 
    suggestion = (response.choices[0].message.content or "").strip()
 
    # Guarantee a non-empty return even if the model gives back nothing.
    if not suggestion:
        return (
            f"Here's a styling idea for the {new_item.get('title', 'item')}: "
            "pair it with neutral basics and let it be the statement piece."
        )
 
    return suggestion


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────


"""
tools.py
 
The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.
 
Complete and test each tool before moving to agent.py.
 
Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""
 
import os
 
from dotenv import load_dotenv
from groq import Groq
 
from utils.data_loader import load_listings
 
_OUTFIT_MODEL = "llama-3.3-70b-versatile"
 
load_dotenv()
 
 
# ── Groq client ───────────────────────────────────────────────────────────────
 
def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)
 
 
# ── Tool 1: search_listings ───────────────────────────────────────────────────
 
def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.
    ...
    """
    listings = load_listings()
 
    # Step 2: Filter by max_price and size
    filtered = []
    for listing in listings:
        if max_price is not None and listing["price"] > max_price:
            continue
        if size is not None:
            if size.lower() not in listing["size"].lower():
                continue
        filtered.append(listing)
 
    # Step 3: Score by keyword overlap with description
    keywords = set(description.lower().split())
 
    def score(listing):
        text = " ".join([
            listing["title"],
            listing["description"],
            " ".join(listing["style_tags"]),
        ]).lower()
        return sum(1 for word in keywords if word in text)
 
    # Step 4 & 5: Drop score=0, sort by score descending
    scored = [(score(l), l) for l in filtered]
    scored = [(s, l) for s, l in scored if s > 0]
    scored.sort(key=lambda x: x[0], reverse=True)
 
    return [l for _, l in scored]
 
 
# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────
 
def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.
 
    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handled gracefully.
 
    Returns:
        A non-empty string with outfit suggestions. If the wardrobe has items,
        the suggestion names specific pieces from it. If the wardrobe is empty,
        returns general styling advice for the new item instead.
    """
    client = _get_groq_client()
 
    # Summarize the new item for the prompt, tolerating missing fields.
    item_summary = (
        f"Title: {new_item.get('title', 'Unknown item')}\n"
        f"Category: {new_item.get('category', 'unknown')}\n"
        f"Style tags: {', '.join(new_item.get('style_tags', [])) or 'none listed'}\n"
        f"Colors: {', '.join(new_item.get('colors', [])) or 'none listed'}\n"
        f"Condition: {new_item.get('condition', 'unknown')}\n"
        f"Price: ${new_item.get('price', 'unknown')}\n"
        f"Platform: {new_item.get('platform', 'unknown')}"
    )
 
    items = wardrobe.get("items", []) if isinstance(wardrobe, dict) else []
 
    system_msg = (
        "You are FitFindr, a sharp thrift-and-styling assistant. You suggest "
        "wearable, specific outfits and keep your answers concise (under ~150 "
        "words). Never invent items the user does not have."
    )
 
    if not items:
        # Empty wardrobe → general styling advice, no exception.
        user_msg = (
            "A user is considering buying this thrifted item:\n\n"
            f"{item_summary}\n\n"
            "They have not shared their existing wardrobe. Suggest 1–2 complete "
            "outfit ideas built around this item. For each, describe the kinds of "
            "pieces (tops, bottoms, shoes, layers, accessories) that pair well "
            "with it and the overall vibe it creates. Keep it practical and "
            "specific so they can picture wearing it."
        )
    else:
        # Format the wardrobe so the model can reference pieces by name.
        wardrobe_lines = []
        for w in items:
            name = w.get("title") or w.get("name") or "unnamed piece"
            descriptors = []
            if w.get("category"):
                descriptors.append(str(w["category"]))
            if w.get("colors"):
                descriptors.append(", ".join(w["colors"]))
            if w.get("style_tags"):
                descriptors.append(", ".join(w["style_tags"]))
            detail = f" ({'; '.join(descriptors)})" if descriptors else ""
            wardrobe_lines.append(f"- {name}{detail}")
        wardrobe_text = "\n".join(wardrobe_lines)
 
        user_msg = (
            "A user is considering buying this thrifted item:\n\n"
            f"{item_summary}\n\n"
            "Here is what they already own:\n\n"
            f"{wardrobe_text}\n\n"
            "Suggest 1–2 complete outfits that combine the new item with pieces "
            "from their wardrobe. Name the specific wardrobe pieces you use in "
            "each outfit, and briefly explain why the combination works."
        )
 
    response = client.chat.completions.create(
        model=_OUTFIT_MODEL,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.7,
    )
 
    suggestion = (response.choices[0].message.content or "").strip()
 
    # Guarantee a non-empty return even if the model gives back nothing.
    if not suggestion:
        return (
            f"Here's a styling idea for the {new_item.get('title', 'item')}: "
            "pair it with neutral basics and let it be the statement piece."
        )
 
    return suggestion
 
 
# ── Tool 3: create_fit_card ───────────────────────────────────────────────────
 

"""
tools.py
 
The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.
 
Complete and test each tool before moving to agent.py.
 
Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""
 
import os
 
from dotenv import load_dotenv
from groq import Groq
 
from utils.data_loader import load_listings
 
_OUTFIT_MODEL = "llama-3.3-70b-versatile"
 
load_dotenv()
 
 
# ── Groq client ───────────────────────────────────────────────────────────────
 
def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)
 
 
# ── Tool 1: search_listings ───────────────────────────────────────────────────
 
def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.
    ...
    """
    listings = load_listings()
 
    # Step 2: Filter by max_price and size
    filtered = []
    for listing in listings:
        if max_price is not None and listing["price"] > max_price:
            continue
        if size is not None:
            if size.lower() not in listing["size"].lower():
                continue
        filtered.append(listing)
 
    # Step 3: Score by keyword overlap with description
    keywords = set(description.lower().split())
 
    def score(listing):
        text = " ".join([
            listing["title"],
            listing["description"],
            " ".join(listing["style_tags"]),
        ]).lower()
        return sum(1 for word in keywords if word in text)
 
    # Step 4 & 5: Drop score=0, sort by score descending
    scored = [(score(l), l) for l in filtered]
    scored = [(s, l) for s, l in scored if s > 0]
    scored.sort(key=lambda x: x[0], reverse=True)
 
    return [l for _, l in scored]
 
 
# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────
 
def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.
 
    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handled gracefully.
 
    Returns:
        A non-empty string with outfit suggestions. If the wardrobe has items,
        the suggestion names specific pieces from it. If the wardrobe is empty,
        returns general styling advice for the new item instead.
    """
    client = _get_groq_client()
 
    # Summarize the new item for the prompt, tolerating missing fields.
    item_summary = (
        f"Title: {new_item.get('title', 'Unknown item')}\n"
        f"Category: {new_item.get('category', 'unknown')}\n"
        f"Style tags: {', '.join(new_item.get('style_tags', [])) or 'none listed'}\n"
        f"Colors: {', '.join(new_item.get('colors', [])) or 'none listed'}\n"
        f"Condition: {new_item.get('condition', 'unknown')}\n"
        f"Price: ${new_item.get('price', 'unknown')}\n"
        f"Platform: {new_item.get('platform', 'unknown')}"
    )
 
    items = wardrobe.get("items", []) if isinstance(wardrobe, dict) else []
 
    system_msg = (
        "You are FitFindr, a sharp thrift-and-styling assistant. You suggest "
        "wearable, specific outfits and keep your answers concise (under ~150 "
        "words). Never invent items the user does not have."
    )
 
    if not items:
        # Empty wardrobe → general styling advice, no exception.
        user_msg = (
            "A user is considering buying this thrifted item:\n\n"
            f"{item_summary}\n\n"
            "They have not shared their existing wardrobe. Suggest 1–2 complete "
            "outfit ideas built around this item. For each, describe the kinds of "
            "pieces (tops, bottoms, shoes, layers, accessories) that pair well "
            "with it and the overall vibe it creates. Keep it practical and "
            "specific so they can picture wearing it."
        )
    else:
        # Format the wardrobe so the model can reference pieces by name.
        wardrobe_lines = []
        for w in items:
            name = w.get("title") or w.get("name") or "unnamed piece"
            descriptors = []
            if w.get("category"):
                descriptors.append(str(w["category"]))
            if w.get("colors"):
                descriptors.append(", ".join(w["colors"]))
            if w.get("style_tags"):
                descriptors.append(", ".join(w["style_tags"]))
            detail = f" ({'; '.join(descriptors)})" if descriptors else ""
            wardrobe_lines.append(f"- {name}{detail}")
        wardrobe_text = "\n".join(wardrobe_lines)
 
        user_msg = (
            "A user is considering buying this thrifted item:\n\n"
            f"{item_summary}\n\n"
            "Here is what they already own:\n\n"
            f"{wardrobe_text}\n\n"
            "Suggest 1–2 complete outfits that combine the new item with pieces "
            "from their wardrobe. Name the specific wardrobe pieces you use in "
            "each outfit, and briefly explain why the combination works."
        )
 
    response = client.chat.completions.create(
        model=_OUTFIT_MODEL,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.7,
    )
 
    suggestion = (response.choices[0].message.content or "").strip()
 
    # Guarantee a non-empty return even if the model gives back nothing.
    if not suggestion:
        return (
            f"Here's a styling idea for the {new_item.get('title', 'item')}: "
            "pair it with neutral basics and let it be the statement piece."
        )
 
    return suggestion
 
 
# ── Tool 3: create_fit_card ───────────────────────────────────────────────────
 
"""
tools.py
 
The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.
 
Complete and test each tool before moving to agent.py.
 
Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""
 
import os
 
from dotenv import load_dotenv
from groq import Groq
 
from utils.data_loader import load_listings
 
_OUTFIT_MODEL = "llama-3.3-70b-versatile"
 
load_dotenv()
 
 
# ── Groq client ───────────────────────────────────────────────────────────────
 
def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)
 
 
# ── Tool 1: search_listings ───────────────────────────────────────────────────
 
def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.
    ...
    """
    listings = load_listings()
 
    # Step 2: Filter by max_price and size
    filtered = []
    for listing in listings:
        if max_price is not None and listing["price"] > max_price:
            continue
        if size is not None:
            if size.lower() not in listing["size"].lower():
                continue
        filtered.append(listing)
 
    # Step 3: Score by keyword overlap with description
    keywords = set(description.lower().split())
 
    def score(listing):
        text = " ".join([
            listing["title"],
            listing["description"],
            " ".join(listing["style_tags"]),
        ]).lower()
        return sum(1 for word in keywords if word in text)
 
    # Step 4 & 5: Drop score=0, sort by score descending
    scored = [(score(l), l) for l in filtered]
    scored = [(s, l) for s, l in scored if s > 0]
    scored.sort(key=lambda x: x[0], reverse=True)
 
    return [l for _, l in scored]
 
 
# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────
 
def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.
 
    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handled gracefully.
 
    Returns:
        A non-empty string with outfit suggestions. If the wardrobe has items,
        the suggestion names specific pieces from it. If the wardrobe is empty,
        returns general styling advice for the new item instead.
    """
    client = _get_groq_client()
 
    # Summarize the new item for the prompt, tolerating missing fields.
    item_summary = (
        f"Title: {new_item.get('title', 'Unknown item')}\n"
        f"Category: {new_item.get('category', 'unknown')}\n"
        f"Style tags: {', '.join(new_item.get('style_tags', [])) or 'none listed'}\n"
        f"Colors: {', '.join(new_item.get('colors', [])) or 'none listed'}\n"
        f"Condition: {new_item.get('condition', 'unknown')}\n"
        f"Price: ${new_item.get('price', 'unknown')}\n"
        f"Platform: {new_item.get('platform', 'unknown')}"
    )
 
    items = wardrobe.get("items", []) if isinstance(wardrobe, dict) else []
 
    system_msg = (
        "You are FitFindr, a sharp thrift-and-styling assistant. You suggest "
        "wearable, specific outfits and keep your answers concise (under ~150 "
        "words). Never invent items the user does not have."
    )
 
    if not items:
        # Empty wardrobe → general styling advice, no exception.
        user_msg = (
            "A user is considering buying this thrifted item:\n\n"
            f"{item_summary}\n\n"
            "They have not shared their existing wardrobe. Suggest 1–2 complete "
            "outfit ideas built around this item. For each, describe the kinds of "
            "pieces (tops, bottoms, shoes, layers, accessories) that pair well "
            "with it and the overall vibe it creates. Keep it practical and "
            "specific so they can picture wearing it."
        )
    else:
        # Format the wardrobe so the model can reference pieces by name.
        wardrobe_lines = []
        for w in items:
            name = w.get("title") or w.get("name") or "unnamed piece"
            descriptors = []
            if w.get("category"):
                descriptors.append(str(w["category"]))
            if w.get("colors"):
                descriptors.append(", ".join(w["colors"]))
            if w.get("style_tags"):
                descriptors.append(", ".join(w["style_tags"]))
            detail = f" ({'; '.join(descriptors)})" if descriptors else ""
            wardrobe_lines.append(f"- {name}{detail}")
        wardrobe_text = "\n".join(wardrobe_lines)
 
        user_msg = (
            "A user is considering buying this thrifted item:\n\n"
            f"{item_summary}\n\n"
            "Here is what they already own:\n\n"
            f"{wardrobe_text}\n\n"
            "Suggest 1–2 complete outfits that combine the new item with pieces "
            "from their wardrobe. Name the specific wardrobe pieces you use in "
            "each outfit, and briefly explain why the combination works."
        )
 
    response = client.chat.completions.create(
        model=_OUTFIT_MODEL,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.7,
    )
 
    suggestion = (response.choices[0].message.content or "").strip()
 
    # Guarantee a non-empty return even if the model gives back nothing.
    if not suggestion:
        return (
            f"Here's a styling idea for the {new_item.get('title', 'item')}: "
            "pair it with neutral basics and let it be the statement piece."
        )
 
    return suggestion
 
 
# ── Tool 3: create_fit_card ───────────────────────────────────────────────────
 
def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.
 
    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.
 
    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.
 
    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)
 
    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.
 
    Before writing code, fill in the Tool 3 section of planning.md.
    """
    # 1. Guard against an empty or whitespace-only outfit string.
    if not outfit or not outfit.strip():
        return (
            "Could not create a fit card: the outfit suggestion was empty. "
            "Run suggest_outfit() to get an outfit before creating a caption."
        )
 
    client = _get_groq_client()
 
    # Pull the three details that must each appear in the caption exactly once.
    title = new_item.get("title", "this thrifted find")
    price = new_item.get("price", "unknown")
    platform = new_item.get("platform", "unknown")
    price_str = f"${price}" if isinstance(price, (int, float)) else str(price)
 
    system_msg = (
        "You are FitFindr, writing short, shareable OOTD captions for thrifted "
        "outfits. You write like a real person posting on Instagram or TikTok: "
        "casual, authentic, and specific about the vibe. Never sound like a "
        "product description or an ad."
    )
 
    user_msg = (
        "Write a 2-4 sentence social media caption for this thrifted outfit.\n\n"
        f"Item name: {title}\n"
        f"Price: {price_str}\n"
        f"Platform: {platform}\n\n"
        f"Outfit being styled:\n{outfit}\n\n"
        "Requirements:\n"
        f"- Work in the item name ({title}), the price ({price_str}), and the "
        f"platform ({platform}) naturally — mention each exactly once.\n"
        "- Capture the specific vibe of THIS outfit; don't just describe the item.\n"
        "- Sound like a genuine OOTD post: casual and authentic, never salesy.\n"
        "- Keep it to 2-4 sentences and return only the caption text."
    )
 
    # Higher temperature than suggest_outfit so captions vary across inputs/runs.
    response = client.chat.completions.create(
        model=_OUTFIT_MODEL,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        temperature=1.0,
    )
 
    caption = (response.choices[0].message.content or "").strip()
 
    # Guarantee a non-empty return even if the model gives back nothing.
    if not caption:
        return (
            f"Just thrifted the {title} for {price_str} on {platform} and I'm "
            "obsessed — styled it up and it's already in heavy rotation."
        )
 
    return caption