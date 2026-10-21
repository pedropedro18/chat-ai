const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');

const client = new Client({ authStrategy: new LocalAuth() });

client.on('qr', qr => qrcode.generate(qr, { small: true }));
client.on('ready', () => console.log('WhatsApp pronto!'));
async function gerarResposta(texto) {
  return 'Olá! Recebi: ' + texto;
}
client.on('message', async msg => {
  if (msg.from.endsWith('@g.us')) return; // ignora grupos
  const resposta = await gerarResposta(msg.body); // a tua função atual
  await msg.reply(resposta);
});
client.on('authenticated', () => console.log('Autenticado'));
client.on('auth_failure', m => console.log('Falha de autenticação:', m));
client.on('loading_screen', (p, msg) => console.log('A carregar', p, msg));
client.on('disconnected', r => console.log('Desligado:', r));

client.initialize();