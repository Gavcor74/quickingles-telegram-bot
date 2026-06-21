const TELEGRAM_BOT_TOKEN = clean(process.env.TELEGRAM_BOT_TOKEN);
export const TELEGRAM_CHANNEL_ID = clean(process.env.TELEGRAM_CHANNEL_ID);
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
const NOTION_API_KEY = clean(process.env.NOTION_API_KEY);
const NOTION_DATABASE_ID = clean(process.env.NOTION_DATABASE_ID);

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

function buildPrompt(topic, recentPosts = []) {
  const customBlock = CUSTOM_PROMPT ? `\nInstrucciones extra del dueno del canal (obligatorias):\n${CUSTOM_PROMPT}\n` : '';
  const recentBlock = recentPosts.length
    ? recentPosts.map((post) => `- ${post.title}${post.topic ? ` (${post.topic})` : ''}`).join('\n')
    : '- (sin historial disponible)';

  return `Crea UN post para canal de Telegram sobre '${topic}'.
Salida obligatoria con esta plantilla exacta (sin cambiar encabezados):
ÃƒÂ°Ã…Â¸Ã‚Â§Ã‚Â  [GANCHO EN PREGUNTA]

ÃƒÂ°Ã…Â¸Ã¢â‚¬Å“Ã…â€™ [TITULO CORTO]
[Very short explanation in ENGLISH only (1-2 lines max), useful and specific]

ÃƒÂ°Ã…Â¸Ã¢â‚¬â„¢Ã‚Â¬ English boost
[One extra English line only, practical, memorable and natural]

ÃƒÂ¢Ã…â€œÃ‚Â¨ 3 ejemplos utiles
- [Ejemplo 1: frase natural en ingles] -> [traduccion/adaptacion natural en espanol]
- [Ejemplo 2: frase natural en ingles] -> [traduccion/adaptacion natural en espanol]
- [Ejemplo 3: frase natural en ingles] -> [traduccion/adaptacion natural en espanol]

ÃƒÂ°Ã…Â¸Ã¢â‚¬Å“Ã‚Â Mini reto
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

Historial reciente que debes evitar repetir:
${recentBlock}

No repitas tema, gancho, ejemplos ni mini reto de ese historial. Si el tema coincide, busca un angulo claramente distinto.
${customBlock}
Devuelve SOLO el post final. No anadas comentarios extra.`;
}

function sanitizePost(content, topic) {
  let text = String(content || '').trim().replace(/\[[^\]]+\]/g, '');
  const lines = text.split('\n').map((line) => line.trimEnd());
  const firstIndex = lines.findIndex((line) => line.trim());
  if (firstIndex >= 0) {
    const first = lines[firstIndex].trim();
    if (['ÃƒÂ°Ã…Â¸Ã‚Â§Ã‚Â ', 'ÃƒÂ°Ã…Â¸Ã‚Â§Ã‚Â  ?', 'ÃƒÂ°Ã…Â¸Ã‚Â§Ã‚Â ?', ''].includes(first) || (first.startsWith('ÃƒÂ°Ã…Â¸Ã‚Â§Ã‚Â ') && first.replace('ÃƒÂ°Ã…Â¸Ã‚Â§Ã‚Â ', '').trim().length < 6)) {
      lines[firstIndex] = `ÃƒÂ°Ã…Â¸Ã‚Â§Ã‚Â  Ãƒâ€šÃ‚Â¿SabÃƒÆ’Ã‚Â­as que dominar ${topic} te hace sonar mÃƒÆ’Ã‚Â¡s natural en inglÃƒÆ’Ã‚Â©s?`;
    }
  }
  text = lines.join('\n').replace(/\n{3,}/g, '\n\n').trim();

  if (BRAND_SIGNATURE) {
    const escapedSignature = BRAND_SIGNATURE.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const duplicateSignaturePattern = new RegExp(`(?:\\n\\s*)?(?:${escapedSignature}\\s*)+$`, 'i');
    text = text.replace(duplicateSignaturePattern, '').trimEnd();
    text = `${text}\n\n${BRAND_SIGNATURE}`;
  }

  return text;
}

async function callAnthropic(topic, recentPosts = []) {
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
      messages: [{ role: 'user', content: buildPrompt(topic, recentPosts) }],
    }),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data?.error?.message || `Anthropic error ${response.status}`);
  return (data.content || []).filter((block) => block.type === 'text').map((block) => block.text).join('');
}

async function callOpenAI(topic, recentPosts = []) {
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
        { role: 'user', content: buildPrompt(topic, recentPosts) },
      ],
      temperature: 0.8,
      max_tokens: MAX_TOKENS,
    }),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data?.error?.message || `OpenAI error ${response.status}`);
  return data.choices?.[0]?.message?.content || '';
}

function extractPlainText(property) {
  if (!property) return '';
  if (property.type === 'title') return property.title.map((item) => item.plain_text).join('');
  if (property.type === 'rich_text') return property.rich_text.map((item) => item.plain_text).join('');
  if (property.type === 'select') return property.select?.name || '';
  if (property.type === 'status') return property.status?.name || '';
  if (property.type === 'multi_select') return property.multi_select.map((item) => item.name).join(', ');
  return '';
}

async function notionRequest(path, options = {}) {
  if (!NOTION_API_KEY || !NOTION_DATABASE_ID) return null;
  const response = await fetch(`https://api.notion.com/v1${path}`, {
    ...options,
    headers: {
      authorization: `Bearer ${NOTION_API_KEY}`,
      'content-type': 'application/json',
      'notion-version': '2022-06-28',
      ...(options.headers || {}),
    },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data?.message || `Notion error ${response.status}`);
  return data;
}

async function getRecentNotionPosts(limit = 20) {
  if (!NOTION_API_KEY || !NOTION_DATABASE_ID) return [];
  const data = await notionRequest(`/databases/${NOTION_DATABASE_ID}/query`, {
    method: 'POST',
    body: JSON.stringify({
      page_size: limit,
      sorts: [{ timestamp: 'created_time', direction: 'descending' }],
    }),
  });

  return (data?.results || []).map((page) => {
    const properties = page.properties || {};
    return {
      title: extractPlainText(properties.Idea || properties.Name || properties.Title) || 'Sin titulo',
      topic: extractPlainText(properties.Topic || properties.Tema || properties.Canal),
      body: extractPlainText(properties['DescripciÃƒÆ’Ã‚Â³n'] || properties.Descripcion || properties.Description || properties.Body),
    };
  });
}

function plain(value) {
  return String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase();
}

function findProperty(properties, candidates, type) {
  for (const name of candidates) {
    if (properties[name] && (!type || properties[name].type === type)) return name;
  }

  const normalizedCandidates = candidates.map(plain);
  return Object.keys(properties).find((name) => {
    const prop = properties[name];
    return (!type || prop.type === type) && normalizedCandidates.some((candidate) => plain(name).includes(candidate));
  });
}

function optionName(prop, preferredNames) {
  const options = prop?.[prop.type]?.options || [];
  if (!options.length) return preferredNames[0];

  for (const preferred of preferredNames) {
    const exact = options.find((option) => plain(option.name) === plain(preferred));
    if (exact) return exact.name;
  }

  for (const preferred of preferredNames) {
    const partial = options.find((option) => plain(option.name).includes(plain(preferred)) || plain(preferred).includes(plain(option.name)));
    if (partial) return partial.name;
  }

  return preferredNames[0];
}

function propertyValue(prop, value) {
  if (!prop) return null;
  if (prop.type === 'rich_text') return { rich_text: [{ text: { content: value } }] };
  if (prop.type === 'title') return { title: [{ text: { content: value } }] };
  if (prop.type === 'select') return { select: { name: optionName(prop, [value]) } };
  if (prop.type === 'multi_select') return { multi_select: [{ name: optionName(prop, [value]) }] };
  if (prop.type === 'status') return { status: { name: optionName(prop, [value]) } };
  return null;
}

function topicTypeCandidates(topic) {
  const map = {
    'phrasal verbs': ['Phrasal Verb', 'Phrasal verbs', 'Verbo frasal'],
    collocations: ['Collocation', 'Collocations'],
    slang: ['Slang'],
    idioms: ['Idiom', 'Idioms'],
    'false friends': ['False Friend', 'False friends'],
    'pronunciation tips': ['PronunciaciÃƒÂ³n', 'Pronunciation'],
    'common mistakes': ['Error comÃƒÂºn', 'Common mistake'],
    'business english': ['Business English'],
    'travel english': ['Travel English'],
    'email writing': ['Writing'],
    'grammar in context': ['GramÃƒÂ¡tica', 'Grammar'],
    'vocabulary builder': ['Vocabulario', 'Vocabulary'],
  };
  return map[topic] || [topic];
}

function slugify(value) {
  return String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 80);
}

function hashText(value) {
  let hash = 5381;
  const text = String(value || '');
  for (let i = 0; i < text.length; i += 1) {
    hash = ((hash << 5) + hash) + text.charCodeAt(i);
    hash &= 0xffffffff;
  }
  return Math.abs(hash >>> 0).toString(16);
}
export async function saveNotionPost({ title, topic, content, telegramMessageId }) {
  if (!NOTION_API_KEY || !NOTION_DATABASE_ID) return;

  const database = await notionRequest(`/databases/${NOTION_DATABASE_ID}`);
  const schema = database?.properties || {};
  const properties = {};

  const titleName = findProperty(schema, ['Idea', 'Name', 'Title'], 'title');
  if (titleName) {
    properties[titleName] = { title: [{ text: { content: title.slice(0, 120) } }] };
  }

  const descriptionName = findProperty(schema, ['DescripciÃƒÂ³n', 'Descripcion', 'Description', 'Body'], 'rich_text');
  if (descriptionName) {
    properties[descriptionName] = { rich_text: [{ text: { content: content.slice(0, 1900) } }] };
  }

  const channelName = findProperty(schema, ['Canal', 'Channel']);
  if (channelName) {
    const value = propertyValue(schema[channelName], 'Ã°Å¸â€œÂ¢ QuickinglÃƒÂ©s');
    if (value) properties[channelName] = value;
  }

  const statusName = findProperty(schema, ['Estado', 'Status']);
  if (statusName) {
    const prop = schema[statusName];
    const value = propertyValue(prop, optionName(prop, ['Borrador', 'Idea', 'En proceso']));
    if (value) properties[statusName] = value;
  }

  const editorialStatusName = findProperty(schema, ['Estatus', 'Estado editorial', 'Revision', 'RevisiÃ³n']);
  if (editorialStatusName && editorialStatusName !== statusName) {
    const prop = schema[editorialStatusName];
    const value = propertyValue(prop, optionName(prop, ['Generada', 'Generado']));
    if (value) properties[editorialStatusName] = value;
  }

  const originName = findProperty(schema, ['Origen', 'Source']);
  if (originName) {
    const prop = schema[originName];
    const value = propertyValue(prop, optionName(prop, ['Bot', 'Vercel Bot', 'AutomÃ¡tico', 'Automatico']));
    if (value) properties[originName] = value;
  }


  const slug = `${new Date().toISOString().slice(0, 10)}-${slugify(title)}`;
  const slugName = findProperty(schema, ['ID Bot / Slug', 'Slug', 'ID Bot', 'Bot ID'], 'rich_text');
  if (slugName) {
    properties[slugName] = { rich_text: [{ text: { content: slug } }] };
  }

  const hashName = findProperty(schema, ['Hash idea', 'Hash', 'Idea hash'], 'rich_text');
  if (hashName) {
    properties[hashName] = { rich_text: [{ text: { content: hashText(`${topic}\n${title}\n${content}`) } }] };
  }

  const telegramMessageName = findProperty(schema, ['Telegram Message ID', 'Message ID', 'Telegram ID'], 'rich_text');
  if (telegramMessageName && telegramMessageId) {
    properties[telegramMessageName] = { rich_text: [{ text: { content: String(telegramMessageId) } }] };
  }
  const dateName = findProperty(schema, ['Fecha', 'Date'], 'date');
  if (dateName) {
    properties[dateName] = { date: { start: new Date().toISOString().slice(0, 10) } };
  }

  const publishedName = findProperty(schema, ['Publicado', 'Publicacion', 'PublicaciÃƒÂ³n'], 'checkbox');
  if (publishedName) {
    properties[publishedName] = { checkbox: false };
  }

  const typeName = findProperty(schema, ['Tipo', 'Type']);
  if (typeName) {
    const prop = schema[typeName];
    const value = propertyValue(prop, optionName(prop, topicTypeCandidates(topic)));
    if (value) properties[typeName] = value;
  }

  const priorityName = findProperty(schema, ['Prioridad', 'Priority']);
  if (priorityName) {
    const prop = schema[priorityName];
    const value = propertyValue(prop, optionName(prop, ['Media', 'Medium', 'Alta']));
    if (value) properties[priorityName] = value;
  }

  await notionRequest('/pages', {
    method: 'POST',
    body: JSON.stringify({
      parent: { database_id: NOTION_DATABASE_ID },
      properties,
    }),
  });
}
function extractTitle(content, topic) {
  const titleLine = content
    .split('\n')
    .map((line) => line.trim())
    .find((line) => line && !line.startsWith('ÃƒÂ°Ã…Â¸Ã‚Â§Ã‚Â '));
  return (titleLine || `Post Quickingles: ${topic}`).replace(/^ÃƒÂ°Ã…Â¸Ã¢â‚¬Å“Ã…â€™\s*/, '').slice(0, 120);
}

export async function generatePost() {
  const topic = chooseTopic();
  const recentPosts = await getRecentNotionPosts();
  const rawContent = AI_PROVIDER === 'openai' ? await callOpenAI(topic, recentPosts) : await callAnthropic(topic, recentPosts);
  const content = sanitizePost(rawContent, topic);
  return { topic, content, title: extractTitle(content, topic) };
}

export async function telegram(method, payload) {
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

export function authorized(userId) {
  return !TELEGRAM_ADMIN_USER_ID || String(userId) === TELEGRAM_ADMIN_USER_ID;
}