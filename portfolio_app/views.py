from django.shortcuts import render
from django.http import HttpResponse, HttpResponseForbidden
from .models import Skill, Technologies, WorkExperience, Project, Education, Languages
import git
from django.views.decorators.csrf import csrf_exempt
import hashlib
import os
import hmac
import subprocess
from datetime import datetime

def portfolio(request):
    current_year = datetime.now().year
    return render(request, "index.html", {
        "skills": Skill.objects.all(),
        "technologies": Technologies.objects.all(),
        "experiences": WorkExperience.objects.all().order_by('-start_date'),
        "projects": Project.objects.all(),
        "education": Education.objects.all().order_by('-start_date'),
        "languages": Languages.objects.all(),
        "current_year": current_year,
    })

WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")

@csrf_exempt
def git_update(request):
    if request.method != "POST":
        return HttpResponseForbidden("Only POST allowed")

    if not WEBHOOK_SECRET:
        return HttpResponse("GITHUB_WEBHOOK_SECRET is not set", status=500)

    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        return HttpResponseForbidden("Missing signature")

    digest = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        msg=request.body,
        digestmod=hashlib.sha256
    ).hexdigest()

    expected_signature = f"sha256={digest}"

    if not hmac.compare_digest(signature, expected_signature):
        return HttpResponseForbidden("Invalid signature")

    try:
        repo = git.Repo("/home/alenjangelov/PersonalPortfolio")
        repo.git.checkout("main")
        repo.git.pull("origin", "main")

        subprocess.run(  
            ["/home/alenjangelov/.virtualenvs/PersonalPortfolio-env/bin/pip", "install", "-r", "requirements.txt"],  
            cwd="/home/alenjangelov/PersonalPortfolio",  
            check=True  
        )  
        
        subprocess.run(  
            ["/home/alenjangelov/.virtualenvs/PersonalPortfolio-env/bin/python", "manage.py", "migrate"],  
            cwd="/home/alenjangelov/PersonalPortfolio",  
            check=True  
        )  

        subprocess.run(
            ["/usr/bin/touch", "/var/www/alenjangelov_pythonanywhere_com_wsgi.py"],
            check=True
        )

        return HttpResponse("Updated successfully", status=200)

    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)