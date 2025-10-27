from django.test import TestCase
from decimal import Decimal
from core.models import AutoPart
from inventory.tasks import import_auto_parts_from_csv


class TaskLogicTests(TestCase):
    """Tests for the import_auto_parts_from_csv task logic."""

    def test_import_auto_parts_from_csv(self):
        csv_content = (
            "nome,descricao,preco,quantidade_inicial\n"
            "Part A,Description A,10.50,20\n"
            "Part B,Description B,15.75,30\n"
            "Part C,Description C,20.00,40\n"
        )

        result_message = import_auto_parts_from_csv(csv_content)

        self.assertIn("3 peças criadas", result_message)
        self.assertEqual(AutoPart.objects.count(), 3)

        part_a = AutoPart.objects.get(name="Part A")
        self.assertEqual(part_a.description, "Description A")
        self.assertEqual(part_a.price, Decimal('10.50'))
        self.assertEqual(part_a.stock_quantity, 20)

    def test_import_auto_parts_from_csv_with_errors(self):
        csv_content = (
            "nome,descricao,preco,quantidade_inicial\n"
            "Part A,Description A,invalid_price,20\n"
            "Part B,Description B,15.75,invalid_quantity\n"
            "Part C,Description C,20.00,40\n"
        )

        result_message = import_auto_parts_from_csv(csv_content)

        self.assertIn("1 peças criadas", result_message)
        self.assertIn("2 erros", result_message)
        self.assertEqual(AutoPart.objects.count(), 1)

        part_c = AutoPart.objects.get(name="Part C")
        self.assertEqual(part_c.description, "Description C")
        self.assertEqual(part_c.price, Decimal('20.00'))
        self.assertEqual(part_c.stock_quantity, 40)
