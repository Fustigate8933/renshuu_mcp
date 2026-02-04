import os
from typing import Any, Optional
import httpx

class RenshuuClient:
    BASE_URL = "https://api.renshuu.org/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the client with the user's renshuu API key.
        
        :param api_key: Renshuu API key. Falls back to RENSHUU_WRITE_KEY, then RENSHUU_READ_KEY.
        :type api_key: Optional[str]
        """
        self.api_key = api_key or os.getenv("RENSHUU_WRITE_KEY") or os.getenv("RENSHUU_READ_KEY")
        if not self.api_key:
            raise ValueError(
                "API key not found. Set RENSHUU_WRITE_KEY or RENSHUU_READ_KEY, or pass it as a parameter."
            )
        
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def headers(self) -> dict[str, str]:
        """Authorization headers for requests."""
        return {"Authorization": f"Bearer {self.api_key}"}
    
    async def __aenter__(self) -> "RenshuuClient":
        """Create async HTTP client"""
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=self.headers,
            timeout=30
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close async HTTP client"""
        if self._client:
            await self._client.aclose()
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None
    ) -> dict[str, Any]:
        """Make HTTP request to renshuu"""
        if not self._client:
            raise RuntimeError("HTTP client not initialized.")
        
        response = await self._client.request(method, endpoint, params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_profile(self) -> dict[str, Any]:
        """Get the user's profile information."""
        return await self._request("GET", "/profile")

    async def get_lists(self) -> dict[str, Any]:
        """Get all the user's lists."""
        return await self._request("GET", "/lists")
    
    async def get_list(self, list_id: str, pg: int = 1) -> dict[str, Any]:
        """Get data of a specific list."""
        return await self._request("GET", f"/list/{list_id}", params={"pg": pg})
    
    async def get_all_studied_terms(self, termtype: str, pg: int = 1) -> dict[str, Any]:
        """Get all terms of some specified type (vocab, grammar, kanji, sent)."""
        return await self._request("GET", f"/list/all/{termtype}", params={"pg": pg})
    
    async def get_schedules(self) -> dict[str, Any]:
        """Get all the user's schedules."""
        return await self._request("GET", "/schedule")
    
    async def get_schedule(self, schedule_id: str) -> dict[str, Any]:
        """Get dat of a specific schedule."""
        return await self._request("GET", f"/schedule/{schedule_id}")
    
    async def get_schedule_terms(
        self,
        schedule_id: str,
        pg: int = 1,
        group: str = "all"
    ) -> dict[str, Any]:
        """Get terms in a schedule."""
        return await self._request("GET", f"/schedule/{schedule_id}/list", params={"pg": pg, "group": group})
    
    # ====== word ======

    async def search_words(self, value: str, pg: int = 1) -> dict[str, Any]:
        """Search renshuu's dictionary."""
        return await self._request("GET", "/word/search", params={"value": value, "pg": pg})
    
    async def get_word(self, word_id: str) -> dict[str, Any]:
        """Get details of a specific word."""
        return await self._request("GET", f"/word/{word_id}")
    
    async def add_word_to_list(self, word_id: str, list_id: str) -> dict[str, Any]:
        """Add a word to a list."""
        return await self._request("PUT", f"/word/{word_id}", params={"list_id": list_id})
    
    async def add_word_to_schedule(self, word_id: str, schedule_id: str) -> dict[str, Any]:
        """Add a word to a schedule."""
        return await self._request("PUT", f"/word/{word_id}", params={"sched_id": schedule_id})
    
    async def remove_word_from_list(self, word_id: str, list_id: str) -> dict[str, Any]:
        """Remove a word from a list."""
        return await self._request("DELETE", f"/word/{word_id}", params={"list_id": list_id})
    
    async def remove_word_from_schedule(self, word_id: str, schedule_id: str) -> dict[str, Any]:
        """Remove a word from a schedule."""
        return await self._request("DELETE", f"/word/{word_id}", params={"sched_id": schedule_id})

    async def add_word_by_schedule_name(
        self,
        schedule_name: str,
        word: str
    ) -> dict[str, Any]:
        """
        Add a word to a schedule by schedule name.
        Combines schedule lookup and word addition in a single operation.
        
        :param schedule_name: Name of the schedule
        :param word: Word to search for and add (Japanese or English)
        :return: Result of the operation
        """
        # First, get all schedules to find the matching one
        schedules_response = await self.get_schedules()
        schedules = schedules_response.get("schedules", [])
        
        # Find schedule by name (case-insensitive)
        matching_schedule = None
        for schedule in schedules:
            if schedule.get("name", "").lower() == schedule_name.lower():
                matching_schedule = schedule
                break
        
        if not matching_schedule:
            return {
                "error": f"Schedule '{schedule_name}' not found",
                "available_schedules": [s.get("name") for s in schedules]
            }
        
        schedule_id = str(matching_schedule.get("id"))
        
        # Search for the word
        word_search_response = await self.search_words(word, pg=1)
        words = word_search_response.get("words", [])
        
        if not words:
            return {
                "error": f"Word '{word}' not found in dictionary"
            }
        
        # Use the first matching word
        word_id = str(words[0].get("id"))
        word_kanji = words[0].get("kanji_full", "")
        word_hiragana = words[0].get("hiragana_full", "")
        
        # Add the word to the schedule
        add_response = await self.add_word_to_schedule(word_id, schedule_id)
        
        return {
            "success": True,
            "schedule": {
                "id": schedule_id,
                "name": matching_schedule.get("name")
            },
            "word": {
                "id": word_id,
                "kanji": word_kanji,
                "hiragana": word_hiragana,
                "definitions": words[0].get("def", [])
            },
            "api_response": add_response
        }

    async def add_word_by_list_name(
        self,
        list_name: str,
        word: str
    ) -> dict[str, Any]:
        """
        Add a word to a list by list name.
        Combines list lookup and word addition in a single operation.
        
        :param list_name: Name of the list
        :param word: Word to search for and add (Japanese or English)
        :return: Result of the operation
        """
        # First, get all lists to find the matching one
        lists_response = await self.get_lists()
        
        # Extract all lists from the nested structure
        all_lists = []
        termtype_groups = lists_response.get("termtype_groups", [])
        for group in termtype_groups:
            groups = group.get("groups", [])
            for subgroup in groups:
                lists = subgroup.get("lists", [])
                all_lists.extend(lists)
        
        # Find list by name (case-insensitive)
        matching_list = None
        for lst in all_lists:
            if lst.get("title", "").lower() == list_name.lower():
                matching_list = lst
                break
        
        if not matching_list:
            return {
                "error": f"List '{list_name}' not found",
                "available_lists": [lst.get("title") for lst in all_lists]
            }
        
        list_id = str(matching_list.get("list_id"))
        
        # Search for the word
        word_search_response = await self.search_words(word, pg=1)
        words = word_search_response.get("words", [])
        
        if not words:
            return {
                "error": f"Word '{word}' not found in dictionary"
            }
        
        # Use the first matching word
        word_id = str(words[0].get("id"))
        word_kanji = words[0].get("kanji_full", "")
        word_hiragana = words[0].get("hiragana_full", "")
        
        # Add the word to the list
        add_response = await self.add_word_to_list(word_id, list_id)
        
        return {
            "success": True,
            "list": {
                "id": list_id,
                "name": matching_list.get("title")
            },
            "word": {
                "id": word_id,
                "kanji": word_kanji,
                "hiragana": word_hiragana,
                "definitions": words[0].get("def", [])
            },
            "api_response": add_response
        }

    # ====== kanji ======

    async def search_kanji(self, value: str) -> dict[str, Any]:
        """Search renshuu's kanji dictionary."""
        return await self._request("GET", "/kanji/search", params={"value": value})
    
    async def get_kanji(self, kanji: str) -> dict[str, Any]:
        """Get details of a specific Kanji from renshuu dictionary."""
        return await self._request("GET", f"/kanji/{kanji}")
    
    async def add_kanji_to_list(self, kanji: str, list_id: str) -> dict[str, Any]:
        """Add a kanji to a list."""
        return await self._request("PUT", f"/kanji/{kanji}", params={"list_id": list_id})
    
    async def add_kanji_to_schedule(self, kanji: str, sched_id: str) -> dict[str, Any]:
        """Add a kanji to a schedule."""
        return await self._request("PUT", f"/kanji/{kanji}", params={"sched_id": sched_id})
    
    async def remove_kanji_from_list(self, kanji: str, list_id: str) -> dict[str, Any]:
        """Remove a kanji from a list."""
        return await self._request("DELETE", f"/kanji/{kanji}", params={"list_id": list_id})
    
    async def remove_kanji_from_schedule(self, kanji: str, schedule_id: str) -> dict[str, Any]:
        """Remove a kanji from a schedule."""
        return await self._request("DELETE", f"/word/{kanji}", params={"sched_id": schedule_id})
    
    # ====== grammar ======
    
    async def search_grammar(self, value: str, pg: int = 1) -> dict[str, Any]:
        """Search renshuu's grammar dictionary."""
        return await self._request("GET", "/grammar/search", params={"value": value, "pg": pg})
    
    async def get_grammar(self, grammar_id: str) -> dict[str, Any]:
        """Get details of a specific grammar."""
        return await self._request("GET", f"/grammar/{grammar_id}")
    
    async def add_grammar_to_list(self, grammar_id: str, list_id: str) -> dict[str, Any]:
        """Add a grammar to a list."""
        return await self._request("PUT", f"/grammar/{grammar_id}", params={"list_id": list_id})
    
    async def add_grammar_to_schedule(self, grammar_id: str, schedule_id: str) -> dict[str, Any]:
        """Add a grammar to a schedule."""
        return await self._request("PUT", f"/grammar/{grammar_id}", params={"sched_id": schedule_id})
    
    async def remove_grammar_from_list(self, grammar_id: str, list_id: str) -> dict[str, Any]:
        """Remove a grammar from a list."""
        return await self._request("DELETE", f"/grammar/{grammar_id}", params={"list_id": list_id})
    
    async def remove_grammar_from_schedule(self, grammar_id: str, schedule_id: str) -> dict[str, Any]:
        """Remove a grammar from a schedule."""
        return await self._request("DELETE", f"/grammar/{grammar_id}", params={"sched_id": schedule_id})

    # ====== sentence ======

    async def search_sentences(self, value: str) -> dict[str, Any]:
        """Search renshuu's sentence library."""
        return await self._request("GET", "/reibun/search", params={"value": value})

    async def get_sentences_for_word(self, word_id: str) -> dict[str, Any]:
        """Get sentences for a given word."""
        return await self._request("GET", f"/reibun/search/{word_id}")
