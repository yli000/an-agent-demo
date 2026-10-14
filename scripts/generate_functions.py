# -*- coding: utf-8 -*-

"""

生成 CLINC150 数据集的 function.py 和 slot_intent.json

使用 LLM 为每个意图生成合适的 function call 定义

"""


import os

import json

import requests

import time


API_KEY = os.environ.get("API_KEY")

BASE_URL = os.environ.get("BASE_URL")


# CLINC150 意图分类及其描述

CLINC150_INTENTS = {

    # 银行与金融

    "accept_reservations": {"category": "restaurant", "desc": "Check if a restaurant accepts reservations", "slots": {}},

    "account_blocked": {"category": "banking", "desc": "Inquire about a blocked bank account", "slots": {}},

    "balance": {"category": "banking", "desc": "Check account balance", "slots": {"account_type": "Type of account (checking, savings, credit)"}},

    "bill_balance": {"category": "banking", "desc": "Check bill balance", "slots": {"bill_type": "Type of bill (credit card, utility, etc.)"}},

    "bill_due": {"category": "banking", "desc": "Check when a bill is due", "slots": {"bill_type": "Type of bill"}},

    "card_declined": {"category": "banking", "desc": "Inquire why a card was declined", "slots": {}},

    "credit_limit": {"category": "banking", "desc": "Check credit limit", "slots": {}},

    "credit_limit_change": {"category": "banking", "desc": "Request to change credit limit", "slots": {"amount": "New credit limit amount"}},

    "credit_score": {"category": "banking", "desc": "Check credit score", "slots": {}},

    "damaged_card": {"category": "banking", "desc": "Report a damaged card", "slots": {}},

    "direct_deposit": {"category": "banking", "desc": "Set up or inquire about direct deposit", "slots": {}},

    "expiration_date": {"category": "banking", "desc": "Check card expiration date", "slots": {}},

    "freeze_account": {"category": "banking", "desc": "Freeze a bank account", "slots": {"account_type": "Type of account to freeze"}},

    "improve_credit_score": {"category": "banking", "desc": "Get tips to improve credit score", "slots": {}},

    "interest_rate": {"category": "banking", "desc": "Check interest rate", "slots": {"account_type": "Type of account"}},

    "international_fees": {"category": "banking", "desc": "Inquire about international transaction fees", "slots": {}},

    "min_payment": {"category": "banking", "desc": "Check minimum payment due", "slots": {}},

    "new_card": {"category": "banking", "desc": "Request a new card", "slots": {}},

    "pay_bill": {"category": "banking", "desc": "Pay a bill", "slots": {"bill_type": "Type of bill", "amount": "Payment amount"}},

    "pin_change": {"category": "banking", "desc": "Change PIN number", "slots": {}},

    "redeem_rewards": {"category": "banking", "desc": "Redeem reward points", "slots": {"points": "Number of points to redeem"}},

    "replacement_card_duration": {"category": "banking", "desc": "Ask how long to get replacement card", "slots": {}},

    "report_fraud": {"category": "banking", "desc": "Report fraudulent activity", "slots": {}},

    "report_lost_card": {"category": "banking", "desc": "Report a lost card", "slots": {}},

    "rewards_balance": {"category": "banking", "desc": "Check rewards balance", "slots": {}},

    "routing": {"category": "banking", "desc": "Get routing number", "slots": {}},

    "spending_history": {"category": "banking", "desc": "View spending history", "slots": {"time_period": "Time period to view"}},

    "transactions": {"category": "banking", "desc": "View recent transactions", "slots": {"time_period": "Time period", "account_type": "Account type"}},

    "transfer": {"category": "banking", "desc": "Transfer money between accounts", "slots": {"amount": "Transfer amount", "from_account": "Source account", "to_account": "Destination account"}},


    # 出行

    "book_flight": {"category": "travel", "desc": "Book a flight", "slots": {"origin": "Departure city", "destination": "Arrival city", "date": "Travel date", "passengers": "Number of passengers"}},

    "book_hotel": {"category": "travel", "desc": "Book a hotel", "slots": {"location": "Hotel location", "check_in": "Check-in date", "check_out": "Check-out date", "guests": "Number of guests"}},

    "car_rental": {"category": "travel", "desc": "Rent a car", "slots": {"location": "Pickup location", "pickup_date": "Pickup date", "return_date": "Return date", "car_type": "Type of car"}},

    "carry_on": {"category": "travel", "desc": "Ask about carry-on luggage rules", "slots": {"airline": "Airline name"}},

    "flight_status": {"category": "travel", "desc": "Check flight status", "slots": {"flight_number": "Flight number", "date": "Flight date"}},

    "international_visa": {"category": "travel", "desc": "Inquire about visa requirements", "slots": {"country": "Destination country"}},

    "lost_luggage": {"category": "travel", "desc": "Report lost luggage", "slots": {"flight_number": "Flight number"}},

    "plug_type": {"category": "travel", "desc": "Ask about electrical plug type in a country", "slots": {"country": "Country name"}},

    "travel_alert": {"category": "travel", "desc": "Check travel alerts for a destination", "slots": {"destination": "Destination"}},

    "travel_notification": {"category": "travel", "desc": "Set travel notification for bank", "slots": {"destination": "Travel destination", "dates": "Travel dates"}},

    "travel_suggestion": {"category": "travel", "desc": "Get travel destination suggestions", "slots": {"preferences": "Travel preferences"}},

    "uber": {"category": "travel", "desc": "Request an Uber ride", "slots": {"destination": "Destination", "pickup": "Pickup location"}},

    "vaccines": {"category": "travel", "desc": "Ask about required vaccines for travel", "slots": {"country": "Destination country"}},


    # 日历与时间

    "alarm": {"category": "utility", "desc": "Set an alarm", "slots": {"time": "Alarm time", "label": "Alarm label", "recurrence": "Repeat pattern"}},

    "calendar": {"category": "utility", "desc": "View calendar", "slots": {"date": "Date to view"}},

    "calendar_update": {"category": "utility", "desc": "Update calendar event", "slots": {"event": "Event name", "date": "Event date", "time": "Event time", "location": "Event location"}},

    "date": {"category": "utility", "desc": "Ask about a date", "slots": {"query": "Date query"}},

    "meeting_schedule": {"category": "utility", "desc": "View meeting schedule", "slots": {"date": "Date to check"}},

    "next_holiday": {"category": "utility", "desc": "Ask about next holiday", "slots": {}},

    "reminder": {"category": "utility", "desc": "Set a reminder", "slots": {"content": "Reminder content", "time": "Reminder time"}},

    "reminder_update": {"category": "utility", "desc": "Update a reminder", "slots": {"reminder_id": "Reminder to update", "new_content": "New content", "new_time": "New time"}},

    "schedule_maintenance": {"category": "utility", "desc": "Schedule maintenance appointment", "slots": {"service_type": "Type of maintenance", "date": "Preferred date"}},

    "schedule_meeting": {"category": "utility", "desc": "Schedule a meeting", "slots": {"title": "Meeting title", "date": "Meeting date", "time": "Meeting time", "attendees": "Meeting attendees"}},

    "time": {"category": "utility", "desc": "Ask current time", "slots": {"location": "Location for time zone"}},

    "timer": {"category": "utility", "desc": "Set a timer", "slots": {"duration": "Timer duration", "label": "Timer label"}},

    "timezone": {"category": "utility", "desc": "Ask about timezone", "slots": {"location": "Location to check"}},


    # 导航与地点

    "current_location": {"category": "navigation", "desc": "Get current location", "slots": {}},

    "directions": {"category": "navigation", "desc": "Get directions", "slots": {"origin": "Starting point", "destination": "Destination", "mode": "Travel mode"}},

    "distance": {"category": "navigation", "desc": "Calculate distance", "slots": {"origin": "Starting point", "destination": "Destination"}},

    "gas": {"category": "navigation", "desc": "Find nearby gas stations", "slots": {"location": "Current location"}},

    "gas_type": {"category": "navigation", "desc": "Ask about gas type for vehicle", "slots": {"vehicle": "Vehicle model"}},

    "share_location": {"category": "navigation", "desc": "Share current location", "slots": {"recipient": "Person to share with"}},

    "traffic": {"category": "navigation", "desc": "Check traffic conditions", "slots": {"route": "Route to check"}},


    # 食物与烹饪

    "calories": {"category": "food", "desc": "Check calories in food", "slots": {"food_item": "Food item"}},

    "cook_time": {"category": "food", "desc": "Ask cooking time for a dish", "slots": {"dish": "Dish name"}},

    "food_last": {"category": "food", "desc": "Ask how long food lasts", "slots": {"food_item": "Food item"}},

    "ingredient_substitution": {"category": "food", "desc": "Find ingredient substitution", "slots": {"ingredient": "Ingredient to substitute"}},

    "ingredients_list": {"category": "food", "desc": "Get ingredients list for a recipe", "slots": {"recipe": "Recipe name"}},

    "meal_suggestion": {"category": "food", "desc": "Get meal suggestions", "slots": {"meal_type": "Type of meal", "preferences": "Dietary preferences"}},

    "nutrition_info": {"category": "food", "desc": "Get nutrition information", "slots": {"food_item": "Food item"}},

    "recipe": {"category": "food", "desc": "Get a recipe", "slots": {"dish": "Dish name"}},


    # 餐厅

    "cancel_reservation": {"category": "restaurant", "desc": "Cancel a restaurant reservation", "slots": {"restaurant": "Restaurant name", "reservation_id": "Reservation ID"}},

    "confirm_reservation": {"category": "restaurant", "desc": "Confirm a restaurant reservation", "slots": {"restaurant": "Restaurant name"}},

    "how_busy": {"category": "restaurant", "desc": "Ask how busy a place is", "slots": {"place": "Place name"}},

    "restaurant_reservation": {"category": "restaurant", "desc": "Make a restaurant reservation", "slots": {"restaurant": "Restaurant name", "date": "Reservation date", "time": "Reservation time", "party_size": "Number of people"}},

    "restaurant_reviews": {"category": "restaurant", "desc": "Get restaurant reviews", "slots": {"restaurant": "Restaurant name"}},

    "restaurant_suggestion": {"category": "restaurant", "desc": "Get restaurant suggestions", "slots": {"cuisine": "Cuisine type", "location": "Location"}},


    # 音乐与媒体

    "next_song": {"category": "media", "desc": "Skip to next song", "slots": {}},

    "play_music": {"category": "media", "desc": "Play music", "slots": {"song": "Song name", "artist": "Artist name", "genre": "Music genre", "playlist": "Playlist name"}},

    "update_playlist": {"category": "media", "desc": "Update a playlist", "slots": {"playlist": "Playlist name", "action": "Add or remove", "song": "Song to add/remove"}},

    "what_song": {"category": "media", "desc": "Ask what song is playing", "slots": {}},


    # 天气

    "weather": {"category": "weather", "desc": "Get weather information", "slots": {"location": "Location", "date": "Date"}},


    # 通讯

    "make_call": {"category": "communication", "desc": "Make a phone call", "slots": {"contact": "Person to call", "phone_number": "Phone number"}},

    "text": {"category": "communication", "desc": "Send a text message", "slots": {"recipient": "Message recipient", "message": "Message content"}},


    # 购物与订单

    "order": {"category": "shopping", "desc": "Place an order", "slots": {"item": "Item to order", "quantity": "Quantity"}},

    "order_checks": {"category": "shopping", "desc": "Order checks from bank", "slots": {}},

    "order_status": {"category": "shopping", "desc": "Check order status", "slots": {"order_id": "Order ID"}},

    "shopping_list": {"category": "shopping", "desc": "View shopping list", "slots": {}},

    "shopping_list_update": {"category": "shopping", "desc": "Update shopping list", "slots": {"item": "Item to add/remove", "action": "Add or remove"}},


    # 工作与人事

    "application_status": {"category": "work", "desc": "Check job application status", "slots": {"company": "Company name", "position": "Position applied for"}},

    "income": {"category": "work", "desc": "Ask about income", "slots": {}},

    "payday": {"category": "work", "desc": "Ask when payday is", "slots": {}},

    "pto_balance": {"category": "work", "desc": "Check PTO balance", "slots": {}},

    "pto_request": {"category": "work", "desc": "Request PTO", "slots": {"start_date": "Start date", "end_date": "End date", "reason": "Reason"}},

    "pto_request_status": {"category": "work", "desc": "Check PTO request status", "slots": {}},

    "pto_used": {"category": "work", "desc": "Check PTO used", "slots": {}},

    "rollover_401k": {"category": "work", "desc": "Inquire about 401k rollover", "slots": {}},

    "taxes": {"category": "work", "desc": "Ask about taxes", "slots": {"tax_type": "Type of tax question"}},

    "w2": {"category": "work", "desc": "Ask about W2 form", "slots": {}},


    # 保险

    "insurance": {"category": "insurance", "desc": "Ask about insurance", "slots": {"insurance_type": "Type of insurance"}},

    "insurance_change": {"category": "insurance", "desc": "Change insurance plan", "slots": {"insurance_type": "Type of insurance", "change_type": "Type of change"}},


    # 车辆

    "jump_start": {"category": "vehicle", "desc": "Request jump start assistance", "slots": {"location": "Current location"}},

    "last_maintenance": {"category": "vehicle", "desc": "Check last maintenance date", "slots": {"maintenance_type": "Type of maintenance"}},

    "mpg": {"category": "vehicle", "desc": "Check vehicle MPG", "slots": {"vehicle": "Vehicle model"}},

    "oil_change_how": {"category": "vehicle", "desc": "Ask how to change oil", "slots": {}},

    "oil_change_when": {"category": "vehicle", "desc": "Ask when to change oil", "slots": {}},

    "tire_change": {"category": "vehicle", "desc": "Request tire change assistance", "slots": {}},

    "tire_pressure": {"category": "vehicle", "desc": "Check tire pressure", "slots": {}},


    # 智能家居

    "find_phone": {"category": "smart_home", "desc": "Find phone", "slots": {}},

    "reset_settings": {"category": "smart_home", "desc": "Reset device settings", "slots": {"device": "Device to reset"}},

    "smart_home": {"category": "smart_home", "desc": "Control smart home device", "slots": {"device": "Device name", "action": "Action to perform", "setting": "Setting value"}},

    "sync_device": {"category": "smart_home", "desc": "Sync a device", "slots": {"device": "Device to sync"}},


    # 实用工具

    "apr": {"category": "utility", "desc": "Ask about APR", "slots": {}},

    "calculator": {"category": "utility", "desc": "Perform calculation", "slots": {"expression": "Math expression"}},

    "definition": {"category": "utility", "desc": "Get word definition", "slots": {"word": "Word to define"}},

    "exchange_rate": {"category": "utility", "desc": "Get exchange rate", "slots": {"from_currency": "Source currency", "to_currency": "Target currency"}},

    "flip_coin": {"category": "utility", "desc": "Flip a coin", "slots": {}},

    "fun_fact": {"category": "utility", "desc": "Get a fun fact", "slots": {"topic": "Topic for fun fact"}},

    "measurement_conversion": {"category": "utility", "desc": "Convert measurements", "slots": {"value": "Value to convert", "from_unit": "Source unit", "to_unit": "Target unit"}},

    "roll_dice": {"category": "utility", "desc": "Roll dice", "slots": {"num_dice": "Number of dice", "num_sides": "Number of sides"}},

    "spelling": {"category": "utility", "desc": "Spell a word", "slots": {"word": "Word to spell"}},

    "tell_joke": {"category": "utility", "desc": "Tell a joke", "slots": {"topic": "Joke topic"}},

    "todo_list": {"category": "utility", "desc": "View todo list", "slots": {}},

    "todo_list_update": {"category": "utility", "desc": "Update todo list", "slots": {"item": "Todo item", "action": "Add or remove"}},

    "translate": {"category": "utility", "desc": "Translate text", "slots": {"text": "Text to translate", "target_language": "Target language"}},


    # 助手自身信息

    "are_you_a_bot": {"category": "meta", "desc": "Ask if assistant is a bot", "slots": {}},

    "cancel": {"category": "meta", "desc": "Cancel current action", "slots": {}},

    "change_accent": {"category": "meta", "desc": "Change assistant accent", "slots": {"accent": "Desired accent"}},

    "change_ai_name": {"category": "meta", "desc": "Change assistant name", "slots": {"name": "New name"}},

    "change_language": {"category": "meta", "desc": "Change assistant language", "slots": {"language": "Desired language"}},

    "change_speed": {"category": "meta", "desc": "Change speech speed", "slots": {"speed": "Speed setting"}},

    "change_user_name": {"category": "meta", "desc": "Change user name", "slots": {"name": "New user name"}},

    "change_volume": {"category": "meta", "desc": "Change volume", "slots": {"level": "Volume level"}},

    "do_you_have_pets": {"category": "meta", "desc": "Ask if assistant has pets", "slots": {}},

    "goodbye": {"category": "meta", "desc": "Say goodbye", "slots": {}},

    "greeting": {"category": "meta", "desc": "Greet the assistant", "slots": {}},

    "how_old_are_you": {"category": "meta", "desc": "Ask assistant age", "slots": {}},

    "maybe": {"category": "meta", "desc": "Express uncertainty", "slots": {}},

    "meaning_of_life": {"category": "meta", "desc": "Ask about meaning of life", "slots": {}},

    "no": {"category": "meta", "desc": "Say no", "slots": {}},

    "repeat": {"category": "meta", "desc": "Ask to repeat", "slots": {}},

    "thank_you": {"category": "meta", "desc": "Thank the assistant", "slots": {}},

    "user_name": {"category": "meta", "desc": "Ask user name", "slots": {}},

    "what_are_your_hobbies": {"category": "meta", "desc": "Ask about assistant hobbies", "slots": {}},

    "what_can_i_ask_you": {"category": "meta", "desc": "Ask what assistant can do", "slots": {}},

    "what_is_your_name": {"category": "meta", "desc": "Ask assistant name", "slots": {}},

    "where_are_you_from": {"category": "meta", "desc": "Ask where assistant is from", "slots": {}},

    "whisper_mode": {"category": "meta", "desc": "Enable whisper mode", "slots": {}},

    "who_do_you_work_for": {"category": "meta", "desc": "Ask who assistant works for", "slots": {}},

    "who_made_you": {"category": "meta", "desc": "Ask who made assistant", "slots": {}},

    "yes": {"category": "meta", "desc": "Say yes", "slots": {}},

}


def generate_function_py():

    """生成 function.py 文件"""


    functions = []


    for intent_name, info in CLINC150_INTENTS.items():

        func = {

            "type": "function",

            "function": {

                "name": intent_name,

                "description": info["desc"],

                "parameters": {

                    "type": "object",

                    "properties": {},

                    "required": []

                }

            }

        }


        # 添加槽位

        for slot_name, slot_desc in info["slots"].items():

            func["function"]["parameters"]["properties"][slot_name] = {

                "type": "string",

                "description": slot_desc

            }


        functions.append(func)


    # 生成 Python 文件内容

    content = '''# -*- coding: utf-8 -*-

# CLINC150 Function Definitions

# Auto-generated for 150 intents



tools1 = '''

    content += json.dumps(functions, indent=4, ensure_ascii=False)

    content += "\n"


    return content


def generate_slot_intent_json():

    """生成 slot_intent.json 文件"""


    slot_intent = {}


    for intent_name, info in CLINC150_INTENTS.items():

        if info["slots"]:

            slot_intent[intent_name] = info["slots"]

        else:

            slot_intent[intent_name] = "none"


    return json.dumps(slot_intent, indent=4, ensure_ascii=False)


if __name__ == "__main__":

    # 生成 function.py

    function_content = generate_function_py()

    with open("../function_call/function_clinc150.py", "w", encoding="utf-8") as f:

        f.write(function_content)

    print("Generated function_clinc150.py")


    # 生成 slot_intent.json

    slot_content = generate_slot_intent_json()

    with open("../config/slot_intent_clinc150.json", "w", encoding="utf-8") as f:

        f.write(slot_content)

    print("Generated slot_intent_clinc150.json")


    print(f"\nTotal intents: {len(CLINC150_INTENTS)}")
