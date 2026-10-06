from datetime import datetime, timedelta, timezone

INDIA = timezone(timedelta(hours=5, minutes=30))

def india_now():
    return datetime.now(INDIA).replace(tzinfo=None)

def parse_datetime(date_value, time_value):
    if not date_value or time_value is None:
        return None
    date_text = str(date_value).split(' ')[0].replace('/', '-')
    time_text = str(time_value).strip().upper()
    for date_fmt in ('%Y-%m-%d', '%d-%m-%Y'):
        for time_fmt in ('%H:%M:%S', '%H:%M', '%I:%M %p', '%I:%M:%S %p'):
            try:
                return datetime.strptime(f'{date_text} {time_text}', f'{date_fmt} {time_fmt}')
            except ValueError:
                pass
    raise ValueError('Quiz schedule has an invalid date or time')

def duration_seconds(value):
    parts = str(value or '').split(':')
    try:
        seconds = (int(parts[0]) * 3600 + int(parts[1]) * 60
                   if len(parts) == 2 else int(float(parts[0]) * 60))
    except (ValueError, IndexError):
        raise ValueError('Quiz duration is invalid')
    if seconds <= 0 or len(parts) > 2 or (len(parts) == 2 and not 0 <= int(parts[1]) < 60):
        raise ValueError('Quiz duration must be positive')
    return seconds

def availability(quiz, mapping, now=None):
    now = now or india_now()
    shown = parse_datetime(quiz.get('show_date'), quiz.get('show_time'))
    start = parse_datetime(quiz.get('quiz_date'), quiz.get('quiz_time'))
    seconds = duration_seconds(quiz.get('duration'))
    end = start + timedelta(seconds=seconds) if start else None
    reason = ''
    if mapping.get('is_submitted') == 1:
        reason = 'Quiz already submitted'
    elif shown and now < shown:
        reason = 'Quiz is not yet visible'
    elif not start:
        reason = 'Quiz schedule is missing'
    elif now < start:
        reason = 'Quiz has not started yet'
    elif now >= end:
        reason = 'Quiz has ended'
    return {'can_start': not reason, 'unavailable_reason': reason,
            'visible': not shown or now >= shown,
            'remaining_seconds': max(0, int((end - now).total_seconds())) if end else 0,
            'duration_minutes': seconds / 60,
            'quiz_start': start.isoformat() + '+05:30' if start else None,
            'quiz_end': end.isoformat() + '+05:30' if end else None}

def calculate_score(questions, correct, selected):
    return sum(float(q.get('marks') or 0) for q in questions
               if correct.get(q['qq_id']) and
               correct[q['qq_id']] == selected.get(q['qq_id'], set()))
