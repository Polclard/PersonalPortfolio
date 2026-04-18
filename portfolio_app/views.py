from django.shortcuts import render
from django.http import HttpResponse, HttpResponseForbidden
from .models import Skill, Technologies, WorkExperience, Project, Education, Languages
import git
from django.views.decorators.csrf import csrf_exempt
import hashlib
import os
import hmac

def portfolio(request):
    return render(request, "index.html", {
        "skills": Skill.objects.all(),
        "technologies": Technologies.objects.all(),
        "experiences": WorkExperience.objects.all().order_by('-start_date'),
        "projects": Project.objects.all(),
        "education": Education.objects.all().order_by('-start_date'),
        "languages": Languages.objects.all(),
    })

WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET", "")

@csrf_exempt
def git_update(request):
    if request.method != "POST":
        return HttpResponseForbidden("Only POST allowed")

    # check secret from URL
    provided_secret = request.GET.get("secret")
    if provided_secret != WEBHOOK_SECRET:
        return HttpResponseForbidden("Invalid secret")

    try:
        repo = git.Repo("/home/alenjangelov/PersonalPortfolio")
        origin = repo.remotes.origin

        origin.fetch()
        repo.git.checkout("main")
        repo.git.reset("--hard", "origin/main")

        return HttpResponse("Updated successfully", status=200)

    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)