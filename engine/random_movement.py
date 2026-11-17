def resolve_command(command, rng):
    op = command['op']
    if op == 'random_step':
        return {'op': rng.choice(('down', 'left', 'right', 'up'))}
    if op == 'random_wait':
        lo = float(command.get('min_seconds', 1))
        hi = float(command.get('max_seconds', 3))
        return {'op': 'wait', 'seconds': rng.uniform(lo, hi)}
    return command
