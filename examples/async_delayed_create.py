import asyncio
import time
import os
from dotenv import load_dotenv

from trbinance import AsyncClient

load_dotenv()

api_key = os.getenv("API_KEY","")
secret_key = os.getenv("SECRET_KEY","")


async def delayed_create_order(client, symbol, side, order_type, quantity, price, delay):
    await asyncio.sleep(delay)
    return await client.create_order(symbol, side, order_type, quantity=quantity, price=price)


async def main():
    async_client = AsyncClient(api_key, secret_key)

    start = time.time()
    symbol = "ARB/TRY"
    side = "SELL"
    order_type = "LIMIT"
    quantity = "2"
    price = "35"

    # Step 1: Create 3 orders together and check their order ids.
    tasks = [
        asyncio.create_task(async_client.create_order(symbol, side, order_type, quantity=quantity, price=price))
    ]
    orders = await asyncio.gather(*tasks)
    order_id = orders[0]["orderId"]
    print("First order:", orders[0])

    tasks = [
        asyncio.create_task(async_client.cancel_order(orderId=order_id)),
        asyncio.create_task(delayed_create_order(async_client, symbol, side, order_type, quantity=quantity, price=price, delay=0.03))
    ]

    results = await asyncio.gather(*tasks) 

    cancelled_order = results[0]
    recreate_order = results[1]
    

    print("Cancelled order:", cancelled_order)
    print("Recreate order:", recreate_order)
    

asyncio.run(main())