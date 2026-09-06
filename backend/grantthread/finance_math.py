"""Exact entered receipt rates and immutable conversion snapshots; no market quotes."""
import re
from datetime import date
from decimal import Decimal, ROUND_HALF_UP, localcontext

from .errors import require

CURRENCIES = ('EUR', 'RON', 'CAD', 'USD', 'GBP', 'CHF', 'AUD', 'NZD')
CATEGORIES = ('1.1 Remuneration', '1.2 Subcontractor Fees', '1.3 Travel Costs',
              '1.4 Goods and Supplies', '1.5 Equipment Costs', '1.6 Project Administration Costs',
              '1.7 Sub-Grants less Sub-Grantee Indirects', '1.8 Indirect Costs', 'Uncategorised')


def currency(value):
    require(value in CURRENCIES, 'Choose a supported two-decimal currency: ' + ', '.join(CURRENCIES))
    return value


def iso_date(value):
    require(isinstance(value, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', value), 'Use a YYYY-MM-DD date')
    try:
        date.fromisoformat(value)
    except ValueError:
        require(False, 'Enter a valid date')
    return value


def parse_amount(value, signed=False):
    pattern = r'-?(?:0|[1-9]\d{0,9})(?:\.\d{1,2})?' if signed else r'(?:0|[1-9]\d{0,9})(?:\.\d{1,2})?'
    require(isinstance(value, str) and re.fullmatch(pattern, value.strip()), 'Use a decimal amount with at most two decimal places')
    return int(Decimal(value.strip()) * 100)


def amount_text(minor):
    return format(Decimal(minor) / 100, '.2f')


def normalize_rate(value, direction='report_per_source'):
    require(isinstance(value, str) and re.fullmatch(r'(?:0|[1-9]\d{0,5})(?:\.\d{1,18})?', value.strip()),
            'Enter a positive exchange rate with up to 18 decimal places')
    require(direction in {'report_per_source', 'source_per_report'}, 'Choose the exchange-rate direction')
    rate = Decimal(value.strip())
    require(Decimal('0.000001') <= rate <= Decimal('100000'), 'Exchange rate must be between 0.000001 and 100000')
    with localcontext() as ctx:
        ctx.prec = 40
        if direction == 'source_per_report':
            rate = Decimal(1) / rate
        require(Decimal('0.000001') <= rate <= Decimal('100000'), 'Normalised rate is outside the supported range')
        return format(rate.quantize(Decimal('0.000000000000000001'), rounding=ROUND_HALF_UP).normalize(), 'f')


def convert_minor(amount, rate):
    with localcontext() as ctx:
        ctx.prec = 40
        result = int((Decimal(amount) * Decimal(rate)).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    require(abs(result) <= 999_999_999_999, 'Converted amount exceeds the supported limit')
    return result


def conversion(data, entry):
    grant = data['grants'][entry['grantId']]
    source, target = currency(entry['currency']), currency(grant['currency'])
    mode = entry.get('conversionMode', 'same_currency')
    details = {'sourceCurrency': source, 'reportCurrency': target, 'mode': mode}
    if source == target:
        rate = '1'
        details['mode'] = 'same_currency'
    elif mode == 'manual':
        rate = normalize_rate(entry.get('manualRate'))
    elif mode == 'receipt':
        receipt = data.get('fundingReceipts', {}).get(entry.get('receiptId'))
        if not entry.get('receiptId'):
            eligible = [r for r in data.get('fundingReceipts', {}).values() if r.get('useAsDefault') is True
                        and r['grantId'] == entry['grantId'] and r['sourceCurrency'] == source
                        and r['reportCurrency'] == target and r['receivedDate'] <= entry['date']]
            receipt = sorted(eligible, key=lambda r: (r['receivedDate'], r.get('createdAt', '')))[-1] if eligible else None
            details['automaticReceipt'] = True
        require(receipt and receipt['grantId'] == entry['grantId'] and receipt['sourceCurrency'] == source
                and receipt['reportCurrency'] == target, 'Record an eligible automatic receipt, or choose a matching receipt for this grant and currency')
        require(receipt['receivedDate'] <= entry['date'], 'Funds receipt is dated after this entry; choose an earlier receipt or an explicit manual rate')
        rate = receipt['rate']
        details.update(receiptId=receipt['id'], receivedDate=receipt['receivedDate'])
    elif mode == 'weighted_average':
        receipts = [r for r in data.get('fundingReceipts', {}).values() if r['grantId'] == entry['grantId']
                    and r['sourceCurrency'] == source and r['reportCurrency'] == target and r['receivedDate'] <= entry['date']]
        require(receipts, 'Record matching funds received on or before this entry date first')
        with localcontext() as ctx:
            ctx.prec = 40
            # Weight by actual local funds received, never an unweighted mean of rates.
            rate = format((sum(Decimal(r['sourceAmountMinor']) * Decimal(r['rate']) for r in receipts)
                           / sum(r['sourceAmountMinor'] for r in receipts)).quantize(Decimal('0.000000000000000001'), rounding=ROUND_HALF_UP).normalize(), 'f')
        details['receiptIds'] = sorted(r['id'] for r in receipts)
    else:
        require(False, 'Select a receipt, weighted receipt rate or explicit manual rate for currency conversion')
    return {**details, 'rate': rate, 'reportAmountMinor': convert_minor(entry['sourceAmountMinor'], rate)}
