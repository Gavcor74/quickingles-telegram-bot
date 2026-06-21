const TELEGRAM_BOT_TOKEN = clean(process.env.TELEGRAM_BOT_TOKEN);
const TELEGRAM_CHANNEL_ID = clean(process.env.TELEGRAM_CHANNEL_ID);
const TELEGRAM_ADMIN_USER_ID = clean(process.env.TELEGRAM_ADMIN_USER_ID);

const AI_PROVIDER = clean(process.env.AI_PROVIDER || 'anthropic').toLowerCase();
const ANTHROPIC_API_KEY = clean(process.env.ANTHROPIC_API_KEY);
const ANTHROPIC_BASE_URL = clean(process.env.ANTHROPIC_BASE_URL || 'https://api.anthropic.com').replace(/\/$/, '');
const ANTHROPIC_MODEL = clean(process.env.ANTHROPIC_MODEL || 'claude-sonnet-4-5');
const OPENAI_API_KEY = clean(process.env.OPENAI_API_KEY);
const OPENAI_BASE_URL = clean(process.env.OPENAI_BASE_URL || 'https://api.openai.com/v1').replace(/\/$/, '');
const OPENAI_MODEL = clean(process.env.OPENAI_MODEL || 'gpt-4o-mini');
const MAX_TOKENS = Number(process.env.MAX_TOKENS || 1200);

const APP_TIMEZONE = clean(process.env.APP_TIMEZONE || 'Europe/Madrid');
const BRAND_SIGNATURE = clean(process.env.BRAND_SIGNATURE || '- Jesus | Quickingles');
const POST_LENGTH = clean(process.env.POST_LENGTH || 'medium').toLowerCase();
const CUSTOM_PROMPT = clean(process.env.CUSTOM_PROMPT || '');

const TOPICS = [
  'phrasal verbs',
  'collocations',
  'slang',
  'idioms',
  'false friends',
  'pronunciation tips',
  'common mistakes',
  'business english',
  'travel english',
  'listening hacks',
  'small talk',
  'email writing',
  'interview english',
  'grammar in context',
  'vocabulary builder',
];

const CONTENT_SYSTEM_PROMPT =
  'Eres copywriter experto para un canal de Telegram de ingles para hispanohablantes. ' +
  'Escribes con voz personal del profesor, directo, cercano y claro. ' +
  'Tu salida SIEMPRE debe seguir una plantilla fija estilo Notion con emojis, sin frases de asistente ni texto meta.';

function clean(value) {
  return String(value || '').trim().replace(/^['"]|['"]$/g, '');
}

function topicPool() {
  const raw = clean(process.env.TOPIC_POOL || '');
  if (!raw) return TOPICS;
  const topics = raw.split(',').map((item) => item.trim().toLowerCase()).filter(Boolean);
  return topics.length ? topics : TOPICS;
}

function chooseTopic() {
  const fixed = clean(process.env.FIXED_TOPIC || '').toLowerCase();
  if (fixed) return fixed;

  const pool = topicPool();
  const date = new Date(new Date().toLocaleString('en-US', { timeZone: APP_TIMEZONE }));
  const dayIndex = Math.floor(date.getTime() / 86400000);
  return pool[dayIndex % pool.length];
}

function lengthInstruction() {
  if (POST_LENGTH === 'short') return '70 a 110 palabras';
  if (POST_LENGTH === 'long') return '150 a 210 palabras';
  return '100 a 150 palabras';
}

function topicGuidance(topic) {
  const guidance = {
    slang: 'Para slang: evita explicar lo obvio. Ensena uso real, matiz, registro y contexto. Cada ejemplo debe incluir una frase natural en ingles y una traduccion/adaptacion util en espanol.',
    'phrasal verbs': 'Para phrasal verbs: no des definiciones abstractas. Prioriza verbo + contexto real + traduccion natural.',
    collocations: 'Para collocations: centra el post en combinaciones naturales que un hispanohablante suele decir mal.',
    'common mistakes': 'Para common mistakes: compara error comun vs forma natural correcta de manera muy clara.',
    'pronunciation tips': 'Para pronunciation tips: incluye contraste de sonido o palabra concreta para practicar.',
    'grammar in context': 'Para grammar in context: explica la estructura con ejemplos cotidianos, no con teoria larga.',
  };
  return guidance[topic] || 'Haz el contenido practico, especifico y util para hispanohablantes adultos que quieren sonar mas naturales.';
}

function buildPrompt(topic) {
  const customBlock = CUSTOM_PROMPT ? `\nInstrucciones extra del dueno del canal (obligatorias):\n${CUSTOM_PROMPT}\n` : '';
  return `Crea UN post para canal de Telegram sobre '${topic}'.
Salida obligatoria con esta plantilla exacta (sin cambiar encabezados):
🧠 [GANCHO EN PREGUNTA]

📌 [TITULO CORTO]
[Very short explanation in ENGLISH only (1-2 lines max), useful and specific]

💬 English boost
[One extra English line only, practical, memorable and natural]

✨ 3 ejemplos utiles
- [Ejemplo 1: frase natural en ingles] -> [traduccion/adaptacion natural en espanol]
- [Ejemplo 2: frase natural en ingles] -> [traduccion/adaptacion natural en espanol]
- [Ejemplo 3: frase natural en ingles] -> [traduccion/adaptacion natural en espanol]

📝 Mini reto
[Un ejercicio corto de practica, pero NO incluyas la solucion]

Reglas obligatorias:
1) Prohibido empezar con: 'Aqui tienes', 'A continuacion', 'Te comparto', 'Como IA'.
2) Escribir como profesor humano (yo/te), no como asistente.
3) Explicacion principal en INGLES, muy corta. Prioriza ejemplos con frases en ingles + traduccion.
4) Longitud objetivo: ${lengthInstruction()}. Mantener texto corto y directo.
5) Reemplaza TODO lo que este entre [corchetes] con contenido real.
6) Cierra siempre con esta firma exacta: ${BRAND_SIGNATURE}
7) PROHIBIDO incluir una seccion de solucion o respuesta del reto.
8) No hagas definiciones obvias o demasiado escolares. Tiene que sonar util para adultos.
9) Cada ejemplo debe ser concreto, idiomatico y listo para reutilizar en una conversacion real.
10) El mini reto debe invitar a producir ingles de verdad, no a dar una opinion vaga.
Guia especifica para este tema:
${topicGuidance(topic)}
${customBlock}
Devuelve SOLO el post final. No anadas comentarios extra.`;
}

function sanitizePost(content, topic) {
  let text = String(content || '').trim().replace(/\[[^\]]+\]/g, '');
  const lines = text.split('\n').map((line) => line.trimEnd());
  const firstIndex = lines.findIndex((line) => line.trim());
  if (firstIndex >= 0) {
    const first = lines[firstIndex].trim();
    if (['🧠', '🧠 ?', '🧠?', ''].includes(first) || (first.startsWith('🧠') && first.replace('🧠', '').trim().length < 6)) {
      lines[firstIndex] = `🧠 ¿Sabías que dominar ${topic} te hace sonar más natural en inglés?`;
    }
  }
  text = lines.join('\n').replace(/\n{3,}/g, '\n\n').trim();
  if (BRAND_SIGNATURE && !text.toLowerCase().endsWith(BRAND_SIGNATURE.toLowerCase())) {
    text = `${text}\n\n${BRAND_SIGNATURE}`;
  }
  return text;
}

async function callAnthropic(topic) {
  if (!ANTHROPIC_API_KEY) throw new Error('Falta ANTHROPIC_API_KEY en variables de entorno.');
  const response = await fetch(`${ANTHROPIC_BASE_URL}/v1/messages`, {
    method: 'POST',
    headers: {
      'x-api-key': ANTHROPIC_API_KEY,
      'anthropic-version': '2023-06-01',
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      model: ANTHROPIC_MODEL,
      max_tokens: MAX_TOKENS,
      temperature: 0.8,
      system: CONTENT_SYSTEM_PROMPT,
      messages: [{ role: 'user', content: buildPrompt(topic) }],
    }),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data?.error?.message || `Anthropic error ${response.status}`);
  return (data.content || []).filter((block) => block.type === 'text').map((block) => block.text).join('');
}

async function callOpenAI(topic) {
  if (!OPENAI_API_KEY) throw new Error('Falta OPENAI_API_KEY en variables de entorno.');
  const response = await fetch(`${OPENAI_BASE_URL}/chat/completions`, {
    method: 'POST',
    headers: {
      authorization: `Bearer ${OPENAI_API_KEY}`,
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      model: OPENAI_MODEL,
      messages: [
        { role: 'system', content: CONTENT_SYSTEM_PROMPT },
        { role: 'user', content: buildPrompt(topic) },
      ],
      temperature: 0.8,
      max_tokens: MAX_TOKENS,
    }),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data?.error?.message || `OpenAI error ${response.status}`);
  return data.choices?.[0]?.message?.content || '';
}

async function generatePost() {
  const topic = chooseTopic();
  const content = AI_PROVIDER === 'openai' ? await callOpenAI(topic) : await callAnthropic(topic);
  return { topic, content: sanitizePost(content, topic) };
}

async function telegram(method, payload) {
  if (!TELEGRAM_BOT_TOKEN) throw new Error('Falta TELEGRAM_BOT_TOKEN en variables de entorno.');
  const response = await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/${method}`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.description || `Telegram error ${response.status}`);
  return data;
}

function authorized(userId) {
  return !TELEGRAM_ADMIN_USER_ID || String(userId) === TELEGRAM_ADMIN_USER_ID;
}

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
