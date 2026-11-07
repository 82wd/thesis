from pathlib import Path
import zipfile,xml.etree.ElementTree as E,posixpath
root=Path('/Users/lzy/Desktop/毕设');build=root/'汇报/.ppt_work_build'
source=root/'汇报/PPT/2026-11-05_组会汇报_成果重点版.pptx'
with zipfile.ZipFile(source) as old,zipfile.ZipFile(build/'candidate.pptx') as new:
 files={n:new.read(n) for n in new.namelist()}
 old_chart=next(n for n in old.namelist() if n.endswith('/chart1.xml'))
 new_chart=next(n for n in new.namelist() if n.endswith('/chart1.xml'))
 files[new_chart]=old.read(old_chart)
 old_rels=posixpath.dirname(old_chart)+'/_rels/chart1.xml.rels'
 rel=E.fromstring(old.read(old_rels))
 for child in rel:
  if child.attrib.get('TargetMode')!='External':
   target=posixpath.normpath(posixpath.join(posixpath.dirname(old_chart),child.attrib['Target']))
   files[target]=old.read(target)
   child.attrib['Target']=posixpath.relpath(target,posixpath.dirname(new_chart))
 E.register_namespace('', 'http://schemas.openxmlformats.org/package/2006/relationships')
 files[posixpath.dirname(new_chart)+'/_rels/chart1.xml.rels']=E.tostring(rel,encoding='utf-8',xml_declaration=True)
 ct=E.fromstring(files['[Content_Types].xml']);orig=E.fromstring(old.read('[Content_Types].xml'))
 for child in orig:
  if child.attrib.get('Extension')=='xlsx' or child.attrib.get('PartName','').endswith('.xlsx'):
   if not any(c.attrib==child.attrib for c in ct):ct.append(child)
 E.register_namespace('', 'http://schemas.openxmlformats.org/package/2006/content-types')
 files['[Content_Types].xml']=E.tostring(ct,encoding='utf-8',xml_declaration=True)
 # Refresh numeric chart caches from the preserved workbook ranges.
 import io
 from openpyxl import load_workbook
 from openpyxl.utils.cell import range_boundaries
 wb=load_workbook(io.BytesIO(files[next(n for n in files if n.endswith('.xlsx'))]),data_only=True)
 chart=E.fromstring(files[new_chart]); ns={'c':'http://schemas.openxmlformats.org/drawingml/2006/chart'}
 for ref in chart.findall('.//c:numRef',ns):
  formula=ref.find('c:f',ns).text; sheet,area=formula.rsplit('!',1)
  ws=wb[sheet.strip("'")]; minc,minr,maxc,maxr=range_boundaries(area)
  vals=[ws.cell(r,c).value for r in range(minr,maxr+1) for c in range(minc,maxc+1)]
  for pt in ref.findall('c:numCache/c:pt',ns):pt.find('c:v',ns).text=str(vals[int(pt.attrib['idx'])])
 E.register_namespace('c',ns['c'])
 files[new_chart]=E.tostring(chart,encoding='utf-8',xml_declaration=True)
 with zipfile.ZipFile(build/'repaired.pptx','w',zipfile.ZIP_DEFLATED) as z:
  for n,data in files.items():z.writestr(n,data)
print('Preserved chart and workbook; resolved relative package paths')
