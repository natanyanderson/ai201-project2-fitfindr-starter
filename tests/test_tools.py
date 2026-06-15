# tests/test_tools.py
from tools import search_listings

def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0

def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []  # empty list, no exception

def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)

from tools import suggest_outfit
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

def test_suggest_outfit_empty_wardrobe():
    new_item = {
        "title": "Y2K Baby Tee",
        "category": "tops",
        "style_tags": ["y2k", "vintage"],
        "colors": ["white", "pink"],
        "condition": "excellent",
        "price": 18.0,
        "platform": "depop"
    }
    result = suggest_outfit(new_item, get_empty_wardrobe())
    assert isinstance(result, str)
    assert len(result) > 0  # must return something, not crash

def test_suggest_outfit_with_wardrobe():
    new_item = {
        "title": "Y2K Baby Tee",
        "category": "tops",
        "style_tags": ["y2k", "vintage"],
        "colors": ["white", "pink"],
        "condition": "excellent",
        "price": 18.0,
        "platform": "depop"
    }
    result = suggest_outfit(new_item, get_example_wardrobe())
    assert isinstance(result, str)
    assert len(result) > 0

from tools import create_fit_card

def test_create_fit_card_returns_caption():
    new_item = {
        "title": "Y2K Baby Tee — Butterfly Print",
        "price": 18.0,
        "platform": "depop",
        "style_tags": ["y2k", "vintage"]
    }
    outfit = "Pair with baggy jeans and chunky sneakers for a streetwear look."
    result = create_fit_card(outfit, new_item)
    assert isinstance(result, str)
    assert len(result) > 0

def test_create_fit_card_empty_outfit():
    new_item = {
        "title": "Y2K Baby Tee — Butterfly Print",
        "price": 18.0,
        "platform": "depop"
    }
    result = create_fit_card("", new_item)
    assert isinstance(result, str)
    assert len(result) > 0  # returns error message, not empty string