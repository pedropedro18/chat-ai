const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');

const SISTEMA = `És o assistente virtual do "Teacher Pedro", professor de inglês em Angola.
Respondes em português, de forma curta, simpática e clara.

Cursos de inglês (níveis CEFR), preços a partir de:
- A1 Iniciante: 8 semanas, Kz 15.000/mês
- A2 Elementar: 8 semanas, Kz 15.000/mês
- B1 Intermédio (o mais procurado): 10 semanas, Kz 18.000/mês
- B2 Intermédio Alto: 10 semanas, Kz 18.000/mês
- C1 Avançado: 12 semanas, preço no WhatsApp
- C2 Proficiente: 12 semanas, preço no WhatsApp

Também há cursos de Excel e programação/web.
Se não souberes algo, não inventes: sugere falar com o professor no WhatsApp.
Responde sempre em no máximo 4 frases curtas ou uma lista breve.`;

const MODELO = process.env.GEMINI_MODEL || 'gemini-3.8-flash';
const URL = `https://generativelanguage.googleapis.com/v1beta/models/${MODELO}:generateContent`;
const ERRO = 'Não consegui responder agora. Fala diretamente com o professor no WhatsApp.';
const ADMIN = process.env.ADMIN_NUMERO; // o seu número pessoal, sem +

// Números que o bot nunca atende (família, pais de alunos...)
const IGNORAR = [
  // '244XXXXXXXXX@c.us',
];

const historicos = new Map();

async function gerarResposta(chatId, texto) {
  const hist = historicos.get(chatId) || [];
  hist.push({ role: 'user', parts: [{ text: texto }] });

  const recentes = hist.slice(-10);
  while (recentes.length && recentes[0].role !== 'user') recentes.shift();

  try {
    const r = await fetch(URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-goog-api-key': process.env.GEMINI_API_KEY,
      },
      body: JSON.stringify({
        systemInstruction: { parts: [{ text: SISTEMA }] },
        contents: recentes,
        generationConfig: {
          maxOutputTokens: 2000,
          thinkingConfig: { thinkingBudget: 0 },
        },
      }),
    });
    if (!r.ok) throw new Error(`Gemini ${r.status}: ${(await r.text()).slice(0, 300)}`);

    const dados = await r.json();
    const resposta = dados.candidates[0].content.parts
      .map(p => p.text || '')
      .join('')
      .trim();
    if (!resposta) throw new Error('Resposta vazia');

    hist.push({ role: 'model', parts: [{ text: resposta }] });
    historicos.set(chatId, hist.slice(-10));
    return resposta;
  } catch (e) {
    console.log('Erro:', e.message);
    hist.pop();
    historicos.set(chatId, hist);
    return ERRO;
  }
}

const client = new Client({ authStrategy: new LocalAuth() });

client.on('qr', qr => qrcode.generate(qr, { small: true }));
client.on('ready', () => console.log('WhatsApp pronto!'));
client.on('authenticated', () => console.log('Autenticado'));
client.on('auth_failure', m => console.log('Falha de autenticação:', m));
client.on('disconnected', r => console.log('Desligado:', r));

client.on('message', async msg => {
  if (msg.from.endsWith('@g.us') || msg.from === 'status@broadcast') return;
  if (!msg.body || IGNORAR.includes(msg.from)) return;

  const resposta = await gerarResposta(msg.from, msg.body);
  await msg.reply(resposta);

  // avisa o professor
  if (ADMIN && msg.from !== `${ADMIN}@c.us`) {
    const numero = msg.from.replace('@c.us', '');
    try {
      await client.sendMessage(
        `${ADMIN}@c.us`,
        `Novo contacto: +${numero}\nPerguntou: ${msg.body}\nBot respondeu: ${resposta}`
      );
    } catch (e) {
      console.log('Falha ao avisar admin:', e.message);
    }
  }
});

client.initialize();