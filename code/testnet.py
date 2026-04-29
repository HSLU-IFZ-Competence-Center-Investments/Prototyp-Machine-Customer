from blockrun_llm import LLMClient
from blockrun_llm import testnet_client
from eth_account import Account

from dotenv import load_dotenv
import os

load_dotenv()
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

# Select Base Sepolia from the network dropdown, paste your wallet address, and request USDC.
# https://faucet.circle.com 

# acct = Account.create()
# print(acct.address)
# print(acct.key.hex())
address = "0xe434ce93D0c05c22e3ff3eec406c9F18DBF3CB81"

client = testnet_client(private_key=PRIVATE_KEY)  # Uses BLOCKRUN_WALLET_KEY
print(client.get_balance())
print(client.api_url)

response = client.chat("openai/gpt-oss-20b", "Hello!")
print(response)
