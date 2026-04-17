from django.shortcuts import render
from .models import Skill, Technologies, WorkExperience, Project, Education, Languages

def portfolio(request):
    return render(request, "index.html", {
        "skills": Skill.objects.all(),
        "technologies": Technologies.objects.all(),
        "experiences": WorkExperience.objects.all().order_by('-start_date'),
        "projects": Project.objects.all(),
        "education": Education.objects.all().order_by('-start_date'),
        "languages": Languages.objects.all(),
    })