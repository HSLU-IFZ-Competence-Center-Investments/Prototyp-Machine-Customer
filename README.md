# x402 Prototype for Autonomous Machine-Customer Payments

This repository contains a blockchain-based prototype for testing how autonomous machine customers can consume paid digital services and how service providers can expose payment-gated API services. The prototype is based on the **x402 payment pattern**, where payment requirements are embedded directly into the HTTP request-response cycle using `402 Payment Required`.

The prototype does not assume that all future machine-customer interactions must run on public blockchains. Instead, blockchain-based settlement is used as an experimental environment to test autonomous machine-to-machine payments, programmable settlement, and cryptographically verifiable execution.

The repository demonstrates two related prototype perspectives:

1. **Buyer-side prototype**  
   An autonomous agent consumes a paid LLM service. The agent receives an x402 payment challenge, signs the payment payload with its own wallet, retries the request with the payment information, and receives the LLM response after successful payment handling.

2. **Provider-side prototype**  
   A local FastAPI service provider exposes a payment-protected dummy API endpoint. The provider returns a `402 Payment Required` response, verifies and settles the payment through a facilitator, and releases the protected dummy service only after the payment condition has been satisfied.

Together, the two prototypes illustrate how x402 can connect autonomous service consumption with programmable API monetization.

---

## Prototype Overview

The prototype focuses on the following architectural capabilities:

- machine-readable service consumption
- non-interactive authentication through wallet-based signatures
- real-time payment execution
- programmable payment handling
- verifiable settlement
- payment-gated API access
- auditability of autonomous machine interactions

---

## Buyer-side Prototype: Autonomous Agent Paying for LLM Inference

The buyer-side prototype tests whether an autonomous agent can technically act as a machine customer. The agent calls a paid LLM endpoint, receives a payment challenge, signs the x402 payment payload with its own wallet, and retries the request with the required payment information.

<img width="879" height="726" alt="Screenshot 2026-05-06 092420" src="https://github.com/user-attachments/assets/fc31cca1-b37a-498f-91ba-91aa6368bab2" />

**Figure: Buyer-side blockchain-based prototype using x402 and USDC on Base.**  
The figure shows how an autonomous agent requests paid LLM inference, receives an x402 payment challenge, signs the payment payload with its own wallet, verifies and settles the payment through a facilitator, and receives the LLM response after successful payment handling.

### Numbered Flow

1. The autonomous agent initiates an inference request to the paid LLM endpoint.
2. The provider returns an HTTP `402 Payment Required` response containing the quoted amount and payment parameters.
3. The agent interprets the challenge and uses its programmatic wallet to sign the x402 payment payload locally.
4. The agent retries the original request and attaches the signed payment payload.
5. The provider submits the payment information to the facilitator for verification.
6. The facilitator returns the verification result and associated payer metadata.
7. The provider initiates settlement through the facilitator.
8. The facilitator submits the USDC transfer authorization to the Base blockchain and waits for confirmation.
9. After successful verification and settlement, the provider forwards the request to the selected upstream LLM backend.
10. The provider returns the requested LLM output to the autonomous agent.

### Buyer-side Test Example

In the testnet setup, the autonomous agent used a funded wallet on the **Base Sepolia test network** to call a paid LLM endpoint via x402.

| Item | Value |
|---|---|
| Network | Base Sepolia |
| Model | `openai/gpt-oss-20b` |
| Prompt | `Hello!` |
| Response | `Hello! How can I help you today?` |
| Wallet balance before execution | `19.996` USDC |
| Wallet balance after execution | `19.995` USDC |
| Approximate cost | `0.001` USDC |

The balance decrease after the LLM request indicates that the agent received the LLM response while the x402 payment was executed automatically in the background.

This demonstrates the basic logic of an autonomous machine customer: a software agent identifies a service need, receives a machine-readable price and payment condition, authorizes the payment cryptographically, and consumes the digital service without direct human intervention.

---

## Provider-side Prototype: Payment-gated API Service

The provider-side prototype demonstrates the opposite perspective. Instead of only consuming a paid service, the prototype also shows how a service provider can expose a machine-consumable API endpoint and protect it with an x402 payment layer.

The provider receives an API request, checks whether payment is required, returns a `402 Payment Required` response, processes a paid retry, verifies and settles the payment, and only then releases the protected service.

<img width="883" height="596" alt="Screenshot 2026-05-06 093631" src="https://github.com/user-attachments/assets/1e1c7bb1-2c32-4551-a3dc-c947d0186ebf" />

**Figure: Provider-side view of x402 as an additional payment layer in the API value chain.**  
The figure shows how a service provider can expose a payment-protected API service, issue a `402 Payment Required` response, verify and settle the payment, and release the protected service only after the payment condition has been satisfied.

### Numbered Flow

1. The buyer-side client first inspects the local provider server at `localhost:4021`.
2. The local FastAPI provider returns basic service metadata, including the protected endpoint, price, network, receiving address, and facilitator configuration.
3. The buyer client sends an unpaid request to the protected endpoint `/api/v1/dummy-service`.
4. The x402 middleware blocks the unpaid request and returns `402 Payment Required` with the required payment challenge.
5. The buyer client uses the buyer wallet loaded from the local environment to sign the x402 payment payload.
6. The buyer client retries the protected API request with the signed payment payload attached.
7. The provider-side x402 middleware sends the payment information to the x402 facilitator for verification.
8. The facilitator returns the payment verification and settlement result to the provider-side middleware.
9. The facilitator coordinates settlement on the Base Sepolia test network using USDC.
10. After successful payment handling, the middleware unlocks the protected dummy service.
11. The protected service returns the paid JSON response to the buyer client.

### Simplified `402 Payment Required` Example

~~~json
{
  "error": "payment_required",
  "accepts": [
    {
      "scheme": "exact",
      "network": "eip155:84532",
      "asset": "USDC",
      "price": "$0.001",
      "payTo": "0xServiceProvider...",
      "resource": "/api/v1/dummy-service",
      "timeout": 60
    }
  ]
}
~~~

### Simplified Paid Retry Example

~~~json
{
  "request": {
    "method": "GET",
    "path": "/api/v1/dummy-service"
  },
  "payment": {
    "scheme": "exact",
    "network": "eip155:84532",
    "asset": "USDC",
    "price": "$0.001",
    "from": "0xAgent...",
    "to": "0xServiceProvider...",
    "sig": "0xabc..."
  }
}
~~~

### Simplified Facilitator Metadata Example

~~~json
{
  "valid": true,
  "settled": true,
  "network": "eip155:84532",
  "asset": "USDC",
  "price": "$0.001",
  "to": "0xServiceProvider...",
  "tx": "0x789..."
}
~~~

### Simplified Interaction Record

~~~json
{
  "route": "/api/v1/dummy-service",
  "status": "served",
  "price": "$0.001",
  "payer": "0xAgent...",
  "payTo": "0xServiceProvider...",
  "tx": "0x789...",
  "response": 200
}
~~~

---

## How to Run the Prototype

### Prerequisites

The prototype requires:

- Python 3.10 or newer
- a local `.env` file
- a funded test wallet on Base Sepolia
- test USDC on Base Sepolia
- internet access for facilitator and blockchain interactions

Install the required Python dependencies:

~~~bash
pip install fastapi uvicorn python-dotenv requests eth-account x402 blockrun-llm
~~~

Depending on the notebook, not all dependencies are required at the same time. The two-sided provider demo mainly uses `fastapi`, `uvicorn`, `requests`, `eth-account`, `python-dotenv`, and `x402`. The BlockRun LLM examples additionally use `blockrun-llm`.

---

### Environment Variables

Create a `.env` file in the same folder as the notebooks.

For the two-sided x402 provider demo and the BlockRun testnet example:

~~~env
PRIVATE_KEY=0xYOUR_TESTNET_BUYER_WALLET_PRIVATE_KEY
TPP_RECEIVE_ADDRESS=0xYOUR_PROVIDER_RECEIVING_ADDRESS
~~~

For the BlockRun mainnet example:

~~~env
BLOCKRUN_WALLET_KEY=0xYOUR_MAINNET_WALLET_PRIVATE_KEY
~~~

Do not commit the `.env` file to GitHub.

The `.env` file should be listed in `.gitignore`:

~~~gitignore
.env
~~~

---

## Running the Buyer-side LLM Prototype

The buyer-side LLM prototype is implemented in the following notebooks:

- `testnet.ipynb`
- `mainnet.ipynb`

### Testnet version

Use `testnet.ipynb` for the Base Sepolia testnet version.

The notebook:

1. loads the buyer wallet private key from `.env`,
2. initializes the BlockRun testnet client,
3. checks the wallet balance before execution,
4. sends a paid LLM request,
5. receives the model response,
6. checks the wallet balance after execution,
7. calculates the approximate payment cost.

The buyer wallet must hold test USDC on Base Sepolia before running the notebook.

### Mainnet version

Use `mainnet.ipynb` only with caution. It uses real funds on Base mainnet.

The wallet must hold:

- ETH on Base for gas
- USDC on Base for API payments

---

## Running the Two-sided x402 Provider Demo

The two-sided x402 provider demo is implemented in:

- `x402_two_sided_demo_notebook_existing_env.ipynb`

This demo starts a local FastAPI provider and protects a dummy API endpoint with x402 payment middleware.

### Step 1: Start the local provider server

The notebook writes the provider server to:

~~~text
x402_tpp_server.py
~~~

Before starting the server, run the notebook cell that writes `x402_tpp_server.py`, or include the generated `x402_tpp_server.py` file directly in the repository.

Start the server from a terminal:

~~~bash
python -m uvicorn x402_tpp_server:app --host 127.0.0.1 --port 4021
~~~

Leave this terminal running.

### Step 2: Run the notebook client

In the notebook, run the client-side cells after the provider server is running.

The notebook will:

1. inspect the local provider at `localhost:4021`,
2. call the protected endpoint without payment,
3. receive `402 Payment Required`,
4. sign the payment payload with the buyer wallet,
5. retry the request with payment attached,
6. verify and settle the payment through the facilitator,
7. receive the protected dummy JSON response.

The protected endpoint is:

~~~text
GET /api/v1/dummy-service
~~~

The demo price is:

~~~text
$0.001
~~~

The test network is:

~~~text
Base Sepolia / eip155:84532
~~~

---

## Interpretation

The buyer-side prototype shows how an autonomous agent can execute payments and consume an LLM service without direct human interaction. The provider-side prototype shows how a local FastAPI service provider can make a dummy API service monetizable, machine-consumable, and conditionally accessible through programmable payments.

Together, the prototypes demonstrate a minimal machine-commerce interaction:

- one autonomous buyer agent
- one payment-protected API service
- one machine-readable payment condition
- one cryptographically signed payment payload
- one facilitator-based verification and settlement process
- one blockchain-based settlement path

The prototype therefore illustrates how x402 can support real-time, pay-per-use API consumption by autonomous machine customers.

---

## ⚠️ Disclaimer

Any concepts, models, data, software elements, or recommendations included are provided solely for research, demonstration, or illustrative purposes. They are not intended for production use, system integration, or operational implementation and do not constitute any representation regarding regulatory compliance. Any use in operational or regulatory-relevant contexts is outside the scope of responsibility of the IFZ.
