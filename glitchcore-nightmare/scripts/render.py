import sys, verovio, cairosvg, io
from pypdf import PdfWriter, PdfReader
src, dst = sys.argv[1], sys.argv[2]
tk = verovio.toolkit()
tk.setOptions({'pageWidth': 2100, 'pageHeight': 2970, 'scale': 35, 'adjustPageHeight': False, 'header': 'auto', 'footer': 'auto', 'breaks': 'auto', 'condenseFirstPage': False})
tk.loadFile(src)
n = tk.getPageCount(); print('pages', n)
w = PdfWriter()
for i in range(1, n + 1):
    svg = tk.renderToSVG(i)
    if i == 1: open(dst.replace('.pdf', '_p1.svg'), 'w').write(svg)
    pdf = cairosvg.svg2pdf(bytestring=svg.encode())
    for pg in PdfReader(io.BytesIO(pdf)).pages: w.add_page(pg)
w.write(dst)
