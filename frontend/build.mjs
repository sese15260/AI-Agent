import {cp, mkdir, writeFile} from 'node:fs/promises';
const target = new URL('./dist/', import.meta.url);
await mkdir(target, {recursive:true});
for (const file of ['index.html','style.css','app.js']) await cp(new URL('./'+file, import.meta.url), new URL('./dist/'+file, import.meta.url));
const url=process.env.API_BASE_URL;
if(!url) throw new Error('API_BASE_URL must be set for deployment');
await writeFile(new URL('./dist/config.js', import.meta.url), `window.API_BASE_URL = ${JSON.stringify(url)};\n`);
