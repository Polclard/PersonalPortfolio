from django.db import models

class Skill(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200)

    def __str__(self):
        return self.name # Fixed

class Technologies(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200)

    def __str__(self):
        return self.name # Fixed

class WorkExperience(models.Model):
    title = models.CharField(max_length=100)
    company = models.CharField(max_length=100) # Added max_length
    description = models.TextField() # Changed to TextField for longer text
    is_current_working_place = models.BooleanField(default=False)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} at {self.company}"

class TechnologiesForProject(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Project(models.Model):
    emoji = models.CharField(max_length=10, default="🚀")
    title = models.CharField(max_length=100)
    description = models.TextField()
    technologies_for_project = models.ManyToManyField(TechnologiesForProject)
    link_to_github_repository = models.URLField(null=True, blank=True)
    link_to_live_demo = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.title
    
class Education(models.Model):
    title = models.CharField(max_length=100)
    school_name = models.CharField(max_length=100, default="University")
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title

class Languages(models.Model):
    emoji = models.CharField(max_length=10, default="🇲🇰")
    language_name = models.CharField(max_length=100)

    def __str__(self):
        return self.language_name