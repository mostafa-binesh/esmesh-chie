import pika
import json
import os
from django.db import transaction
from .models import Person, CreditCard, PhoneNumber, ImportJob, ImportJobStatus
from datetime import datetime
import pandas as pd
import math

def _normalize_card(card_raw: str) -> str:
    value = str(card_raw).strip()
    if 'e' in value.lower():
        try:
            num = float(value)
            value = f'{int(num):016d}'
        except Exception:
            pass
    value = ''.join(ch for ch in value if ch.isdigit())
    return value

def _fix_mojibake_text(value: str) -> str:
    if not value:
        return value
    try:
        return value.encode('windows-1252').decode('utf-8')
    except Exception:
        return value

def process_chunk(chunk_data):
    job = ImportJob.objects.get(id=chunk_data['job_id'])
    try:
        rows = chunk_data['rows']
        source = chunk_data['source']
        inserted = 0
        updated = 0
        
        with transaction.atomic():
            for row in rows:
                national_code = row.get('NATIONAL_CODE', '').strip()
                card_no_raw = row.get('CARD_NO', '')
                full_name = _fix_mojibake_text(row.get('FULL_NAME', '').strip())
                birth_date_raw = row.get('BIRTH_DATE', '').strip()
                mobile_raw = row.get('MOBILE', '').strip()

                first_name = full_name
                last_name = None

                birthdate = None
                if birth_date_raw:
                    date_val = str(birth_date_raw).replace('/', '-')
                    try:
                        birthdate = datetime.strptime(date_val, '%Y-%m-%d').date()
                    except Exception:
                        birthdate = None

                card_number = _normalize_card(card_no_raw)

                if not national_code or len(national_code) > 10 or len(card_number) > 16:
                    continue

                person, created = Person.objects.update_or_create(
                    national_code=national_code,
                    source=source,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'birthdate': birthdate,
                    }
                )
                inserted += 1 if created else 0
                updated += 0 if created else 1

                if card_number:
                    CreditCard.objects.update_or_create(
                        card_number=card_number,
                        source=source,
                        defaults={'person': person}
                    )

                if mobile_raw:
                    mobiles = mobile_raw.split('|')
                    for mobile in mobiles:
                        mobile = ''.join(ch for ch in mobile if ch.isdigit())
                        if mobile:
                            if mobile[0] != '0':
                                mobile = '0' + mobile
                            PhoneNumber.objects.update_or_create(
                                number=mobile,
                                person=person,
                                source=source,
                                defaults={}
                            )
        
        # Update processed chunks
        job.processed_chunks += 1
        if job.processed_chunks >= job.total_chunks:
            job.status = ImportJobStatus.COMPLETED
        job.save()
        
    except Exception as e:
        job.status = ImportJobStatus.FAILED
        job.error_message = str(e)
        job.save()
        raise

def start_rabbitmq_consumer():
    credentials = pika.PlainCredentials(
        os.environ.get('RABBITMQ_DEFAULT_USER', 'guest'),
        os.environ.get('RABBITMQ_DEFAULT_PASS', 'guest')
    )
    parameters = pika.ConnectionParameters(
        host=os.environ.get('RABBITMQ_HOST', 'rabbitmq'),
        port=int(os.environ.get('RABBITMQ_PORT', 5672)),
        credentials=credentials
    )
    
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue='import_queue', durable=True)
    
    def callback(ch, method, properties, body):
        try:
            chunk_data = json.loads(body)
            process_chunk(chunk_data)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"Error processing chunk: {e}")
    
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='import_queue', on_message_callback=callback)
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()
