from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse,HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import db_utilities
import utilities

app = FastAPI(root_path="/RestaurantChatBot")
app.mount("/static",StaticFiles(directory="static"),name="static")
templates = Jinja2Templates(directory="templates")
ongoing_orders = {}

@app.get("/",response_class=HTMLResponse)
async def index(request:Request):
    return templates.TemplateResponse("index.html",{"request":request})

@app.post("/")
async def handle_request(request: Request):
    payload = await request.json()
    intent = payload["queryResult"]["intent"]["displayName"]
    parameters = payload["queryResult"]["parameters"]
    output_contexts = payload["queryResult"]["outputContexts"]
    session_id = utilities.get_session_id(output_contexts[0]["name"])
    

    intent_handler = {
        "order_track - context: ongoing-tracking": track_order,
        "order_add - context: ongoing-order": add_order,
        "order_remove - context: ongoing-order": remove_order,
        "order_complete - context: ongoing-order": complete_order,
        "order_new": new_order,
    }

    return intent_handler[intent](parameters,session_id)

def new_order(parameters: dict, session_id: str):
    if session_id in ongoing_orders:
        ongoing_orders[session_id] = dict()

def remove_order(parameters: dict, session_id: str):
    if session_id not in ongoing_orders:
        fulfillment_text = "I'm having trouble finding your order. Sorry! Can you please place a new order"
    else:
        food_items = ongoing_orders[session_id]
        items_to_remove = parameters["food_item"]
        removed_items = {item: food_items.pop(item) for item in items_to_remove if item in food_items}
        missing_items = [item for item in items_to_remove if item not in removed_items]
        ongoing_orders[session_id] = food_items  
      
        removed_str = ", ".join(removed_items.keys())
        missing_str = ", ".join(missing_items)
        remaining_str = ", ".join(f"{v} {k}" for k, v in food_items.items())
        
        message = []
        if removed_str:
            message.append(f"{removed_str} {'is' if len(removed_items) == 1 else 'are'} removed from the order.")
        if missing_str:
            message.append(f"{missing_str} {'is' if len(missing_items) == 1 else 'are'} not present in your order.")
        if remaining_str:
            message.append(f"Now your order contains {remaining_str}.")
        else:
            message.append("Your order is now empty.")

        fulfillment_text = " ".join(message)

    return JSONResponse(
        content = {
            "fulfillmentText": fulfillment_text
        })



def add_order(parameters: dict,session_id: str):

    items = parameters["food_item"]
    quantity = [int(quan) for quan in parameters["number"]]

    if len(items) != len(quantity):
        fulfillment_text = "Sorry, I didn't get that. Please specify the quantity for each item."
    else:
        order = dict(zip(items,quantity))

        if session_id not in ongoing_orders:
            ongoing_orders[session_id] = order
        else:
            ongoing_orders[session_id].update(order)

        fulfillment_text = f"You have ordered: {', '.join([f'{value} {key}' for key,value in ongoing_orders[session_id].items()])}. Anything else?"
    
    return JSONResponse(
            content={
                "fulfillmentText": fulfillment_text
            }
        )
def track_order(parameters: dict,session_id: str):
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

def complete_order(parameters: dict,session_id: str):
    if session_id not in ongoing_orders:
        fulfillment_text = "Sorry! I'm having trouble finding your order. Can you please place a new order?"
    else:
        fulfillment_text = db_utilities.save_order_details(ongoing_orders[session_id])
        del ongoing_orders[session_id]

    return JSONResponse(
        content = {"fulfillmentText": fulfillment_text}
    )