"""Merge GeoJSON SVG paths into dashboard HTML."""
import re

html_path = r'C:\Users\呼骁\.qoderwork\workspace\mr3bu0bmb7ercsv7\outputs\policy-monitor-dashboard.html'
js_path = r'C:\Users\呼骁\.qoderwork\workspace\mr3bu0bmb7ercsv7\china_map_paths.js'

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()
with open(js_path, 'r', encoding='utf-8') as f:
    js_data = f.read()

match = re.search(r'var provGeoJSON = \[(.*?)\];', js_data, re.DOTALL)
if not match:
    print("ERROR: provGeoJSON not found"); exit(1)
geojson_content = match.group(1).strip()

# === SECTION 1: Replace provMap + helpers with GeoJSON data + riskMap ===
pat1 = r'/\* ========== PROVINCE MAP \(SVG China Map\) ========== \*/.*?function latToY\(lat\)\{return \(54-lat\)\*11\.5\}'
new1 = (
    "/* ========== PROVINCE MAP (GeoJSON-derived SVG Paths) ========== */\n"
    "// Province boundary data from standard GeoJSON (Aliyun DataV), simplified via RDP\n"
    "var provGeoJSON = [" + geojson_content + "];\n\n"
    "// Risk level assignment per province\n"
    "var riskMap={\n"
    "  '天津':'high','广东':'high',\n"
    "  '北京':'moderate','上海':'moderate','江苏':'moderate','重庆':'moderate',\n"
    "  '山东':'low','宁夏':'low','内蒙古':'low','湖北':'low',\n"
    "  '浙江':'low','湖南':'low','四川':'low','辽宁':'low',\n"
    "  '海南':'low','江西':'low'\n"
    "}"
)
html, n1 = re.subn(pat1, new1, html, count=1, flags=re.DOTALL)
print(f"Section 1: {n1} replacements")

# === SECTION 2: Write renderMap JS to temp file then read back ===
# This completely avoids Python string escaping issues
import tempfile, os

render_js_content = """function renderMap(){
  var provCounts={};
  policies.forEach(function(p){
    p.provinces.forEach(function(pr){
      provCounts[pr]=(provCounts[pr]||0)+1;
    });
  });

  var mainProvs=provGeoJSON.filter(function(p){
    if(p.n==='北京'&&p.cy>300) return false;
    if(p.n==='海南'&&p.cy>450) return false;
    return true;
  }).map(function(p){
    return {n:p.n,s:p.s,paths:p.paths,cx:p.cx,cy:p.cy,
            risk:riskMap[p.n]||'none',c:provCounts[p.n]||0};
  });

  var svg='<svg viewBox="-5 0 640 440" xmlns="http://www.w3.org/2000/svg">';
  svg+='<defs>';
  svg+='<filter id="cs" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="1" stdDeviation="2" flood-opacity=".12"/></filter>';
  svg+='</defs>';
  svg+='<rect x="-5" y="0" width="640" height="440" fill="#FAFBFD" rx="8"/>';

  mainProvs.forEach(function(p){
    var rc=riskColors[p.risk]||riskColors.none;
    var strokeW=p.risk==='none'?0.6:1.5;
    var sel=curProv===p.n?' selected':'';
    p.paths.forEach(function(d){
      svg+='<path class="prov-path'+sel+'" d="'+d+'" fill="'+rc.fill+'" stroke="'+rc.stroke+'" stroke-width="'+strokeW+'" stroke-linejoin="round" data-name="'+p.n+'" data-risk="'+p.risk+'" onclick="filterByProvince(\\''+p.n+'\\',this)" title="'+p.n+'：'+p.c+'条政策（'+rc.label+'）"/>';
    });
  });

  mainProvs.forEach(function(p){
    if(p.n==='香港'||p.n==='澳门') return;
    var rc=riskColors[p.risk]||riskColors.none;
    var labelColor=p.risk==='none'?'#94A3B8':rc.textColor;
    svg+='<text class="prov-label" x="'+p.cx.toFixed(1)+'" y="'+(p.cy+2).toFixed(1)+'" fill="'+labelColor+'">'+p.s+'</text>';
  });

  mainProvs.forEach(function(p){
    if(p.c<=0) return;
    var rc=riskColors[p.risk]||riskColors.none;
    var r=6+Math.min(p.c,8)*1.8;
    svg+='<circle class="count-badge" cx="'+p.cx.toFixed(1)+'" cy="'+(p.cy-14).toFixed(1)+'" r="'+r+'" fill="'+rc.badge+'" filter="url(#cs)" data-name="'+p.n+'" onclick="filterByProvince(\\''+p.n+'\\',this)"/>';
    svg+='<text class="count-text" x="'+p.cx.toFixed(1)+'" y="'+(p.cy-14).toFixed(1)+'">'+p.c+'</text>';
  });

  svg+='<text x="500" y="425" fill="#94A3B8" font-size="7" text-anchor="middle">南海诸岛</text>';

  svg+='</svg>';
  document.getElementById('provinceMap').innerHTML=svg;
}"""

# Wait - the \\  ' in the onclick handler: in a Python """ string, \\' becomes \\'
# which writes \\' to the file. In JS source, \\' means: escaped backslash + start of new string.
# We actually want \\' in the file to be just \' (escaped single quote in JS single-quoted string).
# In Python """, \\ is a literal backslash. So \\' in Python """ becomes \' in the output.
# Let me verify: \\' in Python non-raw string → \' in output? No...
# In Python """: \\' = \\(one backslash) + '(single quote) → output is \'
# That IS correct! \' in JS single-quoted string = escaped single quote. 

pat2 = r"function renderMap\(\)\{.*?document\.getElementById\('provinceMap'\)\.innerHTML=svg;\s*\}"
html, n2 = re.subn(pat2, render_js_content, html, count=1, flags=re.DOTALL)
print(f"Section 2: {n2} replacements")

# Verify
ok = True
if 'provGeoJSON' not in html:
    print("ERROR: provGeoJSON missing"); ok = False
if 'mainProvs' not in html:
    print("ERROR: mainProvs missing"); ok = False
if n1 == 0:
    print("ERROR: Section 1 not replaced"); ok = False
if n2 == 0:
    print("ERROR: Section 2 not replaced"); ok = False

# Check for leftover old code
if 'provMap=[' in html:
    print("WARNING: old provMap array still present")
if 'function lonToX' in html:
    print("WARNING: old lonToX still present")
if 'function latToY' in html:
    print("WARNING: old latToY still present")
if "inset-box" in html and "var svg='<svg" not in html:
    pass  # might be in CSS, which is ok

if ok:
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("\nSUCCESS: Dashboard updated with GeoJSON province paths!")
    print("  - provGeoJSON with", geojson_content.count('{n:'), "province entries")
    print("  - renderMap uses <path> SVG elements")
    print("  - viewBox='-5 0 640 440'")
    print("  - South China Sea artifacts filtered")
    print("  - Risk mapping applied")
else:
    print("\nFAILED")
