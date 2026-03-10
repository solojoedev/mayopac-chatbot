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

            #skip rows with no show name
        for row in reader:
                if not row.get('Show Name'):
                    continue

            #Extract month form date column (format: 2026-03-10)
                show_date = row.get('Date', '')
                if show_date: 
                    try:
                        #Parse Date and get month abbreviation
                        date_obj = datetime.strptime(show_date, '%Y-%m-%d')
                        show_month = date_obj.strftime('%b').upper() # MAR
                    except:
                        show_month = None
                else:
                    show_month = None
            #Filter by month if provided
                if month and current_month and current_month.upper() != month.upper():
                    continue

            #Filter by genre if provided
                if genre and genre.upper() not in row.get('Genre', '').upper():
                    continue


                results.append({
                'date': row['Date'],
                'time': row.get('Time', 'N/A'),
                'show': row['Show Name'],
                'genre': row.get('Genre', 'N/A'),
                'description': row.get('Description', '')
            })

    return results