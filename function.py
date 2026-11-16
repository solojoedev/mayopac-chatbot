import csv
from datetime import datetime


def search_shows(month=None, genre=None):
    results = []

    with open('mayopac_4.csv', 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        for row in reader:
            # Skip rows with no show name
            if not row.get('Show Name'):
                continue

            # Dates can be "2026-12-11" or a range "2026-12-11 - 2026-12-27"
            parts = row.get('Date', '').split(' - ')
            try:
                start = datetime.strptime(parts[0].strip(), '%Y-%m-%d')
                end = datetime.strptime(parts[-1].strip(), '%Y-%m-%d')
            except ValueError:
                continue  # policy rows and junk rows land here

            # Skip postponed shows
            if row.get('Status / Notes', '').upper().startswith('POSTPONED'):
                continue

            # Filter by month if provided
            if month:
                wanted = month[:3].upper()
                months = {start.strftime('%b').upper(), end.strftime('%b').upper()}
                if wanted not in months:
                    continue

            # Filter by genre if provided
            if genre and genre.upper() not in row.get('Genre', '').upper():
                continue

            results.append({
                'date': row['Date'],
                'time': row.get('Time', 'N/A'),
                'show': row['Show Name'],
                'genre': row.get('Genre', 'N/A'),
                'venue': row.get('Venue', 'N/A'),
                'price': row.get('Price Range', 'N/A'),
                'status': row.get('Status / Notes', ''),
                'url': row.get('URL', ''),
                'description': row.get('Description', ''),
            })

    return results