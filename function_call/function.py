# 定义工具


tools1 = [

    {

        # A类：槽位+工具调用

        "type": "function",

        "function": {

            "name": "weather",

            "description": "Return current weather conditions or short-term forecast for a given city or region.",

            "parameters": {

                "type": "object",

                "properties": {

                    "location": {

                        "type": "string",

                        "description": "City, state/province, or region the user mentions. Leave empty if no location is provided."

                    },

                    "datetime": {

                        "type": "string",

                        "description": "Optional time reference such as today, tonight, tomorrow morning, next weekend."

                    },

                    "unit": {

                        "type": "string",

                        "description": "Optional temperature unit preference: celsius, fahrenheit."

                    }

                },

                "required": ["location"]

            }

        }

    },

    {

        "type": "function",

        "function": {

            "name": "play_music",

            "description": "Search or play music/podcasts/audiobooks based on song title, artist, genre, or playlist.",

            "parameters": {

                "type": "object",

                "properties": {

                    "song": {"type": "string", "description": "Song or track name."},

                    "artist": {"type": "string", "description": "Artist, band, or performer."},

                    "genre": {"type": "string", "description": "Genre or mood (e.g., jazz, ambient)."},

                    "mood": {"type": "string", "description": "Mood or vibe keywords (e.g., relaxing, upbeat)."},

                    "action": {"type": "string", "description": "Optional action such as play, pause, skip, resume."},

                    "playlist": {"type": "string", "description": "Playlist, album, or station name if specified."}

                },

                "required": []

            }

        }

    },

    {

        "type": "function",

        "function": {

            "name": "time",

            "description": "Tell the current time or date for a specified city or timezone.",

            "parameters": {

                "type": "object",

                "properties": {

                    "location": {"type": "string", "description": "City/region mentioned by the user."},

                    "timezone": {"type": "string", "description": "Explicit timezone ID if provided (e.g., Europe/London)."}

                },

                "required": []

            }

        }

    },


    # B类：只测试槽位

    {

        "type": "function",

        "function": {

            "name": "alarm",

            "description": "Set an alarm for a specific time, optionally adding a label and recurrence pattern.",

            "parameters": {

                "type": "object",

                "properties": {

                    "time": {"type": "string", "description": "Exact trigger time, e.g. '07:30' or '6 am tomorrow'."},

                    "label": {"type": "string", "description": "Optional alarm title such as 'wake up' or 'meeting'."},

                    "recurrence": {"type": "string", "description": "Repeat rule like 'daily', 'weekdays', or 'every Monday'."}

                },

                "required": ["time"]

            }

        }

    },

    {

        "type": "function",

        "function": {

            "name": "book_flight",

            "description": "Search or book flights with specified cities, dates, and cabin preferences.",

            "parameters": {

                "type": "object",

                "properties": {

                    "origin": {"type": "string", "description": "Departure city or airport code."},

                    "destination": {"type": "string", "description": "Arrival city or airport code."},

                    "depart_date": {"type": "string", "description": "Outbound date in YYYY-MM-DD or natural language."},

                    "return_date": {"type": "string", "description": "Return date in YYYY-MM-DD or empty for one-way."},

                    "travelers": {"type": "string", "description": "Passenger description, e.g. '2 adults 1 child'."},

                    "seat_class": {"type": "string", "description": "Cabin class such as economy, premium, business, first."},

                    "airline": {"type": "string", "description": "Preferred airline name or code."}

                },

                "required": ["origin", "destination", "depart_date"]

            }

        }

    },

    {

        "type": "function",

        "function": {

            "name": "book_hotel",

            "description": "Find or reserve hotels with location, dates, and guest preferences.",

            "parameters": {

                "type": "object",

                "properties": {

                    "location": {"type": "string", "description": "City, neighborhood, or landmark the user mentions."},

                    "check_in_date": {"type": "string", "description": "Check-in date (YYYY-MM-DD or natural phrase)."},

                    "nights": {"type": "string", "description": "Number of nights or checkout date details."},

                    "guests": {"type": "string", "description": "Guest count such as '2 adults'."},

                    "room_type": {"type": "string", "description": "Room preference (suite, double, twin, king, etc.)."},

                    "amenities": {"type": "string", "description": "Desired amenities such as pool, gym, wifi."}

                },

                "required": ["location", "check_in_date", "nights", "guests"]

            }

        }

    },

    {

        "type": "function",

        "function": {

            "name": "calendar_update",

            "description": "Create or modify a calendar event with date, time, and location.",

            "parameters": {

                "type": "object",

                "properties": {

                    "event": {"type": "string", "description": "Event title or subject."},

                    "date": {"type": "string", "description": "Event date (YYYY-MM-DD or relative)."},

                    "time": {"type": "string", "description": "Event time such as '15:00' or 'tomorrow morning'."},

                    "location": {"type": "string", "description": "Venue or meeting location."}

                },

                "required": ["event", "date"]

            }

        }

    },

    {

        "type": "function",

        "function": {

            "name": "car_rental",

            "description": "Reserve a rental car with pickup/dropoff details and dates.",

            "parameters": {

                "type": "object",

                "properties": {

                    "pickup_location": {"type": "string", "description": "City or office where the car is collected."},

                    "dropoff_location": {"type": "string", "description": "Return location or 'same as pickup'."},

                    "pickup_date": {"type": "string", "description": "Pickup date/time."},

                    "return_date": {"type": "string", "description": "Return date/time."},

                    "car_type": {"type": "string", "description": "Vehicle class such as sedan, SUV, compact."}

                },

                "required": ["pickup_location", "pickup_date", "return_date"]

            }

        }

    },

    {

        "type": "function",

        "function": {

            "name": "directions",

            "description": "Provide navigation directions between two points.",

            "parameters": {

                "type": "object",

                "properties": {

                    "origin": {"type": "string", "description": "Starting point; use 'current location' if absent."},

                    "destination": {"type": "string", "description": "Destination point."},

                    "mode": {"type": "string", "description": "Travel mode such as driving, walking, transit."}

                },

                "required": ["destination"]

            }

        }

    },

    {

        "type": "function",

        "function": {

            "name": "distance",

            "description": "Check the distance between two locations in a requested unit.",

            "parameters": {

                "type": "object",

                "properties": {

                    "origin": {"type": "string", "description": "Starting point."},

                    "destination": {"type": "string", "description": "End point."},

                    "unit": {"type": "string", "description": "Unit preference such as km, miles, meters."}

                },

                "required": ["origin", "destination"]

            }

        }

    },

    {

        "type": "function",

        "function": {

            "name": "timer",

            "description": "Set a countdown timer for a specified duration.",

            "parameters": {

                "type": "object",

                "properties": {

                    "duration": {"type": "string", "description": "Interval such as '5 minutes' or '90 seconds'."},

                    "label": {"type": "string", "description": "Optional label describing what the timer is for."}

                },

                "required": ["duration"]

            }

        }

    },

    {

        "type": "function",

        "function": {

            "name": "make_call",

            "description": "Place a phone call to a specific contact or number.",

            "parameters": {

                "type": "object",

                "properties": {

                    "contact": {"type": "string", "description": "Contact name or identifier."},

                    "phone_number": {"type": "string", "description": "Explicit phone number if provided."}

                },

                "required": ["contact"]

            }

        }

    },

    {

        "type": "function",

        "function": {

            "name": "reminder",

            "description": "Create a reminder with content and due time.",

            "parameters": {

                "type": "object",

                "properties": {

                    "content": {"type": "string", "description": "Reminder message or task."},

                    "datetime": {"type": "string", "description": "When the reminder should trigger."}

                },

                "required": ["content", "datetime"]

            }

        }

    },

    {

        "type": "function",

        "function": {

            "name": "reminder_update",

            "description": "Modify an existing reminder's content or time.",

            "parameters": {

                "type": "object",

                "properties": {

                    "content": {"type": "string", "description": "Reminder identifier or updated message."},

                    "datetime": {"type": "string", "description": "New scheduled time."}

                },

                "required": ["content", "datetime"]

            }

        }

    },

    {

        "type": "function",

        "function": {

            "name": "restaurant_reservation",

            "description": "Book a table at a restaurant with party size and time.",

            "parameters": {

                "type": "object",

                "properties": {

                    "restaurant": {"type": "string", "description": "Restaurant name or cuisine."},

                    "date": {"type": "string", "description": "Reservation date."},

                    "time": {"type": "string", "description": "Reservation time."},

                    "party_size": {"type": "string", "description": "Number of guests."}

                },

                "required": ["restaurant", "date", "time", "party_size"]

            }

        }

    },

    {

        "type": "function",

        "function": {

            "name": "text",

            "description": "Send an SMS or text message to a contact.",

            "parameters": {

                "type": "object",

                "properties": {

                    "contact": {"type": "string", "description": "Recipient contact name or identifier."},

                    "message": {"type": "string", "description": "Message body to send."}

                },

                "required": ["contact", "message"]

            }

        }

    },

    {

        "type": "function",

        "function": {

            "name": "translate",

            "description": "Translate text between languages.",

            "parameters": {

                "type": "object",

                "properties": {

                    "text": {"type": "string", "description": "Phrase or sentence to translate."},

                    "source_lang": {"type": "string", "description": "Source language code or name; allow empty for auto-detect."},

                    "target_lang": {"type": "string", "description": "Target language code or name."}

                },

                "required": ["text", "target_lang"]

            }

        }

    },

    {

        "type": "function",

        "function": {

            "name": "uber",

            "description": "Request a ride-hailing trip with pickup and destination details.",

            "parameters": {

                "type": "object",

                "properties": {

                    "destination": {"type": "string", "description": "Drop-off location."},

                    "pickup_location": {"type": "string", "description": "Pickup location; default to current location if missing."}

                },

                "required": ["destination"]

            }

        }

    },


    {

        "type": "function",

        "function": {

          "name": "balance",

          "description": "Check the current account balance.",

          "parameters": {

            "type": "object",

            "properties": {}

          }

  }

},

  {

    "type": "function",

    "function": {

      "name": "accept_reservations",

      "description": "Check if a specific establishment accepts reservations.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "account_blocked",

      "description": "Inquire why an account is blocked or how to unblock it.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "application_status",

      "description": "Check the status of a submitted application.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "apr",

      "description": "Inquire about the Annual Percentage Rate (APR) for an account.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "are_you_a_bot",

      "description": "Ask if the assistant is an AI or a human.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "bill_balance",

      "description": "Check the outstanding balance on a bill.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "bill_due",

      "description": "Find out the due date for a bill.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "calculator",

      "description": "Open the calculator tool or request a calculation.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "calendar",

      "description": "View general calendar information or schedule.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "calories",

      "description": "Inquire about the calorie count of a food item.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "cancel",

      "description": "Cancel the current ongoing action or dialogue flow.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "cancel_reservation",

      "description": "Cancel an existing reservation (hotel, restaurant, flight booking). Use this ONLY when user wants to cancel something they previously booked, NOT for sending messages.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "card_declined",

      "description": "Inquire why a credit or debit card was declined.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "carry_on",

      "description": "Ask about carry-on luggage rules and restrictions.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "change_accent",

      "description": "Request to change the accent of the AI voice.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "change_ai_name",

      "description": "Request to change the name the user calls the AI.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "change_language",

      "description": "Change the language of the conversation.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "change_speed",

      "description": "Adjust the speaking speed of the AI.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "change_user_name",

      "description": "Request to change the name the AI uses to address the user.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "change_volume",

      "description": "Adjust the volume of the device or response.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "confirm_reservation",

      "description": "Confirm the details of an existing reservation.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "cook_time",

      "description": "Ask for the cooking time of a specific dish.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "credit_limit",

      "description": "Check the current credit limit on a card.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "credit_limit_change",

      "description": "Request to increase or decrease a credit limit.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "credit_score",

      "description": "Check the current credit score.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "current_location",

      "description": "Get the user's current geographical location.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "damaged_card",

      "description": "Report a damaged physical card.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "date",

      "description": "Ask for the current date or a specific date.",

      "parameters": {

        "type": "object",

        "properties": {

          "datetime": {"type": "string", "description": "Date reference such as 'today', 'tomorrow', 'in 5 days'."},

          "calendar": {"type": "string", "description": "Calendar type if specified."}

        }

      }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "definition",

      "description": "Ask for the definition of a word or phrase.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "direct_deposit",

      "description": "Inquire about setting up or checking direct deposit.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "do_you_have_pets",

      "description": "Ask the AI if it has any pets (chitchat).",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "exchange_rate",

      "description": "Check the currency exchange rate between two currencies.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "expiration_date",

      "description": "Check the expiration date of a card or document.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "find_phone",

      "description": "Trigger a feature to help locate a lost phone.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "flight_status",

      "description": "Check the status of a scheduled flight.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "flip_coin",

      "description": "Simulate flipping a coin (heads or tails).",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "food_last",

      "description": "Check how long a specific food item lasts.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "freeze_account",

      "description": "Request to temporarily freeze an account.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "fun_fact",

      "description": "Ask for a random fun fact.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "gas",

      "description": "Find nearby gas stations.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "gas_type",

      "description": "Ask what type of gas a car needs.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "goodbye",

      "description": "Say goodbye to the assistant.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "greeting",

      "description": "Greet the assistant.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "how_busy",

      "description": "Ask how busy a specific place is currently.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "how_old_are_you",

      "description": "Ask the AI for its age.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "improve_credit_score",

      "description": "Ask for advice on improving credit score.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "income",

      "description": "Discuss or update income information.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "ingredient_substitution",

      "description": "Ask for a substitute for a cooking ingredient.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "ingredients_list",

      "description": "Ask for the list of ingredients in a recipe.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "insurance",

      "description": "Inquire about insurance coverage or details.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "insurance_change",

      "description": "Request to change insurance policy details.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "interest_rate",

      "description": "Inquire about the interest rate of a loan or account.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "international_fees",

      "description": "Ask about fees for international transactions.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "international_visa",

      "description": "Inquire about visa requirements for international travel.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "jump_start",

      "description": "Ask for instructions on how to jump-start a car.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "last_maintenance",

      "description": "Check when the last maintenance was performed.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "lost_luggage",

      "description": "Report or inquire about lost luggage.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "maybe",

      "description": "Express uncertainty or a 'maybe' response.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "meal_suggestion",

      "description": "Ask for a recommendation on what to eat.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "meaning_of_life",

      "description": "Ask the philosophical question about the meaning of life.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "measurement_conversion",

      "description": "Convert measurements between different units.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "meeting_schedule",

      "description": "Check or view the schedule for upcoming meetings, or ask about meeting room availability. Use this when user wants to SEE existing meetings or check room availability, NOT to create new meetings.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "min_payment",

      "description": "Check the minimum payment due on a bill.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "mpg",

      "description": "Ask about the miles per gallon (fuel efficiency) of a vehicle.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "new_card",

      "description": "Request a new credit or debit card.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "next_holiday",

      "description": "Ask when the next public holiday is.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "next_song",

      "description": "Skip to the next song in the playlist.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "no",

      "description": "Express a negative response (No).",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "nutrition_info",

      "description": "Ask for nutritional information about food.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "oil_change_how",

      "description": "Ask for instructions on how to change oil in a car.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "oil_change_when",

      "description": "Ask when the next oil change is due.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "order",

      "description": "Place a general order.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "order_checks",

      "description": "Order new physical bank checks.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "order_status",

      "description": "Check the status of a pending order.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "pay_bill",

      "description": "Initiate a bill payment.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "payday",

      "description": "Ask when the next payday is.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "pin_change",

      "description": "Request to change the PIN for a card or account.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "plug_type",

      "description": "Ask about the type of electrical plug used in a location.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "pto_balance",

      "description": "Check the balance of Paid Time Off (PTO).",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "pto_request",

      "description": "Request Paid Time Off (PTO).",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "pto_request_status",

      "description": "Check the status of a PTO request.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "pto_used",

      "description": "Check how much PTO has been used.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "recipe",

      "description": "Search for a cooking recipe.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "redeem_rewards",

      "description": "Redeem earned rewards or points.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "repeat",

      "description": "Ask the assistant to repeat the last statement.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "replacement_card_duration",

      "description": "Ask how long it takes to get a replacement card.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "report_fraud",

      "description": "Report fraudulent or unauthorized activity on an account (e.g., someone else used my account, unauthorized transactions). Use this for fraud/unauthorized use, NOT for lost/stolen cards.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "report_lost_card",

      "description": "Report a lost or stolen physical credit/debit card. Use this ONLY when the card itself is lost/stolen, NOT for unauthorized transactions or fraud.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "reset_settings",

      "description": "Reset application or device settings to default.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "restaurant_reviews",

      "description": "Look up reviews for a restaurant.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "restaurant_suggestion",

      "description": "Ask for a restaurant recommendation.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "rewards_balance",

      "description": "Check the balance of rewards points.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "roll_dice",

      "description": "Simulate rolling dice.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "rollover_401k",

      "description": "Inquire about rolling over a 401k account.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "routing",

      "description": "Ask for the bank routing number.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "schedule_maintenance",

      "description": "Schedule a maintenance appointment.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "schedule_meeting",

      "description": "Schedule or create a NEW meeting. Use this when user wants to SET UP or ARRANGE a new meeting, NOT to check existing schedules.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "share_location",

      "description": "Share the current location with someone.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "shopping_list",

      "description": "View the shopping list.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "shopping_list_update",

      "description": "Update items in the shopping list.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "smart_home",

      "description": "Control smart home devices.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "spelling",

      "description": "Ask how to spell a word.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "spending_history",

      "description": "Review past spending or transactions.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "sync_device",

      "description": "Sync a device with the account or system.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "taxes",

      "description": "Inquire about tax-related information.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "tell_joke",

      "description": "Ask the assistant to tell a joke.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "thank_you",

      "description": "Express gratitude.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "timezone",

      "description": "Ask for timezone information for a location.",

      "parameters": {

        "type": "object",

        "properties": {

          "location": {"type": "string", "description": "City or region to get timezone for."},

          "direction": {"type": "string", "description": "Direction or offset information."}

        }

      }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "tire_change",

      "description": "Ask about tire changing services or instructions.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "tire_pressure",

      "description": "Check recommended tire pressure.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "todo_list",

      "description": "View or check items on the to-do list. Use this when user wants to SEE what's on their todo list, NOT for reminders.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "todo_list_update",

      "description": "Update the to-do list.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "traffic",

      "description": "Check current traffic conditions.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "transactions",

      "description": "View recent account transactions.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "transfer",

      "description": "Initiate a fund transfer.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "travel_alert",

      "description": "Check for travel alerts or warnings.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "travel_notification",

      "description": "Notify the bank of upcoming travel.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "travel_suggestion",

      "description": "Ask for travel destination suggestions.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "update_playlist",

      "description": "Update or modify a music playlist.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "user_name",

      "description": "Ask what the assistant calls the user.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "vaccines",

      "description": "Inquire about required or recommended vaccines.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "w2",

      "description": "Inquire about W2 tax forms.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "what_are_your_hobbies",

      "description": "Ask the assistant about its hobbies (chitchat).",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "what_can_i_ask_you",

      "description": "Ask what capabilities the assistant has.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "what_is_your_name",

      "description": "Ask the assistant for its name.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "what_song",

      "description": "Identify the song currently playing.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "where_are_you_from",

      "description": "Ask the assistant about its origin.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "whisper_mode",

      "description": "Enable whisper mode for the assistant.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "who_do_you_work_for",

      "description": "Ask which company the assistant works for.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "who_made_you",

      "description": "Ask who created the assistant.",

      "parameters": { "type": "object", "properties": {} }

    }

  },

  {

    "type": "function",

    "function": {

      "name": "yes",

      "description": "Express an affirmative response (Yes).",

      "parameters": { "type": "object", "properties": {} }

    }

  }

]
