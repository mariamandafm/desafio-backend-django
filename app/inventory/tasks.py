from celery import shared_task
import csv
import io
from core.models import AutoPart


@shared_task
def import_auto_parts_from_csv(csv_file):
    """Reads a CSV file and imports auto parts into the database."""
    csv_file = io.StringIO(csv_file)
    reader = csv.DictReader(csv_file)

    bulk_data = []
    errors = []

    for index, row in enumerate(reader):
        try:
            bulk_data.append(
                AutoPart(
                    name=row['nome'],
                    description=row['descricao'],
                    price=float(row['preco']),
                    stock_quantity=int(row['quantidade_inicial'])
                )
            )
        except Exception as e:
            errors.append(f"Linha {index+2}: Erro. {e}")

    if bulk_data:
        try:
            AutoPart.objects.bulk_create(bulk_data)
            return f"Importação concluída. {len(bulk_data)} peças criadas. {len(errors)} erros."
        except Exception as e:
            return f"Falha crítica na importação. Nenhuma peça foi criada. Erro: {e}"

    return f"Importação finalizada. Nenhuma peça nova para criar. {len(errors)} erros."


@shared_task
def replenish_stock():
    """Replenishes stock for auto parts that are below 10."""
    low_stock_parts = AutoPart.objects.filter(stock_quantity__lt=10)

    count = low_stock_parts.count()

    if count > 0:
        low_stock_parts.update(stock_quantity=10)
        return f"Reabastecimento concluído. {count} peças reabastecidas."

    return "Nenhuma peça precisa de reabastecimento."
