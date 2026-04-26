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
from .pdf_cv_generation_utils import generate_cv
import requests
from django.core.cache import cache
from decouple import config


GITHUB_CONTRIBUTIONS_CACHE_KEY = "github_contributions"


def _github_contribution_intensity(count):
    if count == 0:
        return 0
    if count < 3:
        return 1
    if count < 6:
        return 2
    if count < 10:
        return 3
    return 4


def _empty_github_contribution_context(message=None):
    return {
        "github_contributions_available": False,
        "github_contribution_weeks": [],
        "github_contributions": [],
        "github_total": 0,
        "github_username": config("GITHUB_USERNAME", default="Polclard"),
        "github_error": message,
        "contributions": [],
        "weeks": [],
        "total": 0,
    }

def get_github_contribution_context():
    cached_data = cache.get(GITHUB_CONTRIBUTIONS_CACHE_KEY)
    if cached_data is not None:
        return cached_data
        
    token = config("GITHUB_TOKEN", default="")
    username = config("GITHUB_USERNAME", default="Polclard")

    if not token:
        return _empty_github_contribution_context("GitHub token is not configured.")

    if not username:
        return _empty_github_contribution_context("GitHub username is not configured.")

    query = """
    query($username: String!) {
      user(login: $username) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
                color
              }
            }
          }
        }
      }
    }
    """

    try:
        response = requests.post(
            "https://api.github.com/graphql",
            json={
                "query": query,
                "variables": {"username": username}
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=8,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("errors"):
            raise ValueError(data["errors"][0].get("message", "GitHub returned an error."))

        calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]

        weeks = []
        days = []
        for week in calendar["weeks"]:
            contribution_days = []
            for day in week["contributionDays"]:
                contribution_day = {
                    **day,
                    "intensity": _github_contribution_intensity(day["contributionCount"]),
                }
                contribution_days.append(contribution_day)
                days.append(contribution_day)
            weeks.append({"contributionDays": contribution_days})

        context = {
            "github_contributions_available": True,
            "github_contribution_weeks": weeks,
            "github_contributions": days,
            "github_total": calendar["totalContributions"],
            "github_username": username,
            "github_error": None,
            "contributions": days,
            "weeks": weeks,
            "total": calendar["totalContributions"],
        }
        cache.set(GITHUB_CONTRIBUTIONS_CACHE_KEY, context, 60 * 60 * 6)
        return context
    except Exception as e:
        context = _empty_github_contribution_context(str(e))
        cache.set(GITHUB_CONTRIBUTIONS_CACHE_KEY, context, 60 * 5)
        return context


def portfolio(request):
    current_year = datetime.now().year
    context = {
        "skills": Skill.objects.all(),
        "technologies": Technologies.objects.all(),
        "experiences": WorkExperience.objects.all().order_by('-start_date'),
        "projects": Project.objects.all(),
        "education": Education.objects.all().order_by('-start_date'),
        "languages": Languages.objects.all(),
        "current_year": current_year,
    }
    context.update(get_github_contribution_context())
    return render(request, "index.html", context)

WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", default=os.getenv("GITHUB_WEBHOOK_SECRET", ""))

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

def download_cv_pdf(request):
    pdf = generate_cv()
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="Alen_Jangelov_CV.pdf"'
    return response

def github_contributions(request):
    return render(request, "github_contributions.html", get_github_contribution_context())
