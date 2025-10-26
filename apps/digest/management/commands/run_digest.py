"""
Django команда для запуска пайплайна обработки новостей.
"""

from django.core.management.base import BaseCommand, CommandError
from apps.digest.services.pipeline_runner import run_pipeline_for_project
from apps.digest.models import Project


class Command(BaseCommand):
    help = 'Запускает пайплайн обработки новостей для проекта'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project-id',
            type=int,
            help='ID проекта для запуска (если не указан, используется активный проект)',
        )
        parser.add_argument(
            '--list-projects',
            action='store_true',
            help='Показать список всех проектов',
        )

    def handle(self, *args, **options):
        # Показываем список проектов
        if options['list_projects']:
            self.stdout.write(self.style.SUCCESS('📋 Список проектов:'))
            projects = Project.objects.all().order_by('-is_active', 'name')

            if not projects:
                self.stdout.write(self.style.WARNING('  Проектов не найдено. Создайте проект через админку.'))
                return

            for project in projects:
                status = '✅ АКТИВНЫЙ' if project.is_active else '❌ неактивный'
                self.stdout.write(f'  [{project.id}] {project.name} - {status}')
            return

        # Запускаем пайплайн
        project_id = options.get('project_id')

        try:
            self.stdout.write(self.style.SUCCESS('🚀 Запуск пайплайна...'))

            result = run_pipeline_for_project(project_id)

            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n✅ Пайплайн завершен успешно!\n"
                        f"   Проект: {result['project']}\n"
                        f"   Создано постов: {result['total_posts']}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"\n❌ Ошибка выполнения пайплайна!\n"
                        f"   Проект: {result['project']}\n"
                        f"   Ошибка: {result['error']}"
                    )
                )
                raise CommandError(result['error'])

        except ValueError as e:
            raise CommandError(str(e))
        except Exception as e:
            raise CommandError(f'Неожиданная ошибка: {str(e)}')
