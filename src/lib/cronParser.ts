// src/utils/cronParser.ts

const MONTHS = [
  'янв', 'фев', 'мар', 'апр', 'май', 'июн',
  'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'
];

const WEEKDAYS = [
  'пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс'
];

export function cronToHuman(cron: string): string {
  const parts = cron.trim().split(/\s+/);
  if (parts.length < 5) return 'Неверный формат Cron';
  
  const [minute, hour, dayMonth, month, dayWeek] = parts;
  
  const descriptions = [
    parseField(minute, 'минута', 'минуту', 'минуты', 'минуте', parseMinute),
    parseField(hour, 'час', 'час', 'часов', 'часов', parseHour),
    parseField(dayMonth, 'день', 'день', 'дня', 'месяца', parseDayMonth),
    parseField(month, 'месяц', 'месяц', 'месяца', 'месяце', parseMonth),
    parseField(dayWeek, 'день', 'день', 'дня', 'недели', parseDayWeek)
  ];
  
  return descriptions.join(', ');
}

function parseField(
  value: string,
  unit: string,
  unitAcc: string,
  unitGen: string,
  unitPre: string,
  parser: (val: string) => string
): string {
  return parser(value);
}

function parseMinute(value: string): string {
  if (value === '*') return 'Каждую минуту';
  if (value.startsWith('*/')) return `Каждую минуту с шагом ${value.slice(2)}`;
  if (value.includes('/') && !value.includes('-')) {
    const [start, step] = value.split('/');
    return `Начиная с ${start}-й минуты, каждую минуту с шагом ${step}`;
  }
  if (value.includes('-') && value.includes('/')) {
    const [range, step] = value.split('/');
    const [from, to] = range.split('-');
    return `С ${from}-й по ${to}-ю минуту с шагом ${step}`;
  }
  if (value.includes('-')) {
    const [from, to] = value.split('-');
    return `С ${from}-й по ${to}-ю минуту`;
  }
  if (value.includes(',')) {
    const values = value.split(',').map(v => `${v}-я`).join(', ');
    return `На ${values} минутах`;
  }
  return `На ${value}-й минуте`;
}

function parseHour(value: string): string {
  if (value === '*') return 'Каждый час';
  if (value.startsWith('*/')) return `Каждый час с шагом ${value.slice(2)}`;
  if (value.includes('/') && !value.includes('-')) {
    const [start, step] = value.split('/');
    return `Начиная с ${start} часов, каждый час с шагом ${step}`;
  }
  if (value.includes('-') && value.includes('/')) {
    const [range, step] = value.split('/');
    const [from, to] = range.split('-');
    return `С ${from} до ${to} часов с шагом ${step}`;
  }
  if (value.includes('-')) {
    const [from, to] = value.split('-');
    return `С ${from} до ${to} часов`;
  }
  if (value.includes(',')) {
    const values = value.split(',').join(', ');
    return `В ${values} часов`;
  }
  return `В ${value} часов`;
}

function parseDayMonth(value: string): string {
  if (value === '*') return 'Каждый день месяца';
  if (value.startsWith('*/')) return `Каждый день месяца с шагом ${value.slice(2)}`;
  if (value.includes('/') && !value.includes('-')) {
    const [start, step] = value.split('/');
    return `Начиная с ${start}-го числа, каждый день месяца с шагом ${step}`;
  }
  if (value.includes('-') && value.includes('/')) {
    const [range, step] = value.split('/');
    const [from, to] = range.split('-');
    return `С ${from}-го по ${to}-е число с шагом ${step}`;
  }
  if (value.includes('-')) {
    const [from, to] = value.split('-');
    return `С ${from}-го по ${to}-е число`;
  }
  if (value.includes(',')) {
    const values = value.split(',').map(v => `${v}-го`).join(', ');
    return `${values} числа`;
  }
  return `${value}-го числа`;
}

function parseMonth(value: string): string {
  if (value === '*') return 'Каждый месяц';
  if (value.startsWith('*/')) return `Каждый месяц с шагом ${value.slice(2)}`;
  if (value.includes('/') && !value.includes('-')) {
    const [start, step] = value.split('/');
    const startName = MONTHS[parseInt(start) - 1] || start;
    return `Начиная с ${startName}, каждый месяц с шагом ${step}`;
  }
  if (value.includes('-') && value.includes('/')) {
    const [range, step] = value.split('/');
    const [from, to] = range.split('-');
    const fromName = MONTHS[parseInt(from) - 1] || from;
    const toName = MONTHS[parseInt(to) - 1] || to;
    return `С ${fromName} по ${toName} с шагом ${step}`;
  }
  if (value.includes('-')) {
    const [from, to] = value.split('-');
    const fromName = MONTHS[parseInt(from) - 1] || from;
    const toName = MONTHS[parseInt(to) - 1] || to;
    return `С ${fromName} по ${toName}`;
  }
  if (value.includes(',')) {
    const values = value.split(',').map(v => MONTHS[parseInt(v) - 1] || v).join(', ');
    return `В ${values}`;
  }
  const monthName = MONTHS[parseInt(value) - 1] || value;
  return `В ${monthName}`;
}

function parseDayWeek(value: string): string {
  if (value === '*') return 'Каждый день недели';
  if (value.startsWith('*/')) return `Каждый день недели с шагом ${value.slice(2)}`;
  if (value.includes('/') && !value.includes('-')) {
    const [start, step] = value.split('/');
    const startName = WEEKDAYS[parseInt(start)] || start;
    return `Начиная с ${startName}, каждый день недели с шагом ${step}`;
  }
  if (value.includes('-') && value.includes('/')) {
    const [range, step] = value.split('/');
    const [from, to] = range.split('-');
    const fromName = WEEKDAYS[parseInt(from)] || from;
    const toName = WEEKDAYS[parseInt(to)] || to;
    return `С ${fromName} по ${toName} с шагом ${step}`;
  }
  if (value.includes('-')) {
    const [from, to] = value.split('-');
    const fromName = WEEKDAYS[parseInt(from)] || from;
    const toName = WEEKDAYS[parseInt(to)] || to;
    return `С ${fromName} по ${toName}`;
  }
  if (value.includes(',')) {
    const values = value.split(',').map(v => WEEKDAYS[parseInt(v)] || v).join(', ');
    return `В ${values}`;
  }
  const dayName = WEEKDAYS[parseInt(value)] || value;
  return `В ${dayName}`;
}