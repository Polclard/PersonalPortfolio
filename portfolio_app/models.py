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
    
class PageVisit(models.Model):
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    ip_hash = models.CharField(max_length=64, blank=True, db_index=True)
    user_agent = models.CharField(max_length=255, blank=True)
    referrer = models.CharField(max_length=255, blank=True)
    session_key = models.CharField(max_length=100, blank=True)
    visited_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.path} - {self.visited_at}"


class ClickEvent(models.Model):
    element = models.CharField(max_length=255)
    element_id = models.CharField(max_length=255, blank=True)
    element_class = models.CharField(max_length=255, blank=True)
    text = models.CharField(max_length=255, blank=True)
    page = models.CharField(max_length=255)
    target_url = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    ip_hash = models.CharField(max_length=64, blank=True, db_index=True)
    user_agent = models.CharField(max_length=255, blank=True)
    referrer = models.CharField(max_length=255, blank=True)
    session_key = models.CharField(max_length=100, blank=True)
    clicked_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.element} on {self.page} - {self.clicked_at}"


class DailyPageVisit(models.Model):
    date = models.DateField(db_index=True)
    path = models.CharField(max_length=255)
    visit_count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("date", "path"), name="unique_daily_page_visit")
        ]
        ordering = ("-date", "path")

    def __str__(self):
        return f"{self.date} {self.path} ({self.visit_count})"


class DailyClickAggregate(models.Model):
    date = models.DateField(db_index=True)
    page = models.CharField(max_length=255)
    element = models.CharField(max_length=255)
    target_url = models.CharField(max_length=500, blank=True)
    click_count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("date", "page", "element", "target_url"),
                name="unique_daily_click_aggregate",
            )
        ]
        ordering = ("-date", "page", "element")

    def __str__(self):
        return f"{self.date} {self.page} {self.element} ({self.click_count})"
