from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from meeting_reservation_system.models import SupportTicket


class Command(BaseCommand):
    help = 'Автоматически закрывает старые тикеты'

    def handle(self, *args, **options):
        three_days_ago = timezone.now() - timedelta(days=3)

        # Находим тикеты в работе, где не было активности более 3 дней
        old_tickets = SupportTicket.objects.filter(
            status='in_progress',
            last_activity__lte=three_days_ago
        )

        tickets_count = old_tickets.count()

        # Закрываем тикеты
        for ticket in old_tickets:
            ticket.status = 'closed'
            ticket.save()

        self.stdout.write(
            self.style.SUCCESS(f'✅ Закрыто {tickets_count} тикетов')
        )