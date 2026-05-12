# WordPress Post Uploader

Aquesta eina permet crear o actualitzar posts de WordPress des de la terminal amb la REST API oficial de WordPress.

El script fa servir un usuari de WordPress i una `application password`. No cal guardar la contrasenya real del compte i no s'ha de posar cap contrasenya dins del codi.

## Fitxers

- `wp_post.py`: script principal per crear o actualitzar posts.
- `README.md`: aquesta guia.

## Requisits

- Python 3.9 o superior.
- Un WordPress accessible per HTTPS.
- Permisos d'usuari suficients per crear posts.
- La REST API activada. En una instal·lacio normal de WordPress ja ho esta.

No hi ha dependències obligatòries fora de la llibreria estàndard de Python. Si vols convertir Markdown a HTML amb `--markdown`, instal·la el paquet opcional:

```bash
python3 -m pip install markdown
```

## 1. Crear una application password a WordPress

No facis servir la contrasenya normal del teu usuari. WordPress permet crear contrasenyes específiques per aplicacions.

Passos:

1. Entra al panell d'administració de WordPress.
2. Ves a `Usuaris` i obre el teu perfil.
3. Busca la secció `Application Passwords` o `Contrasenyes d'aplicacio`.
4. Escriu un nom descriptiu, per exemple `terminal-uploader`.
5. Clica per crear-la.
6. Copia la contrasenya generada. WordPress la mostra una sola vegada.

Guarda aquesta contrasenya en un lloc segur. Si la perds, elimina-la i crea'n una de nova.

## 2. Configurar usuari, URL i password

Hi ha tres maneres de configurar l'accés. La més recomanada és fer servir variables d'entorn.

### Opcio A: variables d'entorn

```bash
export WP_SITE_URL="https://example.com"
export WP_USER="el_teu_usuari"
export WP_APP_PASSWORD="xxxx xxxx xxxx xxxx xxxx xxxx"
```

WordPress mostra les `application passwords` sovint separades per espais. Conserva-les tal com te les dona WordPress o copia-les sense espais; habitualment totes dues formes funcionen segons la configuració del servidor.

Per evitar escriure-les cada vegada, pots afegir aquestes línies al teu `~/.zshrc` o `~/.bashrc`. Si ho fas, assegura't que aquest fitxer no es comparteix ni es puja a GitHub.

### Opcio B: fitxer de configuracio local

També pots crear un fitxer JSON a:

```bash
~/.config/wp-uploader/config.json
```

Contingut:

```json
{
  "site_url": "https://example.com",
  "user": "el_teu_usuari",
  "app_password": "xxxx xxxx xxxx xxxx xxxx xxxx"
}
```

Protegeix el fitxer perquè només el pugui llegir el teu usuari:

```bash
chmod 600 ~/.config/wp-uploader/config.json
```

### Opcio C: arguments de terminal

```bash
python3 publishingTools/wp_post.py \
  --site "https://example.com" \
  --user "el_teu_usuari" \
  --password "xxxx xxxx xxxx xxxx xxxx xxxx" \
  --title "Titol del post" \
  --content-file post.html
```

Aquesta opció és menys recomanable perquè la contrasenya pot quedar registrada a l'historial de la terminal.

Si no passes cap password per argument, variable d'entorn o fitxer de configuració, el script te la demanarà de forma interactiva.

## 3. Crear un post en esborrany

Per defecte, el script crea posts amb estat `draft`.

```bash
python3 publishingTools/wp_post.py \
  --title "El meu primer post des de terminal" \
  --content-file post.html
```

També pots passar el contingut directament:

```bash
python3 publishingTools/wp_post.py \
  --title "Nota rapida" \
  --content "<p>Aquest post s'ha creat des de la terminal.</p>"
```

O per pipe:

```bash
printf "<p>Contingut generat amb una comanda.</p>" | python3 publishingTools/wp_post.py \
  --title "Post via pipe"
```

## 4. Publicar directament

Per publicar sense deixar el post com a esborrany:

```bash
python3 publishingTools/wp_post.py \
  --title "Post publicat des de terminal" \
  --content-file post.html \
  --status publish
```

Estats disponibles:

- `draft`: esborrany.
- `publish`: publicat.
- `pending`: pendent de revisió.
- `private`: privat.
- `future`: programat, si també configures la data des de WordPress o amplies el payload.

## 5. Escriure en Markdown

Si tens un fitxer Markdown:

```bash
python3 -m pip install markdown
```

Després:

```bash
python3 publishingTools/wp_post.py \
  --title "Post en Markdown" \
  --content-file post.md \
  --markdown
```

El script convertirà el Markdown a HTML abans d'enviar-lo a WordPress.

## 6. Categories, tags, slug i excerpt

WordPress espera IDs numèrics per categories i tags.

Exemple:

```bash
python3 publishingTools/wp_post.py \
  --title "Post categoritzat" \
  --content-file post.html \
  --categories 2,7 \
  --tags 4,9 \
  --slug "post-categoritzat" \
  --excerpt "Resum curt del post"
```

Per trobar els IDs pots mirar l'URL d'edició dins del panell de WordPress o consultar la REST API:

```bash
curl "https://example.com/wp-json/wp/v2/categories"
curl "https://example.com/wp-json/wp/v2/tags"
```

## 7. Actualitzar un post existent

Si ja tens l'ID del post:

```bash
python3 publishingTools/wp_post.py \
  --post-id 123 \
  --title "Titol actualitzat" \
  --content-file post_actualitzat.html \
  --status draft
```

Sense `--post-id`, el script crea un post nou. Amb `--post-id`, envia els canvis al post existent.

## 8. Provar sense publicar res

Abans d'enviar res a WordPress pots revisar el JSON que s'enviaria:

```bash
python3 publishingTools/wp_post.py \
  --title "Prova" \
  --content-file post.html \
  --status draft \
  --dry-run
```

`--dry-run` no fa cap connexió amb WordPress.

## 9. Exemple complet

```bash
export WP_SITE_URL="https://example.com"
export WP_USER="jordi"
export WP_APP_PASSWORD="xxxx xxxx xxxx xxxx xxxx xxxx"

python3 publishingTools/wp_post.py \
  --title "Resultats de l'analisi" \
  --content-file resultats.md \
  --markdown \
  --status draft \
  --categories 3 \
  --tags 8,12 \
  --excerpt "Resum dels resultats principals."
```

Si tot va bé, veuràs una sortida semblant a:

```text
OK: post ID 456
Status: draft
Link: https://example.com/resultats-de-lanalisi/
```

## 10. Seguretat

- No pugis mai `config.json` amb contrasenyes a GitHub.
- No escriguis la `application password` dins del script.
- Evita `--password` si treballes en un ordinador compartit.
- Fes servir HTTPS.
- Si sospites que una `application password` s'ha filtrat, elimina-la des del perfil d'usuari de WordPress i crea'n una de nova.

## 11. Errors habituals

### HTTP 401 o 403

L'usuari o la `application password` no són correctes, o l'usuari no té permisos per crear posts.

### HTTP 404

La URL del WordPress pot ser incorrecta, o la REST API pot estar bloquejada per un plugin de seguretat. Prova:

```bash
curl "https://example.com/wp-json/wp/v2/posts"
```

### El contingut Markdown surt com text pla

Assegura't d'haver instal·lat `markdown` i d'afegir l'opció `--markdown`.

### Categories o tags no funcionen

Has de passar IDs numèrics, no noms. Per exemple `--categories 2,7`, no `--categories blog,noticies`.
