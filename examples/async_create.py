import asyncio
import time
import os
from dotenv import load_dotenv

from trbinance import AsyncClient

load_dotenv()

api_key = os.getenv("API_KEY","")
secret_key = os.getenv("SECRET_KEY","")

async def main():
    async_client = AsyncClient(api_key, secret_key)

    start = time.time()
    symbol = "BTC/USDT"
    side = "BUY"
    order_type = "LIMIT"
    quantity = 0.001
    price = 20000

    # Step 1: Create 3 orders together and check their order ids.
    tasks = [
        asyncio.create_task(async_client.create_order(symbol, side, order_type, quantity=quantity, price=price+i*100)) for i in range(3)
    ]
    orders = await asyncio.gather(*tasks)
    order_ids = [order["orderId"] for order in orders]
    print("Created orders:", order_ids)

    # Step 2: Cancel all of them and at the same time get account information and get all open orders.
    tasks = [
        asyncio.create_task(async_client.cancel_order(order_id)) for order_id in order_ids
    ]
    tasks.append(asyncio.create_task(async_client.account_information()))
    tasks.append(asyncio.create_task(async_client.all_orders(symbol=symbol)))
    results = await asyncio.gather(*tasks)

    cancelled_orders = results[:3]
    account_info = results[3]
    all_orders = results[4]

    print("Cancelled orders:", [order["orderId"] for order in cancelled_orders])
    print("Account information:", account_info)
    print("All open orders:", [order["orderId"] for order in all_orders if order["status"] == "OPEN"])
    end = time.time()
    print("Time elapsed:", end-start)

asyncio.run(main())