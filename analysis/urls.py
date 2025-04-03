from django.urls import path
from .views import general_analysis_view, secretary_general_analysis_view, accountant_general_analysis_view  # Import the new view

urlpatterns = [
    path('general-analysis/', general_analysis_view, name='general_analysis'),
    path('secretary-general-analysis/', secretary_general_analysis_view, name='secretary_general_analysis'),
    path('accountant-general-analysis/', accountant_general_analysis_view, name='accountant_general_analysis'),
]
