from django.contrib import admin
from .models import Skill, Technologies, WorkExperience, TechnologiesForProject, Project, Education, Languages

# Register them all so they show up in the dashboard
admin.site.register(Skill)
admin.site.register(Technologies)
admin.site.register(WorkExperience)
admin.site.register(TechnologiesForProject)
admin.site.register(Project)
admin.site.register(Education)
admin.site.register(Languages)
