from django.shortcuts import render
from .models import Skill, Technologies, WorkExperience, Project, Education, Languages
import git 

def portfolio(request):
    return render(request, "index.html", {
        "skills": Skill.objects.all(),
        "technologies": Technologies.objects.all(),
        "experiences": WorkExperience.objects.all().order_by('-start_date'),
        "projects": Project.objects.all(),
        "education": Education.objects.all().order_by('-start_date'),
        "languages": Languages.objects.all(),
    })

def git_update(request):
    repo = git.Repo('./PersonalPortfolio')
    origin = repo.remotes.origin
    repo.create_head('main', origin.refs.main).set_tracking_branch(origin.refs.main).checkout()
    origin.pull()
    return '', 200