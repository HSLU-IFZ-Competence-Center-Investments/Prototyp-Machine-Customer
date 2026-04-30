"""
x402_streamlit_dashboard.py

Streamlit dashboard for the x402 two-sided demo.

Run in Terminal 2 after starting x402_tpp_server.py:
    python -m streamlit run x402_streamlit_dashboard.py

.env in same folder:
    PRIVATE_KEY=0xYOUR_BUYER_PRIVATE_KEY
    TPP_RECEIVE_ADDRESS=0xYOUR_TPP_RECEIVING_ADDRESS

The buyer wallet needs test USDC on Base Sepolia.
"""

import base64
import json
import os
import re
from typing import Any

import requests
import streamlit as st
from dotenv import load_dotenv
from eth_account import Account

from x402 import x402ClientSync
from x402.http import x402HTTPClientSync
from x402.http.clients import x402_requests
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact.register import register_exact_evm_client


load_dotenv()

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
TPP_RECEIVE_ADDRESS = os.getenv("TPP_RECEIVE_ADDRESS")

HOST = "127.0.0.1"
PORT = 4021
PROTECTED_PATH = "/api/v1/dummy-service"

TPP_ROOT_URL = f"http://{HOST}:{PORT}/"
TPP_URL = f"http://{HOST}:{PORT}{PROTECTED_PATH}"

EVM_NETWORK = "eip155:84532"
PRICE = "$0.001"

BASE_SEPOLIA_TX_EXPLORER = "https://sepolia.basescan.org/tx/"
BASE_SEPOLIA_ADDRESS_EXPLORER = "https://sepolia.basescan.org/address/"


def decode_possible_base64_json(value: str) -> Any:
    if not value:
        return None

    try:
        padded = value + "=" * (-len(value) % 4)
        raw = base64.b64decode(padded)
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return value


def get_payment_headers(response: requests.Response) -> dict[str, Any]:
    result = {}

    for key, value in response.headers.items():
        if "payment" in key.lower() or "x402" in key.lower():
            result[key] = decode_possible_base64_json(value)

    return result


def response_body(response: requests.Response) -> Any:
    try:
        return response.json()
    except Exception:
        return response.text


def find_transaction_hash(obj: Any) -> str | None:
    tx_pattern = re.compile(r"^0x[a-fA-F0-9]{64}$")

    if obj is None:
        return None

    if isinstance(obj, str):
        value = obj.strip()
        if tx_pattern.match(value):
            return value
        return None

    # Support Pydantic v2 models
    if hasattr(obj, "model_dump"):
        try:
            return find_transaction_hash(obj.model_dump())
        except Exception:
            pass

    # Support Pydantic v1 models
    if hasattr(obj, "dict"):
        try:
            return find_transaction_hash(obj.dict())
        except Exception:
            pass

    # Support ordinary Python objects
    if hasattr(obj, "__dict__"):
        try:
            return find_transaction_hash(vars(obj))
        except Exception:
            pass

    if isinstance(obj, dict):
        preferred_keys = [
            "transaction",
            "txHash",
            "transactionHash",
            "transaction_hash",
            "settlementTxHash",
            "settlementTransactionHash",
            "hash",
        ]

        for key in preferred_keys:
            value = obj.get(key)
            found = find_transaction_hash(value)
            if found:
                return found

        for value in obj.values():
            found = find_transaction_hash(value)
            if found:
                return found

    if isinstance(obj, list):
        for item in obj:
            found = find_transaction_hash(item)
            if found:
                return found

    return None


def short_address(address: str) -> str:
    if not address or len(address) < 12:
        return address
    return f"{address[:6]}...{address[-4:]}"


def require_env() -> tuple[bool, str | None, Account | None]:
    if not PRIVATE_KEY:
        return False, "Missing PRIVATE_KEY in .env", None

    if not TPP_RECEIVE_ADDRESS:
        return False, "Missing TPP_RECEIVE_ADDRESS in .env", None

    try:
        buyer = Account.from_key(PRIVATE_KEY)
    except Exception as exc:
        return False, f"Invalid PRIVATE_KEY: {exc}", None

    if not TPP_RECEIVE_ADDRESS.startswith("0x"):
        return False, "TPP_RECEIVE_ADDRESS must start with 0x", None

    return True, None, buyer


def inspect_provider() -> dict[str, Any]:
    response = requests.get(TPP_ROOT_URL, timeout=20)

    return {
        "status_code": response.status_code,
        "body": response_body(response),
    }


def call_without_payment() -> dict[str, Any]:
    response = requests.get(TPP_URL, timeout=30)

    return {
        "status_code": response.status_code,
        "headers": get_payment_headers(response),
        "body": response_body(response),
    }


def call_with_payment(buyer: Account) -> dict[str, Any]:
    x402_client = x402ClientSync()
    signer = EthAccountSigner(buyer)

    register_exact_evm_client(x402_client, signer)

    http_client = x402HTTPClientSync(x402_client)

    with x402_requests(x402_client) as session:
        response = session.get(TPP_URL, timeout=90)

    payment_headers = get_payment_headers(response)

    try:
        parsed_payment_response = http_client.get_payment_settle_response(
            lambda name: response.headers.get(name)
        )
    except Exception:
        parsed_payment_response = payment_headers

    tx_hash = find_transaction_hash(parsed_payment_response)

    if not tx_hash:
        tx_hash = find_transaction_hash(dict(response.headers))

    if not tx_hash:
        tx_hash = find_transaction_hash(response_body(response))

    return {
        "status_code": response.status_code,
        "headers": payment_headers,
        "body": response_body(response),
        "payment_response": parsed_payment_response,
        "transaction_hash": tx_hash,
    }


st.set_page_config(
    page_title="x402 Two-Sided Demo",
    page_icon="💸",
    layout="wide",
)

ok, error, buyer = require_env()

st.title("x402 Two-Sided Demo")
st.caption("Buyer agent + third-party provider / TPP + dummy paid API endpoint")

if not ok:
    st.error(error)
    st.write("Create a .env file in the same folder as this app with:")
    st.code(
        "PRIVATE_KEY=0xYOUR_BUYER_PRIVATE_KEY\n"
        "TPP_RECEIVE_ADDRESS=0xYOUR_TPP_RECEIVING_ADDRESS",
        language="env",
    )
    st.stop()

with st.sidebar:
    st.header("Demo configuration")

    st.write("Network")
    st.code(EVM_NETWORK)

    st.write("Price")
    st.code(PRICE)

    st.write("TPP endpoint")
    st.code(TPP_URL)

    st.write("Buyer wallet")
    st.code(buyer.address)

    st.write("TPP receiving wallet")
    st.code(TPP_RECEIVE_ADDRESS)

    st.markdown("---")

    st.markdown(
        f"[Open buyer on Base Sepolia]"
        f"({BASE_SEPOLIA_ADDRESS_EXPLORER}{buyer.address})"
    )
    st.markdown(
        f"[Open TPP receiver on Base Sepolia]"
        f"({BASE_SEPOLIA_ADDRESS_EXPLORER}{TPP_RECEIVE_ADDRESS})"
    )

st.subheader("Demo setup")

col1, col2, col3 = st.columns(3)

with col1:
    st.info(
        f"""
**Buyer agent**

Wallet: `{short_address(buyer.address)}`

Signs the x402 payment payload.
"""
    )

with col2:
    st.warning(
        f"""
**Third-party provider**

Endpoint: `{PROTECTED_PATH}`

Returns `402 Payment Required` unless payment is attached.
"""
    )

with col3:
    st.success(
        f"""
**Settlement**

Network: `{EVM_NETWORK}`

Payment is verified and settled through the facilitator.
"""
    )

st.text(
    "Flow:\n"
    "Buyer agent -> TPP dummy endpoint -> 402 challenge\n"
    "Buyer agent -> signs x402 payment -> retries request\n"
    "TPP -> facilitator verification/settlement -> returns service response"
)

st.markdown("---")
st.subheader("Step 0 — Check that the provider server is running")

st.write("Start the provider in a separate terminal first:")
st.code(
    "python -m uvicorn x402_tpp_server:app --host 127.0.0.1 --port 4021",
    language="powershell",
)

if st.button("Check provider connection", type="secondary"):
    with st.spinner("Checking provider..."):
        try:
            st.session_state["provider_status"] = inspect_provider()
        except Exception as exc:
            st.session_state["provider_status"] = {
                "error": repr(exc)
            }

if "provider_status" in st.session_state:
    provider_status = st.session_state["provider_status"]

    if "error" in provider_status:
        st.error(provider_status["error"])
        st.warning("The TPP server is probably not running. Start it in Terminal 1 first.")
    else:
        st.success("Provider server is reachable.")
        st.write("HTTP status:", provider_status["status_code"])
        st.json(provider_status["body"])

st.markdown("---")
st.subheader("Step 1 — Call the API without payment")

st.write(
    "This simulates a normal HTTP client calling the protected endpoint. "
    "The expected result is HTTP 402 Payment Required."
)

if st.button("Call without payment", type="secondary"):
    with st.spinner("Calling protected endpoint without payment..."):
        try:
            st.session_state["unpaid_result"] = call_without_payment()
        except Exception as exc:
            st.session_state["unpaid_result"] = {
                "error": repr(exc)
            }

if "unpaid_result" in st.session_state:
    result = st.session_state["unpaid_result"]

    if "error" in result:
        st.error(result["error"])
    else:
        if result["status_code"] == 402:
            st.success("The provider correctly returned HTTP 402 Payment Required.")
        else:
            st.warning(f"Unexpected status code: {result['status_code']}")

        unpaid_left, unpaid_right = st.columns(2)

        with unpaid_left:
            st.write("HTTP status")
            st.code(result["status_code"])

            st.write("Response body")
            st.json(result["body"])

        with unpaid_right:
            st.write("Payment challenge headers")
            if result["headers"]:
                st.json(result["headers"])
            else:
                st.write("No payment-related headers found.")

st.markdown("---")
st.subheader("Step 2 — Manual authorization on behalf of the buyer agent")

st.write(
    "For the live demonstration, the human presenter explicitly authorizes the "
    "buyer agent. After clicking the button, the agent signs the x402 payment "
    "payload and retries the request."
)

auth_col1, auth_col2, auth_col3 = st.columns(3)

with auth_col1:
    st.metric("Price", PRICE)

with auth_col2:
    st.metric("Network", EVM_NETWORK)

with auth_col3:
    st.metric("Endpoint", PROTECTED_PATH)

st.write("Payment recipient")
st.code(TPP_RECEIVE_ADDRESS)

if st.button("Authorize agent payment", type="primary"):
    with st.spinner("Agent is signing payment payload and calling the TPP..."):
        try:
            st.session_state["paid_result"] = call_with_payment(buyer)
        except Exception as exc:
            st.session_state["paid_result"] = {
                "error": repr(exc)
            }

st.markdown("---")
st.subheader("Step 3 — Service received after payment")

if "paid_result" not in st.session_state:
    st.info("Authorize the payment above to show the paid service response.")
else:
    result = st.session_state["paid_result"]

    if "error" in result:
        st.error(result["error"])
    else:
        if result["status_code"] == 200:
            st.success("Payment accepted. The protected service response was returned.")
        else:
            st.error(f"Paid request failed with HTTP status {result['status_code']}.")

        paid_left, paid_right = st.columns(2)

        with paid_left:
            st.write("HTTP status")
            st.code(result["status_code"])

            st.write("Service response")
            try:
                st.json(result["body"])
            except Exception:
                st.write(result["body"])

        with paid_right:
            st.write("Payment response / settlement metadata")
            if result["payment_response"]:
                try:
                    st.json(result["payment_response"])
                except Exception:
                    st.write(result["payment_response"])
            else:
                st.write("No parsed payment response available.")

            st.write("Payment-related headers")
            if result["headers"]:
                st.json(result["headers"])
            else:
                st.write("No payment-related headers found.")

st.markdown("---")
st.subheader("Step 4 — Testnet evidence")

if "paid_result" not in st.session_state:
    st.info("No paid transaction yet.")
else:
    result = st.session_state["paid_result"]

    if "error" in result:
        st.error("No transaction evidence because the paid request failed.")
    else:
        tx_hash = result.get("transaction_hash")

        if tx_hash:
            st.success("Transaction hash found.")
            st.code(tx_hash)
            st.markdown(
                f"Open transaction on Base Sepolia BaseScan: "
                f"{BASE_SEPOLIA_TX_EXPLORER}{tx_hash}"
            )
        else:
            st.warning(
                "No transaction hash was exposed by the SDK/facilitator response. "
                "You can still inspect the buyer and receiver addresses on Base Sepolia."
            )

            st.markdown(
                f"Open buyer address: "
                f"{BASE_SEPOLIA_ADDRESS_EXPLORER}{buyer.address}"
            )
            st.markdown(
                f"Open TPP receiving address: "
                f"{BASE_SEPOLIA_ADDRESS_EXPLORER}{TPP_RECEIVE_ADDRESS}"
            )

st.markdown("---")
st.subheader("Narrative for the audience")

st.markdown(
    """
1. The TPP exposes a normal API endpoint, but wraps it with x402 payment middleware.
2. A first unpaid request receives HTTP 402 Payment Required.
3. The presenter authorizes the buyer agent to proceed.
4. The buyer agent signs the payment payload with its wallet.
5. The paid request is retried.
6. The TPP releases the protected dummy service response.
7. The payment can be inspected on Base Sepolia, either by transaction hash or by wallet address.
"""
)