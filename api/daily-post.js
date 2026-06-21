import { TELEGRAM_CHANNEL_ID, generatePost, saveNotionPost, telegram } from './lib.js';

export default async function handler(req, res) {
  if (req.method !== 'GET' && req.method !== 'POST') {
    return res.status(405).json({ ok: false, error: 'method_not_allowed' });
  }

  if (!TELEGRAM_CHANNEL_ID) {
    return res.status(500).json({ ok: false, error: 'missing_TELEGRAM_CHANNEL_ID' });
  }

  try {
    const { title, topic, content } = await generatePost();
    await telegram('sendMessage', { chat_id: TELEGRAM_CHANNEL_ID, text: content });
    await saveNotionPost({ title, topic, content });
    return res.status(200).json({ ok: true, topic });
  } catch (error) {
    return res.status(500).json({ ok: false, error: error.message });
  }
}