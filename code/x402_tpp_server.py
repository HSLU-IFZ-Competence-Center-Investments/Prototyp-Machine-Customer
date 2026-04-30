"""
x402_tpp_server.py

Local third-party provider / TPP for the x402 demo.

Run in Terminal 1:
    python -m uvicorn x402_tpp_server:app --host 127.0.0.1 --port 4021

.env in same folder:
    TPP_RECEIVE_ADDRESS=0xYOUR_TPP_RECEIVING_ADDRESS

The provider exposes:
    GET /
    GET /api/v1/dummy-service

The dummy service is protected by x402. Without payment it returns HTTP 402.
With a valid x402 payment it returns a dummy JSON service response.
"""

import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI

from x402.http import FacilitatorConfig, HTTPFacilitatorClient, PaymentOption
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.http.types import RouteConfig
from x402.mechanisms.evm.exact import ExactEvmServerScheme
from x402.schemas import Network
from x402.server import x402ResourceServer


load_dotenv()

TPP_RECEIVE_ADDRESS = os.getenv("TPP_RECEIVE_ADDRESS")

HOST = "127.0.0.1"
PORT = 4021
PROTECTED_PATH = "/api/v1/dummy-service"

# Base Sepolia testnet. Base mainnet would be eip155:8453.
EVM_NETWORK: Network = "eip155:84532"

# Public x402 test facilitator base URL.
FACILITATOR_URL = "https://x402.org/facilitator"

# Demo price.
PRICE = "$0.001"


if not TPP_RECEIVE_ADDRESS:
    raise RuntimeError(
        "Missing TPP_RECEIVE_ADDRESS in .env. "
        "Example: TPP_RECEIVE_ADDRESS=0xYOUR_TPP_RECEIVING_ADDRESS"
    )

if not TPP_RECEIVE_ADDRESS.startswith("0x"):
    raise RuntimeError("TPP_RECEIVE_ADDRESS must be an EVM address starting with 0x.")


def create_app() -> FastAPI:
    provider_app = FastAPI(
        title="x402 Demo Third-Party Provider",
        description="Dummy x402-protected third-party provider.",
        version="1.0.0",
    )

    facilitator = HTTPFacilitatorClient(
        FacilitatorConfig(url=FACILITATOR_URL)
    )

    resource_server = x402ResourceServer(facilitator)
    resource_server.register(EVM_NETWORK, ExactEvmServerScheme())

    routes: dict[str, RouteConfig] = {
        f"GET {PROTECTED_PATH}": RouteConfig(
            accepts=[
                PaymentOption(
                    scheme="exact",
                    pay_to=TPP_RECEIVE_ADDRESS,
                    price=PRICE,
                    network=EVM_NETWORK,
                )
            ],
            mime_type="application/json",
            description="Paid dummy API service for x402 demonstration.",
        )
    }

    provider_app.add_middleware(
        PaymentMiddlewareASGI,
        routes=routes,
        server=resource_server,
    )

    @provider_app.get("/")
    async def root() -> dict[str, Any]:
        return {
            "role": "third-party provider / TPP",
            "service": "dummy paid API",
            "protected_endpoint": PROTECTED_PATH,
            "price": PRICE,
            "network": EVM_NETWORK,
            "pay_to": TPP_RECEIVE_ADDRESS,
            "facilitator": FACILITATOR_URL,
            "demo_note": (
                "This is the provider side. The protected route returns "
                "HTTP 402 unless paid via x402."
            ),
        }

    @provider_app.get(PROTECTED_PATH)
    async def dummy_service() -> dict[str, Any]:
        return {
            "service_received": True,
            "service_name": "Dummy Third-Party API",
            "message": (
                "The buyer agent has paid through x402. "
                "This is the protected service response."
            ),
            "payload": {
                "example_result": "42",
                "note": (
                    "This endpoint intentionally leads nowhere beyond this "
                    "dummy response."
                ),
            },
        }

    return provider_app


# This global variable is required by:
# python -m uvicorn x402_tpp_server:app --host 127.0.0.1 --port 4021
app = create_app()
