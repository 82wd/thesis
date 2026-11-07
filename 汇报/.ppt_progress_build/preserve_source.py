from pathlib import Path
import zipfile,json,copy
from lxml import etree as E
b=Path('汇报/.ppt_progress_build');ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
changes=json.loads((b/'changes.json').read_text())
with zipfile.ZipFile(b/'source_user_edited.pptx') as src, zipfile.ZipFile(b/'authored.pptx') as new:
 files={n:src.read(n) for n in src.namelist()}
 for n,items in changes.items():
  name=f'ppt/slides/slide{n}.xml';r=E.fromstring(files[name]);q=E.fromstring(new.read(name))
  rs=r.findall('p:cSld/p:spTree/p:sp',ns);qs=q.findall('p:cSld/p:spTree/p:sp',ns)
  assert len(rs)==len(qs),(n,len(rs),len(qs))
  for j in items:
   j=int(j);old=rs[j].find('p:txBody',ns);replacement=qs[j].find('p:txBody',ns)
   rs[j].replace(old,copy.deepcopy(replacement))
  if n=='6':
   a=r.find('.//a:tbl',ns);v=q.find('.//a:tbl',ns)
   a.getparent().replace(a,copy.deepcopy(v))
  files[name]=E.tostring(r,xml_declaration=True,encoding='UTF-8',standalone=True)
 # Only transplant speaker notes text, preserving source notes relationships and placeholders.
 for n in [4,6,7,8,9,10,11,12]:
  name=f'ppt/notesSlides/notesSlide{n}.xml';r=E.fromstring(files[name]);q=E.fromstring(new.read(name))
  def body(tree):
   return next(s for s in tree.findall('.//p:sp',ns) if s.find('.//p:ph',ns) is not None and s.find('.//p:ph',ns).get('type')=='body')
  a=body(r);v=body(q);a.replace(a.find('p:txBody',ns),copy.deepcopy(v.find('p:txBody',ns)))
  files[name]=E.tostring(r,xml_declaration=True,encoding='UTF-8',standalone=True)
 with zipfile.ZipFile(b/'candidate.pptx','w',zipfile.ZIP_DEFLATED) as z:
  for n,data in files.items():z.writestr(n,data)
 print('Preserved all source assets, charts, user-edited introductory slides and unchanged slide XML')
