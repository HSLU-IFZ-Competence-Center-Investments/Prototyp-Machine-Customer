# Blockchain-based Prototype

This repository contains a blockchain-based prototype for testing how autonomous machine customers can consume and provide paid digital services. The prototype is based on the **x402 payment pattern**, where payment requirements are embedded directly into the HTTP request-response cycle using `402 Payment Required`.

The prototype does not assume that all future machine-customer interactions must run on public blockchains. Instead, blockchain-based settlement is used as an experimental environment to test autonomous machine-to-machine payments, programmable settlement, and cryptographically verifiable execution.

The repository demonstrates two related prototype perspectives:

1. **Buyer-side prototype**  
   An autonomous agent consumes a paid LLM service. The agent receives an x402 payment challenge, signs the payment payload with its own wallet, retries the request with the payment information, and receives the LLM response after successful payment handling.

2. **Provider-side prototype**  
   A service provider exposes a payment-protected API endpoint. The provider returns a `402 Payment Required` response, verifies and settles the payment through a facilitator, and releases the protected API service only after the payment condition has been satisfied.

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

~~~mermaid
flowchart LR

    %% --------------------------------------------------
    %% STYLES
    %% --------------------------------------------------
    classDef box fill:#ffffff,stroke:#333,stroke-width:1px,rx:8px,ry:8px;
    classDef note fill:#f7f7f7,stroke:#777,stroke-width:1px,rx:6px,ry:6px;
    classDef group fill:#ffffff,stroke:#999,stroke-width:1px,stroke-dasharray: 4 3;

    %% --------------------------------------------------
    %% BUYER SIDE
    %% --------------------------------------------------
    subgraph Buyer["Buyer side / autonomous agent"]
        Agent["**Autonomous AI agent / orchestrator**<br/><br/><i>Prototype scope: internal reasoning omitted</i><br/><br/>• decides it needs LLM inference<br/>• calls a paid HTTP endpoint<br/>• handles 402 challenge automatically"]
        Wallet["**Agent wallet**<br/><br/>EOA / programmatic wallet<br/>funded with **USDC on Base**<br/>signs x402 payment payload locally"]
    end

    %% --------------------------------------------------
    %% PROVIDER SIDE
    %% --------------------------------------------------
    subgraph Provider["LLM service provider"]
        BlockRun["**LLM provider:**<br/>BlockRun<br/><br/>**Paid endpoint:**<br/>POST https://blockrun.ai/api/v1/chat/completions<br/><br/>**Example model ID:**<br/>openai/gpt-oss-20b<br/><br/>Acts as x402-paid gateway / router for LLM inference"]
        Gateway["**Resource server logic**<br/><br/>• returns 402 Payment Required<br/>• includes PAYMENT-REQUIRED<br/>• validates payment via facilitator<br/>• settles payment<br/>• then serves the LLM result"]
        Upstream["**Upstream model vendors**<br/><br/>OpenAI / Anthropic / Google / others<br/>selected by provider routing logic"]
    end

    %% --------------------------------------------------
    %% FACILITATOR AND SETTLEMENT
    %% --------------------------------------------------
    subgraph Settlement["Verification and on-chain settlement"]
        Facilitator["**x402 facilitator**<br/><br/>https://api.cdp.coinbase.com/platform/v2/x402<br/><br/>**Core protocol endpoints:**<br/>• POST /verify<br/>• POST /settle<br/><br/>Optionally exposes discovery APIs"]
        Base["**Base blockchain settlement layer**<br/><br/>**Network:** eip155:8453<br/>**Asset:** USDC<br/>**USDC contract:**<br/>0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"]
    end

    %% --------------------------------------------------
    %% OPTIONAL DISCOVERY
    %% --------------------------------------------------
    Discovery["**Optional service discovery**<br/><br/>GET /discovery/resources<br/><br/>Agent queries the x402 Bazaar for available payable LLM/API services, for example BlockRun, then selects one provider endpoint."]

    %% --------------------------------------------------
    %% NOTES
    %% --------------------------------------------------
    PaymentRequired["**Typical PAYMENT-REQUIRED contents**<br/><br/>• scheme = exact<br/>• network = eip155:8453<br/>• asset = USDC on Base<br/>• amount<br/>• payTo<br/>• maxTimeoutSeconds"]

    Interpretation["**Prototype interpretation**<br/><br/>The figure suppresses internal planning/tool logic and highlights only:<br/><br/>request → 402 challenge → sign → verify → settle → response"]

    %% --------------------------------------------------
    %% NUMBERED FLOW
    %% --------------------------------------------------
    Agent -->|"1"| BlockRun
    BlockRun -->|"2"| Agent
    Agent -->|"3"| Wallet
    Wallet -->|"4"| Gateway
    Gateway -->|"5"| Facilitator
    Facilitator -->|"6"| Gateway
    Gateway -->|"7"| Facilitator
    Facilitator -->|"8"| Base
    Gateway -->|"9"| Upstream
    Upstream -->|"10"| Agent

    %% Optional discovery path
    Agent -.-> Discovery
    Discovery -.-> Facilitator

    %% Notes
    Wallet -.-> PaymentRequired
    Base -.-> Interpretation

    %% Classes
    class Agent,Wallet,BlockRun,Gateway,Upstream,Facilitator,Base box;
    class Discovery,PaymentRequired,Interpretation note;
~~~

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

~~~mermaid
sequenceDiagram
    autonumber

    participant Client as Customer / Machine Agent
    participant Provider as Service Provider API
    participant X402 as x402 Payment Layer
    participant Settlement as Facilitator and Blockchain Settlement
    participant Service as Protected API Service

    Client->>Provider: API request
    Provider->>X402: Payment check
    X402-->>Client: 402 Payment Required
    Client->>X402: Paid retry with payment payload
    X402->>Settlement: Verify and settle payment
    Settlement-->>X402: Payment confirmed
    X402->>Provider: Unlock protected service
    Provider->>Service: Execute service logic
    Service-->>Provider: Service result
    Provider-->>Client: Service response
~~~

**Figure: Provider-side view of x402 as an additional payment layer in the API value chain.**  
The figure shows how a service provider can expose a payment-protected API service, issue a `402 Payment Required` response, verify and settle the payment, and release the protected service only after the payment condition has been satisfied.

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

## Interpretation

The buyer-side prototype shows how an autonomous agent can execute payments and consume an LLM service without direct human interaction. The provider-side prototype shows how a service provider can make an API service monetizable, machine-consumable, and conditionally accessible through programmable payments.

Together, the prototypes demonstrate a minimal machine-commerce interaction:

- one autonomous buyer agent
- one payment-protected API service
- one machine-readable payment condition
- one cryptographically signed payment payload
- one facilitator-based verification and settlement process
- one blockchain-based settlement path

The prototype therefore illustrates how x402 can support real-time, pay-per-use API consumption by autonomous machine customers.

⚠️ Disclaimer

Included concepts, models, data, software elements, or recommendations are intended solely for research, demonstration, or illustrative purposes. They are not meant for productive use, system integration, or operational implementation and do not constitute any statement regarding regulatory compliance. Use in operational or regulatory-relevant contexts occurs outside the responsibility of the IFZ.
