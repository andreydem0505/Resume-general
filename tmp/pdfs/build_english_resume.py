from pathlib import Path
import html
import re

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[2]
source = (ROOT / 'README.md').read_text()
OUTPUT = ROOT / 'output/pdf/Andrey_Dementiev_Resume_English.pdf'
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
pdfmetrics.registerFont(TTFont('ArialResume', '/System/Library/Fonts/Supplemental/Arial.ttf'))
pdfmetrics.registerFont(TTFont('ArialResumeBold', '/System/Library/Fonts/Supplemental/Arial Bold.ttf'))
pdfmetrics.registerFontFamily('ArialResume', normal='ArialResume', bold='ArialResumeBold')

INK = colors.HexColor('#242a35')
BLUE = colors.HexColor('#216e98')
MUTED = colors.HexColor('#67717e')
W, H = A4
MARGIN = 45.35433
WIDTH = W - 2 * MARGIN
c = canvas.Canvas(str(OUTPUT), pagesize=A4, pageCompression=1)
c.setTitle('Andrey Dementiev - English Resume')
c.setAuthor('Andrey Dementiev')
y = H - MARGIN


def plain(value):
    return html.unescape(re.sub(r'<[^>]+>', '', value)).strip()


def paragraph_markup(value):
    value = value.strip().replace('—', '-').replace('–', '-')
    value = re.sub(r'<br\s*/?>', '<br/>', value)
    value = re.sub(r'<a href="([^"]+)"[^>]*>(.*?)</a>',
                   lambda m: f'<link href="{html.escape(m[1], quote=True)}" color="#216e98">{m[2]}</link>', value)
    return value


def text(value, size=11.2, bold=False, color=INK, after=7, x=None, width=None, leading=None):
    global y
    x = MARGIN if x is None else x
    width = WIDTH if width is None else width
    style = ParagraphStyle('resume', fontName='ArialResumeBold' if bold else 'ArialResume',
                           fontSize=size, leading=leading or size * 1.35, textColor=color)
    p = Paragraph(paragraph_markup(value), style)
    _, height = p.wrap(width, H)
    if y - height < 65:
        raise ValueError(f'Content would overlap footer: {plain(value)[:60]}')
    p.drawOn(c, x, y - height)
    y -= height + after
    return height


def heading(value, before=12, after=9):
    global y
    y -= before
    text(value, size=13.3, bold=True, after=after, leading=16)


def bullet(value):
    global y
    top = y
    text(value, x=MARGIN + 12, width=WIDTH - 12, after=7)
    c.setFillColor(INK)
    c.circle(MARGIN + 2, top - 8.2, 1.15, fill=1, stroke=0)


def footer(number):
    c.setFillColor(MUTED)
    c.setFont('ArialResume', 8)
    c.drawRightString(W - MARGIN, 26, str(number))


def optimized_image(path, max_size):
    image = Image.open(path)
    image.thumbnail(max_size, Image.Resampling.LANCZOS)
    return ImageReader(image)


def company(title, body, logo):
    global y
    top = y
    text(html.escape(plain(title)), size=12.1, bold=True,
         x=MARGIN + 24, width=WIDTH - 24, after=10, leading=16)
    c.drawImage(optimized_image(ROOT / logo, (160, 160)), MARGIN - 1, top - 15,
                width=15, height=15, preserveAspectRatio=True, anchor='c', mask='auto')
    for item in re.findall(r'<li>([\s\S]*?)</li>', body):
        bullet(item)
    stack = re.search(r'Tech Stack:\s*<b>(.*?)</b>', body).group(1)
    y -= 4
    text(f'Tech Stack: <b>{stack}</b>', size=10.9, after=7)


name = re.search(r'<h1>(.*?)</h1>', source).group(1)
intro = re.findall(r'<h3>(.*?)</h3>', source)
education = re.search(r'<h3>Education:</h3>\s*([\s\S]*?)<h3>Contact:</h3>', source).group(1)
about = re.search(r'<h3>About Me:</h3>\s*([\s\S]*?)<hr/>', source).group(1)
jobs = re.findall(r'<h3><img[^>]+/>&nbsp;([\s\S]*?)</h3>\s*<ul>([\s\S]*?)</ul>', source)
assert len(jobs) == 2

c.drawImage(optimized_image(ROOT / 'images/me.jpg', (600, 750)), W - MARGIN - 106, H - MARGIN - 133,
            width=106, height=133, preserveAspectRatio=True, anchor='c', mask='auto')
text(name, size=21.3, bold=True, width=WIDTH - 125, leading=26, after=10)
text(intro[0], size=14.5, bold=True, color=BLUE, after=8, width=WIDTH - 125)
text(intro[1], size=11.2, after=24, width=WIDTH - 125)
heading('Education:', before=0)
text(education, after=15, width=WIDTH - 125)
heading('Contact:', before=0)
contact_section = source.split('<h3>Contact:</h3>')[1].split('<hr/>')[0]
contacts = []
for url, label in re.findall(r'<a href="([^"]+)"><img[^>]+alt="([^"]+)"[^>]*></a>', contact_section):
    label = url.removeprefix('mailto:') if url.startswith('mailto:') else label
    contacts.append(f'<a href="{url}">{html.escape(label)}</a>')
text(' &nbsp; | &nbsp; '.join(contacts), size=10.9, after=13)
c.setStrokeColor(colors.HexColor('#d1d6db'))
c.setLineWidth(.6)
c.line(MARGIN, y, W - MARGIN, y)
heading('About Me:', before=15, after=9)
text(about, size=10.9, after=0)
heading('Work Experience:', before=16, after=12)
company(jobs[0][0], jobs[0][1], 'images/avito.png')
print(f'Page 1 content bottom: {y:.1f} pt')
footer(1)
c.showPage()
y = H - MARGIN
company(jobs[1][0], jobs[1][1], 'images/yandex.png')
heading('Achievements:', before=25, after=12)
achievement = source.split('<h3>Achievements:</h3>')[1].strip()
bullet(achievement)
print(f'Page 2 content bottom: {y:.1f} pt')
footer(2)
c.save()

reader = PdfReader(OUTPUT)
assert len(reader.pages) == 2
extracted = ' '.join(page.extract_text() for page in reader.pages)
normalized = ' '.join(extracted.split())
for value in [about, *[item for _, body in jobs for item in re.findall(r'<li>([\s\S]*?)</li>', body)], achievement]:
    expected = ' '.join(plain(value).replace('—', '-').replace('–', '-').split())
    assert expected in normalized, f'Missing text: {expected[:60]}'
uris = {a.get_object().get('/A', {}).get('/URI') for page in reader.pages for a in page.get('/Annots', [])}
expected_uris = set(re.findall(r'<a href="([^"]+)"', source))
assert expected_uris <= uris, f'Missing links: {expected_uris - uris}'
print(f'Created {OUTPUT}; {len(reader.pages)} pages; {len(uris)} clickable links; all paragraphs verified.')
