"""Replay bounded decimal arithmetic from data; never execute draft code."""
from decimal import Decimal, localcontext, ROUND_HALF_EVEN, DecimalException
import re


def replay(draft):
    records = draft.get('calculations', [])
    if not isinstance(records, list) or len(records) > 1000:
        raise ValueError('calculations must be an array of at most 1000 operations')
    values, output = {}, []
    numbers = {n.get('id'): n for n in draft.get('numbers', [])}
    with localcontext() as ctx:
        ctx.prec = 50
        ctx.rounding = ROUND_HALF_EVEN
        ctx.traps[__import__('decimal').Inexact] = False
        for item in records:
            identity = item.get('id')
            if not isinstance(identity, str) or not re.fullmatch(r'K\d+', identity) or identity in values:
                raise ValueError('Invalid or duplicate calculation id')
            args = item.get('operands')
            if not isinstance(args, list) or len(args) != 2:
                raise ValueError('Each calculation needs two operands')
            resolved = []
            for value in args:
                if isinstance(value, dict) and set(value) == {'number_id'}:
                    number = numbers.get(value['number_id'])
                    if number is None or number.get('basis') == 'calculation':
                        raise ValueError('Operand number_id must reference a non-calculation number')
                    value = number['value']
                if isinstance(value, str) and value in values:
                    resolved.append(values[value])
                elif isinstance(value, str) and re.fullmatch(r'-?\d{1,30}(?:\.\d{1,30})?', value):
                    resolved.append(Decimal(value))
                else:
                    raise ValueError('Use bounded decimal literals or earlier calculation IDs')
            a, b = resolved
            try:
                op = item.get('operation')
                if op == 'add': result = a + b
                elif op == 'subtract': result = a - b
                elif op == 'multiply': result = a * b
                elif op == 'divide': result = a / b
                else: raise ValueError('Unsupported arithmetic operation')
                places = item.get('decimal_places')
                if places is not None:
                    if type(places) is not int or not 0 <= places <= 20:
                        raise ValueError('decimal_places must be 0..20')
                    result = result.quantize(Decimal(1).scaleb(-places))
                if not result.is_finite() or abs(result.adjusted()) > 100:
                    raise ValueError('Calculation outside finite bounded range')
            except DecimalException as exc:
                raise ValueError('Invalid decimal arithmetic: ' + identity) from exc
            values[identity] = result
            output.append({'id': identity, 'value': format(result, 'f'),
                           'operation': op, 'operands': args, 'decimal_places': places})
        for number in draft.get('numbers', []):
            identity = number.get('calculation_id')
            if identity is None:
                continue
            if number.get('basis') != 'calculation' or identity not in values:
                raise ValueError('Invalid number calculation_id')
            try:
                if Decimal(number['value']) != values[identity]:
                    raise ValueError('Number differs from replayed calculation: ' + number['id'])
            except DecimalException as exc:
                raise ValueError('Calculated number must contain a plain decimal value') from exc
    return {'schema_version': 'paperscope-arithmetic/1.0', 'precision': 50,
            'rounding': 'ROUND_HALF_EVEN', 'results': output,
            'scope': 'Arithmetic of reader-supplied operands only; no source, unit, formula-choice or scientific validation.'}
