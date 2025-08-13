from django.shortcuts import render, redirect
from collections import defaultdict
from .models import RIASECResult, ProgramRecommendation
from django.db.models import Q
from itertools import permutations
import random
from django.views.decorators.csrf import csrf_exempt
from itertools import permutations
import uuid
import requests
import logging
from django.utils.timezone import now

logger = logging.getLogger(__name__)

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
    if not request.session.session_key:
        request.session.save()
    return render(request, 'main/test.html', {'questions': questions})

def expand_code_if_needed(top_types, scores_dict):
    """Возвращает всегда 3 буквы кода, дополняя недостающие по убыванию баллов."""
    if len(top_types) >= 3:
        return top_types[:3]
    all_sorted = sorted(scores_dict.items(), key=lambda x: x[1], reverse=True)
    add = [t for t, _ in all_sorted if t not in top_types]
    res = list(top_types)
    while len(res) < 3 and add:
        res.append(add.pop(0))
    return res[:3]

WEBHOOK_URL = 'https://octs.guap.ru/services/n8n/webhook/webhook/84f646dc-8c27-46dd-b2d6-a57e0cf7b09b'

def test_result(request):
    if not request.session.session_key:
        request.session.save()
    if request.method != 'POST':
        return redirect('test')

    # коэффициенты
    type_weights = {'R': 1.3, 'I': 1.2, 'A': 0.7, 'S': 0.8, 'E': 0.9, 'C': 1.4}

    # подсчёт «сырых» баллов
    raw = defaultdict(int)
    for q_id in range(1, 13):
        ans = request.POST.get(f'q{q_id}')
        if ans in type_weights:
            raw[ans] += 1

    # применение коэффициентов
    scores = {k: round(raw[k] * type_weights.get(k, 1.0), 2) for k in raw}
    scores_dict = dict(scores)

    # сортировка и топы
    sorted_results = sorted(scores_dict.items(), key=lambda x: x[1], reverse=True)
    top_types = [t for t, v in sorted_results if v > 0]

    # всегда делаем код из 3 букв
    code3 = expand_code_if_needed(top_types, scores_dict)
    riasec_code = ''.join(code3)

    match_type = "exact"
    recommended_programs = []

    POPULAR_CODES_BY_LEAD = {
        'I': ['ICR', 'IRE', 'IEC', 'IRC', 'IAC'],
        'A': ['AIC', 'AIE', 'AES', 'ARS'],
        'C': ['CIR', 'CRI', 'CIE', 'CRE', 'CES'],
        'R': ['RIC', 'RCI', 'REI'],
        'E': ['ESC'],
    }

    if len(top_types) == 1:
        lead = top_types[0]
        used_ids = set()
        for code in POPULAR_CODES_BY_LEAD.get(lead, []):
            qs = ProgramRecommendation.objects.filter(riasec_type=code).exclude(id__in=used_ids)
            if qs.exists():
                p = qs.order_by('?').first()
                recommended_programs.append(p)
                used_ids.add(p.id)
            if len(recommended_programs) >= 5:
                break
    elif len(top_types) == 2:
        all_types = {'R', 'I', 'A', 'S', 'E', 'C'}
        candidates = [''.join(top_types + [t]) for t in all_types - set(top_types)]
        match_type = "short"
        recommended_programs = list(ProgramRecommendation.objects.filter(riasec_type__in=candidates))
    else:
        recommended_programs = list(ProgramRecommendation.objects.filter(riasec_type=riasec_code))
        match_type = "permutation"
        perms = [''.join(p) for p in permutations(code3, 3)]
        recommended_programs = list(ProgramRecommendation.objects.filter(riasec_type__in=perms))

        if len(recommended_programs) < 5:
            match_type = "similar"
            all_codes = ProgramRecommendation.objects.values_list('riasec_type', flat=True).distinct()
            similar = []
            for code in all_codes:
                if len(code) == 3 and sum(1 for c in code if c in code3) >= 2:
                    similar.append(code)

            already_ids = set(p.id for p in recommended_programs)
            additional = ProgramRecommendation.objects.filter(riasec_type__in=similar).exclude(id__in=already_ids)
            recommended_programs += list(additional[:5 - len(recommended_programs)])
        if not recommended_programs:
            match_type = "similar"
            all_codes = ProgramRecommendation.objects.values_list('riasec_type', flat=True).distinct()
            similar = []
            for code in all_codes:
                if len(code) == 3 and sum(1 for c in code if c in code3) >= 2:
                    similar.append(code)
            recommended_programs = list(ProgramRecommendation.objects.filter(riasec_type__in=similar))

    recommended_programs = recommended_programs[:5]
    final_direction = recommended_programs[0].program_name if recommended_programs else ""

    # сохраняем в БД (как было)
    result = RIASECResult(
        user=request.user if request.user.is_authenticated else None,
        session_key=request.session.session_key if not request.user.is_authenticated else None,
        realistic=scores_dict.get('R', 0),
        investigative=scores_dict.get('I', 0),
        artistic=scores_dict.get('A', 0),
        social=scores_dict.get('S', 0),
        enterprising=scores_dict.get('E', 0),
        conventional=scores_dict.get('C', 0),
        primary_type=code3[0] if len(code3) > 0 else 'R',
        secondary_type=code3[1] if len(code3) > 1 else 'I',
        tertiary_type=code3[2] if len(code3) > 2 else 'A',
    )
    result.save()

    # стабильный session_id (ключ Django‑сессии)
    session_id = request.session.session_key
    if not session_id:
        request.session.save()
        session_id = request.session.session_key
    request.session['session_id'] = session_id  # пригодится в nps_submit

    # список всех направлений: "код — название"
    programs_list = [f"{p.program_code} — {p.program_name}" for p in recommended_programs]

    # отправка на вебхук
    payload = {
        "type": "test_result",
        "session_id": session_id,
        "code": riasec_code,
        "programs": programs_list,
        "timestamp": now().isoformat(),
    }
    try:
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=4)
        logger.info("[WEBHOOK] test_result sent: %s", resp.status_code)
    except Exception as e:
        logger.exception("WEBHOOK send error: %s", e)

    context = {
        'scores': scores_dict,
        'sorted_results': sorted_results,
        'top_types': code3,
        'recommended_programs': recommended_programs,
        'match_type': match_type,
        'session_id': session_id,
    }
    return render(request, 'main/test_result.html', context)

@csrf_exempt
def nps_submit(request):
    if request.method == 'POST':
        score = request.POST.get('score')
        session_id = request.POST.get('session_id') or request.session.get('session_id')

        payload = {
            "type": "nps_feedback",
            "session_id": session_id,
            "score": score,
            "timestamp": now().isoformat(),
        }
        try:
            requests.post(WEBHOOK_URL, json=payload, timeout=4)
        except Exception as e:
            logger.exception("NPS webhook error: %s", e)

        return render(request, 'main/thanks.html')

    return redirect('test')
