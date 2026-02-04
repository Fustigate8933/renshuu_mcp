#!/usr/bin/env python3
"""
OpenAPI proxy server for Renshuu API.
Serves the OpenAPI spec and proxies requests to the Renshuu API with authentication.
"""

import os
import httpx
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse, FileResponse
from starlette.requests import Request
import uvicorn
import json
from src.client import RenshuuClient

# Load API key from environment
API_KEY = os.getenv("RENSHUU_WRITE_KEY") or os.getenv("RENSHUU_READ_KEY")
if not API_KEY:
    print("WARNING: No API key found. Set RENSHUU_WRITE_KEY or RENSHUU_READ_KEY environment variable.")

RENSHUU_BASE_URL = "https://api.renshuu.org/v1"


async def serve_openapi_spec(request: Request):
    """Serve the OpenAPI specification."""
    return FileResponse("api-docs-local.json", media_type="application/json")


async def add_word_by_schedule_name_handler(request: Request):
    """Handle the convenience endpoint for adding a word by schedule name."""
    try:
        body = await request.json()
        schedule_name = body.get("schedule_name")
        word = body.get("word")
        
        if not schedule_name or not word:
            return JSONResponse(
                {"ok": False, "error": "Missing schedule_name or word"},
                status_code=400
            )
        
        async with RenshuuClient(API_KEY) as client:
            result = await client.add_word_by_schedule_name(schedule_name, word)
            
            if "error" in result:
                return JSONResponse(
                    {"ok": False, "status": 400, "data": result},
                    status_code=400
                )
            
            return JSONResponse(
                {"ok": True, "status": 200, "data": result},
                status_code=200
            )
    except Exception as e:
        return JSONResponse(
            {"ok": False, "error": str(e)},
            status_code=500
        )


async def add_word_by_list_name_handler(request: Request):
    """Handle the convenience endpoint for adding a word by list name."""
    try:
        body = await request.json()
        list_name = body.get("list_name")
        word = body.get("word")
        
        if not list_name or not word:
            return JSONResponse(
                {"ok": False, "error": "Missing list_name or word"},
                status_code=400
            )
        
        async with RenshuuClient(API_KEY) as client:
            result = await client.add_word_by_list_name(list_name, word)
            
            if "error" in result:
                return JSONResponse(
                    {"ok": False, "status": 400, "data": result},
                    status_code=400
                )
            
            return JSONResponse(
                {"ok": True, "status": 200, "data": result},
                status_code=200
            )
    except Exception as e:
        return JSONResponse(
            {"ok": False, "error": str(e)},
            status_code=500
        )


from starlette.responses import JSONResponse

async def proxy_request(request: Request):
    path = request.url.path.replace("/api/v1", "")
    target_url = f"{RENSHUU_BASE_URL}{path}"

    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }

        params = dict(request.query_params)
        body = await request.body()

        if request.method == "GET":
            response = await client.get(target_url, headers=headers, params=params)
        elif request.method == "POST":
            response = await client.post(target_url, headers=headers, params=params, content=body)
        elif request.method == "PUT":
            response = await client.put(target_url, headers=headers, params=params, content=body)
        elif request.method == "DELETE":
            response = await client.delete(target_url, headers=headers, params=params)
        else:
            return JSONResponse({"ok": False, "error": "Method not allowed"}, status_code=405)

        try:
            payload = {
                "ok": response.status_code < 400,
                "status": response.status_code,
                "data": response.json()
            }
        except Exception:
            payload = {
                "ok": response.status_code < 400,
                "status": response.status_code,
                "raw": response.text
            }

        return JSONResponse(payload, status_code=response.status_code)

app = Starlette(
    routes=[
        Route("/openapi.json", serve_openapi_spec),
        Route("/api-docs.json", serve_openapi_spec),  # Alternative path
        Route("/api/v1/renshuu/add-word-by-name", add_word_by_schedule_name_handler, methods=["POST"]),
        Route("/api/v1/renshuu/add-word-to-list-by-name", add_word_by_list_name_handler, methods=["POST"]),
        Mount("/api/v1", routes=[
            Route("/{path:path}", proxy_request, methods=["GET", "POST", "PUT", "DELETE"])
        ])
    ]
)


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    
    print(f"Starting OpenAPI proxy server on {host}:{port}")
    print(f"OpenAPI spec available at: http://{host}:{port}/openapi.json")
    print(f"API base URL: http://{host}:{port}/api/v1")
    if API_KEY:
        print(f"Using API key: {API_KEY[:10]}...")
    else:
        print("WARNING: No API key configured!")
    
    uvicorn.run(app, host=host, port=port)
