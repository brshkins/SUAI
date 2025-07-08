from django.core.management.base import BaseCommand
from main.models import ProgramRecommendation
import pandas as pd
import os

class Command(BaseCommand):
    help = 'Загрузка программ из CSV с помощью pandas с валидацией'

    def handle(self, *args, **options):
        file_path = os.path.join('main', 'data', 'гуап.csv')
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'❌ Файл не найден: {file_path}'))
            return

        try:
            df = pd.read_csv(file_path, sep=';', encoding='utf-8-sig', quotechar='"', on_bad_lines='skip')
            print(f"всего строк: {len(df)}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка при чтении CSV: {e}'))
            return

        ProgramRecommendation.objects.all().delete()
        count = 0

        for index, row in df.iterrows():
            try:
                raw_riasec = str(row.get('riasec', '')).strip()
                riasec = ''.join(c for c in raw_riasec.upper() if c.isalpha())

                if len(riasec) != 3:
                    self.stdout.write(
                        self.style.WARNING(f"⛔ Пропуск строки {index + 1}: некорректный код RIASEC '{raw_riasec}'"))
                    continue

                program_name = str(row['название программы']).strip()
                description = str(row['описание']).strip()

                ProgramRecommendation.objects.create(
                    riasec_type=riasec,
                    program_name=program_name,
                    description=description,
                    skills=str(row['навыки']).strip(),
                    professions=str(row['профессии']).strip(),
                    ege_subjects=str(row['егэ']).strip(),
                    entrance_tests=str(row['ви']).strip(),
                    program_code=''  # можешь позже подставить код направления, если нужно
                )
                self.stdout.write(self.style.SUCCESS(f'✅ Импортировано: {program_name} — {description[:30]}...'))
                count += 1

            except Exception as e:
                self.stdout.write(self.style.WARNING(f'🔥 Ошибка в строке {index + 1}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'🎯 Итог: импортировано {count} программ.'))