function parseUtcDate(value) {
  if (!value) return null;

  // バックエンドのnaive datetimeはUTCとして保存・返却される。
  // タイムゾーン表記がない場合だけZを補い、ブラウザにUTCとして解釈させる。
  const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(value);
  return new Date(hasTimezone ? value : `${value}Z`);
}

export function formatJapanDateTime(value) {
  const date = parseUtcDate(value);
  if (!date || Number.isNaN(date.getTime())) return "";

  return new Intl.DateTimeFormat("ja-JP", {
    timeZone: "Asia/Tokyo",
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}
