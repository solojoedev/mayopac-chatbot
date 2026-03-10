import csv
import anthropic
from dotenv import load_dotenv
import os
from datetime import datetime

#import api key for Claude
client =anthropic.Anthropic(api_key=os.environ.get("CLAUDE_API"))

#Get current date and time
current_month = datetime.now().strftime("%b").upper()  # "MAR"

#Search Function using month, genre, and venue as parameters
def search_shows(month=None, genre=None):
    #where the results will be entered
    results = []

    with open('mayopac.csv', 'r') as file:
        next(file)
        reader = csv.DictReader(file)
        current_month = None

        for row in reader:
            #skip empty rows
            if row.get('Month'):
                current_month = row['Month']

            #skip rows with no show name
            if not row.get('Show / Event'):
                continue

            #Filter by month if provided
            if month and current_month and current_month.upper() != month.upper():
                continue

            #Filter by genre if provided
            if genre and genre.upper() not in row.get('Genre', '').upper():
                continue


            results.append({
                'month': current_month,
                'date': row['Date(s)'],
                'show': row['Show / Event'],
                'genre': row.get('Genre', 'N/A'),
            })

    return results