"""Offline planning arithmetic. No device discovery or configuration."""
import argparse
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path


def number(value, name, zero=False):
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError(f'{name}: use a JSON number')
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f'{name}: invalid number') from exc
    if not result.is_finite() or result < 0 or (not zero and result == 0) or result > 1000000:
        raise ValueError(f'{name}: number outside allowed range')
    return result


def fields(obj, expected):
    if not isinstance(obj, dict) or set(obj) != set(expected):
        raise ValueError(f'Expected fields: {", ".join(expected)}')


def plan(data):
    fields(data, ('budget_w', 'reserve_percent', 'poe_ports', 'devices'))
    budget = number(data['budget_w'], 'budget_w')
    reserve = number(data['reserve_percent'], 'reserve_percent', zero=True)
    if reserve >= 100:
        raise ValueError('reserve_percent must be below 100')
    ports = data['poe_ports']
    if type(ports) is not int or not 1 <= ports <= 10000:
        raise ValueError('poe_ports must be an integer from 1 to 10000')
    if not isinstance(data['devices'], list) or not data['devices']:
        raise ValueError('devices must be a nonempty list')
    seen, failures = set(), []
    total = Decimal(0)
    for device in data['devices']:
        fields(device, ('port', 'pse_w', 'port_limit_w'))
        port = device['port']
        if type(port) is not int or not 1 <= port <= ports or port in seen:
            raise ValueError('port must be unique and within poe_ports')
        seen.add(port)
        watts = number(device['pse_w'], 'pse_w')
        limit = number(device['port_limit_w'], 'port_limit_w')
        total += watts
        if watts > limit:
            failures.append(port)
    usable = budget * (100 - reserve) / 100
    physical_ok = total <= budget
    reserve_ok = total <= usable
    status = 'BLOCKED' if failures or not physical_ok else ('REVIEW' if not reserve_ok else 'WITHIN_INPUT_LIMITS')
    return {'status': status, 'allocated_ports': len(seen), 'free_poe_ports': ports - len(seen),
            'demand_w': str(total), 'budget_w': str(budget), 'planning_limit_w': str(usable),
            'remaining_physical_w': str(budget - total), 'remaining_planning_w': str(usable - total),
            'over_limit_ports': failures, 'physical_budget_ok': physical_ok,
            'reserve_target_met': reserve_ok,
            'note': 'Arithmetic estimate only. Verify PSE allocations, standards, cable loss, startup load and hardware specifications.'}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate JSON key: {key}')
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inventory', type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.inventory.read_text(encoding='utf-8-sig'), parse_float=Decimal,
                          object_pairs_hook=unique_object)
        result = plan(data)
    except (ValueError, OSError, ArithmeticError) as exc:
        print(f'Input error: {exc}', file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if result['status'] != 'WITHIN_INPUT_LIMITS' else 0


if __name__ == '__main__':
    sys.exit(main())
