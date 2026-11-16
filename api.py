from fastapi import FastAPI
from function import search_shows
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import anthropic 
import os
import json  

load_dotenv()

app = FastAPI()

client = anthropic.Anthropic(api_key=os.environ.get("CLAUDE_API_KEY"))

with open("mpac_policies.json") as f:
     policies = json.load(f)

# Define tools
tools = [{
    "name": "search_shows",
    "description": "Searches for shows at Mayo Performing Arts Center by month and genre",
    "input_schema": {
        "type": "object",
        "properties": {
            "month": {"type": "string", "description": "Month (NOV, DEC, JAN, FEB, MAR, APR, MAY)"},
            "genre": {"type": "string", "description": "Genre (Jazz, Rock, Comedy, Dance, Family, etc.)"}
        },
        "required": []
    }
}]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], #ALLOW ALL ORIGINS FOR NOW
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
def process_date_references(question: str) -> str:
    """Convert natural language dates to month codes"""
    current_date = datetime.now()
    current_month = current_date.strftime("%b").upper() # "MAR"

    question_lower = question.lower()

    #Month Mapping
    next_month_map = {
        "JAN": "FEB", "FEB": "MAR", "MAR": "APR", "APR": "MAY", 
        "MAY": "JUN", "JUN": "JUL", "JUL": "AUG", "AUG": "SEP",
        "SEP": "OCT", "OCT": "NOV", "NOV": "DEC", "DEC": "JAN"
    }

    # Replace natual language with actual months
    processed = question
    if "this month" in question_lower:
            processed = question_lower.replace("this month", current_month)
    elif "next month" in question_lower:
         next_month = next_month_map.get(current_month, current_month)
         processed = question_lower.replace("next month", next_month)

    return processed

@app.get("/search")
def search_opa(question: str):
    # Process date references
    processed_question = process_date_references(question)

    system_prompt = f"""You are Mo, the premier cultural concierge at The Mayo Performing Arts Center.

    You have impeccable taste and deep knowledge of the performing arts. Like a sommelier recommending the perfect pairing, you thoughtfully match guests with shows that suit their exact preferences and occasion.

    RESPONSE FORMAT (you must follow this structure):

    1. Opening statement (personalized to their request)
    2. Maximum 3 show recommendations with elegant descriptions

    For EACH show, include this format immediately after the description:
    🎟 Learn More & Book Tickets: [use the exact "url" from the search results. If it is empty, skip this line.

    3. REQUIRED: After all recommendations, include:
    🎟 View Full Calendar: https://www.mayoarts.org/events

    4. REQUIRED: One follow-up question

    Examples of your tone:
    - "For an evening that balances spectacle with substance, I'd recommend..."
    - "If you're seeking something that will resonate with the entire family..."
    - "Guests with your particular taste tend to appreciate..."

    Examples of follow-up questions:
    - "Will this be an intimate evening or a celebration with company?"
    - "Do you prefer something emotionally stirring or lighthearted?"
    - "Are you drawn to contemporary works or timeless classics?"

    You don't just list shows - you craft experiences. When recommending shows, always end with the calendar link and a follow-up question.
    Use plain text only. No markdown, no asterisks, no bullet symbols.
    For policy questions, answer in 2-4 sentences covering only what was asked. Offer more detail if they want it.

    If the question is about venue policies (parking, security and bags, ticketing, seating, code of conduct), answer directly from VENUE POLICIES below and skip the show format.
    VENUE POLICIES:
    {json.dumps(policies, indent=2)} """

    messages = [{"role": "user", "content": processed_question}]

    for _ in range(3):  # allow up to 3 rounds of searching
        response = client.messages.create(
            model="claude-sonnet-5-5",
            max_tokens=4096,
            tools=tools,
            system=system_prompt,
            messages=messages,
        )
        print(response.stop_reason, [b.type for b in response.content])

        if response.stop_reason != "tool_use":
            break  # the model is done searching and has answered

        # Keep the model's turn, then answer EVERY search it asked for
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                results = search_shows(
                    month=block.input.get("month"),
                    genre=block.input.get("genre"),
                )
                print(block.input, len(results))
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(results),
                })
        messages.append({"role": "user", "content": tool_results})

    text_block = next((b for b in response.content if b.type == "text"), None)
    if text_block:
        return {"answer": text_block.text}
    return {"answer": "I'm having trouble processing that request. Could you rephrase?"}