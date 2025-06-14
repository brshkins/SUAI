from django.shortcuts import render, redirect
from collections import defaultdict
from .models import RIASECResult, ProgramRecommendation
from django.db.models import Q
from itertools import permutations


# 12 вопросов с вариантами RIASEC
questions = {
    1: {
        "text": "Какое занятие тебе кажется наиболее привлекательным?",
        "variants": {
            "R": "Починить сломанный механизм",
            "I": "Провести научное исследование",
            "A": "Нарисовать иллюстрацию",
            "S": "Выслушать человека в трудной ситуации",
            "E": "Организовать мероприятие",
            "C": "Упорядочить документы"
        }
    },
    2: {
        "text": "Как ты предпочитаешь решать проблемы?",
        "variants": {
            "R": "С практической стороны",
            "I": "Анализируя причины",
            "A": "Используя нестандартное мышление",
            "S": "Советуясь с другими",
            "E": "Принимая решения быстро",
            "C": "Следуя инструкциям"
        }
    },
    3: {
        "text": "Какое занятие тебе ближе всего?",
        "variants": {
            "R": "Работать руками (ремонт, строительство)",
            "I": "Решать сложные задачи",
            "A": "Творить (писать, петь, играть)",
            "S": "Обучать и помогать",
            "E": "Управлять и продавать идеи",
            "C": "Работать с бумагами и данными"
        }
    },
    4: {
        "text": "Что ты делаешь в свободное время?",
        "variants": {
            "R": "Что-нибудь мастерю",
            "I": "Читаю или изучаю новое",
            "A": "Занимаюсь творчеством",
            "S": "Общаюсь с друзьями",
            "E": "Занимаюсь проектами",
            "C": "Навожу порядок"
        }
    },
    5: {
        "text": "Какая работа кажется тебе наиболее интересной?",
        "variants": {
            "R": "Техник или инженер",
            "I": "Аналитик или учёный",
            "A": "Дизайнер или актёр",
            "S": "Педагог или психолог",
            "E": "Менеджер или предприниматель",
            "C": "Бухгалтер или администратор"
        }
    },
    6: {
        "text": "Что тебя больше всего мотивирует?",
        "variants": {
            "R": "Создавать что-то реальное",
            "I": "Понимать, как всё устроено",
            "A": "Самовыражение",
            "S": "Чувство, что помог другим",
            "E": "Достижение целей",
            "C": "Чёткая структура"
        }
    },
    7: {
        "text": "Что тебе легче всего даётся?",
        "variants": {
            "R": "Использовать инструменты",
            "I": "Делать выводы",
            "A": "Фантазировать",
            "S": "Сочувствовать",
            "E": "Вдохновлять людей",
            "C": "Поддерживать порядок"
        }
    },
    8: {
        "text": "Как ты принимаешь решения?",
        "variants": {
            "R": "На основе опыта",
            "I": "Логически и обоснованно",
            "A": "Интуитивно",
            "S": "С учётом чувств других",
            "E": "Смело и быстро",
            "C": "По правилам"
        }
    },
    9: {
        "text": "Какую роль ты обычно берешь в группе?",
        "variants": {
            "R": "Реализую идеи руками",
            "I": "Обдумываю и анализирую",
            "A": "Предлагаю креативные решения",
            "S": "Поддерживаю и помогаю",
            "E": "Руководитель и мотиватор",
            "C": "Организую процесс"
        }
    },
    10: {
        "text": "Как ты предпочитаешь работать?",
        "variants": {
            "R": "В реальном физическом мире",
            "I": "С данными и гипотезами",
            "A": "С идеями и образами",
            "S": "С людьми и чувствами",
            "E": "С проектами и задачами",
            "C": "С правилами и процедурами"
        }
    },
    11: {
        "text": "Какие качества ты ценишь в работе?",
        "variants": {
            "R": "Практическая польза",
            "I": "Интеллектуальный вызов",
            "A": "Креативность",
            "S": "Забота о других",
            "E": "Лидерство",
            "C": "Порядок и точность"
        }
    },
    12: {
        "text": "Где бы ты хотел оказаться через 5 лет?",
        "variants": {
            "R": "На производстве или в мастерской",
            "I": "В лаборатории или исследовательском центре",
            "A": "На сцене или в студии",
            "S": "В школе или центре помощи",
            "E": "Во главе команды",
            "C": "В офисе с чёткими задачами"
        }
    },
}
def index(request):
    return render(request, 'main/index.html')

def test_views(request):
    return render(request, 'main/test.html', {'questions': questions})

def test_result(request):
    if request.method != 'POST':
        return redirect('test')  # если не POST-запрос, уводим

    # Подсчёт баллов по каждому типу
    scores = defaultdict(int)
    for q_id in range(1, 13):
        answer = request.POST.get(f'q{q_id}')
        if answer in ['R', 'I', 'A', 'S', 'E', 'C']:
            scores[answer] += 1

    # Преобразуем и сортируем
    scores_dict = dict(scores)
    sorted_results = sorted(scores_dict.items(), key=lambda x: x[1], reverse=True)
    unique_types = []
    for t, score in sorted_results:
        if t not in unique_types:
            unique_types.append(t)
        if len(unique_types) == 3:
            break
    top_types = unique_types

    # Сохраняем результат в БД
    result = RIASECResult(
        user=request.user if request.user.is_authenticated else None,
        session_key=request.session.session_key if not request.user.is_authenticated else None,
        realistic=scores_dict.get('R', 0),
        investigative=scores_dict.get('I', 0),
        artistic=scores_dict.get('A', 0),
        social=scores_dict.get('S', 0),
        enterprising=scores_dict.get('E', 0),
        conventional=scores_dict.get('C', 0),
        primary_type=top_types[0] if len(top_types) > 0 else 'R',
        secondary_type=top_types[1] if len(top_types) > 1 else 'I',
        tertiary_type=top_types[2] if len(top_types) > 2 else 'A',
    )
    result.save()

    # Строгое совпадение трёхбуквенного кода
    riasec_code = ''.join(top_types[:3])
    recommended_programs = []
    match_type = "exact"

    # 1. Ищем точное совпадение
    recommended_programs = list(ProgramRecommendation.objects.filter(riasec_type=riasec_code))

    # 2. Перестановки
    if not recommended_programs:
        match_type = "permutation"
        perms = [''.join(p) for p in permutations(top_types, 3)]
        recommended_programs = list(
            ProgramRecommendation.objects.filter(riasec_type__in=perms)
        )

    # 3. Похожие по 2/3 буквам
    if not recommended_programs:
        match_type = "similar"
        all_codes = ProgramRecommendation.objects.values_list('riasec_type', flat=True).distinct()
        similar_codes = []
        for code in all_codes:
            if len(code) != 3:
                continue
            match_count = sum(1 for c in code if c in top_types)
            if match_count >= 2:
                similar_codes.append(code)

        recommended_programs = list(ProgramRecommendation.objects.filter(riasec_type__in=similar_codes))

    context = {
        'scores': scores_dict,
        'sorted_results': sorted_results,
        'top_types': top_types,
        'recommended_programs': recommended_programs,
        'match_type': match_type
    }

    return render(request, 'main/test_result.html', context)