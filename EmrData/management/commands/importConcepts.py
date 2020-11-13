from django.core.management.base import BaseCommand
import csv
from django.db import transaction
from EmrData.OMOPModels.vocabularyModels import *
from Utility.resource import checkCsvColumns, getRowCount
from Utility.progress import printProgressBar

import pytz
from datetime import datetime


class Command(BaseCommand):

    help = 'Import OMOP CONCEPT.csv.'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, help="File path to CONCEPT.CSV")

    def handle(self, *args, **kwargs):
        expectedColumns = ['concept_id', 'concept_name', 'domain_id', 'vocabulary_id', 'concept_class_id',
                           'standard_concept', 'concept_code', 'valid_start_date', 'valid_end_date', 'invalid_reason']

        filePath = kwargs.get('path')
        timeZone = pytz.timezone('UTC')

        print(f"Importing OMOP concepts from: {filePath}")

        if not filePath:
            print("File path not specified.")
            return

        maxRow = getRowCount(filePath) - 1

        with open(filePath, 'r') as f:
            csvReader = csv.reader(f, delimiter='\t')

            columns = next(csvReader)
            checkCsvColumns(expectedColumns, columns)

            createdCounter = 0
            updatedCounter = 0

            with transaction.atomic():

                for i, row in enumerate(csvReader):
                    row = [item.strip() for item in row]

                    concept_id, concept_name, _, _, _, standard_concept, concept_code, valid_start_date, valid_end_date, invalid_reason = row

                    defaults = {
                        'concept_id': concept_id,
                        'concept_code': concept_code,
                        'concept_name': concept_name,
                        'standard_concept': standard_concept,
                        'valid_start_date': timeZone.localize(datetime.strptime(valid_start_date, '%Y%m%d')),
                        'valid_end_date': timeZone.localize(datetime.strptime(valid_end_date, '%Y%m%d')),
                        'invalid_reason': invalid_reason,
                    }

                    _, created = CONCEPT.objects.update_or_create(concept_id=concept_id, defaults=defaults)

                    if created:
                        createdCounter += 1
                    else:
                        updatedCounter += 1

                    if i % 500 == 0:
                        printProgressBar(i, maxRow, prefix="Importing OMOP CONCEPTS: ",
                                         suffix=f"{'{:,}'.format(i)}/{'{:,}'.format(maxRow)}", decimals=2, length=5)

            print(
                f"Finished importing OMOP concepts: {createdCounter} concepts created, {updatedCounter} concepts updated.")
