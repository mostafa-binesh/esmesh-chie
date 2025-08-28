from django.contrib import admin, messages
from django.urls import path
from django import forms
from django.shortcuts import redirect, render
from .models import Person, CreditCard, PhoneNumber, Source
import csv
from datetime import datetime
import os
import pandas as pd


class ImportForm(forms.Form):
    file_path = forms.CharField(label='File path', max_length=500)
    source = forms.ChoiceField(choices=Source.choices)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'national_code', 'birthdate', 'source')
    search_fields = ('first_name', 'last_name', 'national_code')
    change_list_template = 'admin/people/person/change_list.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import/', self.admin_site.admin_view(self.import_view), name='people_person_import'),
        ]
        return custom_urls + urls

    def import_view(self, request):
        if request.method == 'POST':
            form = ImportForm(request.POST)
            if form.is_valid():
                file_path = form.cleaned_data['file_path']
                source = form.cleaned_data['source']
                inserted, updated = import_melli_file(file_path=file_path, source=source)
                messages.success(request, f'Imported successfully: {inserted} inserted, {updated} updated')
                return redirect('..')
        else:
            form = ImportForm()
        return render(request, 'admin/people/person/import.html', {'form': form})


@admin.register(CreditCard)
class CreditCardAdmin(admin.ModelAdmin):
    list_display = ('id', 'card_number', 'person', 'source')
    search_fields = ('card_number',)


class PhoneNumberForm(forms.ModelForm):
    numbers = forms.CharField(
        label='Phone Numbers',
        help_text='Enter one or more phone numbers separated by | character',
        required=False
    )

    class Meta:
        model = PhoneNumber
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Get all numbers for this person/source
            numbers = PhoneNumber.objects.filter(
                person=self.instance.person,
                source=self.instance.source
            ).values_list('number', flat=True)
            self.initial['numbers'] = '|'.join(numbers)


@admin.register(PhoneNumber)
class PhoneNumberAdmin(admin.ModelAdmin):
    form = PhoneNumberForm
    list_display = ('get_numbers', 'person', 'source')
    search_fields = ('number',)

    def get_numbers(self, obj):
        # Return all numbers for this person/source
        numbers = PhoneNumber.objects.filter(
            person=obj.person,
            source=obj.source
        ).values_list('number', flat=True)
        return '|'.join(numbers)
    get_numbers.short_description = 'Phone Numbers'

    def save_model(self, request, obj, form, change):
        numbers = form.cleaned_data.get('numbers', '').split('|')
        numbers = [n.strip() for n in numbers if n.strip()]
        
        # Always delete existing numbers for this person/source
        PhoneNumber.objects.filter(
            person=obj.person,
            source=obj.source
        ).delete()
        
        # Create new records for each number
        for number in numbers:
            PhoneNumber.objects.create(
                number=number,
                person=obj.person,
                source=obj.source
            )


# --- Importer utility for Melli CSV/XLSX schema ---
# Expected columns in the file (header present preferred):
# NATIONAL_CODE, CARD_NO, FULL_NAME, BIRTH_DATE, MOBILE
# Notes:
# - CARD_NO may appear in scientific notation in CSV; handle normalization to 16 digits.
# - FULL_NAME Persian encodings handled; pandas used for robustness.
# - BIRTH_DATE format like YYYY-MM-DD; we try to parse, else store NULL.
# Function to encode and decode a single string
# Define the encode_decode function
def encode_decode(value, source_encoding):
    if pd.isna(value) or not isinstance(value, str):  # Handle None, NaN, or non-strings
        return value
    try:
        return value.encode(source_encoding, errors='ignore').decode('utf-8', errors='ignore').strip()
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value.strip()  # Return trimmed original if encoding fails
def _open_rows(file_path):
    _, ext = os.path.splitext(file_path.lower())
    if ext in ['.csv', '.txt']:
        encodings = [
            'latin-1',
            'utf-8-sig',
            'utf-8',
            'windows-1256',
            'cp1256',
        ]
        last_err = None
        for enc in encodings:
            try:
                df = pd.read_csv(file_path, encoding=enc, dtype=str, keep_default_na=False)
                # Ensure strings and trimmed
                df = df.apply(lambda col: col.map(lambda v: encode_decode(v, enc)) if col.dtype == "object" else col)                # df = df.applymap(lambda v: (str(v).strip() if v is not None else ''))
                rows = [list(df.columns)] + df.values.tolist()
                return rows
            except Exception as e:
                last_err = e
            raise ValueError(f'Unable to read CSV with supported encodings: {last_err}')
    elif ext in ['.xlsx', '.xlsm']:
        try:
            df = pd.read_excel(file_path, dtype=str, engine='openpyxl')
            df = df.fillna('').applymap(lambda v: (str(v).strip().encode('windows-1252').decode('utf-8') if v is not None else ''))
            rows = [list(df.columns)] + df.values.tolist()
            return rows
        except Exception as e:
            raise ValueError(f'Unable to read Excel file: {e}')
    else:
        raise ValueError('Unsupported file extension. Use .csv or .xlsx')


def _normalize_card(card_raw: str) -> str:
    value = str(card_raw).strip()
    # Handle scientific notation like 6.03799E+15
    if 'e' in value.lower():
        try:
            num = float(value)
            value = f'{int(num):016d}'
        except Exception:
            pass
    value = ''.join(ch for ch in value if ch.isdigit())
    return value


def _fix_mojibake_text(value: str) -> str:
    """Fix common mojibake where UTF-8 bytes were decoded as latin-1 producing characters like 'Ø¹'.
    If that pattern is detected, try to re-decode via latin-1 -> utf-8.
    """
    if not value:
        return value
    if any(ch in value for ch in ['Ø', 'Ù', 'Ð', 'Â']):
        try:
            return value.encode('latin-1', errors='ignore').decode('utf-8', errors='ignore')
        except Exception:
            return value
    return value


def import_melli_file(file_path: str, source: str) -> tuple[int, int]:
    rows = _open_rows(file_path)
    inserted = 0
    updated = 0
    # Detect header row
    start_idx = 1 if rows and rows[0] and any(
        isinstance(cell, str) and any(h in cell.upper() for h in ['NATIONAL', 'CARD', 'FULL', 'BIRTH', 'MOBILE'])
        for cell in rows[0]
    ) else 0
    print(f"rows length: {len(rows)}")
    try:
        for row in rows[start_idx:]:
            # print('new row', datetime.now())
            if not row:
                continue
            national_code = (row[0] or '').strip() if len(row) > 0 else ''
            card_no_raw = row[1] if len(row) > 1 else ''
            full_name = _fix_mojibake_text((row[2] or '').strip()) if len(row) > 2 else ''
            birth_date_raw = (row[3] or '').strip() if len(row) > 3 else ''
            mobile_raw = (row[4] or '').strip() if len(row) > 4 else ''

            first_name = ''
            last_name = ''
            # Keep current behavior: store full name in first_name if requested earlier by user
            if full_name:
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

            if not national_code:
                continue

            if len(national_code) > 10:
                print(f"national code of {national_code} is too long")
                continue

            if len(card_number) > 16:
                print(f"national code of {national_code} is too long")
                continue

            person, created = Person.objects.update_or_create(
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'birthdate': birthdate,
                    'source': source,
                },
                national_code=national_code,
                source=source,
            )
            inserted += 1 if created else 0
            updated += 0 if created else 1

            if card_number:
                CreditCard.objects.update_or_create(
                    defaults={'person': person, 'source': source},
                    card_number=card_number,
                    source=source,
                )

        if mobile_raw:
            # Split multiple numbers by pipe
            mobiles = mobile_raw.split('|')
            for mobile in mobiles:
                mobile = ''.join(ch for ch in mobile if ch.isdigit())
                if mobile:
                    # Use update_or_create with new unique constraint
                    PhoneNumber.objects.update_or_create(
                        number=mobile,
                        person=person,
                        source=source,
                        defaults={}
                    )

        return inserted, updated
    except Exception as e:
        print(e)
        raise
