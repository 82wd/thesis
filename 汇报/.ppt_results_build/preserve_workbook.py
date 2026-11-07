from pathlib import Path
import zipfile,xml.etree.ElementTree as E
E.register_namespace('', 'http://schemas.openxmlformats.org/package/2006/content-types')
root=Path('/Users/lzy/Desktop/毕设')
source=root/'汇报/PPT/2026-11-05_组会汇报_SEATrack空间自相似性.pptx'
build=root/'汇报/.ppt_results_build'
with zipfile.ZipFile(source) as old,zipfile.ZipFile(build/'candidate.pptx') as new:
 files={n:new.read(n) for n in new.namelist()}
 for n in ['ppt/slides/charts/chart1.xml','ppt/slides/charts/_rels/chart1.xml.rels','ppt/embeddings/chart-data-snapshot-001.xlsx']:
  files[n]=old.read(n)
 ns='{http://schemas.openxmlformats.org/package/2006/content-types}'
 ct=E.fromstring(files['[Content_Types].xml'])
 orig=E.fromstring(old.read('[Content_Types].xml'))
 for child in orig:
  if child.attrib.get('Extension')=='xlsx' or child.attrib.get('PartName','').endswith('.xlsx'):
   if not any(c.attrib==child.attrib for c in ct):ct.append(child)
 files['[Content_Types].xml']=E.tostring(ct,encoding='utf-8',xml_declaration=True)
 with zipfile.ZipFile(build/'repaired.pptx','w',zipfile.ZIP_DEFLATED) as z:
  for n,data in files.items():z.writestr(n,data)
print('Preserved original chart XML, relationships, and workbook byte-for-byte')
