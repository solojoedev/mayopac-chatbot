from fastapi import FastAPI
from function import search_shows
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
import anthropic 
import os  

app = FastAPI()

client = anthropic.Anthropic(api_key=os.environ.get("CLAUDE_API_KEY"))

# Define tools
tools = [{
    "name": "search_shows",
    "description": "Searches for shows at Mayo Performing Arts Center by month and genre",
    "input_schema": {
        "type": "object",
        "properties": {
            "month": {"type": "string", "description": "Month (MAR, APR, MAY, JUN)"},
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

    system_prompt = """You are Mo, the premier cultural concierge at The Mayo Performing Arts Center.

    You have impeccable taste and deep knowledge of the performing arts. Like a sommelier recommending the perfect pairing, you thoughtfully match guests with shows that suit their exact preferences and occasion.

    RESPONSE FORMAT (you must follow this structure):

    1. Opening statement (personalized to their request)
    2. Maximum 3 show recommendations with elegant descriptions

    For EACH show, include this format immediately after the description:
    🎟 Learn More & Book Tickets: https://www.mayoarts.org/events/[show-name]

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

    You don't just list shows - you craft experiences. Always end with the calendar link and a follow-up question."""

    #Send question to Claude
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        tools=tools,
        system=system_prompt,
        messages=[
            {"role": "user", "content": processed_question}
        ]
    )

    # Check if Claude wants to use a tool
    if message.stop_reason == "tool_use":
        tool_use = next(block for block in message.content if block.type == "tool_use")

        # Execute the search
        month = tool_use.input.get("month")
        genre = tool_use.input.get("genre")
        results = search_shows(month=month, genre=genre)

        # Send Results back to Claude
        response = client.messages.create(
            model="claude-4-sonnet-20250514",
            max_tokens=1024,
            tools=tools, 
            system=system_prompt,
            messages=[
                {"role": "user", "content": processed_question},
                {"role": "assistant", "content": message.content},
                {
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": str(results)
                    }]
                }
            ]
        )

        return {"answer": response.content[0].text}
    
    # If no tool use, return Claude's direct response
    return {"answer": message.content[0].text}