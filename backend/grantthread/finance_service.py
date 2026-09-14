"""Private financial imports and human-confirmed ledger changes."""
import base64
import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import PurePath

from .errors import DomainError, require
from .finance_math import CATEGORIES, CURRENCIES, MAX_AMOUNT_MINOR, amount_text, conversion, convert_minor, currency, iso_date, normalize_rate, parse_amount
from .service import Service, clean_text, new_id, now

ENTRY_KINDS = {'expense', 'refund', 'transfer', 'income', 'adjustment', 'payment_match', 'unclassified'}


def public_import(item):
    return {k: copy.deepcopy(v) for k, v in item.items() if k not in {'objectKey', 'parsedKey'}}


def expected(record, body):
    require(type(body.get('expectedVersion')) is int and body['expectedVersion'] == record['version'],
            'This record changed. Refresh and review the latest version.', 'stale', 409)


def grant_in(data, key):
    require(isinstance(key, str) and key in data['grants'], 'Grant not found in your workspace', 'not_found', 404)
    return data['grants'][key]


def entry_in(data, key):
    require(isinstance(key, str) and key in data.get('financeEntries', {}), 'Financial entry not found', 'not_found', 404)
    return data['financeEntries'][key]


def import_in(data, key):
    require(isinstance(key, str) and key in data.get('financeImports', {}), 'Financial import not found', 'not_found', 404)
    return data['financeImports'][key]


class FinancialService(Service):
    def overview(self):
        data = self.data()
        imports = [public_import(item) for item in data.get('financeImports', {}).values()]
        return {'grants': self.grants(), 'expenses': list(data['expenses'].values()), 'receipts': list(data.get('fundingReceipts', {}).values()),
                'entries': [self.project_entry(data, e) for e in data.get('financeEntries', {}).values()],
                'imports': [i for i in imports if i['kind'] != 'template'],
                'templates': [i for i in imports if i['kind'] == 'template'],
                'currencies': list(CURRENCIES), 'categories': list(CATEGORIES)}

    def create_grant(self, body):
        self.grantee()
        name = clean_text(body.get('name'), 'Grant name', 100)
        funder = clean_text(body.get('funderName'), 'Funder name', 100)
        code = currency(body.get('currency'))
        award = parse_amount(body.get('award'))
        def commit(data):
            require(len(data['grants']) < 30, 'This workspace supports up to 30 grants')
            key = new_id('grant')
            grant = {'id': key, 'name': name, 'granteeOrgId': self.org_id, 'funderOrgId': new_id('funder'),
                     'funderName': funder, 'currency': code, 'awardMinor': award, 'fundingMode': 'Configured financial reporting',
                     'template': 'riverbend-financial', 'deadline': None, 'version': 1, 'rulesConfirmed': False, 'synthetic': False}
            data['grants'][key] = grant
            data['factVersion'] += 1
            self.audit(data, 'grant_created', key)
            return self.grant(data, key)
        return self.repository.mutate(self.org_id, commit)

    def add_receipt(self, body):
        self.grantee()
        source = currency(body.get('sourceCurrency'))
        received = iso_date(body.get('receivedDate'))
        require(received <= now()[:10], 'A received-funds date cannot be in the future')
        amount = parse_amount(body.get('sourceAmount'))
        require(amount > 0, 'Funds received must be positive')
        rate = normalize_rate(body.get('rate'), body.get('rateDirection', 'report_per_source'))
        note = str(body.get('note', '')).strip()
        require(len(note) <= 500, 'Receipt note is too long')
        use_default = body.get('useAsDefault', False)
        require(type(use_default) is bool, 'Choose whether to apply this receipt automatically')
        def commit(data):
            grant = grant_in(data, body.get('grantId'))
            require(source != grant['currency'] or rate == '1', 'Same-currency receipts use a rate of 1')
            receipts = data.setdefault('fundingReceipts', {})
            require(len(receipts) < 150, 'Receipt limit reached')
            require(not any(r['grantId'] == grant['id'] and r['receivedDate'] == received and r['sourceCurrency'] == source
                            and r['sourceAmountMinor'] == amount and r['rate'] == rate and r.get('note', '') == note for r in receipts.values()),
                    'An identical receipt is already recorded. Use a distinct reference in the note for a separate receipt.', 'duplicate', 409)
            key = new_id('receipt')
            result = {'id': key, 'grantId': grant['id'], 'receivedDate': received, 'sourceCurrency': source,
                      'reportCurrency': grant['currency'], 'sourceAmountMinor': amount, 'reportAmountMinor': convert_minor(amount, rate),
                      'rate': rate, 'rateDirection': 'report_per_source', 'enteredRate': body['rate'],
                      'enteredDirection': body.get('rateDirection', 'report_per_source'), 'useAsDefault': use_default, 'note': note, 'createdAt': now()}
            receipts[key] = result
            for draft in data.get('financeEntries', {}).values():
                if draft['status'] == 'draft' and draft['grantId'] == grant['id'] and draft['currency'] == source and draft['date'] >= received:
                    if draft.get('conversionMode') == 'weighted_average' or (use_default and draft.get('conversionMode') == 'receipt' and not draft.get('receiptId')):
                        # A stale screen must not approve a conversion basis it never displayed.
                        draft['version'] += 1
            # Existing confirmed conversions stay frozen; future drafts use the new receipt set.
            data['factVersion'] += 1
            self.audit(data, 'funds_receipt', key)
            return result
        return self.repository.mutate(self.org_id, commit)

    def normalize_entry(self, data, body, previous=None):
        value = copy.deepcopy(previous or {})
        for field in ('kind', 'date', 'description', 'reference', 'currency', 'grantId', 'category', 'conversionMode',
                      'receiptId', 'manualRate', 'matchExpenseId', 'reason'):
            if field in body:
                value[field] = body[field]
        value.setdefault('kind', 'expense')
        require(isinstance(value['kind'], str) and value['kind'] in ENTRY_KINDS, 'Choose a valid entry type')
        if not previous or not previous.get('adjustsEntryId'):
            require(value['kind'] != 'adjustment', 'Create a linked adjustment from a confirmed expense')
        grant = grant_in(data, value.get('grantId'))
        value['currency'] = currency(value.get('currency'))
        value['date'] = iso_date(value.get('date'))
        value['description'] = clean_text(value.get('description'), 'Description', 300)
        value['reference'] = str(value.get('reference', '')).strip()
        require(len(value['reference']) <= 180, 'Reference is too long')
        value['category'] = str(value.get('category') or 'Uncategorised').strip()
        require(len(value['category']) <= 120, 'Category is too long')
        if 'amount' in body:
            value['sourceAmountMinor'] = parse_amount(body['amount'], signed=value['kind'] == 'adjustment')
        require(type(value.get('sourceAmountMinor')) is int and value['sourceAmountMinor'] != 0,
                'Enter a non-zero amount')
        require(value['kind'] == 'adjustment' or value['sourceAmountMinor'] > 0, 'Enter a positive amount and choose the cash movement type')
        value.setdefault('conversionMode', 'same_currency' if value['currency'] == grant['currency'] else 'receipt')
        require(isinstance(value['conversionMode'], str) and value['conversionMode'] in {'same_currency', 'receipt', 'weighted_average', 'manual'}, 'Choose a conversion method')
        for field in ('receiptId', 'matchExpenseId'):
            require(value.get(field) is None or isinstance(value[field], str), 'Choose a valid receipt or matching expense identifier')
        if value.get('manualRate'):
            value['manualRate'] = normalize_rate(value['manualRate'])
        if value.get('adjustsEntryId'):
            original = entry_in(data, value['adjustsEntryId'])
            require(original['status'] == 'confirmed' and original['kind'] == 'expense', 'Adjust a confirmed expense')
            require(value['kind'] == 'adjustment' and value['grantId'] == original['grantId'] and value['currency'] == original['currency']
                    and value['category'] == original['category'], 'An adjustment keeps its original grant, currency and category')
            value['conversionMode'], value['manualRate'] = 'manual', original['fxRate']
            value['reason'] = clean_text(value.get('reason'), 'Adjustment reason', 500)
        return value

    def project_entry(self, data, entry):
        result = copy.deepcopy(entry)
        if entry['status'] == 'draft':
            try:
                snapshot = self.entry_conversion(data, entry)
                result.update(reportAmountMinor=snapshot['reportAmountMinor'], reportCurrency=snapshot['reportCurrency'], fxRate=snapshot['rate'])
            except DomainError as exc:
                result.update(reportAmountMinor=None, warning=exc.message)
        return result

    def entry_conversion(self, data, entry):
        if entry.get('adjustsEntryId'):
            original = entry_in(data, entry['adjustsEntryId'])
            previous = [e for e in data.get('financeEntries', {}).values()
                        if e['status'] == 'confirmed' and e.get('adjustsEntryId') == original['id']]
            corrected_native = original['sourceAmountMinor'] + sum(e['sourceAmountMinor'] for e in previous) + entry['sourceAmountMinor']
            require(corrected_native >= 0, 'The corrections would reduce this expense below zero')
            require(corrected_native <= MAX_AMOUNT_MINOR, 'The corrected source amount exceeds the supported limit')
            corrected_report = convert_minor(corrected_native, original['fxRate'])
            delta = corrected_report - original['reportAmountMinor'] - sum(e['reportAmountMinor'] for e in previous)
            return {**conversion(data, entry), 'reportAmountMinor': delta, 'roundingBasis': 'cumulative_original_rate',
                    'correctedSourceAmountMinor': corrected_native, 'correctedReportAmountMinor': corrected_report}
        if entry['kind'] == 'payment_match':
            expense = data['expenses'].get(entry.get('matchExpenseId'))
            if expense:
                allocation = next((a for a in expense['allocations'] if a['grantId'] == entry['grantId']), None)
                if allocation and allocation.get('conversion'):
                    return copy.deepcopy(allocation['conversion'])
        return conversion(data, entry)

    def create_entry(self, body):
        self.grantee()
        def commit(data):
            entries = data.setdefault('financeEntries', {})
            require(len(entries) < 500, 'Financial entry limit reached')
            value = self.normalize_entry(data, body)
            key = new_id('entry')
            value.update(id=key, version=1, status='draft', createdAt=now(), history=[])
            entries[key] = value
            data['factVersion'] += 1
            self.audit(data, 'financial_draft_created', key)
            return self.project_entry(data, value)
        return self.repository.mutate(self.org_id, commit)

    def update_entry(self, key, body):
        self.grantee()
        def commit(data):
            original = entry_in(data, key)
            expected(original, body)
            require(original['status'] == 'draft', 'Confirmed entries are immutable. Create a linked adjustment.', 'already_handled', 409)
            value = self.normalize_entry(data, body, original)
            history = value.setdefault('history', [])
            require(len(history) < 30, 'Draft edit history limit reached')
            history.append({'action': 'edited', 'at': now(), 'actorId': self.identity['id'],
                            'before': {k: original.get(k) for k in ('kind', 'date', 'description', 'sourceAmountMinor', 'currency', 'grantId', 'category', 'conversionMode', 'receiptId', 'manualRate')}})
            value['version'] += 1
            data['financeEntries'][key] = value
            data['factVersion'] += 1
            self.audit(data, 'financial_draft_edited', key)
            return self.project_entry(data, value)
        return self.repository.mutate(self.org_id, commit)

    def source_direction(self, data, entry, legacy_rows):
        direction = entry.get('sourceDirection') or entry.get('bankDirection')
        if direction:
            return direction
        source = entry.get('source', {})
        if not source.get('importId'):
            return None
        item = import_in(data, source['importId'])
        rows = item.get('rows', [])
        if item['kind'] == 'ledger' and item.get('mapping', {}).get('direction'):
            # Older ledgers discarded an explicitly mapped direction in their cached rows.
            # Recover it from the immutable workbook, never from editable draft amounts.
            if item['id'] not in legacy_rows:
                from .finance_io import parse_ledger_xlsx
                raw = self.storage.get(item['objectKey'])
                require(hashlib.sha256(raw).hexdigest() == item['sha256'],
                        'The original financial source changed. Restore the original file before confirming this draft.', 'source_unavailable', 409)
                legacy_rows[item['id']] = parse_ledger_xlsx(raw, item)['rows']
            rows = legacy_rows[item['id']]
        coordinates = {key: value for key, value in source.items() if key != 'importId'}
        matches = [row for row in rows if row.get('source') == coordinates]
        require(coordinates and len(matches) == 1,
                'The original movement cannot be identified. Review its source before confirming this draft.', 'source_unavailable', 409)
        original = matches[0]
        return 'credit' if original.get('direction') == 'credit' or parse_amount(original['amount'], signed=True) < 0 else 'debit'

    def confirm_one(self, data, entry, legacy_rows=None):
        require(entry['status'] == 'draft', 'Entry has already been handled', 'already_handled', 409)
        require(entry['kind'] != 'unclassified', 'Classify this bank movement before confirming')
        grant = grant_in(data, entry['grantId'])
        snapshot = self.entry_conversion(data, entry)
        kind = entry['kind']
        bank_source = bool(entry.get('source', {}).get('importId') and import_in(data, entry['source']['importId'])['kind'] == 'bank')
        if bank_source:
            duplicate_movement = next((other for other in data.get('financeEntries', {}).values()
                if other['status'] == 'confirmed' and other.get('bankDirection') == entry.get('bankDirection')
                and other['currency'] == entry['currency'] and other['sourceAmountMinor'] == entry['sourceAmountMinor']
                and other['date'] == entry['date'] and ((entry['reference'] and other.get('reference') == entry['reference'])
                    or (not (entry['reference'] and other.get('reference')) and other['description'].strip().casefold() == entry['description'].strip().casefold()))), None)
            require(not duplicate_movement, 'This bank movement is already confirmed from another source. Reject the duplicate draft.', 'duplicate', 409)
        if kind in {'expense', 'adjustment'}:
            require(entry['category'] != 'Uncategorised', 'Choose a reporting category before confirming an expense')
        if kind == 'expense':
            direction = self.source_direction(data, entry, legacy_rows if legacy_rows is not None else {})
            require(direction != 'credit',
                    'Incoming credits cannot be reported as expenses. Classify the receipt or create a linked correction.')
            if direction:
                entry['sourceDirection'] = direction
            # Same reference/date/amount/currency is a duplicate, even from a different uploaded file.
            duplicate = next((e for e in data['expenses'].values() if e['currency'] == entry['currency'] and e['amountMinor'] == entry['sourceAmountMinor']
                              and ((e.get('reference') and e.get('reference') == entry['reference'] and (bank_source or e['date'] == entry['date']))
                                   or (not (e.get('reference') and entry['reference']) and e['date'] == entry['date']
                                       and e['description'].strip().casefold() == entry['description'].strip().casefold()))), None)
            require(not duplicate, 'This transaction is already an expense. Match its payment instead of counting it again.', 'duplicate', 409)
            expense_id = 'financial-' + entry['id']
            data['expenses'][expense_id] = {'id': expense_id, 'description': entry['description'], 'date': entry['date'],
                'currency': entry['currency'], 'amountMinor': entry['sourceAmountMinor'], 'reference': entry['reference'],
                'category': entry['category'], 'version': 1, 'financeEntryId': entry['id'],
                'allocations': [{'grantId': grant['id'], 'amountMinor': entry['sourceAmountMinor'],
                                 'reportAmountMinor': snapshot['reportAmountMinor'], 'conversion': snapshot}]}
            entry['expenseId'] = expense_id
        elif kind == 'payment_match':
            expense = data['expenses'].get(entry.get('matchExpenseId'))
            require(expense and expense['currency'] == entry['currency'] and expense['amountMinor'] == entry['sourceAmountMinor']
                    and any(a['grantId'] == entry['grantId'] for a in expense['allocations']),
                    'Choose an existing expense with the same amount, currency and grant')
            require(not expense.get('paymentEntryId'), 'This expense already has a confirmed payment match', 'duplicate', 409)
            require(entry.get('source', {}).get('importId') and import_in(data, entry['source']['importId'])['kind'] == 'bank',
                    'A payment match must come from a bank statement')
            require(entry.get('bankDirection') == 'debit', 'Only a bank debit can pay an expense')
            expense.update(paymentEntryId=entry['id'], paidStatus='matched_bank_payment', paymentDate=entry['date'])
        entry.update(status='confirmed', version=entry['version'] + 1, confirmedAt=now(), confirmedBy=self.identity['id'],
                     conversion=snapshot, reportAmountMinor=snapshot['reportAmountMinor'], reportCurrency=grant['currency'], fxRate=snapshot['rate'])
        if kind == 'adjustment':
            # Their cumulative rounding basis has changed, even when the entered rate has not.
            # An older screen must review the new amount before approving another correction.
            for draft in data.get('financeEntries', {}).values():
                if draft['status'] == 'draft' and draft.get('adjustsEntryId') == entry['adjustsEntryId']:
                    draft['version'] += 1
        entry.setdefault('history', []).append({'action': 'confirmed', 'at': now(), 'actorId': self.identity['id']})
        self.audit(data, 'financial_' + kind + '_confirmed', entry['id'])

    def confirm_entries(self, body):
        self.grantee()
        items = body.get('entries')
        require(isinstance(items, list) and 1 <= len(items) <= 50 and all(isinstance(i, dict) for i in items), 'Select one to fifty draft entries')
        ids = [i.get('id') for i in items]
        require(all(isinstance(i, str) for i in ids) and len(set(ids)) == len(ids), 'Select distinct entries')
        def commit(data):
            selected = [entry_in(data, item['id']) for item in items]
            for entry, item in zip(selected, items):
                expected(entry, item)
            adjusted_ids = [entry['adjustsEntryId'] for entry in selected if entry.get('adjustsEntryId')]
            require(len(set(adjusted_ids)) == len(adjusted_ids),
                    'Confirm one correction per original expense at a time, then refresh to review the remaining corrections.', 'conflict', 409)
            legacy_rows = {}
            for entry in selected:
                self.confirm_one(data, entry, legacy_rows)
            data['factVersion'] += 1
            return {'confirmed': len(selected), 'entries': selected}
        return self.repository.mutate(self.org_id, commit)

    def reject_entry(self, key, body):
        self.grantee()
        def commit(data):
            entry = entry_in(data, key)
            expected(entry, body)
            require(entry['status'] == 'draft', 'Only drafts can be rejected', 'already_handled', 409)
            entry.update(status='rejected', version=entry['version'] + 1)
            data['factVersion'] += 1
            entry.setdefault('history', []).append({'action': 'rejected', 'actorId': self.identity['id'], 'at': now()})
            self.audit(data, 'financial_draft_rejected', key)
            return entry
        return self.repository.mutate(self.org_id, commit)

    def adjust_entry(self, key, body):
        self.grantee()
        def commit(data):
            original = entry_in(data, key)
            expected(original, body)
            require(original['status'] == 'confirmed' and original['kind'] == 'expense', 'Choose a confirmed expense to adjust')
            require(len(data.get('financeEntries', {})) < 500, 'Financial entry limit reached')
            adjustment = {k: original.get(k) for k in ('date', 'description', 'reference', 'currency', 'grantId', 'category')}
            adjustment.update(id=new_id('entry'), adjustsEntryId=key, kind='adjustment', status='draft', version=1,
                              conversionMode='manual', manualRate=original['fxRate'], reason=body.get('reason'), history=[], createdAt=now())
            adjustment = self.normalize_entry(data, {'amount': body.get('amount')}, adjustment)
            data.setdefault('financeEntries', {})[adjustment['id']] = adjustment
            data['factVersion'] += 1
            self.audit(data, 'financial_correction_created', adjustment['id'])
            return self.project_entry(data, adjustment)
        return self.repository.mutate(self.org_id, commit)

    def upload_import(self, body):
        data = self.data()
        grant = grant_in(data, body.get('grantId'))
        name = clean_text(body.get('name'), 'File name', 180)
        require(PurePath(name).name == name and '/' not in name and '\\' not in name, 'Use a plain file name')
        kind = body.get('kind')
        require(isinstance(kind, str) and kind in {'ledger', 'bank', 'template'}, 'Choose ledger, bank statement or report template')
        encoded = body.get('contentBase64')
        require(isinstance(encoded, str) and len(encoded) <= 2_800_000, 'Financial files must be no larger than 2 MB')
        try:
            raw = base64.b64decode(encoded, validate=True)
        except ValueError:
            raise DomainError('Invalid file encoding')
        require(0 < len(raw) <= 2 * 1024 * 1024, 'Financial files must be no larger than 2 MB')
        digest = hashlib.sha256(raw).hexdigest()
        existing = next((i for i in data.get('financeImports', {}).values() if i['sha256'] == digest and i['kind'] == kind and i['grantId'] == grant['id']), None)
        if existing:
            return {**public_import(existing), 'alreadyImported': True}
        from .finance_io import inspect_xlsx, parse_ledger_xlsx, parse_bank_pdf
        item = {'id': new_id('import'), 'organisationId': self.org_id, 'version': 1, 'name': name, 'kind': kind,
                'grantId': grant['id'], 'sha256': digest, 'createdAt': now(), 'status': 'preview', 'rows': [], 'warnings': [], 'entryIds': [], 'sheets': []}
        suffix = PurePath(name).suffix.lower()
        pages = None
        if kind in {'ledger', 'template'}:
            require(suffix == '.xlsx', 'Upload an .xlsx workbook')
            overview = inspect_xlsx(raw)
            item.update(overview)
            item['contentType'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            if kind == 'ledger':
                options = {**overview, **{k: body[k] for k in ('sheet', 'headerRow', 'mapping', 'defaultCurrency', 'dateFormat', 'decimalSeparator') if k in body}}
                options['sheet'] = body.get('sheet') or overview.get('defaultSheet')
                try:
                    item.update(parse_ledger_xlsx(raw, options))
                except DomainError as exc:
                    item.update(status='needs_mapping', message=exc.message)
            else:
                item['status'] = 'template'
                if any(s['name'] == 'Financial Report' for s in item['sheets']):
                    # Detect the known category layout; a sheet name alone is not a valid mapping.
                    if overview.get('templateMapping'):
                        hints = overview.get('templateHints', {})
                        item['templateMapping'] = {'sheet': 'Financial Report', 'categoryColumn': 'B', 'actualColumn': 'G', 'startRow': 25, 'endRow': 32,
                            'totalCell': 'G33', **{key: hints[key] for key in ('periodStartCell', 'periodEndCell') if hints.get(key)}}
        else:
            require(suffix == '.pdf', 'Upload a text-based bank-statement PDF')
            result = parse_bank_pdf(raw)
            pages = result.pop('textPages', [])
            item.update(result, contentType='application/pdf')
            item['engine'] = 'statement-parser' if result.get('recognized') else 'awaiting-strands'
            item['status'] = 'preview' if result.get('recognized') else 'needs_ai'
        key = f'{self.org_id}/financial-imports/{item["id"]}'
        item['objectKey'] = key + '/original'
        self.storage.put(item['objectKey'], raw, item['contentType'])
        if pages is not None:
            item['parsedKey'] = key + '/pages.json'
            self.storage.put(item['parsedKey'], json.dumps({'pages': pages}).encode(), 'application/json')
        def commit(current):
            grant_in(current, grant['id'])
            imports = current.setdefault('financeImports', {})
            prior = next((i for i in imports.values() if i['sha256'] == digest and i['kind'] == kind and i['grantId'] == grant['id']), None)
            if prior:
                return {**public_import(prior), 'alreadyImported': True}
            require(len(imports) < 40, 'Financial import limit reached')
            imports[item['id']] = item
            if kind != 'template':
                current['factVersion'] += 1
            return public_import(item)
        return self.repository.mutate(self.org_id, commit)

    def preview_import(self, key, body):
        data = self.data()
        item = import_in(data, key)
        require(item['kind'] == 'ledger' and not item['entryIds'], 'Only an uncommitted ledger can be remapped')
        from .finance_io import parse_ledger_xlsx
        parsed = parse_ledger_xlsx(self.storage.get(item['objectKey']), body)
        def commit(current):
            record = import_in(current, key)
            require(record['version'] == item['version'] and not record['entryIds'], 'Import changed; refresh', 'stale', 409)
            record.update(parsed, status='preview', version=record['version'] + 1)
            record.pop('message', None)
            return public_import(record)
        return self.repository.mutate(self.org_id, commit)

    def commit_import(self, key, body):
        self.grantee()
        def commit(data):
            item = import_in(data, key)
            expected(item, body)
            require(item['kind'] != 'template' and item['status'] in {'preview', 'parsed'}, 'This import needs a parsed preview first')
            require(not item['entryIds'], 'This import was already committed', 'duplicate', 409)
            grant = grant_in(data, body.get('grantId') or item['grantId'])
            require(grant['id'] == item['grantId'], 'An import remains scoped to its selected grant')
            require(item.get('rows'), 'No transaction rows to import')
            entries = data.setdefault('financeEntries', {})
            require(len(entries) + len(item['rows']) <= 500, 'Financial entry limit reached')
            for row in item['rows']:
                native = parse_amount(row['amount'], signed=True)
                is_credit = row.get('direction') == 'credit' or native < 0
                entry = {'kind': 'unclassified' if is_credit else 'expense', 'grantId': grant['id'], 'date': row['date'],
                         'description': row['description'], 'reference': row.get('reference', ''), 'currency': row.get('currency') or item.get('defaultCurrency'),
                         'amount': amount_text(abs(native)), 'category': row.get('category') or 'Uncategorised',
                         'conversionMode': 'manual' if row.get('rate') else 'same_currency' if row.get('currency') == grant['currency'] else 'receipt',
                         'manualRate': row.get('rate') or None}
                value = self.normalize_entry(data, entry)
                entry_id = new_id('entry')
                value.update(id=entry_id, version=1, status='draft', createdAt=now(), history=[],
                             source={'importId': key, **row.get('source', {})},
                             sourceDirection='credit' if is_credit else 'debit',
                             bankDirection=row.get('direction') if item['kind'] == 'bank' else None)
                if item['kind'] == 'bank' and not is_credit:
                    matches = [e for e in data['expenses'].values() if e['currency'] == value['currency'] and e['amountMinor'] == abs(native)
                               and value['reference'] and e.get('reference') == value['reference']
                               and any(a['grantId'] == grant['id'] for a in e['allocations'])]
                    if len(matches) == 1:
                        value.update(kind='payment_match', matchExpenseId=matches[0]['id'], category=matches[0].get('category', 'Uncategorised'),
                                     reason='Exact bank reference, amount, currency and grant match. Review before confirming.')
                if is_credit:
                    value['reason'] = 'Incoming money needs classification. A refund or internal transfer is not automatically a new expense or grant award.'
                entries[entry_id] = value
                item['entryIds'].append(entry_id)
            item.update(status='imported', version=item['version'] + 1)
            data['factVersion'] += 1
            self.audit(data, 'financial_import_drafted', key)
            return public_import(item)
        return self.repository.mutate(self.org_id, commit)

    def source_bytes(self, key):
        item = import_in(self.data(), key)
        link = self.storage.presign_get(item['objectKey'], item['contentType'], item['name'])
        return link or self.storage.get(item['objectKey']), item['contentType'], item['name']

    def map_template(self, key, body):
        item = import_in(self.data(), key)
        require(item['kind'] == 'template', 'Choose a report-template workbook')
        from .finance_io import fill_report_template
        # Validate the exact mapping against the private source before saving it.
        fill_report_template(self.storage.get(item['objectKey']), self.financial_report(item['grantId']), body)
        def commit(data):
            record = import_in(data, key)
            require(record['version'] == item['version'], 'Template changed; refresh', 'stale', 409)
            record.update(templateMapping=copy.deepcopy(body), version=record['version'] + 1)
            return public_import(record)
        return self.repository.mutate(self.org_id, commit)

    def review_import(self, key, body):
        self.grantee()
        note = clean_text(body.get('note'), 'Source review note', 500)
        def commit(data):
            item = import_in(data, key)
            expected(item, body)
            require(item['kind'] != 'template' and item['status'] == 'imported', 'Create and review this source\'s drafts first')
            require(not any(e['status'] == 'draft' and e.get('source', {}).get('importId') == key
                            for e in data.get('financeEntries', {}).values()), 'Review every draft from this source first')
            item.update(reviewedAt=now(), reviewedBy=self.identity['id'], reviewNote=note, version=item['version'] + 1)
            data['factVersion'] += 1
            self.audit(data, 'financial_source_reviewed', key)
            return public_import(item)
        return self.repository.mutate(self.org_id, commit)

    def save_report_settings(self, grant_id, body):
        self.grantee()
        start, end = iso_date(body.get('periodStart')), iso_date(body.get('periodEnd'))
        require(start <= end, 'Reporting start must be on or before the end date')
        budgets = body.get('budgets', {})
        require(isinstance(budgets, dict) and len(budgets) <= 50, 'Provide up to fifty category budgets')
        parsed = {clean_text(k, 'Category', 120): parse_amount(v) for k, v in budgets.items()}
        def commit(data):
            grant_in(data, grant_id)
            data.setdefault('financialReportSettings', {})[grant_id] = {'periodStart': start, 'periodEnd': end, 'budgets': parsed}
            data['factVersion'] += 1
            return self.report_projection(data, grant_id)
        return self.repository.mutate(self.org_id, commit)

    def report_projection(self, data, grant_id):
        grant = self.grant(data, grant_id)
        year = now()[:4]
        settings = data.get('financialReportSettings', {}).get(grant_id, {'periodStart': year + '-01-01', 'periodEnd': year + '-12-31', 'budgets': {}})
        start, end = settings['periodStart'], settings['periodEnd']
        rows = {category: {'category': category, 'budgetMinor': amount, 'actualMinor': 0} for category, amount in settings.get('budgets', {}).items()}
        entries = []
        for expense in data['expenses'].values():
            if not start <= expense['date'] <= end:
                continue
            for allocation in expense['allocations']:
                if allocation['grantId'] != grant_id:
                    continue
                entry = data.get('financeEntries', {}).get(expense.get('financeEntryId'), {})
                category = expense.get('category', 'Uncategorised')
                amount = allocation.get('reportAmountMinor', allocation['amountMinor'])
                rows.setdefault(category, {'category': category, 'budgetMinor': 0, 'actualMinor': 0})['actualMinor'] += amount
                entries.append({**entry, 'id': entry.get('id', expense['id']), 'date': expense['date'], 'description': expense['description'],
                                'sourceAmountMinor': allocation['amountMinor'], 'currency': expense['currency'], 'reportCurrency': grant['currency'],
                                'reportAmountMinor': amount, 'category': category, 'status': 'confirmed', 'kind': 'expense'})
        for entry in data.get('financeEntries', {}).values():
            if entry['status'] == 'confirmed' and entry['grantId'] == grant_id and entry['kind'] == 'adjustment' and start <= entry['date'] <= end:
                category = entry['category']
                rows.setdefault(category, {'category': category, 'budgetMinor': 0, 'actualMinor': 0})['actualMinor'] += entry['reportAmountMinor']
                entries.append(copy.deepcopy(entry))
        for row in rows.values():
            row['varianceMinor'] = row['budgetMinor'] - row['actualMinor']
        receipts = [r for r in data.get('fundingReceipts', {}).values() if r['grantId'] == grant_id and start <= r['receivedDate'] <= end]
        from .domain import unresolved_financial_imports
        imports = [i for i in data.get('financeImports', {}).values() if i['grantId'] == grant_id and i['kind'] != 'template']
        rates = {(e['currency'], e['fxRate']) for e in entries if e['currency'] != grant['currency'] and e.get('fxRate')}
        return {'grant': grant, 'periodStart': start, 'periodEnd': end, 'rows': sorted(rows.values(), key=lambda r: r['category']),
                'entries': sorted(entries, key=lambda e: e['date']), 'totalMinor': sum(r['actualMinor'] for r in rows.values()),
                'currency': grant['currency'], 'unresolvedCount': sum(e['status'] == 'draft' and e['grantId'] == grant_id and start <= e['date'] <= end
                    for e in data.get('financeEntries', {}).values()), 'receiptsTotalMinor': sum(r['reportAmountMinor'] for r in receipts),
                'unresolvedImportCount': len(unresolved_financial_imports(data, grant_id)),
                'sourceWarnings': [i['name'] + ': ' + warning for i in imports for warning in i.get('warnings', [])],
                'rate': next(iter(rates))[1] if len(rates) == 1 else None,
                'version': data['factVersion'], 'synthetic': grant.get('synthetic') is not False and not imports
                    and not any(e['grantId'] == grant_id for e in data.get('financeEntries', {}).values())}

    def financial_report(self, grant_id):
        data = self.data()
        grant_in(data, grant_id)
        return self.report_projection(data, grant_id)

    def export_report(self, grant_id, template=False, template_id=None):
        data = self.data()
        report = self.report_projection(data, grant_id)
        from .finance_io import export_financial_xlsx, fill_report_template
        if template:
            sources = [i for i in data.get('financeImports', {}).values() if i['kind'] == 'template' and i['grantId'] == grant_id
                       and i.get('templateMapping') and (not template_id or i['id'] == template_id)]
            require(sources, 'Upload and map a financial report template first')
            source = sources[-1]
            require(not source['templateMapping'].get('rateCell') or report.get('rate'),
                    'This report has no single foreign exchange rate. Leave the template FX rate cell unmapped and use the ledger conversion detail.')
            return fill_report_template(self.storage.get(source['objectKey']), report, source['templateMapping'])
        return export_financial_xlsx(report, report['entries'], [r for r in data.get('fundingReceipts', {}).values() if r['grantId'] == grant_id])

    def create_bank_job(self, key):
        self.grantee()
        from .worker import agent_configured
        configured = agent_configured()
        def commit(data):
            item = import_in(data, key)
            require(item['kind'] == 'bank' and item.get('parsedKey') and not item['entryIds'], 'Choose an uncommitted bank PDF')
            active = []
            timestamp = datetime.now(timezone.utc).timestamp()
            for job in data['jobs'].values():
                same_import = job.get('kind') == 'bank_statement' and job.get('importId') == key
                if job['status'] not in {'queued', 'running'} or not (same_import or job['actorId'] == self.identity['id']):
                    continue
                lease = job.get('leaseExpiresAt')
                expired = (lease is not None and lease <= timestamp) or (job['status'] == 'running' and lease is None)
                stale = job['inputVersion'] != data['factVersion']
                if job.get('kind') == 'bank_statement':
                    source = data.get('financeImports', {}).get(job.get('importId'))
                    stale = stale or not source or source['version'] != job.get('importVersion') or source['status'] != 'needs_ai'
                if stale or expired:
                    job.update(status='failed', finishedAt=now(), message='Inputs changed or the worker lease expired. Start a fresh agent run.')
                    job.pop('claimToken', None)
                    job.pop('leaseExpiresAt', None)
                else:
                    active.append(job)
            existing = next((j for j in active if j.get('kind') == 'bank_statement' and j.get('importId') == key), None)
            if existing:
                return existing
            # An unrelated reconciliation cannot be repurposed into a bank extraction.
            require(not active, 'Another agent run is already active for you. Retry this bank statement when it finishes.', 'job_in_progress', 409)
            require(sum(j['createdAt'][:10] == now()[:10] and j['actorId'] == self.identity['id'] for j in data['jobs'].values()) < 30,
                    'Daily agent run limit reached', 'job_limit', 429)
            item['status'] = 'needs_ai'
            key_id = new_id('job')
            job = {'id': key_id, 'kind': 'bank_statement', 'importId': key, 'importVersion': item['version'], 'grantId': item['grantId'],
                   'organisationId': self.org_id, 'actorId': self.identity['id'], 'actor': copy.deepcopy(self.identity),
                   'inputVersion': data['factVersion'], 'status': 'queued' if configured else 'unavailable', 'engine': 'strands-bedrock',
                   'createdAt': now(), 'toolEvents': [], 'message': 'Bank statement queued for AI review.' if configured else 'Bank AI is unavailable until AWS/Bedrock is configured. No transactions were invented.'}
            if not configured:
                job['finishedAt'] = now()
            data['jobs'][key_id] = job
            item.update(jobId=key_id, message=job['message'])
            return job
        return self.repository.mutate(self.org_id, commit)
