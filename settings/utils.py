import json
from settings.models import Year, OutStation, Cell

def get_settings_distribution_analysis():
    """
    Fetches the count of total years, outstations, and cells for a bar chart visualization.
    """
    years_count = Year.objects.count()
    outstations_count = OutStation.objects.count()
    cells_count = Cell.objects.count()

    # Data and labels for the bar chart
    labels = ["Years", "Outstations", "Cells"]  # Removed "Apostolic Movements"
    data = [years_count, outstations_count, cells_count]

    # Construct a simple analysis message
    analysis = (
        f"There are **{years_count}** year(s), **{outstations_count}** outstation(s), "
        f"and **{cells_count}** cell(s)."
    )

    # Return JSON data for Chart.js
    return json.dumps({
        "labels": labels,
        "data": data,
        "analysis": analysis,
        "years_count": years_count,
        "outstations_count": outstations_count,
        "cells_count": cells_count,
    })