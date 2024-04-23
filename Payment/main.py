from fastapi import FastAPI
from fastapi.background import BackgroundTasks
from redis_om import get_redis_connection, HashModel
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
import requests, time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ['http://localhost:3000'],
    allow_methods = ['*'],
    allow_headers = ['*']
)

# This should be a different database
redis = get_redis_connection(
    host="redis-14215.c15.us-east-1-4.ec2.cloud.redislabs.com",
    port=14215,
    password = "vss9C1FaqVYmZAVeUUfFlqy3vFJENvZO",
    decode_responses = True
)


class Order(HashModel):
    product_id : str
    price : float
    fee : float
    total : float
    quantity : int
    status : str # Pending, Completed, Refunded

    class Meta:
        database = redis

@app.get("/orders/{pk}")
def getOrder(pk: str):
    return Order.get(pk=pk)

@app.post('/orders')
async def create(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    req = requests.get('http://localhost:8000/products/%s' % body['id'])
    product = req.json()

    order = Order(
        product_id = body['id'],
        price = product['price'],
        fee = product['price'] * 0.20,
        total = product['price'] + (product['price'] * 0.20),
        quantity = body['quantity'],
        status = 'pending'
    )
    order.save()

    background_tasks.add_task(order_completed, order)
    # order_completed(order) 
    return order

def order_completed(order: Order):
    time.sleep(2)
    order.status = 'Completed'
    order.save()
    redis.xadd('order_completed', order.dict(), '*')



