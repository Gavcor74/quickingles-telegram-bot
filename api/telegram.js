import { TELEGRAM_CHANNEL_ID, authorized, generatePost, telegram } from './lib.js';

export default async function handler(req, res) {
  if (req.method === 'GET') {
    return res.status(200).json({ ok: true, service: 'quickingles-content-bot' });
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ ok: false, error: 'method_not_allowed' });
  }

  let chatId;
  try {
    const update = req.body || {};
    const message = update.message || update.edited_message || {};
    const chat = message.chat || {};
    const user = message.from || {};
    const text = String(message.text || '').trim();
    chatId = chat.id;

    if (!chatId || !text) return res.status(200).json({ ok: true });

    if (!authorized(user.id)) {
      await telegram('sendMessage', { chat_id: chatId, text: 'No autorizado para este comando.' });
      return res.status(200).json({ ok: true });
    }

    const command = text.split(/\s+/)[0].split('@')[0].toLowerCase();

    if (command === '/start') {
      await telegram('sendMessage', { chat_id: chatId, text: 'Bot listo. Comandos: /post_now /status' });
    } else if (command === '/status') {
      await telegram('sendMessage', { chat_id: chatId, text: `Vercel activo. Canal de revision: ${TELEGRAM_CHANNEL_ID || '(sin configurar)'}` });
    } else if (command === '/post_now') {
      if (!TELEGRAM_CHANNEL_ID) {
        await telegram('sendMessage', { chat_id: chatId, text: 'Falta TELEGRAM_CHANNEL_ID en variables de entorno.' });
      } else {
        await telegram('sendMessage', { chat_id: chatId, text: 'Generando post... te aviso en cuanto se envie al canal de revision.' });
        const { topic, content } = await generatePost();
        await telegram('sendMessage', { chat_id: TELEGRAM_CHANNEL_ID, text: content });
        await telegram('sendMessage', { chat_id: chatId, text: `Post enviado a revision. Tema: ${topic}` });
      }
    } else {
      await telegram('sendMessage', { chat_id: chatId, text: 'Comando disponible: /post_now' });
    }

    return res.status(200).json({ ok: true });
  } catch (error) {
    if (chatId) {
      try {
        await telegram('sendMessage', { chat_id: chatId, text: `Error: ${error.message}` });
      } catch (_) {}
    }
    return res.status(200).json({ ok: false, error: error.message });
  }
}
