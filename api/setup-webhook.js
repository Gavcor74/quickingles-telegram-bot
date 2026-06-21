const TELEGRAM_BOT_TOKEN = String(process.env.TELEGRAM_BOT_TOKEN || '').trim().replace(/^['"]|['"]$/g, '');

export default async function handler(req, res) {
  if (!TELEGRAM_BOT_TOKEN) {
    return res.status(500).json({ ok: false, error: 'missing TELEGRAM_BOT_TOKEN' });
  }

  const proto = req.headers['x-forwarded-proto'] || 'https';
  const host = req.headers.host;
  const webhookUrl = `${proto}://${host}/api/telegram`;

  const response = await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ url: webhookUrl }),
  });
  const data = await response.json().catch(() => ({}));
  return res.status(response.ok ? 200 : 500).json({ ok: response.ok, webhookUrl, telegram: data });
}
