from pathlib import Path
import zipfile,io,posixpath
from lxml import etree as E
from openpyxl import load_workbook
from openpyxl.utils.cell import range_boundaries
b=Path('汇报/.ppt_progress_build')
with zipfile.ZipFile(b/'candidate.pptx') as z:files={n:z.read(n) for n in z.namelist()}
cn=next(n for n in files if n.endswith('/chart1.xml'))
rel=E.fromstring(files[posixpath.dirname(cn)+'/_rels/chart1.xml.rels'])
tr=next(x.get('Target') for x in rel if x.get('Type').endswith('/package'))
wn=posixpath.normpath(posixpath.join(posixpath.dirname(cn),tr))
w=load_workbook(io.BytesIO(files[wn]),data_only=True)
r=E.fromstring(files[cn]);ns={'c':'http://schemas.openxmlformats.org/drawingml/2006/chart'}
for ref in r.findall('.//c:numRef',ns):
 sheet,area=ref.find('c:f',ns).text.rsplit('!',1);ws=w[sheet.strip("'")]
 c1,r1,c2,r2=range_boundaries(area);vals=[ws.cell(i,j).value for i in range(r1,r2+1) for j in range(c1,c2+1)]
 for pt in ref.findall('c:numCache/c:pt',ns):pt.find('c:v',ns).text=str(vals[int(pt.get('idx'))])
files[cn]=E.tostring(r,xml_declaration=True,encoding='UTF-8',standalone=True)
with zipfile.ZipFile(b/'candidate.pptx','w',zipfile.ZIP_DEFLATED) as z:
 for n,v in files.items():z.writestr(n,v)
print('Refreshed chart cache from unchanged embedded workbook')
