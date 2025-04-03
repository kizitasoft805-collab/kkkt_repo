import json
from django.db.models import Count
from members.models import ChurchMember

def get_sacraments_trend_analysis():
    """
    Fetches the count of baptized, confirmed, married males, 
    married females, unbaptized, unconfirmed, unmarried males, and unmarried females.
    Returns JSON data for Chart.js.
    """

    # Get total counts for each category
    total_baptized = ChurchMember.objects.filter(is_baptised=True).count()
    total_unbaptized = ChurchMember.objects.filter(is_baptised=False).count()

    total_confirmed = ChurchMember.objects.filter(is_confirmed=True).count()
    total_unconfirmed = ChurchMember.objects.filter(is_confirmed=False).count()

    total_married_males = ChurchMember.objects.filter(marital_status="Married", gender="Male").count()
    total_married_females = ChurchMember.objects.filter(marital_status="Married", gender="Female").count()

    total_unmarried_males = ChurchMember.objects.exclude(marital_status="Married").filter(gender="Male").count()
    total_unmarried_females = ChurchMember.objects.exclude(marital_status="Married").filter(gender="Female").count()

    # Data Labels and Values
    labels = [
        "Baptized", "Unbaptized",
        "Confirmed", "Unconfirmed",
        "Married Males", "Married Females",
        "Unmarried Males", "Unmarried Females"
    ]
    data = [
        total_baptized, total_unbaptized,
        total_confirmed, total_unconfirmed,
        total_married_males, total_married_females,
        total_unmarried_males, total_unmarried_females
    ]

    # Generate an analysis message
    analysis = (
        f"The total number of baptized members is **{total_baptized}**, while **{total_unbaptized}** remain unbaptized. "
        f"**{total_confirmed}** members are confirmed, and **{total_unconfirmed}** are not. "
        f"Among the married members, **{total_married_males}** are males and **{total_married_females}** are females. "
        f"Meanwhile, **{total_unmarried_males}** males and **{total_unmarried_females}** females remain unmarried."
    )

    # Return JSON data for Chart.js
    return json.dumps({
        "labels": labels,
        "data": data,
        "total_baptized": total_baptized,
        "total_unbaptized": total_unbaptized,
        "total_confirmed": total_confirmed,
        "total_unconfirmed": total_unconfirmed,
        "total_married_males": total_married_males,
        "total_married_females": total_married_females,
        "total_unmarried_males": total_unmarried_males,
        "total_unmarried_females": total_unmarried_females,
        "analysis": analysis
    })