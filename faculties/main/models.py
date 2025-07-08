from django.db import models
from django.contrib.auth.models import User


class RIASECResult(models.Model):
    RIASEC_TYPES = [
        ('R', 'Реалистичный'),
        ('I', 'Интеллектуальный'),
        ('A', 'Артистичный'),
        ('S', 'Социальный'),
        ('E', 'Предприимчивый'),
        ('C', 'Конвенциональный'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    date_taken = models.DateTimeField(auto_now_add=True)

    # Результаты по каждому типу
    realistic = models.PositiveIntegerField(default=0)
    investigative = models.PositiveIntegerField(default=0)
    artistic = models.PositiveIntegerField(default=0)
    social = models.PositiveIntegerField(default=0)
    enterprising = models.PositiveIntegerField(default=0)
    conventional = models.PositiveIntegerField(default=0)

    # Топ-3 типа
    primary_type = models.CharField(max_length=1, choices=RIASEC_TYPES)
    secondary_type = models.CharField(max_length=1, choices=RIASEC_TYPES)
    tertiary_type = models.CharField(max_length=1, choices=RIASEC_TYPES)

    class Meta:
        ordering = ['-date_taken']
        verbose_name = 'Результат теста RIASEC'
        verbose_name_plural = 'Результаты тестов RIASEC'

    def __str__(self):
        return f"Результат {self.pk} ({self.get_primary_type_display()})"

    def get_scores_dict(self):
        """Возвращает результаты в виде словаря"""
        return {
            'R': self.realistic,
            'I': self.investigative,
            'A': self.artistic,
            'S': self.social,
            'E': self.enterprising,
            'C': self.conventional
        }

    def get_top_types(self):
        """Возвращает топ-3 типа в порядке убывания"""
        scores = self.get_scores_dict()
        sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [t[0] for t in sorted_types[:3]]

class ProgramRecommendation(models.Model):

    riasec_type = models.CharField(max_length=3)
    program_name = models.CharField(max_length=200)
    description = models.TextField()
    skills = models.TextField(help_text="Перечислите навыки через запятую")
    ege_subjects = models.TextField(
        help_text="Необходимые ЕГЭ (через запятую): Математика, Русский язык, Физика и т.д."
    )
    entrance_tests = models.TextField(
        blank=True,
        default='',
        help_text="Необходимые ВИ (через запятую)..."
    )
    professions = models.TextField(help_text="Перечислите профессии через запятую")
    program_code = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.program_code} ({self.riasec_type})"

    def get_skills_list(self):
        return [s.strip() for s in self.skills.split(',')]

    def get_ege_list(self):
        return [e.strip() for e in self.ege_subjects.split(',')]

    def get_professions_list(self):
        return [p.strip() for p in self.professions.split(',')]

    def get_vi_list(self):
        return [v.strip() for v in self.entrance_tests.split(',')]