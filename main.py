from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse
import db_utilities
app = FastAPI()

@app.post("/")
async def handle_request(request: Request):
    payload = await request.json()
    intent = payload["queryResult"]["intent"]["displayName"]
    parameters = payload["queryResult"]["parameters"]
    output_contexts = payload["queryResult"]["outputContexts"]

    intent_handler = {
        "order_track - context: ongoing-tracking": track_order,
        "order_add - context: ongoing-order": add_order,
       # "order_remove - context: ongoing-order": remove_order,
       # "order_complete - context: ongoing-order": complete_order	
    }

    return intent_handler[intent](parameters)
        
def add_order(parameters: dict):

    items = parameters["food_item"]
    quantity = [int(quan) for quan in parameters["number"]]

    if len(items) != len(quantity):
        fullfillment_text = "Sorry, I didn't get that. Please specify the quantity for each item."
    else:
        fullfillment_text = f"Received order for {', '.join([f'{quantity[i]} {items[i]}' for i in range(len(items))])}."
    return JSONResponse(
            content={
                "fulfillmentText": fullfillment_text
            }
        )
def track_order(parameters: dict):
    order_id  = str(int(parameters["order_id"]))
    status = db_utilities.get_order_status(order_id)
    
    if status:
        fulfillment_text = f"The order status for order id {order_id} is {status}."
    else:
        fulfillment_text = f"Order id {order_id} not found."

    return JSONResponse(
            content={
                "fulfillmentText": fulfillment_text
            }
        )